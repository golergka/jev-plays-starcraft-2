"""Compare concrete-order context with and without the type summary; six calls."""
import asyncio
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
    eligible = [r for r in rows if r['event'] == 'jev'
                and set(r['questions']) in ({'Marine'}, {'MobileCombat'})
                and 'type_selection_facts' in r['state']]
    if len(eligible) < 3:
        raise ValueError('Need at least three concrete combat requests')
    samples = [eligible[i] for i in (0, len(eligible)//2, len(eligible)-1)]
    model = Jev(lambda *a, **k: None, 'order-summary-probe', max_calls=6)
    result = {'source':str(source), 'method':'First/middle/last eligible recorded concrete combat requests. Remove only type_selection_facts. Keep every offered choice and all other state. Alternate pair order. Six calls maximum; no gameplay commands. Removing summaries is not assumed behaviorally lossless.', 'pairs':[]}
    for row in samples:
        reduced = {k:v for k,v in row['state'].items() if k != 'type_selection_facts'}
        pair = {'recorded_time':row['time'], 'state_chars':len(json.dumps(row['state'])), 'reduced_state_chars':len(json.dumps(reduced))}
        variants = [('original',row['state']), ('without_type_summary',reduced)]
        if len(result['pairs']) % 2:
            variants.reverse()
        for label,state in variants:
            pair[label] = await model.ask(state,row['questions'])
        result['pairs'].append(pair)
        result.update(calls=model.calls,cost=model.cost)
        output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))

if __name__ == '__main__':
    asyncio.run(main())
