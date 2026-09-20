"""uv run python -m jev_sc2 --map /absolute/path/to/mission.SC2Map"""
from .bookmark import BookmarkRecovery
from .episodes import previous_attempts
import argparse
import asyncio
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv
from openrouter.errors import PaymentRequiredResponseError
from s2clientprotocol import sc2api_pb2 as sc, error_pb2
from .sc2 import SC2, launch, find_executable
from .jev import Jev, CallBudgetReached
from .spend import SpendThrottled
from .reload import PlayerLoader
from .view import make_view, validate_commands
from .camera import choose_shot
from .outcome import OutcomeMonitor

ROOT = Path(__file__).resolve().parent.parent


def result_for_player(players, player_id):
    """An ally's win or an ended clock is not proof of our mission result."""
    if len(players)>1 and len({p['result'] for p in players})==1 and players[0]['result'] in {'Victory','Defeat'}:
        return 'incomplete'  # Campaign objective transitions can synthesize these results.
    own = next((p['result'] for p in players if p['player']==player_id),None)
    return {'Victory':'victory','Defeat':'defeat','Tie':'tie'}.get(own,'incomplete')


def check_map_identity(info, expected):
    actual = info.local_map_path.replace('\\','/').split('/')[-1]
    if actual.casefold()!=Path(expected).name.casefold():
        raise RuntimeError(f'Resume map mismatch: expected {Path(expected).name}, got {actual!r}')


def action_feedback(actions, results, loop, requested, age, max_age):
    failures = []
    for action, result in zip(actions, results):
        if result != error_pb2.Success:
            cmd = action.action_raw.unit_command
            failures.append({'ability_id':cmd.ability_id,'unit_tags':list(cmd.unit_tags),
                             'result':error_pb2.ActionResult.Name(result)})
    return {'loop':loop,'requested':requested,'submitted':len(actions),
            'accepted':sum(r==error_pb2.Success for r in results),
            'failures':failures,'discarded_as_stale':bool(requested and age>max_age),
            'note':'Accepted means engine accepted the request, not completed the action.'}


async def restart_attached_game(client, expected_map, log):
    """Explicit same-map retry; keep the socket for subsequent player control."""
    info = await client.request('game_info',sc.RequestGameInfo())
    check_map_identity(info,expected_map)
    before = await client.observe()
    started_at = time.time()
    reply = await client.request('restart_game',sc.RequestRestartGame())
    if reply.need_hard_reset:
        raise RuntimeError('SC2 restart requires a hard reset; no automatic relaunch')
    after = await client.observe()
    if client.status != sc.in_game:
        raise RuntimeError('SC2 restart did not enter an active game')
    if before.observation.game_loop and after.observation.game_loop >= before.observation.game_loop:
        raise RuntimeError('SC2 restart did not reset the observed game clock')
    log('restarted_game',map=info.local_map_path,before_loop=before.observation.game_loop,
        after_loop=after.observation.game_loop)
    return started_at


def observe_action_failures(observation, memory, log):
    """Retain delayed engine failures, independently of request acknowledgments."""
    loop = observation.observation.game_loop
    history = memory.setdefault('engine_action_feedback', [])
    if loop < memory.get('engine_feedback_last_loop',loop):
        history.clear()
    memory['engine_feedback_last_loop'] = loop
    history = [e for e in history if 0 <= loop-e['loop'] <= 672][-32:]
    memory['engine_action_feedback'] = history
    if not observation.action_errors:
        return
    failures = [{'ability_id':e.ability_id, 'unit_tags':[e.unit_tag],
                 'result':error_pb2.ActionResult.Name(e.result)}
                for e in observation.action_errors]
    entry = {'loop':loop, 'failures':failures,
             'note':'Delayed execution failures reported by the engine. Observation loop is not the original request loop; resolved ability may differ from Smart. No target or causal request attribution is assumed.'}
    if not history or history[-1] != entry:
        history.append(entry)
        log('engine_action_error',loop=loop,failures=failures)
    memory['engine_action_feedback'] = [e for e in history if 0 <= loop-e['loop'] <= 672][-32:]


