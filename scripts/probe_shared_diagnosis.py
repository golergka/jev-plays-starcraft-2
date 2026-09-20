"""Replay order-family choices with Jev's preceding, still-valid diagnosis."""
import asyncio
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dotenv import load_dotenv
from jev_sc2.jev import Jev

async def main():
    source, output = map(Path, sys.argv[1:3])
    eligible = []; diagnosis = None
    for line in source.read_text().splitlines():
        e = json.loads(line)
        if e['event'] == 'bottleneck_diagnosis':
            diagnosis = e
        if e['event'] != 'jev' or not diagnosis:
            continue
        q = e.get('questions', {}).get('MobileCombat', {})
        s = e['state']; loop = s.get('game_loop', -1)
        if ('regroup' in q.get('criteria', {})
                and diagnosis['loop'] <= loop < diagnosis['review_at']
                and diagnosis['strategy'] == s.get('strategy_chosen_by_jev', {}).get('choice')
                and diagnosis['choice'] in ('ground_combat', 'survival')):
            eligible.append((e, dict(diagnosis)))
    if len(eligible) < 3:
        raise ValueError('Need three eligible family reviews')
    load_dotenv(Path(__file__).resolve().parents[1] / '.env')
    model = Jev(lambda *a, **k: None, 'shared-diagnosis-probe', max_calls=6)
    result = {'source': str(source), 'eligible_states': len(eligible), 'pairs': [], 'method': 'First/middle/last MobileCombat order-family reviews with an already logged unexpired ground-combat/survival diagnosis and matching strategy. Same full questions/options/state except sharing that Jev diagnosis. No future observations or root-chosen diagnosis. Alternating arms; six-call ceiling; offline only.'}
    for i, (e, d) in enumerate([eligible[0], eligible[len(eligible)//2], eligible[-1]]):
        added = {'answer': d['description'], 'chosen_at_loop': d['loop'], 'review_at_loop': d['review_at'], 'meaning': 'Your previously selected bottleneck diagnosis for the same observed mission. Consider it alongside the current observations when selecting orders. It does not require an action or eliminate any offered order.'}
        state = {**e['state'], 'jev_bottleneck_diagnosis': added}
        pair = {'loop': e['state']['game_loop'], 'diagnosis': added, 'answers': {}}
        result['pairs'].append(pair)
        for arm in (['baseline', 'shared'] if i % 2 == 0 else ['shared', 'baseline']):
            answer = (await model.ask(e['state'] if arm == 'baseline' else state, e['questions']))['MobileCombat']
            pair['answers'][arm] = answer
            result.update(calls=model.calls, cost_usd=model.cost)
            output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'calls': model.calls, 'cost': model.cost, 'eligible': len(eligible), 'pairs': [{'loop': p['loop'], 'diagnosis': p['diagnosis']['answer'], **{k:v['choice'] for k,v in p['answers'].items()}} for p in result['pairs']]}))

if __name__ == '__main__':
    asyncio.run(main())
