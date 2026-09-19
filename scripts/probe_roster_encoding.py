"""Compare Jev answers for object and columnar rosters on identical recorded facts."""
import asyncio
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dotenv import load_dotenv
from jev_sc2.jev import Jev
from player import order_state

async def main():
    source, output = map(Path, sys.argv[1:3])
    if output.exists():
        raise FileExistsError(output)
    candidates = []
    for line in source.read_text().splitlines():
        row = json.loads(line)
        if row['event'] == 'jev' and isinstance(row['state'].get('units'), list):
            candidates.append(row)
    if not candidates:
        raise ValueError('No recorded object rosters')
    selected = [candidates[i] for i in sorted({0, len(candidates)//2, len(candidates)-1})]
    load_dotenv(Path(__file__).resolve().parents[1]/'.env')
    jev = Jev(lambda *a, **kw: None, 'roster-encoding-probe', max_calls=30)
    results = []
    for index, row in enumerate(selected):
        # Only replace the roster; do not reapply other presentation transforms.
        compact = {**row['state'], 'units': order_state(row['state'])['units']}
        variants = [('object', row['state']), ('columns', compact)]
        if index % 2:
            variants.reverse()
        result = {'recorded_time': row['time'], 'questions': list(row['questions']),
                  'units': len(row['state']['units']), 'variants': {}}
        for label, state in variants:
            try:
                answers = await jev.ask(state, row['questions'])
                result['variants'][label] = {'state_chars': len(json.dumps(state)), 'answers': answers}
            except Exception as exc:
                result['variants'][label] = {'error': type(exc).__name__, 'detail': str(exc)[:180]}
        results.append(result)
    payload = {'source': str(source), 'method': 'First, middle, last recorded object roster; identical questions and facts; alternate request order. No game commands. Single trials, not a quality benchmark.',
               'calls': jev.calls, 'cost': jev.cost, 'results': results}
    output.write_text(json.dumps(payload, indent=2)+'\n')
    print(json.dumps({'output':str(output),'calls':jev.calls,'cost':jev.cost}))

if __name__ == '__main__':
    asyncio.run(main())
