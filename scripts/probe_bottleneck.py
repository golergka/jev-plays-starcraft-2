"""Paired offline probe: Jev diagnoses a bottleneck before purchasing."""
import asyncio
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dotenv import load_dotenv
from jev_sc2.jev import Jev

async def main():
    source, output = map(Path, sys.argv[1:3])
    rows = []
    for line in source.read_text().splitlines():
        e = json.loads(line)
        if e['event'] != 'jev' or 'investment' not in e.get('questions', {}):
            continue
        s = e['state']
        if (s.get('jev_production_intentions', {}).get('goals')
                and not s.get('selection_facts', {}).get('Barracks', {}).get('count', 0)
                and any(v.startswith('Purchase one Barracks.') for v in e['questions']['investment']['criteria'].values())):
            rows.append(e)
    if len(rows) < 3:
        raise ValueError('Need three affordable rebuilding states')
    load_dotenv(Path(__file__).resolve().parents[1] / '.env')
    model = Jev(lambda *a, **k: None, 'bottleneck-probe', max_calls=9)
    result = {'source': str(source), 'eligible_states': len(rows), 'pairs': [],
              'method': 'First/middle/last states with absent Barracks, advisory goals and immediate Barracks purchase offered. Jev chooses one bottleneck diagnosis or none from ten broad alternatives. Full investment menus unchanged; baseline/enriched order alternates. Nine-call ceiling, exploratory offline only, no game commands.'}
    for i, e in enumerate([rows[0], rows[len(rows)//2], rows[-1]]):
        state = e['state']
        criteria = {
            'income': 'Insufficient resource income limits progress.',
            'ground_combat': 'Insufficient capability to overcome ground enemies limits progress.',
            'air_combat': 'Insufficient capability to overcome flying enemies limits progress.',
            'survival': 'Inability to keep threatened owned units or structures alive limits progress.',
            'production': 'Insufficient production facilities or prerequisites limits progress.',
            'supply': 'Insufficient supply capacity limits progress.',
            'coordination': 'Positioning, movement or coordination of existing units limits progress.',
            'information': 'Insufficient information about the map or objective limits progress.',
            'interaction': 'An objective interaction or ability use limits progress.',
            'none': 'No single limiting capability can be identified from the observations.'}
        q = {'type': 'choice', 'instructions': 'Identify the most important current bottleneck preventing progress toward the primary mission objective. Diagnose from the observations, not from a preferred action. A diagnosis does not authorize an action or require a purchase.', 'criteria': criteria}
        answer = (await model.ask(state, {'priority': q}))['priority']
        choice = answer['choice']
        if choice not in criteria:
            raise ValueError('Invalid bottleneck diagnosis')
        enriched = {**state, 'jev_bottleneck_diagnosis': {'answer': criteria[choice], 'meaning': 'Your diagnosis of the current bottleneck. Consider whether a purchase would address it. All purchases and saving remain available; this does not authorize or require any purchase.'}}
        pair = {'loop': state.get('game_loop'), 'priority': answer, 'diagnosis_description': criteria[choice], 'answers': {}}
        result['pairs'].append(pair)
        for arm in (['baseline', 'priority'] if i % 2 == 0 else ['priority', 'baseline']):
            answers = await model.ask(state if arm == 'baseline' else enriched, e['questions'])
            a = answers['investment']
            pair['answers'][arm] = {'answer': a, 'description': e['questions']['investment']['criteria'][a['choice']]}
            result.update(calls=model.calls, cost_usd=model.cost)
            output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'calls': model.calls, 'cost': model.cost, 'pairs': [{'loop': p['loop'], 'diagnosis': p['diagnosis_description'], **{k: v['description'] for k,v in p['answers'].items()}} for p in result['pairs']]}))

if __name__ == '__main__':
    asyncio.run(main())
