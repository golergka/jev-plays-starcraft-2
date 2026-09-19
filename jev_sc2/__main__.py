"""uv run python -m jev_sc2 --map /absolute/path/to/mission.SC2Map"""
import argparse
import asyncio
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv
from openrouter.errors import PaymentRequiredResponseError
from s2clientprotocol import sc2api_pb2 as sc, error_pb2
from .sc2 import SC2, launch, find_executable
from .jev import Jev, CallBudgetReached
from .reload import PlayerLoader
from .view import make_view, validate_commands
from .camera import choose_shot

ROOT = Path(__file__).resolve().parent.parent


def result_for_player(players, player_id):
    """An ally's win or an ended clock is not proof of our mission result."""
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


async def run(args):
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
        elif event=='stopped':
            outcome['reason'] = fields['reason']
        elif event=='finished':
            outcome.update(calls=fields['calls'],cost=fields['cost'],replay=str(directory/'game.SC2Replay'))
            if outcome['status']=='incomplete' and 'reason' not in outcome:
                outcome['reason']='call budget reached' if fields['calls']>=args.max_calls else 'time limit reached'
            (directory/'result.json').write_text(json.dumps(outcome,indent=2)+'\n')
        row = {'time':time.time(), 'event':event, **fields}
        events.write(json.dumps(row)+'\n')
        if event != 'jev':
            print(json.dumps(row),flush=True)
    loader = PlayerLoader(ROOT)
    loader.refresh()
    memory = {}
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
    try:
        ping = await client.request('ping',sc.RequestPing())
        log('connected',version=ping.game_version,revision=loader.revision,
            objective=args.objective,seconds=args.seconds,max_calls=args.max_calls,
            max_age_loops=args.max_age_loops)
        attached_info = None
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
                replay = await client.request('save_replay',sc.RequestSaveReplay())
                (directory/'game.SC2Replay').write_bytes(replay.data)
                log('finished',calls=0,cost=0,run=str(directory))
                return outcome
            if client.status != sc.in_game:
                raise RuntimeError('--attach without --map needs an API game already in progress')
        info = attached_info if attached_info is not None else await client.request('game_info',sc.RequestGameInfo())
        outcome.update(map_name=info.map_name,local_map_path=info.local_map_path)
        data = await client.request('data',sc.RequestData(unit_type_id=True,ability_id=True,upgrade_id=True))
        started = time.monotonic()
        failures = 0
        empty_since = None
        last_loop = None
        clock_changed_at = time.monotonic()
        while time.monotonic()-started < args.seconds and jev.calls < args.max_calls:
            try:
                revision = loader.refresh()
                if revision:
                    log('reload',revision=revision)
            except Exception as exc:
                log('reload_error',error=str(exc),retained_revision=loader.revision)
            observation = await client.observe()
            if observation.action_errors:
                log('engine_action_error',errors=[str(e) for e in observation.action_errors])
            if observation.player_result or client.status == sc.ended:
                log('result',players=[{'player':r.player_id,'result':sc.Result.Name(r.result)}
                                     for r in observation.player_result],loop=observation.observation.game_loop,
                    api_status=sc.Status.Name(client.status))
                break
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
            decision_start = time.monotonic()
            try:
                commands = await asyncio.wait_for(loader.module.decide(view,jev,memory),3)
                failures = 0
            except CallBudgetReached:
                log('stopped',reason='Jev call budget reached')
                break
            except PaymentRequiredResponseError:
                log('stopped',reason='OpenRouter credits unavailable; replenish account credits or check the key cap')
                break
            except Exception as exc:
                log('decision_error',error=type(exc).__name__,detail=str(exc)[:200])
                failures += 1
                if failures >= 5:
                    log('stopped',reason='five consecutive decision failures')
                    break
                await asyncio.sleep(0.5)
                continue
            fresh = await client.observe()
            if fresh.player_result or client.status == sc.ended:
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
            await asyncio.sleep(max(0,args.interval-(time.monotonic()-decision_start)))
        replay = await client.request('save_replay',sc.RequestSaveReplay())
        (directory/'game.SC2Replay').write_bytes(replay.data)
        log('finished',calls=jev.calls,cost=jev.cost,run=str(directory))
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
    parser.add_argument('--opponent',action='store_true',help='Add VeryEasy Zerg AI for a melee map')
    parser.add_argument('--port',type=int,default=5001)
    parser.add_argument('--window-size',type=int,nargs=2,default=(1280,800),metavar=('WIDTH','HEIGHT'))
    parser.add_argument('--window-position',type=int,nargs=2,metavar=('X','Y'))
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
    except KeyboardInterrupt:
        print('Harness stopped. SC2 was left running.')


if __name__ == '__main__':
    main()
