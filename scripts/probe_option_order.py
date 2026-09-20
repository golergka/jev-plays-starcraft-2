"""Paired offline menu-order probe; identical facts/options, no game actions."""
import asyncio
import copy
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dotenv import load_dotenv
from jev_sc2.jev import Jev

async def main():
    source, output, key = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
    load_dotenv(Path(__file__).resolve().parents[1] / '.env')
    rows = [json.loads(line) for line in source.read_text().splitlines()]
    eligible = [r for r in rows if r['event'] == 'jev' and key in r.get('questions', {})
                and len(r['questions'][key].get('criteria', {})) > 2]
    if len(eligible) < 3:
        raise ValueError('Need three eligible observations')
    samples = [eligible[i] for i in (0, len(eligible)//2, len(eligible)-1)]
    jev = Jev(lambda *args, **kwargs: None, 'option-order-probe', max_calls=6)
    pairs = []
    for i, row in enumerate(samples):
        original = row['questions'][key]
        reversed_menu = copy.deepcopy(original)
        reversed_menu['criteria'] = dict(reversed(list(original['criteria'].items())))
        variants = [('original', original), ('reversed', reversed_menu)]
        if i % 2:
            variants.reverse()
        pair = {'loop': row['state'].get('game_loop'),
                'original_order': list(original['criteria'])}
        for name, question in variants:
            pair[name] = (await jev.ask(row['state'], {key: question}))[key]
        pairs.append(pair)
        output.write_text(json.dumps({'source': str(source), 'question': key,
            'method': 'First/middle/last eligible recorded states; reverse criteria insertion order only; alternate pair request order. Six requests maximum, shared spend governor, no game actions. Small diagnostic, not statistical proof.',
            'pairs': pairs, 'calls': jev.calls, 'cost': jev.cost}, indent=2)+'\n')
    print(json.dumps({'calls': jev.calls, 'cost': jev.cost,
        'choices': [{k: v.get('choice') for k,v in p.items() if isinstance(v,dict)} for p in pairs]}))

if __name__ == '__main__':
    asyncio.run(main())
