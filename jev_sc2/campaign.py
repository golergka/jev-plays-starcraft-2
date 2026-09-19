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
                       follow_camera=False, resume_current=False, retry_stalls=False, max_age_loops=32, api_bookmark_recovery=False, mission_runner=run):
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
    if progress['completed']!=ids[:len(progress['completed'])]:
        raise ValueError('Completed missions are not a prefix of this sequence')
    if progress['manifest_sha256']!=digest:
        saved = progress.get('mission_definitions')
        completed_count = len(progress['completed'])
        if saved is None or saved[:completed_count]!=missions[:completed_count]:
            raise ValueError('Completed mission definitions changed; refusing to transfer victories')
    # Appending later missions must not erase earlier verified wins. Definitions
    # of the completed prefix remain immutable; unplayed entries may be extended.
    progress.update(manifest_sha256=digest,mission_definitions=missions)
    save_progress(state_path,progress)
    remaining = call_budget
    resume_now = resume_current
    for mission in missions[len(progress['completed']):]:
        map_path = (manifest_path.parent / mission['map']).resolve()
        if not map_path.is_file():
            progress.update(status='needs_attention',reason=f'Missing map: {map_path}')
            save_progress(state_path, progress)
            return progress
        if resume_now and (not progress['attempts'] or
                progress['attempts'][-1]['mission']!=mission['id'] or
                progress['attempts'][-1]['status']!='incomplete'):
            raise ValueError('Resume requires an incomplete checkpoint for this mission')
        attempts = sum(a['mission']==mission['id'] and not a.get('resumed',False) for a in progress['attempts'])
        while (resume_now or attempts < max_attempts) and remaining > 0:
            was_resume = resume_now
            args = SimpleNamespace(doctor=False, attach=True, map=None if was_resume else str(map_path),
                expected_map=map_path.name if was_resume else None,
                opponent=False, race=mission['race'], objective=mission['objective'],
                port=port, seconds=seconds_per_attempt, max_calls=remaining,
                follow_camera=follow_camera, max_age_loops=max_age_loops, interval=.35,
                api_bookmark_recovery=api_bookmark_recovery)
            progress.update(status='running',current_mission=mission['id'])
            progress.pop('reason',None)
            save_progress(state_path, progress)
            try:
                result = await mission_runner(args)
            except Exception as exc:
                progress.update(status='needs_attention',reason=f'{type(exc).__name__}: {exc}')
                save_progress(state_path, progress)
                return progress
            resume_now = False
            if not was_resume:
                attempts += 1
            remaining -= result.get('calls',0)
            progress['attempts'].append({'mission':mission['id'],'resumed':was_resume,**result})
            if result['status']=='victory':
                progress['completed'].append(mission['id'])
                save_progress(state_path, progress)
                break
            if (retry_stalls and result['status']=='incomplete'
                    and result.get('reason','').startswith('Game clock stalled')):
                # Administrative recovery, not a claim of defeat. Never advance
                # unknown outcomes. Existing attempt and call caps still apply.
                progress['attempts'][-1]['recovery'] = 'restart_same_mission_after_clock_stall'
                save_progress(state_path,progress)
                continue
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
    parser.add_argument('--max-age-loops',type=int,default=32,help='Discard decisions older than this many game loops; fresh command validation still applies')
    parser.add_argument('--port',type=int,default=5001)
    parser.add_argument('--api-bookmark-recovery',action='store_true')
    parser.add_argument('--follow-camera',action='store_true')
    parser.add_argument('--retry-stalls',action='store_true',help='Bounded restart of the current map after clock stalls; records unknown outcome, never advances it')
    parser.add_argument('--resume-current',action='store_true',help='Continue the checkpointed incomplete game after verifying its map')
    args = parser.parse_args()
    result = asyncio.run(run_sequence(args.manifest,args.state,
        call_budget=args.call_budget,seconds_per_attempt=args.seconds_per_attempt,
        max_attempts=args.max_attempts,port=args.port,follow_camera=args.follow_camera,resume_current=args.resume_current,retry_stalls=args.retry_stalls,max_age_loops=args.max_age_loops,api_bookmark_recovery=args.api_bookmark_recovery))
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    main()
