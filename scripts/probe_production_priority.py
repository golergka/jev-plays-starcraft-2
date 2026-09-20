"""Paired offline probe: Jev prioritizes its advisory production goals."""
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
    model = Jev(lambda *a, **k: None, 'production-priority-probe', max_calls=9)
    result = {'source': str(source), 'eligible_states': len(rows), 'pairs': [],
              'method': 'First/middle/last states with absent Barracks, advisory goals and immediate Barracks purchase offered. Jev chooses one advisory goal priority or none. Full investment menus unchanged; baseline/enriched order alternates. Nine-call ceiling, exploratory offline only, no game commands.'}
    for i, e in enumerate([rows[0], rows[len(rows)//2], rows[-1]]):
        state = e['state']
        goals = state['jev_production_intentions']['goals']
        criteria = {f'goal_{j}': g['question'] + ' Chosen intent: ' + g['chosen_intent'] for j, g in enumerate(goals)}
        criteria['none'] = 'Do not give any single production goal priority now.'
        q = {'type': 'choice', 'instructions': 'Choose which of your production goals should take priority when allocating shared resources now to complete the mission objective. This is advisory, not a purchase authorization. Purchases and saving remain separate decisions.', 'criteria': criteria}
        answer = (await model.ask(state, {'priority': q}))['priority']
        choice = answer['choice']
        if choice not in criteria:
            raise ValueError('Invalid production priority')
        enriched = {**state, 'jev_production_priority': {'answer': criteria[choice], 'meaning': 'Your advisory priority for this allocation. All purchases and saving remain available; this does not authorize or require any purchase.'}}
        pair = {'loop': state.get('game_loop'), 'priority': answer, 'priority_description': criteria[choice], 'answers': {}}
        result['pairs'].append(pair)
        for arm in (['baseline', 'priority'] if i % 2 == 0 else ['priority', 'baseline']):
            answers = await model.ask(state if arm == 'baseline' else enriched, e['questions'])
            a = answers['investment']
            pair['answers'][arm] = {'answer': a, 'description': e['questions']['investment']['criteria'][a['choice']]}
            result.update(calls=model.calls, cost_usd=model.cost)
            output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'calls': model.calls, 'cost': model.cost, 'pairs': [{'loop': p['loop'], 'goal_priority': p['priority_description'], **{k: v['description'] for k,v in p['answers'].items()}} for p in result['pairs']]}))

if __name__ == '__main__':
    asyncio.run(main())
