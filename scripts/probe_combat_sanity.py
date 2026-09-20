"""Offline synthetic controls: explicit outcomes, not campaign orders or a simulator."""
import asyncio
import json
import math
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dotenv import load_dotenv
from jev_sc2.jev import Jev
from jev_sc2.order_scores import RATINGS

CASES = [
    {'name': 'immediate_threat', 'state': {
        'objective': 'Keep the owned structure alive through the next turn.',
        'rules': 'Synthetic one-turn control, not StarCraft mechanics. The listed outcomes are certain. Only the chosen action occurs.',
        'structure_health': 5, 'enemy_damage_next_turn': 10,
        'options': {'attack': 'Eliminates the enemy before it can fire; the structure remains alive.',
                    'move': 'Moves the defender away; the enemy destroys the structure.',
                    'hold': 'Takes no action; the enemy destroys the structure.'}}, 'expected': 'attack'},
    {'name': 'hazard_escape', 'state': {
        'objective': 'Keep the owned unit alive through the next turn.',
        'rules': 'Synthetic one-turn control, not StarCraft mechanics. The listed outcomes are certain. Only the chosen action occurs.',
        'unit_health': 5, 'hazard_damage_next_turn': 10,
        'options': {'attack': 'Fires at an invulnerable target without moving; the hazard kills the owned unit.',
                    'move': 'Leaves the hazard before it triggers; the owned unit survives.',
                    'hold': 'Stays in the hazard; the owned unit dies.'}}, 'expected': 'move'},
    {'name': 'safe_wait', 'state': {
        'objective': 'Keep the owned unit alive through the next turn.',
        'rules': 'Synthetic one-turn control, not StarCraft mechanics. The listed outcomes are certain. Only the chosen action occurs.',
        'options': {'attack': 'Attacks an invulnerable target that retaliates and kills the owned unit.',
                    'move': 'Moves into a lethal hazard; the owned unit dies.',
                    'hold': 'Remains in the safe location; the owned unit survives.'}}, 'expected': 'hold'},
]

async def main():
    load_dotenv(Path(__file__).resolve().parents[1]/'.env')
    output = Path(sys.argv[1])
    model = Jev(lambda *a, **k: None, 'combat-sanity-control', max_calls=6)
    result = {'scope': 'Synthetic explicit one-turn outcomes. Passing is necessary elementary comprehension evidence, not evidence of SC2 competence or rollout prediction.', 'cases': []}
    for i, case in enumerate(CASES):
        state = case['state']
        item = {**case}
        async def choice():
            item['choice'] = (await model.ask(state, {'order': {
                'type': 'choice', 'instructions': 'Choose the action that best achieves the stated objective under the stated rules.',
                'criteria': state['options']}}))['order']
        async def scores():
            item['scores'] = await model.ask(state, {key: {
                'type': 'score', 'instructions': 'Rate how well this action achieves the stated objective under the stated rules. Action: '+description,
                'criteria': RATINGS} for key, description in state['options'].items()})
            values = {k:v.get('score') for k,v in item['scores'].items()}
            if set(values) != set(state['options']) or any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or not 0<=v<=4 for v in values.values()):
                raise ValueError('Invalid score response')
            best = max(values.values())
            item['highest_rated'] = [k for k,v in values.items() if v == best]
        for action in ([choice,scores] if i%2==0 else [scores,choice]):
            await action()
        result['cases'].append(item)
        result.update(calls=model.calls,cost=model.cost)
        output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'calls':model.calls,'cost':model.cost,'results':[{'name':c['name'],'expected':c['expected'],'choice':c['choice']['choice'],'highest_rated':c['highest_rated']} for c in result['cases']]}))

if __name__ == '__main__':
    asyncio.run(main())
