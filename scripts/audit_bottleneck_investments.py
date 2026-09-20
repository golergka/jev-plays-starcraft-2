"""Read-only join of Jev diagnoses, investment answers and sampled intentions."""
import json
import sys
from pathlib import Path


def audit(source):
    rows = []
    pending = {}
    calls = cost = 0
    for line in source.read_text().splitlines():
        try:
            e = json.loads(line)
        except json.JSONDecodeError:
            continue  # A running writer may not have finished the final line.
        if e['event'] == 'jev':
            calls += 1
            cost += e['response'].get('usage', {}).get('cost') or 0
            if 'investment' not in e.get('questions', {}):
                continue
            state = e['state']; loop = state.get('game_loop')
            criteria = e['questions']['investment']['criteria']
            answer = e['response']['answers']['investment']
            choice = answer.get('choice')
            row = {'loop': loop, 'diagnosis': state.get('jev_bottleneck_diagnosis'),
                   'resources': state.get('resources'),
                   'owned_counts': {k:v.get('count', 0) for k,v in state.get('selection_facts', {}).items()},
                   'top_choice': choice, 'top_description': criteria.get(choice),
                   'sampled_choice': None, 'sampled_description': None}
            rows.append(row); pending[loop] = (row, criteria)
        elif e['event'] == 'investment_sample' and e.get('loop') in pending:
            row, criteria = pending[e['loop']]
            row.update(sampled_choice=e['sampled_choice'], sampled_description=criteria.get(e['sampled_choice']))
    return {'source': str(source), 'calls': calls, 'cost_usd': cost,
            'note': 'Snapshot of model investment reviews. Top choice and sampled intention differ; neither establishes command acceptance, completed production or mission outcome. Carried commitments without a new model investment review are not listed.',
            'reviews': rows}


if __name__ == '__main__':
    result = audit(Path(sys.argv[1]))
    if len(sys.argv) > 2:
        Path(sys.argv[2]).write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'calls': result['calls'], 'cost_usd': result['cost_usd'], 'reviews': [
        {'loop': r['loop'], 'diagnosis': (r['diagnosis'] or {}).get('answer'),
         'top': (r['top_description'] or '')[:80], 'sampled': (r['sampled_description'] or '')[:80]}
        for r in result['reviews'][-8:]]}))
