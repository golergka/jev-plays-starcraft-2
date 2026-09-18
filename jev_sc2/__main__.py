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
from s2clientprotocol import sc2api_pb2 as sc
from .sc2 import SC2, launch, find_executable
from .jev import Jev, CallBudgetReached
from .reload import PlayerLoader
from .view import make_view, validate_commands

ROOT = Path(__file__).resolve().parent.parent


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
    def log(event, **fields):
        row = {'time':time.time(), 'event':event, **fields}
        events.write(json.dumps(row)+'\n')
        if event != 'jev':
            print(json.dumps(row),flush=True)
    loader = PlayerLoader(ROOT)
    loader.refresh()
    memory = {}
    jev = Jev(log, stamp, max_calls=args.max_calls)
    proc = None
    if not args.attach:
        if not args.map:
            raise ValueError('--map is required unless --attach is supplied')
        proc = launch(sc2root,args.port,(directory/'sc2.log').open('w'),
                      args.window_size, args.window_position)
    client = await SC2.connect(args.port, process=proc)
    try:
        ping = await client.request('ping',sc.RequestPing())
        log('connected',version=ping.game_version,revision=loader.revision,
            objective=args.objective,seconds=args.seconds,max_calls=args.max_calls,
            max_age_loops=args.max_age_loops)
        if args.map:
            log('loading_map',map=Path(args.map).name,opponent=args.opponent)
            await client.start(args.map,args.opponent)
            log('joined_game')
        else:
            await client.observe()
            if client.status != sc.in_game:
                raise RuntimeError('--attach without --map needs an API game already in progress')
        info = await client.request('game_info',sc.RequestGameInfo())
        data = await client.request('data',sc.RequestData(unit_type_id=True,ability_id=True))
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
                                     for r in observation.player_result])
                break
            if observation.observation.game_loop == last_loop:
                if time.monotonic()-clock_changed_at >= 10:
                    log('stopped',reason='Game clock stalled for ten seconds; inspect pause/tutorial UI')
                    break
                await asyncio.sleep(0.2)
                continue
            last_loop = observation.observation.game_loop
            clock_changed_at = time.monotonic()
            view = await make_view(client,observation,data,info,args.objective)
            empty_since = None if view['self'] else (empty_since or time.monotonic())
            if empty_since is not None and time.monotonic()-empty_since >= 10:
                log('stopped',reason='No owned units observed for ten seconds; inspect mission UI for outcome')
                break
            if args.follow_camera and view['self']:
                # Presentation only: raw observations/actions do not depend on camera.
                camera = sc.Action()
                camera.action_raw.camera_move.center_world_space.x = sum(u['position'][0] for u in view['self'])/len(view['self'])
                camera.action_raw.camera_move.center_world_space.y = sum(u['position'][1] for u in view['self'])/len(view['self'])
                await client.request('action',sc.RequestAction(actions=[camera]))
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
                                     for r in fresh.player_result])
                break
            age = fresh.observation.game_loop-view['loop']
            actions = validate_commands(commands,view,fresh) if age <= args.max_age_loops else []
            results = []
            if actions:
                response = await client.request('action',sc.RequestAction(actions=actions))
                results = list(response.result)
            log('tick',loop=view['loop'],revision=loader.revision,own_units=len(view['self']),
                units=[{k:u[k] for k in ('tag','type','position','health','health_fraction')}
                       for u in view['self']],
                score=fresh.observation.score.score,decision_age_loops=age,
                commands=commands,submitted=len(actions),action_results=results,
                action_errors=[str(e) for e in fresh.action_errors],
                latency_ms=round((time.monotonic()-decision_start)*1000))
            await asyncio.sleep(max(0,args.interval-(time.monotonic()-decision_start)))
        replay = await client.request('save_replay',sc.RequestSaveReplay())
        (directory/'game.SC2Replay').write_bytes(replay.data)
        log('finished',calls=jev.calls,cost=jev.cost,run=str(directory))
    finally:
        await client.ws.close()
        events.close()
        # Keep SC2 alive: --attach can resume after harness edits or a budget stop.


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--map',help='Local .SC2Map path; single-player unless --opponent')
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
