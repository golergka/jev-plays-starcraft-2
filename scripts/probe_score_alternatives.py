"""Bounded replay: do explicit competing investments change independent scores?"""
import asyncio
import copy
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dotenv import load_dotenv
from jev_sc2.jev import Jev

async def main():
    root = Path(__file__).resolve().parents[1]
    load_dotenv(root / '.env')
    source, output = map(Path, sys.argv[1:3])
    rows = [json.loads(line) for line in source.read_text().splitlines()]
    eligible = [r for r in rows if r['event'] == 'jev' and
                'save' in r['questions'] and
                all(q.get('type') == 'score' for q in r['questions'].values())]
    if len(eligible) < 3:
        raise ValueError('Need at least three recorded scored investment requests')
    model = Jev(lambda *a, **k: None, 'score-alternatives-probe', max_calls=6)
    result = {'source': str(source), 'method':
              'First/middle/last scored requests. Identical questions and ratings; '
              'treatment adds all exact competing action descriptions to shared state. '
              'Alternate order. Six-call cap; no game commands. Scores are not calibrated utilities.',
              'pairs': []}
    for index in (0, len(eligible)//2, len(eligible)-1):
        row = eligible[index]
        actions = {k: q['instructions'].split('Action: ', 1)[1]
                   for k, q in row['questions'].items()}
        treatment = copy.deepcopy(row['state'])
        treatment['available_investment_alternatives'] = {
            'meaning': 'These are the mutually exclusive investment alternatives available for this decision. Only one can be selected now.',
            'actions': actions}
        pair = {'recorded_time': row['time'], 'actions': actions}
        variants = [('baseline', row['state']), ('alternatives', treatment)]
        if len(result['pairs']) % 2:
            variants.reverse()
        for label, state in variants:
            pair[label] = await model.ask(state, row['questions'])
            pair[label+'_ranking'] = sorted(pair[label], key=lambda k: pair[label][k]['score'], reverse=True)
        result['pairs'].append(pair)
        result.update(calls=model.calls, cost=model.cost)
        output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({'calls': model.calls, 'cost': model.cost,
        'tops': [{label: (p[label+'_ranking'][0], p[label][p[label+'_ranking'][0]]['score'])
                  for label in ('baseline', 'alternatives')} for p in result['pairs']]}))

if __name__ == '__main__':
    asyncio.run(main())
