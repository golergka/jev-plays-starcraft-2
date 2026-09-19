"""Compare independent income-role choices with a joint count; no game orders."""
import asyncio
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dotenv import load_dotenv
from jev_sc2.jev import Jev


async def main():
    root = Path(__file__).resolve().parents[1]
    load_dotenv(root/'.env')
    source, output = map(Path, sys.argv[1:3])
    rows = [json.loads(line) for line in source.read_text().splitlines()]
    eligible = []
    for row in rows:
        if row.get('event') != 'jev':
            continue
        questions = {k: q for k, q in row['questions'].items()
                     if k.startswith('purpose_') and 'income' in q['criteria']}
        if len(questions) >= 2:
            eligible.append((row, questions))
    indices = sorted({0, len(eligible)//2, len(eligible)-1})
    if len(indices) != 3:
        raise ValueError('Need three recorded multi-worker role states')
    jev = Jev(lambda *a, **k: None, 'worker-allocation-probe', max_calls=6)
    pairs = []
    for i, index in enumerate(indices):
        row, questions = eligible[index]
        count = len(questions)
        joint = {'income_count': {
            'type': 'choice',
            'instructions': 'Choose jointly how many of the listed selections should receive the income contribution for up to 224 game loops. '
                            'Each listed selection contains one resource-capable worker. Concrete worker identities and resource targets would be chosen separately. '
                            'Consider the objective, current orders, resources, capabilities and threats. This is a role allocation, not a recommendation to maximize income.',
            'criteria': {f'count_{n}': f'Assign the income role (collect resources for production and construction) to {n} of these {count} workers. '
                         f'The other {count-n} receive separate choices among their non-income roles; continue may preserve existing harvesting.'
                         for n in range(count+1)},
        }}
        # Validate singleton scope from recorded facts instead of assuming it.
        facts = row['state'].get('selection_facts', {})
        if any(facts.get(k.removeprefix('purpose_'), {}).get('count') != 1 for k in questions):
            raise ValueError('Allocation probe requires singleton selections')
        state = {**row['state'], 'allocation_selections': list(questions)}
        variants = [('independent', questions), ('joint', joint)]
        if i % 2:
            variants.reverse()
        pair = {'recorded_time': row['time'], 'worker_count': count,
                'resources': state.get('resources')}
        for label, qs in variants:
            pair[label] = await jev.ask(state, qs)
        pair['independent_income_probability_sum'] = sum(a.get('probabilities', {}).get('income', 0) for a in pair['independent'].values())
        pair['joint_top_choice'] = pair['joint']['income_count'].get('choice')
        pairs.append(pair)
    artifact = {'source': str(source), 'calls': jev.calls, 'cost': jev.cost, 'pairs': pairs,
                'method': 'First/middle/last multi-worker recorded states; alternating paired order. Same state, different decision representation. '
                          'Independent probability sum is descriptive, not calibrated expected utility. Count menu does not resolve identities or concrete orders. '
                          'Continue can already harvest. Three unreplicated pairs, no survival claim, no game commands.'}
    output.write_text(json.dumps(artifact, indent=2)+'\n')
    print(json.dumps({'calls': jev.calls, 'cost': jev.cost, 'pairs': [
        {k: p[k] for k in ('worker_count', 'independent_income_probability_sum', 'joint_top_choice')} for p in pairs]}))


if __name__ == '__main__':
    asyncio.run(main())
