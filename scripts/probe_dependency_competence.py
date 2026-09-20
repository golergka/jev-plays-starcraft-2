"""Synthetic dependency controls, not campaign observations or player policy."""
import asyncio
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dotenv import load_dotenv
from jev_sc2.jev import Jev


def cases():
    for vocabulary, worker, producer, soldier in [
        ('sc2_names', 'SCV', 'Barracks', 'Marine'),
        ('abstract_names', 'Unit A', 'Facility B', 'Unit C'),
    ]:
        for task in ('worker', 'missing_producer', 'existing_producer'):
            existing = task == 'existing_producer'
            state = {
                'scenario': 'Synthetic deterministic dependency test. These stipulated rules override any real-game knowledge. This is not a live game observation.',
                'objective': f'Obtain exactly one additional {worker if task == "worker" else soldier} within the next two actions.',
                'resources': {'credits': 200},
                'owned': {worker: 1, producer: int(existing), soldier: 0},
                'rules': [
                    'Each action completes immediately. No income, refunds, combat, losses, movement, upgrades, supply constraints or other requirements exist.',
                    f'Buying one {worker} costs 50 credits and has no other effects.',
                    f'Buying one {producer} costs 150 credits and has no other effects.',
                    f'Training one {soldier} costs 50 credits and requires owning at least one {producer}. Training does not consume the producer.',
                    'Waiting uses an action and changes nothing.',
                    'Only the first action is being selected. A second action may be selected afterward using the same rules and remaining credits.',
                ],
            }
            criteria = {
                'a': f'Buy one {worker} now.',
                'b': 'Wait without purchasing anything.',
                'c': f'Buy one {producer} now.',
            }
            if existing:
                criteria['d'] = f'Train one {soldier} now.'
            # Goal worker: buying producer first also leaves enough to buy worker.
            # Tie-break immediate goal attainment makes the expected action unique.
            state['tie_break'] = 'If multiple first actions permit success, choose the one that obtains the required unit in the fewest actions.'
            yield {'id': vocabulary + '_' + task, 'state': state,
                   'questions': {'first_action': {'type': 'choice', 'instructions': 'Choose the first action to achieve the stated objective under the stated rules and tie-break.', 'criteria': criteria}},
                   'expected': 'a' if task == 'worker' else 'd' if existing else 'c'}


async def main():
    output = Path(sys.argv[1])
    load_dotenv(Path(__file__).resolve().parents[1] / '.env')
    model = Jev(lambda *a, **k: None, 'dependency-competence-probe', max_calls=6)
    result = {'method': 'Six synthetic deterministic controls: worker target, missing producer, existing producer; SC2 names and neutral names. Full state and questions retained. No live policy or orders. Expected first action derived from explicit toy rules, not StarCraft strategy.', 'cases': []}
    for case in cases():
        answer = (await model.ask(case['state'], case['questions']))['first_action']
        result['cases'].append({**case, 'answer': answer, 'correct': answer['choice'] == case['expected']})
        result.update(calls=model.calls, cost_usd=model.cost)
        output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'calls': model.calls, 'cost': model.cost, 'results': [{'id': c['id'], 'choice': c['answer']['choice'], 'expected': c['expected'], 'correct': c['correct']} for c in result['cases']]}))

if __name__ == '__main__':
    asyncio.run(main())
