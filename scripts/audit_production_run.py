"""Offline audit: distinguish model investment choices, submissions and sightings.

Usage: uv run python scripts/audit_production_run.py RUN_DIRECTORY OUTPUT_JSON
No API calls or game commands. New unit sightings are not attributed to production:
campaign reinforcements, transformations and gaps between ticks can confound them.
"""
import json
import sys
from collections import Counter
from pathlib import Path


def audit(run):
    events = [json.loads(line) for line in (run / 'events.jsonl').read_text().splitlines()]
    samples = {e['loop']: e for e in events if e['event'] == 'investment_sample'}
    top, selected = Counter(), Counter()
    for event in events:
        if event['event'] != 'investment_choice' or event['loop'] not in samples:
            continue
        def label(key):
            if key.startswith(('project_', 'batch_')):
                prefix, index = key.split('_')
                return prefix + ':' + event['projects'][int(index)]
            if key.startswith('save_for_'):
                return 'save_for:' + event['future_projects'][int(key.rsplit('_', 1)[1])]
            return key
        sample = samples[event['loop']]
        top[label(sample['top_choice'])] += 1
        selected[label(sample['sampled_choice'])] += 1
    results = Counter()
    seen = set()
    initial, later = Counter(), Counter()
    first_tick = True
    timeline = []
    for event in events:
        for action in event.get('submitted_actions', []):
            results[f"{action['ability_id']}:{action['result']}"] += 1
        if event['event'] != 'tick':
            continue
        new = [u for u in event['units'] if u['tag'] not in seen]
        (initial if first_tick else later).update(u['type'] for u in new)
        seen.update(u['tag'] for u in event['units'])
        timeline.append({'loop': event['loop'], 'owned': dict(Counter(u['type'] for u in event['units'])),
                         'newly_observed': dict(Counter(u['type'] for u in new))})
        first_tick = False
    return {'run': str(run), 'top_investments': dict(top), 'selected_investments': dict(selected),
            'submitted_command_results_by_ability': dict(results),
            'initial_observed_units': dict(initial), 'later_first_seen_units': dict(later),
            'production_job_releases': [{'loop': e['current_loop'], 'project': e['job']['target_project'],
                                        'reason': e['reason'], 'remaining_requests': e['job']['remaining']}
                                       for e in events if e['event'] == 'production_job_released'],
            'timeline': timeline,
            'limits': 'Immediate Success is not completion. First sightings are not attributed births; scripts, transformations and observation gaps can confound them. Top-choice alternatives are not a simulated counterfactual trajectory.'}


if __name__ == '__main__':
    run, output = map(Path, sys.argv[1:])
    result = audit(run)
    output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'timeline'}, indent=2))
