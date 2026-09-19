"""Summarize measured runs without inventing a performance score."""
import collections
import json
import math
import statistics
import sys
from s2clientprotocol import error_pb2
from pathlib import Path

path = Path(sys.argv[1]) if len(sys.argv)>1 else max(Path('runs').glob('*/events.jsonl'),key=lambda p:p.stat().st_mtime)
rows = [json.loads(line) for line in path.read_text().splitlines()]
calls = [r for r in rows if r['event']=='jev']
spend_window = collections.deque()
window_cost = peak_window_cost = 0.0
for call in sorted(calls, key=lambda r:r['time']):
    while spend_window and spend_window[0][0] <= call['time']-300:
        window_cost -= spend_window.popleft()[1]
    cost = call['response']['usage'].get('cost',0) or 0
    spend_window.append((call['time'],cost))
    window_cost += cost
    peak_window_cost = max(peak_window_cost,window_cost)
paced = [r for r in rows if r['event']=='spend_pacing']
ticks = [r for r in rows if r['event']=='tick']
age_limit = next((r['max_age_loops'] for r in rows if r['event']=='connected' and 'max_age_loops' in r),32)
latencies = sorted(r['latency_ms'] for r in calls)
decision_latencies = sorted(r['latency_ms'] for r in ticks)
choices = collections.Counter(a.get('choice','unknown') for r in calls for a in r['response']['answers'].values())
navigation = [r for r in calls if 'navigation' in r['questions']]
batches = [r for r in rows if r['event']=='decision_batch']
groups = [r for r in rows if r['event']=='group_choice']
resource_samples = [r['state']['resources'] for r in calls if isinstance(r['state'].get('resources'),dict)]
income_samples = [r['estimated_minerals_per_minute'] for r in resource_samples
                  if r.get('estimated_minerals_per_minute') is not None]
commitments = [r for r in rows if r['event']=='contribution_commitment']
outcome_path = path.parent/'result.json'
recorded_outcome = json.loads(outcome_path.read_text()) if outcome_path.is_file() else None
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
    'spend_governor': {
        'scope':'This run only; excludes other runs/probes and unresolved reservations. Shared admission uses the SQLite ledger.',
        'peak_actual_usd_in_any_300_seconds':round(peak_window_cost,9),
        'budget_failure_events':sum(r['event']=='budget_error' for r in rows),
        'planned_idle_seconds':sum(r.get('planned_idle_seconds',0) for r in paced) if any('planned_idle_seconds' in r for r in paced) else None,
        'max_target_decision_interval_seconds':max((r['target_interval_seconds'] for r in paced),default=None),
        'throttle_events':sum(r['event']=='spend_throttled' for r in rows),
        'latest_limit_usd_per_300_seconds':next((r['rolling_limit_usd'] for r in reversed(paced)),None),
        'median_target_decision_interval_seconds':statistics.median(r['target_interval_seconds'] for r in paced) if paced else None,
    },
    'recorded_outcome':recorded_outcome,
    'latest_observed_resources':resource_samples[-1] if resource_samples else None,
    'max_observed_mineral_income_estimate_per_minute':max(income_samples) if income_samples else None,
    'contribution_sampling':{
        'reviews':len(commitments),
        'departures_from_top_choice':sum(r.get('sampled_choice')!=r.get('top_choice') for r in commitments),
        'top_to_sampled':dict(collections.Counter(str(r.get('top_choice'))+' -> '+str(r.get('sampled_choice')) for r in commitments)),
        'note':'Role sampling diagnostic, not evidence that either choice is tactically better.'},
    'contribution_commitments':{key:dict(collections.Counter(r.get('sampled_choice') for r in commitments if r['question']==key))
                              for key in sorted({r['question'] for r in commitments})},
    'resource_category_choices':dict(collections.Counter(r.get('choice') for r in rows if r['event']=='resource_category_choice')),
    'latest_observed_completed_upgrades':next((r['state']['completed_upgrades'] for r in reversed(calls) if 'completed_upgrades' in r['state']),None),
    'support_executor_choices':dict(collections.Counter(r.get('choice') for r in rows if r['event']=='support_assignment')),
    'camera_shot_reasons':dict(collections.Counter(r['reason'] for r in rows if r['event']=='camera_shot')),
    'latency_median_ms':statistics.median(latencies) if latencies else None,
    'latency_p95_ms':latencies[min(len(latencies)-1,int(len(latencies)*.95))] if latencies else None,
    'decision_median_ms':statistics.median(decision_latencies) if decision_latencies else None,
    'decision_p95_ms':decision_latencies[min(len(decision_latencies)-1,int(len(decision_latencies)*.95))] if decision_latencies else None,
    'cost_usd':sum(r['response']['usage'].get('cost',0) or 0 for r in calls),
    'actions_submitted':sum(r['submitted'] for r in ticks),
    'decision_batches':len(batches),
    'routine_execution_questions_avoided':sum(r['event']=='routine_execution' and r.get('avoided_concrete_question',False) for r in rows),
    'group_decisions':len(groups),
    'group_choices':dict(collections.Counter(r['choice'] for r in groups)),
    'investment_choices':dict(collections.Counter(
        'save' if r['choice']=='save' else r['projects'][int(r['choice'].split('_')[1])]
        for r in rows if r['event']=='investment_choice' and r.get('choice')
        and (r['choice']=='save' or r['choice'].startswith('project_')))),
    'saving_targets':dict(collections.Counter(r.get('future_projects',[])[int(r['choice'].split('_')[-1])]
                         for r in rows if r['event']=='investment_choice' and (r.get('choice') or '').startswith('save_for_'))),
    'investment_commitment_waits':sum(r['event']=='investment_wait' for r in rows),
    'investment_commitment_requests':dict(collections.Counter(r['target_project'] for r in rows if r['event']=='investment_plan_ready')),
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
    'action_result_names':dict(collections.Counter(error_pb2.ActionResult.Name(code) for r in ticks for code in r.get('action_results',[]))),
    'action_result_counts':dict(collections.Counter(str(code) for r in ticks for code in r.get('action_results',[]))),
    'configured_max_age_loops':age_limit,
    'ticks_older_than_configured_limit':sum(r['decision_age_loops']>age_limit for r in ticks),
    'submitted_commands_from_decisions_older_than_32_loops':sum(r['submitted'] for r in ticks if r['decision_age_loops']>32),
    'ticks_older_than_32_loops':sum(r['decision_age_loops']>32 for r in ticks),
    'request_rejections':{
        'total':sum(r['event']=='jev_request_rejected' for r in rows),
        'single_question':sum(r['event']=='jev_request_rejected' and r.get('question_count')==1 for r in rows),
        'max_state_chars':max((r.get('state_chars',0) for r in rows if r['event']=='jev_request_rejected'),default=0),
        'question_names':dict(collections.Counter(k for r in rows if r['event']=='jev_request_rejected'
                                                  for k in r.get('question_chars',{})))},
    'request_splits_by_reason':dict(collections.Counter(r.get('reason','size_heuristic') for r in rows if r['event']=='jev_request_split')),
    'errors':[r for r in rows if r['event'].endswith('error')],
    'results':[r for r in rows if r['event']=='result'],
    'reloads':[r for r in rows if r['event']=='reload'],
    'first_tick':ticks[0] if ticks else None, 'last_tick':ticks[-1] if ticks else None,
},indent=2))