async def run(args):
    if getattr(args,'restart',False) and (
        not args.attach or args.map or not getattr(args,'expected_map',None)):
        raise ValueError('--restart requires --attach and --expected-map, without --map')
    load_dotenv(ROOT / '.env')
    sc2root = os.getenv('SC2PATH', '/Applications/StarCraft II')
    if args.doctor:
        status = {'key_present':bool(os.getenv('OPENROUTER_API_KEY'))}
        try:
            status['executable'] = str(find_executable(sc2root))
        except FileNotFoundError as exc:
            status['executable'] = None
            status['next_step'] = str(exc)
        print(json.dumps(status,indent=2))
        if not status['key_present'] or not status['executable']:
            raise SystemExit(1)
        return
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')
    directory = ROOT / 'runs' / stamp
    directory.mkdir(parents=True)
    events = (directory/'events.jsonl').open('a',buffering=1)
    outcome = {'status':'incomplete','players':[],'player_id':None,'run':str(directory)}
    def log(event, **fields):
        if event=='result':
            outcome['players'] = fields['players']
            outcome['status'] = result_for_player(fields['players'],outcome['player_id'])
            if outcome['status']=='incomplete':
                outcome['reason']='API result does not verify campaign completion; inspect objective/UI outcome'
        elif event=='campaign_outcome':
            outcome['status'] = fields['status'] if fields.get('credit_enabled') else 'incomplete'
            outcome['verification'] = fields
            if not fields.get('credit_enabled'):
                outcome['reason'] = 'Instrumented mission ending detected; experimental build requires independent UI verification'
        elif event=='replay_unavailable':
            outcome['replay_error'] = fields['error']
        elif event=='api_bookmark_restored':
            outcome['api_bookmark_restores'] = outcome.get('api_bookmark_restores',0)+1
        elif event=='stopped':
            outcome['reason'] = fields['reason']
            if fields.get('error'):
                outcome['controller_error'] = fields['error']
        elif event=='finished':
            outcome.update(calls=fields['calls'],cost=fields['cost'],
                           replay=str(directory/'game.SC2Replay') if (directory/'game.SC2Replay').exists() else None)
            if outcome['status']=='incomplete' and 'reason' not in outcome:
                outcome['reason']='call budget reached' if fields['calls']>=args.max_calls else 'time limit reached'
            (directory/'result.json').write_text(json.dumps(outcome,indent=2)+'\n')
        row = {'time':time.time(), 'event':event, **fields}
        events.write(json.dumps(row)+'\n')
        if event != 'jev':
            print(json.dumps(row),flush=True,
                  file=sys.stderr if fields.get('severity')=='error' else sys.stdout)
    loader = PlayerLoader(ROOT)
    loader.refresh()
    budget_error = None
    memory = {"production_executor_enabled": True}
    camera_memory = {}
    jev = Jev(log, stamp, max_calls=args.max_calls)
    proc = None
    if not args.attach:
        if not args.map:
            raise ValueError('--map is required unless --attach is supplied')
        proc = launch(sc2root,args.port,(directory/'sc2.log').open('w'),
                      args.window_size, args.window_position)
    client = await SC2.connect(args.port, process=proc)
    client.log = log
    async def save_replay():
        try:
            replay = await client.request('save_replay',sc.RequestSaveReplay())
            (directory/'game.SC2Replay').write_bytes(replay.data)
        except Exception as exc:
            # QuickLoad can stop replay recording; keep the actual run result.
            log('replay_unavailable',error=str(exc))
    try:
        ping = await client.request('ping',sc.RequestPing())
        log('connected',version=ping.game_version,revision=loader.revision,
            objective=args.objective,seconds=args.seconds,max_calls=args.max_calls,
            max_age_loops=args.max_age_loops)
        attached_info = None
        restart_started_at = None
        if getattr(args,'restart',False):
            restart_started_at = await restart_attached_game(client,args.expected_map,log)
        outcome_monitor = OutcomeMonitor.for_map(args.map, time.time())
        if args.map:
            log('loading_map',map=Path(args.map).name,opponent=args.opponent)
            joined = await client.start(args.map,args.opponent,getattr(args,'race','terran').capitalize())
            outcome['player_id'] = joined.player_id
            log('joined_game')
        else:
            existing = await client.observe()
            outcome['player_id'] = existing.observation.player_common.player_id or None
            if getattr(args,'expected_map',None):
                attached_info = await client.request('game_info',sc.RequestGameInfo())
                check_map_identity(attached_info,args.expected_map)
            if client.status == sc.ended:
                log('result',players=[{'player':r.player_id,'result':sc.Result.Name(r.result)}
                                     for r in existing.player_result],source='attach_to_ended_game',
                    loop=existing.observation.game_loop,api_status=sc.Status.Name(client.status))
                await save_replay()
                log('finished',calls=0,cost=0,run=str(directory))
                return outcome
            if client.status != sc.in_game:
                raise RuntimeError('--attach without --map needs an API game already in progress')
        info = attached_info if attached_info is not None else await client.request('game_info',sc.RequestGameInfo())
        outcome.update(map_name=info.map_name,local_map_path=info.local_map_path)
        memory['previous_attempts'] = previous_attempts(ROOT/'runs', info.local_map_path, directory)
        log('episode_history_loaded', attempts=len(memory['previous_attempts']['attempts']))
        if not args.map:
            # A reconnect must keep ending telemetry. The current API map name
            # selects a local, hash-checked build; an existing ACTIVE marker may
            # arm the monitor, but an already-terminal bank alone never can.
            local_name = info.local_map_path.replace('\\','/').split('/')[-1]
            outcome_monitor = OutcomeMonitor.for_map(ROOT/'maps'/local_name, restart_started_at or 0)
        data = await client.request('data',sc.RequestData(unit_type_id=True,ability_id=True,upgrade_id=True))
        started = time.monotonic()
        failures = 0
        empty_since = None
        last_loop = None
        clock_changed_at = time.monotonic()
        bookmark = BookmarkRecovery(client,data,log,getattr(args,'api_bookmark_recovery',False))
        async def try_restore(observation):
            nonlocal last_loop, empty_since, clock_changed_at, failures
            if not await bookmark.recover(observation):
                return False
            # QuickLoad preserves the world but resets API loops; old policy
            # deadlines, tags, action feedback and camera history must be discarded.
            memory.clear()
            camera_memory.clear()
            last_loop = empty_since = None
            clock_changed_at = time.monotonic()
            failures = 0
            return True
        while time.monotonic()-started < args.seconds and jev.calls < args.max_calls:
            try:
                revision = loader.refresh()
                if revision:
                    log('reload',revision=revision)
            except Exception as exc:
                log('reload_error',error=str(exc),retained_revision=loader.revision)
            observation = await client.observe()
            observe_action_failures(observation,memory,log)
            if outcome_monitor:
                ending = outcome_monitor.poll()
                if ending:
                    log('campaign_outcome',**ending,loop=observation.observation.game_loop)
                    break
            if observation.player_result or client.status == sc.ended:
                if await try_restore(observation):
                    continue
                log('result',players=[{'player':r.player_id,'result':sc.Result.Name(r.result)}
                                     for r in observation.player_result],loop=observation.observation.game_loop,
                    api_status=sc.Status.Name(client.status))
                break
            await bookmark.maybe_save(observation)
            if observation.observation.game_loop == last_loop:
                if time.monotonic()-clock_changed_at >= 10:
                    log('stopped',reason='Game clock stalled for ten seconds; inspect pause/tutorial UI')
                    break
                await asyncio.sleep(0.2)
                continue
            last_loop = observation.observation.game_loop
            clock_changed_at = time.monotonic()
            observe_player = loader.view_module.make_view if loader.view_module else make_view
            view = await observe_player(client,observation,data,info,args.objective)
            if view['self']:
                empty_since = None
            else:
                if empty_since is None:
                    empty_since = time.monotonic()
                    log('awaiting_units',reason='No owned units; campaign cinematics can temporarily hide the force')
                if time.monotonic()-empty_since >= 90:
                    log('stopped',reason='No owned units observed for ninety seconds; inspect mission UI for outcome')
                    break
                await asyncio.sleep(0.2)
                continue
            if args.follow_camera and view['self']:
                director = loader.camera_module.choose_shot if loader.camera_module else choose_shot
                shot = director(view,camera_memory)
                if shot:
                    camera = sc.Action()
                    camera.action_raw.camera_move.center_world_space.x = shot['position'][0]
                    camera.action_raw.camera_move.center_world_space.y = shot['position'][1]
                    await client.request('action',sc.RequestAction(actions=[camera]))
                    log('camera_shot',loop=view['loop'],**shot)
            from .jobs import next_request, acknowledge_initial, cancel as cancel_job
            job_commands = next_request(view, memory, log)
            if job_commands:
                job_fresh = await client.observe()
                observe_action_failures(job_fresh,memory,log)
                ending = outcome_monitor.poll() if outcome_monitor else None
                if ending:
                    log('campaign_outcome',**ending,loop=job_fresh.observation.game_loop)
                    break
                job_age = job_fresh.observation.game_loop-view['loop']
                job_actions = (validate_commands(job_commands,view,job_fresh)
                               if not job_fresh.player_result and client.status != sc.ended
                               and 0 <= job_age <= args.max_age_loops else [])
                job_results = []
                if job_actions:
                    job_response = await client.request('action',sc.RequestAction(actions=job_actions))
                    job_results = list(job_response.result)
                log('production_job_execution',loop=view['loop'],commands=job_commands,
                    submitted=len(job_actions),results=job_results,age=job_age)
                if len(job_results) != len(job_commands) or any(r != 1 for r in job_results):
                    cancel_job(memory,log,view['loop'],'request rejected or stale; no automatic retry')
                await asyncio.sleep(0.2)
                continue
            if time.monotonic() < memory.get('spend_resume_at', 0):
                await asyncio.sleep(0.2)
                continue
            decision_start = time.monotonic()
            decision_cost_before = jev.cost
            decision_charge_before = jev.spend.charged
            try:
                commands = await asyncio.wait_for(loader.module.decide(view,jev,memory),
                                                  max(3,args.max_age_loops/22.4))
                failures = 0
            except SpendThrottled as exc:
                budget_error = exc
                log('budget_error', severity='error', error=type(exc).__name__,
                    detail=str(exc), retry_after=exc.retry_after,
                    rolling_usd=exc.spent, limit_usd=exc.limit,
                    loop=view['loop'], partial_decision_usd=max(0,jev.cost-decision_cost_before),
                    commands_discarded=True, automatic_retry=False)
                log('stopped', severity='error', error='SpendThrottled',
                    reason='Decision exceeded rolling spending allowance; fix request rate before resuming')
                break
            except CallBudgetReached:
                log('stopped',reason='Jev call budget reached')
                break
            except PaymentRequiredResponseError:
                log('stopped',reason='OpenRouter credits unavailable; replenish account credits or check the key cap')
                break
            except Exception as exc:
                if memory.get('production_batch',{}).get('executor') and not memory['production_batch'].get('armed'):
                    cancel_job(memory,log,view['loop'],'decision failed before initial request')
                log('decision_error',error=type(exc).__name__,detail=str(exc)[:200])
                failures += 1
                if failures >= 5:
                    log('stopped',reason='five consecutive decision failures')
                    break
                paid = max(0, jev.cost-decision_cost_before)
                charged = max(paid, jev.spend.charged-decision_charge_before)
                interval = max(args.interval, charged*jev.spend.window/(jev.spend.limit*0.6))
                memory['spend_resume_at'] = decision_start+interval
                log('spend_pacing', decision_usd=paid, accounted_usd=charged,
                    target_interval_seconds=interval, rolling_limit_usd=jev.spend.limit,
                    requested_interval_seconds=args.interval, pacing_budget_fraction=0.6,
                    after_decision_error=True,
                    planned_idle_seconds=max(0,decision_start+interval-time.monotonic()))
                await asyncio.sleep(0.5)
                continue
            fresh = await client.observe()
            observe_action_failures(fresh,memory,log)
            ending = outcome_monitor.poll() if outcome_monitor else None
            if ending:
                log('campaign_outcome',**ending,loop=fresh.observation.game_loop)
                break
            if fresh.player_result or client.status == sc.ended:
                if await try_restore(fresh):
                    continue
                log('result',players=[{'player':r.player_id,'result':sc.Result.Name(r.result)}
                                     for r in fresh.player_result],loop=fresh.observation.game_loop,
                    api_status=sc.Status.Name(client.status))
                break
            age = fresh.observation.game_loop-view['loop']
            actions = validate_commands(commands,view,fresh) if age <= args.max_age_loops else []
            results = []
            if actions:
                response = await client.request('action',sc.RequestAction(actions=actions))
                results = list(response.result)
            acknowledge_initial(memory,actions,results,view['loop'],log)
            feedback = action_feedback(actions,results,view['loop'],len(commands),age,args.max_age_loops)
            history = memory.setdefault('action_feedback',[])
            history.append(feedback)
            memory['action_feedback'] = history[-8:]
            log('tick',loop=view['loop'],revision=loader.revision,own_units=len(view['self']),
                units=[{k:u[k] for k in ('tag','type','position','health','health_fraction','build_progress')}
                       for u in view['self']],
                score=fresh.observation.score.score,decision_age_loops=age,
                commands=commands,submitted=len(actions),action_results=results,
                action_errors=[str(e) for e in fresh.action_errors],
                latency_ms=round((time.monotonic()-decision_start)*1000))
            # Pace completed decisions by their measured cost as the dollar
            # allowance tapers. Bursts within a decision remain permitted; the
            # shared ledger separately guards concurrent and probe spending.
            paid = max(0, jev.cost-decision_cost_before)
            # Leave room for pre-dispatch reservations and variable decision cost.
            # Admission remains fail-fast if a burst still exceeds this headroom.
            charged = max(paid, jev.spend.charged-decision_charge_before)
            interval = max(args.interval, charged*jev.spend.window/(jev.spend.limit*0.6))
            memory['spend_resume_at'] = decision_start+interval
            log('spend_pacing', decision_usd=paid, accounted_usd=charged, target_interval_seconds=interval,
                rolling_limit_usd=jev.spend.limit,
                requested_interval_seconds=args.interval, pacing_budget_fraction=0.6,
                planned_idle_seconds=max(0,decision_start+interval-time.monotonic()))
        await save_replay()
        log('finished',calls=jev.calls,cost=jev.cost,run=str(directory))
        if budget_error is not None:
            budget_error.outcome = dict(outcome)
            raise budget_error
        return outcome
    finally:
        await client.ws.close()
        events.close()
        # Keep SC2 alive: --attach can resume after harness edits or a budget stop.


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--map',help='Local .SC2Map path; single-player unless --opponent')
    parser.add_argument('--race',choices=('terran','zerg','protoss','random'),default='terran')
    parser.add_argument('--attach',action='store_true',help='Reuse an API-enabled SC2 process')
    parser.add_argument('--restart',action='store_true',help='Explicitly restart the attached mission and immediately control it; requires --expected-map and no --map')
    parser.add_argument('--expected-map',help='Require the attached API map filename to match before continuing or restarting')
    parser.add_argument('--opponent',action='store_true',help='Add VeryEasy Zerg AI for a melee map')
    parser.add_argument('--port',type=int,default=5001)
    parser.add_argument('--window-size',type=int,nargs=2,default=(1280,800),metavar=('WIDTH','HEIGHT'))
    parser.add_argument('--window-position',type=int,nargs=2,metavar=('X','Y'))
    parser.add_argument('--api-bookmark-recovery',action='store_true',help='Experimental: save periodically and restore once on anomalous all-player defeat with owned structures')
    parser.add_argument('--follow-camera',action='store_true',help='Center display camera on owned units; does not change raw policy observations')
    parser.add_argument('--seconds',type=float,default=180)
    parser.add_argument('--max-calls',type=int,default=300)
    parser.add_argument('--interval',type=float,default=0.35)
    parser.add_argument('--max-age-loops',type=int,default=32)
    parser.add_argument('--objective',default='Keep your units alive and defeat visible enemy units.')
    parser.add_argument('--doctor',action='store_true')
    args=parser.parse_args()
    try:
        asyncio.run(run(args))
    except SpendThrottled as exc:
        print(f'ERROR: {exc}. Controller stopped; no automatic retry. SC2 remains running.',file=sys.stderr)
        raise SystemExit(2) from exc
    except KeyboardInterrupt:
        print('Harness stopped. SC2 was left running.')


if __name__ == '__main__':
    main()
