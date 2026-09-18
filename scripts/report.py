"""Summarize measured runs without inventing a performance score."""
import collections
import json
import statistics
import sys
from pathlib import Path

path = Path(sys.argv[1]) if len(sys.argv)>1 else sorted(Path('runs').glob('*/events.jsonl'))[-1]
rows = [json.loads(line) for line in path.read_text().splitlines()]
calls = [r for r in rows if r['event']=='jev']
ticks = [r for r in rows if r['event']=='tick']
latencies = sorted(r['latency_ms'] for r in calls)
choices = collections.Counter(a.get('choice','unknown') for r in calls for a in r['response']['answers'].values())
print(json.dumps({
    'run':str(path), 'calls':len(calls),
    'latency_median_ms':statistics.median(latencies) if latencies else None,
    'latency_p95_ms':latencies[min(len(latencies)-1,int(len(latencies)*.95))] if latencies else None,
    'cost_usd':sum(r['response']['usage'].get('cost',0) or 0 for r in calls),
    'actions_submitted':sum(r['submitted'] for r in ticks),
    'ticks_with_zero_submissions':sum(r['submitted']==0 for r in ticks),
    'choices':dict(choices),
    'errors':[r for r in rows if r['event'].endswith('error')],
    'results':[r for r in rows if r['event']=='result'],
    'reloads':[r for r in rows if r['event']=='reload'],
    'first_tick':ticks[0] if ticks else None, 'last_tick':ticks[-1] if ticks else None,
},indent=2))
