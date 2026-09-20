"""Recorded-state probe of last-seen own-unit locations; never issues game orders."""
import asyncio
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dotenv import load_dotenv
from jev_sc2.jev import Jev


async def main():
    source, output = map(Path, sys.argv[1:3])
    rows = [json.loads(line) for line in source.read_text().splitlines()]
    previous = None
    history, samples = [], []
    for row in rows:
        if row['event'] == 'tick':
            current = {u['tag']: u for u in row['units']}
            if previous:
                old = {u['tag']: u for u in previous['units']}
                missing = old.keys() - current.keys()
                if missing:
                    history.append({'last_seen_loop': previous['loop'], 'absent_at_loop': row['loop'],
                                    'units': [{k: old[t][k] for k in ('tag','type','position','health')} for t in sorted(missing)]})
            previous = row
        if row['event'] != 'jev' or not history:
            continue
        questions = {k:q for k,q in row.get('questions', {}).items()
                     if any(c.startswith('group_map_attack_move_') for c in q.get('criteria', {}))}
        if not questions or len(json.dumps(questions)) > 40000:
            continue
        samples.append((row, questions, history[-8:]))
    if len(samples) < 3:
        raise ValueError('Need three bounded tactical requests after observed disappearances')
    load_dotenv(Path(__file__).resolve().parents[1] / '.env')
    model = Jev(lambda *a, **k: None, 'spatial-disappearance-probe', max_calls=6)
    result = {'source': str(source), 'method': 'First/middle/last eligible tactical requests after earlier logged own-unit disappearance. Same state and question subset in both arms; append up to eight prior observation intervals. Alternate arm order. No commands, no causal or death attribution. Not a performance test.', 'pairs': []}
    for index in (0, len(samples)//2, len(samples)-1):
        row, questions, history = samples[index]
        evidence = {'intervals': history, 'meaning': 'Own units present in the earlier observation but absent in the later one. Positions and health are last-seen, not death sites. Transport loading, transformations or mission triggers may explain absence. No causal link to any order is established.'}
        pair = {'time': row['time'], 'questions': questions, 'added_evidence': evidence}
        result['pairs'].append(pair)
        for arm in (['baseline','spatial_history'] if len(result['pairs'])%2 else ['spatial_history','baseline']):
            state = row['state'] if arm == 'baseline' else {**row['state'], 'recent_own_disappearance_locations': evidence}
            pair[arm] = await model.ask(state, questions)
            result.update(calls=model.calls, cost_usd=model.cost)
            output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({'calls':model.calls,'cost_usd':model.cost,'choices':[
        {a:{k:v['choice'] for k,v in p[a].items()} for a in ('baseline','spatial_history')} for p in result['pairs']]}))


if __name__ == '__main__':
    asyncio.run(main())
