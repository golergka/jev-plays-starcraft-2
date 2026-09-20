"""Offline diagnostic only: imposed unit goal in recorded recovery states."""
import asyncio
import copy
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dotenv import load_dotenv
from jev_sc2.jev import Jev

async def main():
    source, output = map(Path, sys.argv[1:3])
    eligible = []
    for line in source.read_text().splitlines():
        e = json.loads(line)
        if e['event'] != 'jev' or 'investment' not in e.get('questions', {}):
            continue
        if (not e['state'].get('selection_facts', {}).get('Barracks', {}).get('count', 0)
                and any(v.startswith('Purchase one Barracks.') for v in e['questions']['investment']['criteria'].values())):
            eligible.append(e)
    if len(eligible) < 3:
        raise ValueError('Need three affordable rebuilding states')
    load_dotenv(Path(__file__).resolve().parents[1] / '.env')
    model = Jev(lambda *a, **k: None, 'explicit-production-goal-probe', max_calls=6)
    result = {'source': str(source), 'pairs': [], 'method': 'First/middle/last affordable absent-Barracks states. Same full observations and every purchase option. Treatment replaces investment instructions with an explicit Marine goal, superseding recorded goals for this offline diagnostic only. Alternate arms, six-call ceiling. No commands or policy deployment; this is a deliberately imposed goal to separate goal execution from goal selection.'}
    for i, e in enumerate([eligible[0], eligible[len(eligible)//2], eligible[-1]]):
        treatment = copy.deepcopy(e['questions'])
        treatment['investment']['instructions'] = (
            'For this offline diagnostic only, the goal is to obtain one additional owned Marine as soon as feasible. '
            'This diagnostic goal supersedes the recorded mission objective, strategic priority and advisory production intentions for this question. '
            'Choose the next purchase, bounded batch or saving action toward that goal using the observed resources, owned units and available controls. '
            'All game facts remain as recorded; do not assume additional units, income or production controls. '
            'This decision selects the next new purchase. Other selections cannot start additional purchases in this review, '
            'but worker repairs can still consume shared minerals. Existing queues continue.')
        pair = {'loop': e['state'].get('game_loop'), 'treatment_instructions': treatment['investment']['instructions'], 'answers': {}}
        result['pairs'].append(pair)
        for arm in (['baseline', 'explicit_goal'] if i % 2 == 0 else ['explicit_goal', 'baseline']):
            questions = e['questions'] if arm == 'baseline' else treatment
            answer = (await model.ask(e['state'], questions))['investment']
            pair['answers'][arm] = {'answer': answer, 'description': questions['investment']['criteria'][answer['choice']]}
            result.update(calls=model.calls, cost_usd=model.cost)
            output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'calls': model.calls, 'cost': model.cost, 'pairs': [{'loop': p['loop'], **{k:v['description'][:100] for k,v in p['answers'].items()}} for p in result['pairs']]}))

if __name__ == '__main__':
    asyncio.run(main())
