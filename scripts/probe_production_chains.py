"""Offline test of conditional two-step production plans versus single purchases."""
import asyncio
import copy
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dotenv import load_dotenv
from jev_sc2.jev import Jev


def chains(state, questions, historical):
    criteria = questions['investment']['criteria']
    plans = {}
    for producer, controls in sorted(state.get('observed_capabilities_by_type', {}).items()):
        if state.get('selection_facts', {}).get(producer, {}).get('count', 0):
            continue
        purchases = [(k, v) for k, v in criteria.items() if v.startswith(f'Purchase one {producer}.')]
        if not purchases:
            continue
        first_key, first_description = purchases[0]
        for target in sorted({label[6:] for label in controls if label.startswith('Train ')}):
            facts = historical.get(target)
            if facts is None:
                continue
            plans[f'chain_{len(plans)}'] = {
                'producer': producer, 'target': target, 'first_purchase_key': first_key,
                'description': f'Conditional two-step plan: purchase one {producer}, then request training of one {target} from it when complete, affordable and executable. Reserve subsequent new purchases for this target for at most 2016 game loops; existing queues and repairs continue. Release the plan if the producer is lost, the strategy changes, or the deadline expires. The training control was observed previously; current prerequisites or attached addons may be missing, so this plan may expire without producing the unit. No extra prerequisites will be built automatically. First step: ' + first_description + ' Second-step previously observed unit catalog: ' + json.dumps(facts, sort_keys=True)}
    return plans


async def main():
    source, output = map(Path, sys.argv[1:3])
    eligible = []
    historical = {}
    for line in source.read_text().splitlines():
        e = json.loads(line)
        if e['event'] != 'jev':
            continue
        s = e['state']
        # Only facts already exposed in model requests; no future observations.
        historical.update(s.get('unit_type_facts', {}))
        historical.update(s.get('historical_production_type_facts', {}))
        if ('investment' in e.get('questions', {})
            and not s.get('selection_facts', {}).get('Barracks', {}).get('count', 0)
            and any(v.startswith('Purchase one Barracks.') for v in e['questions']['investment']['criteria'].values())):
            eligible.append((e, copy.deepcopy(historical)))
    if len(eligible) < 3:
        raise ValueError('Need three affordable rebuilding states')
    load_dotenv(Path(__file__).resolve().parents[1] / '.env')
    model = Jev(lambda *a, **k: None, 'production-chain-probe', max_calls=6)
    result = {'source': str(source), 'eligible_states': len(eligible), 'pairs': [],
              'method': 'First/middle/last affordable absent-Barracks states. Preserve every original option and add conditional producer-then-one-unit plans for all absent producers with an immediate purchase and previously observed Train controls/catalog. Historical facts accumulated only through each sample. Same state, alternate baseline/chain order, six calls maximum. No plan execution; selection and feasibility are separate questions.'}
    for i, (e, historical) in enumerate([eligible[0], eligible[len(eligible)//2], eligible[-1]]):
        plans = chains(e['state'], e['questions'], historical)
        expanded = copy.deepcopy(e['questions'])
        expanded['investment']['criteria'].update({k:p['description'] for k,p in plans.items()})
        expanded['investment']['instructions'] += ' Conditional two-step plans are also available; their complete effects and limitations are stated in each option.'
        pair = {'loop': e['state'].get('game_loop'), 'plans': plans, 'answers': {}}
        result['pairs'].append(pair)
        for arm in (['baseline', 'chains'] if i % 2 == 0 else ['chains', 'baseline']):
            questions = e['questions'] if arm == 'baseline' else expanded
            answer = (await model.ask(e['state'], questions))['investment']
            pair['answers'][arm] = {'answer': answer, 'description': questions['investment']['criteria'][answer['choice']]}
            result.update(calls=model.calls, cost_usd=model.cost)
            output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'calls': model.calls, 'cost': model.cost, 'pairs': [{'loop': p['loop'], 'plans': len(p['plans']), **{k:v['description'][:120] for k,v in p['answers'].items()}} for p in result['pairs']]}))

if __name__ == '__main__':
    asyncio.run(main())
