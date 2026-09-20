"""Compare broad objective priority against explicit immediate commitment."""
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
    events = [json.loads(line) for line in source.read_text().splitlines()]
    rows = [e for e in events if e['event'] == 'jev' and 'strategy' in e.get('questions', {})]
    # First, middle, last strategic reviews while a Marine is observed.
    rows = [e for e in rows if any(u['type'] == 'Marine' for f in e['state'].get('selection_facts', {}).values() for u in f.get('members', []))]
    if len(rows) < 3:
        raise ValueError('Need at least three eligible recorded states')
    samples = [rows[0], rows[len(rows)//2], rows[-1]]
    load_dotenv(Path(__file__).resolve().parents[1]/'.env')
    jev = Jev(lambda *a, **k: None, 'strategy-commitment-probe', max_calls=6)
    result = {'source': str(source), 'pairs': [], 'method': 'First/middle/last strategic reviews with an observed Marine. Identical full states and question batches; treatment narrows only pursue_objective description to immediate commitment. All other options unchanged. Alternating arm order, one sample each; exploratory, not causal evidence. No game commands.'}
    for i, row in enumerate(samples):
        questions = copy.deepcopy(row['questions'])
        questions['strategy']['criteria']['pursue_objective'] = (
            'Commit the currently available force now to directly advancing the active primary mission objectives described in mission_context. '
            'Choose this when the current force should proceed now rather than first accumulate strength, assemble, recover or defend. '
            'Further Jev decisions choose concrete movement, interactions and combat; the objective need not be destruction of an enemy base.')
        pair = {'loop': row['state'].get('game_loop'), 'answers': {},
                'treatment_description': questions['strategy']['criteria']['pursue_objective']}
        result['pairs'].append(pair)
        for arm in (['baseline', 'commitment'] if i % 2 == 0 else ['commitment', 'baseline']):
            pair['answers'][arm] = await jev.ask(row['state'], row['questions'] if arm == 'baseline' else questions)
            result.update(calls=jev.calls, cost_usd=jev.cost)
            output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({'calls':jev.calls,'cost_usd':jev.cost,'pairs':[{'loop':p['loop'], **{a:v['strategy']['choice'] for a,v in p['answers'].items()}} for p in result['pairs']]}))

if __name__ == '__main__':
    asyncio.run(main())
