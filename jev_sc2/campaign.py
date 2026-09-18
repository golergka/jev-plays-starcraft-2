"""Run a declared mission sequence; only the controlled player's victory advances it."""
import argparse
import asyncio
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

from .__main__ import ROOT, run


def save_progress(path, progress):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(progress, indent=2)+'\n')
    temporary.replace(path)


async def run_sequence(manifest_path, state_path, *, call_budget=1000,
                       seconds_per_attempt=600, max_attempts=3, port=5001,
                       follow_camera=False, mission_runner=run):
    manifest_path, state_path = Path(manifest_path), Path(state_path)
    payload = manifest_path.read_bytes()
    manifest = json.loads(payload)
    missions = manifest['missions']
    ids = [m['id'] for m in missions]
    if not ids or len(ids)!=len(set(ids)):
        raise ValueError('Provide a nonempty sequence with unique mission IDs')
    digest = hashlib.sha256(payload).hexdigest()
    progress = (json.loads(state_path.read_text()) if state_path.exists() else
                {'manifest_sha256':digest,'completed':[],'attempts':[]})
    if progress['manifest_sha256']!=digest:
        raise ValueError('Manifest changed; use a new state file to avoid misattributing results')
    if progress['completed']!=ids[:len(progress['completed'])]:
        raise ValueError('Completed missions are not a prefix of this sequence')
    remaining = call_budget
    for mission in missions[len(progress['completed']):]:
        map_path = (manifest_path.parent / mission['map']).resolve()
        if not map_path.is_file():
            progress.update(status='needs_attention',reason=f'Missing map: {map_path}')
            save_progress(state_path, progress)
            return progress
        attempts = sum(a['mission']==mission['id'] for a in progress['attempts'])
        while attempts < max_attempts and remaining > 0:
            args = SimpleNamespace(doctor=False, attach=True, map=str(map_path),
                opponent=False, race=mission['race'], objective=mission['objective'],
                port=port, seconds=seconds_per_attempt, max_calls=remaining,
                follow_camera=follow_camera, max_age_loops=32, interval=.35)
            progress.update(status='running',current_mission=mission['id'])
            save_progress(state_path, progress)
            try:
                result = await mission_runner(args)
            except Exception as exc:
                progress.update(status='needs_attention',reason=f'{type(exc).__name__}: {exc}')
                save_progress(state_path, progress)
                return progress
            attempts += 1
            remaining -= result.get('calls',0)
            progress['attempts'].append({'mission':mission['id'],**result})
            if result['status']=='victory':
                progress['completed'].append(mission['id'])
                save_progress(state_path, progress)
                break
            if result['status']!='defeat':
                progress.update(status='needs_attention',reason=result.get('reason',result['status']))
                save_progress(state_path, progress)
                return progress
            # A verified defeat starts another independent Jev attempt. The
            # sequencer supplies no tactics, locations, builds or policy edits.
            save_progress(state_path, progress)
        else:
            progress.update(status='needs_attention',reason='Attempt or call budget exhausted')
            save_progress(state_path, progress)
            return progress
    progress.update(status='sequence_complete',current_mission=None)
    progress.pop('reason',None)
    save_progress(state_path, progress)
    return progress


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest',type=Path)
    parser.add_argument('--state',type=Path,default=ROOT/'runs/campaign/progress.json')
    parser.add_argument('--call-budget',type=int,default=1000)
    parser.add_argument('--seconds-per-attempt',type=float,default=600)
    parser.add_argument('--max-attempts',type=int,default=3)
    parser.add_argument('--port',type=int,default=5001)
    parser.add_argument('--follow-camera',action='store_true')
    args = parser.parse_args()
    result = asyncio.run(run_sequence(args.manifest,args.state,
        call_budget=args.call_budget,seconds_per_attempt=args.seconds_per_attempt,
        max_attempts=args.max_attempts,port=args.port,follow_camera=args.follow_camera))
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    main()
