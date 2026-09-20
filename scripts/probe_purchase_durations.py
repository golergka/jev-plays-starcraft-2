"""Paired recorded-state purchase probe using same-run catalog durations."""
import asyncio
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dotenv import load_dotenv
from jev_sc2.jev import Jev

async def main():
    source, output = map(Path, sys.argv[1:3])
    events = [json.loads(line) for line in source.read_text().splitlines()]
    durations = {u['type']: u['catalog_build_time'] for e in events
                 if e['event'] == 'catalog_duration_diagnostic' for u in e['units']}
    rows = [e for e in events if e['event'] == 'jev' and 'investment' in e.get('questions', {})]
    if len(rows) < 3 or not durations:
        raise ValueError('Need three purchase states and catalog diagnostics')
    load_dotenv(Path(__file__).resolve().parents[1]/'.env')
    model = Jev(lambda *a, **k: None, 'purchase-duration-probe', max_calls=6)
    out = {'source': str(source), 'method': 'First/middle/last purchase requests. Same questions and full state. Treatment adds same-run catalog durations for types already in state. Alternating arms; six-call ceiling; no game orders. Positive durations are raw fields, zeros marked unknown. Barracks loop calibration does not verify every type.', 'pairs': []}
    for i, e in enumerate([rows[0], rows[len(rows)//2], rows[-1]]):
        facts = {k: (v if v > 0 else None) for k, v in durations.items()
                 if k in e['state'].get('unit_type_facts', {})}
        changed = {**e['state'], 'catalog_production_durations': {
            'values': facts, 'meaning': 'Catalog build_time values; null means unavailable, not instant. Barracks 960 matches about 960 observed game loops in this run. Units for other entries are not independently calibrated. Queue delays, resource waiting, travel, interruption and destruction are additional; these are not guaranteed completion deadlines.'}}
        pair = {'loop': e['state']['game_loop'], 'added_facts': facts, 'answers': {}}
        out['pairs'].append(pair)
        for arm in (['baseline', 'durations'] if i % 2 == 0 else ['durations', 'baseline']):
            a = (await model.ask(e['state'] if arm == 'baseline' else changed, e['questions']))['investment']
            if a['choice'] not in e['questions']['investment']['criteria']:
                raise ValueError('Invalid investment answer')
            pair['answers'][arm] = {'answer': a, 'description': e['questions']['investment']['criteria'][a['choice']]}
            out.update(calls=model.calls, cost_usd=model.cost)
            output.write_text(json.dumps(out, indent=2)+'\n')
    print(json.dumps({'calls': model.calls, 'cost': model.cost, 'pairs': [
        {'loop': p['loop'], **{a: r['description'].split('.')[0] for a, r in p['answers'].items()}} for p in out['pairs']]}))

if __name__ == '__main__':
    asyncio.run(main())
