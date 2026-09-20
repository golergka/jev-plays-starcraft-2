"""Read-only comparison of completed opening windows; no model or game calls."""
import argparse
import json
import statistics
from pathlib import Path


def audit(path, end_loop):
    rows = [json.loads(line) for line in Path(path).read_text().splitlines()]
    observed = max((r.get('loop', 0) for r in rows), default=0)
    if observed < end_loop:
        raise ValueError(f'{path}: observed through {observed}, need {end_loop}')
    calls = [r for r in rows if r.get('event') == 'jev'
             and isinstance(r.get('state', {}).get('game_loop'), int)
             and 0 <= r['state']['game_loop'] <= end_loop]
    combat = sorted({r['state']['game_loop'] for r in calls
                     if 'MobileCombat' in r.get('questions', {})})
    gaps = [b-a for a, b in zip(combat, combat[1:])]
    costs = [r['response'].get('usage', {}).get('cost') for r in calls]
    if any(not isinstance(c, (int, float)) for c in costs):
        raise ValueError('Missing request cost; cannot report a complete sum')
    return {'source': str(path), 'through_loop': end_loop,
            'loop_located_requests': len(calls), 'cost_usd': sum(costs),
            'combat_review_loops': combat,
            'mean_combat_gap_loops': statistics.mean(gaps) if gaps else None,
            'diagnosis_requests': sum('bottleneck' in r['questions'] for r in calls),
            'unlocated_requests_in_entire_file': sum(r.get('event') == 'jev' and
                not isinstance(r.get('state', {}).get('game_loop'), int) for r in rows),
            'scope': 'Only loop-located successful request records; unlocated requests are not assigned to this window. MobileCombat measures that named selection only, not every possible combat group.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('logs', nargs='+', type=Path)
    parser.add_argument('--through-loop', type=int, default=1800)
    args = parser.parse_args()
    print(json.dumps([audit(p, args.through_loop) for p in args.logs], indent=2))
