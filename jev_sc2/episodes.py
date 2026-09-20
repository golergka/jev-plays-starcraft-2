"""Small summaries of the player's verified, completed attempts; no map scripts."""
import json
from collections import Counter
from pathlib import Path


def previous_attempts(runs, map_path, exclude=None, limit=3):
    name = map_path.replace('\\', '/').split('/')[-1]
    summaries = []
    for result_path in sorted(Path(runs).glob('*/result.json'), reverse=True):
        if exclude and result_path.parent.resolve() == Path(exclude).resolve():
            continue
        try:
            result = json.loads(result_path.read_text())
            status = result.get('status')
            if (status not in ('victory', 'defeat')
                    or result.get('ui_verification', {}).get('result') != status
                    or result.get('local_map_path', '').replace('\\', '/').split('/')[-1] != name):
                continue
            first = last = None
            peaks, strategies, purchases, roles = Counter(), Counter(), Counter(), Counter()
            resources = {}
            investment_choices = Counter()
            peak_minerals = None
            errors = 0
            job_project = None
            job_attempts, job_accepted = Counter(), Counter()
            joined = False
            with (result_path.parent/'events.jsonl').open() as stream:
                for line in stream:
                    row = json.loads(line)
                    event = row.get('event')
                    if event == 'joined_game':
                        joined = True
                    elif event == 'restarted_game':
                        # Only the controller's verified same-map rewind counts
                        # as a fresh episode, and never after observed gameplay.
                        restart_map = str(row.get('map', '')).replace('\\', '/').split('/')[-1]
                        before, after = row.get('before_loop'), row.get('after_loop')
                        if (first is None and restart_map == name
                                and type(before) is int and type(after) is int
                                and before > after and after == 0):
                            joined = True
                        else:
                            joined = False
                            break
                    elif event == 'tick':
                        first = row['loop'] if first is None else first
                        last = row['loop']
                        counts = Counter(u['type'] for u in row['units'])
                        peaks |= counts
                    elif event == 'strategy_choice':
                        strategies[row['choice']] += 1
                    elif event == 'contribution_commitment':
                        roles[row['sampled_choice']] += 1
                    elif event == 'investment_choice':
                        choice = row.get('choice', '')
                        investment_choices['purchase' if choice.startswith('project_') else 'save_for_project' if choice.startswith('save_for_') else choice] += 1
                        if choice.startswith('project_'):
                            purchases[row['projects'][int(choice.split('_')[1])]] += 1
                    elif event == 'production_job_armed':
                        job_project = row.get('job', {}).get('target_project')
                    elif event == 'production_job_request' and job_project:
                        job_attempts[job_project] += 1
                    elif event == 'production_job_execution' and job_project:
                        job_accepted[job_project] += sum(result == 1 for result in row.get('results', []))
                    elif event == 'production_job_released':
                        job_project = None
                    elif event == 'decision_error':
                        errors += 1
                    elif event == 'jev':
                        resources = row.get('state', {}).get('resources') or resources
                        minerals = resources.get('minerals')
                        if isinstance(minerals, (int, float)):
                            peak_minerals = minerals if peak_minerals is None else max(peak_minerals, minerals)
            # Attach-only terminal segments omit earlier decisions; do not call
            # them full episodes or infer a fresh start from a small loop alone.
            if not joined or first is None or first > 128:
                continue
            summaries.append({
                'result': status, 'observed_loop_span': [first, last],
                'controller_interrupted': bool(result.get('controller_error') or
                                               result.get('controller_stop_status') == 'incomplete'),
                'controller_stop_status': result.get('controller_stop_status'),
                'peak_observed_owned_counts': dict(peaks),
                'strategy_choice_counts': dict(strategies),
                'contribution_choice_counts': dict(roles),
                'purchase_proposal_counts': dict(purchases),
                'investment_choice_counts': dict(investment_choices),
                'background_training_attempt_counts': dict(job_attempts),
                'background_training_accepted_counts': dict(job_accepted),
                'peak_observed_minerals': peak_minerals,
                'last_observed_resources': {k: resources[k] for k in
                    ('minerals', 'vespene', 'estimated_minerals_per_minute', 'food_used', 'food_cap') if k in resources},
                'decision_errors': errors,
            })
            if len(summaries) >= limit:
                break
        except (OSError, ValueError, KeyError, TypeError, IndexError):
            continue
    return {'attempts': summaries,
            'interpretation': 'Previous attempts with independently verified outcomes on the same map filename, newest first. '
            'controller_interrupted marks a known controller stop before the verified outcome; '
            'its ending may include uncontrolled play and is not a clean policy comparison. '
            'False means no recorded interruption, not proof of continuous control. '
            'Observed counts are not kills or production totals; cargo and morphing change presence. '
            'Purchase proposals and background attempts/engine acceptances are not confirmed completions. Background counts exclude the initial purchase request. Policies and timing may differ. '
            'These are measured associations, not causal lessons or recommended actions.'}
