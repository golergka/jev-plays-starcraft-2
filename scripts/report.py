"""Summarize measured runs without inventing a performance score."""
import collections
import json
import math
import statistics
import sys
from pathlib import Path

path = Path(sys.argv[1]) if len(sys.argv)>1 else max(Path('runs').glob('*/events.jsonl'),key=lambda p:p.stat().st_mtime)
rows = [json.loads(line) for line in path.read_text().splitlines()]
calls = [r for r in rows if r['event']=='jev']
ticks = [r for r in rows if r['event']=='tick']
latencies = sorted(r['latency_ms'] for r in calls)
decision_latencies = sorted(r['latency_ms'] for r in ticks)
choices = collections.Counter(a.get('choice','unknown') for r in calls for a in r['response']['answers'].values())
navigation = [r for r in calls if 'navigation' in r['questions']]
batches = [r for r in rows if r['event']=='decision_batch']
groups = [r for r in rows if r['event']=='group_choice']
seen_at, update_gaps = {}, []
for batch in batches:
    for tag in batch['unit_tags']:
        if tag in seen_at:
            update_gaps.append(batch['loop']-seen_at[tag])
        seen_at[tag] = batch['loop']
def distribution(tick):
    units = tick.get('units', [])
    if not units:
        return None
    return {'health_total': sum(u['health'] for u in units),
            'max_separation': round(max(math.dist(a['position'],b['position'])
                                        for a in units for b in units),1),
            'by_type':{kind:{'count':len(selected),
                             'health_total':sum(u['health'] for u in selected),
                             'center':[round(sum(u['position'][i] for u in selected)/len(selected),1) for i in (0,1)],
                             'max_separation':round(max(math.dist(a['position'],b['position']) for a in selected for b in selected),1)}
                       for kind in sorted({u['type'] for u in units})
                       for selected in [[u for u in units if u['type']==kind]]}}
print(json.dumps({
    'run':str(path), 'calls':len(calls),
    'latency_median_ms':statistics.median(latencies) if latencies else None,
    'latency_p95_ms':latencies[min(len(latencies)-1,int(len(latencies)*.95))] if latencies else None,
    'decision_median_ms':statistics.median(decision_latencies) if decision_latencies else None,
    'decision_p95_ms':decision_latencies[min(len(decision_latencies)-1,int(len(decision_latencies)*.95))] if decision_latencies else None,
    'cost_usd':sum(r['response']['usage'].get('cost',0) or 0 for r in calls),
    'actions_submitted':sum(r['submitted'] for r in ticks),
    'decision_batches':len(batches),
    'group_decisions':len(groups),
    'group_choices':dict(collections.Counter(r['choice'] for r in groups)),
    'investment_choices':dict(collections.Counter(
        'save' if r['choice']=='save' else r['projects'][int(r['choice'].split('_')[1])]
        for r in rows if r['event']=='investment_choice' and r.get('choice')
        and (r['choice']=='save' or r['choice'].startswith('project_')))),
    'producer_site_deferrals':sum(r['response']['answers'].get('producer_site',{}).get('choice')=='defer' for r in calls),
    'strategy_choices':dict(collections.Counter(r['choice'] for r in rows if r['event']=='strategy_choice')),
    'purposes_by_cohort':{cohort:dict(collections.Counter(r['choice'] for r in rows if r['event']=='purpose_choice' and r['cohort']==cohort))
                          for cohort in sorted({r['cohort'] for r in rows if r['event']=='purpose_choice'})},
    'group_calls':sum(any('individual' in q.get('criteria',{}) for q in r['questions'].values()) for r in calls),
    'choices_by_cohort':{cohort:dict(collections.Counter(r['choice'] for r in groups if r.get('cohort','whole_force')==cohort))
                         for cohort in sorted({r.get('cohort','whole_force') for r in groups})},
    'units_scheduled':len(seen_at),
    'median_scheduled_update_loops':statistics.median(update_gaps) if update_gaps else None,
    'max_scheduled_update_loops':max(update_gaps) if update_gaps else None,
    'ticks_with_zero_submissions':sum(r['submitted']==0 for r in ticks),
    'choices':dict(choices),
    'navigation_choices':dict(collections.Counter(r['response']['answers'].get('navigation',{}).get('choice','unknown') for r in navigation)),
    'sampled_navigation_choices':dict(collections.Counter(r['sampled_choice'] for r in rows if r['event']=='navigation_sample')),
    'navigation_samples':[r for r in rows if r['event']=='navigation_sample'],
    'navigation_centers':[r['state']['squad_center'] for r in navigation],
    'first_distribution':distribution(ticks[0]) if ticks else None,
    'last_distribution':distribution(ticks[-1]) if ticks else None,
    'action_result_counts':dict(collections.Counter(str(code) for r in ticks for code in r.get('action_results',[]))),
    'ticks_older_than_32_loops':sum(r['decision_age_loops']>32 for r in ticks),
    'errors':[r for r in rows if r['event'].endswith('error')],
    'results':[r for r in rows if r['event']=='result'],
    'reloads':[r for r in rows if r['event']=='reload'],
    'first_tick':ticks[0] if ticks else None, 'last_tick':ticks[-1] if ticks else None,
},indent=2))
