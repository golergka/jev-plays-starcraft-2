"""Paired recorded-state probe: put the selection's facts beside its role question."""
import asyncio
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dotenv import load_dotenv
from jev_sc2.jev import Jev

async def main():
    source, output = map(Path, sys.argv[1:3])
    rows = []
    for line in source.read_text().splitlines():
        row = json.loads(line)
        if row['event'] == 'jev' and any(k.startswith('purpose_') and 'income' in q.get('criteria', {}) for k, q in row.get('questions', {}).items()):
            rows.append(row)
    if len(rows) < 3:
        raise ValueError('Need three recorded economic-role decision states')
    selected = [rows[0], rows[len(rows)//2], rows[-1]]
    load_dotenv(Path(__file__).resolve().parents[1]/'.env')
    model = Jev(lambda *a, **k: None, 'role-local-facts-probe', max_calls=6)
    result = {'source': str(source), 'method': 'First, middle, last economic-role states. Full original question batch and state in both arms. Treatment repeats each selection factual record verbatim next to its question, with an explicit field reference. No tactical advice, filtering, action changes or game commands. One paired observation per state; variation is not causal proof.', 'pairs': []}
    for i, row in enumerate(selected):
        local = {}
        for key, question in row['questions'].items():
            name = key.removeprefix('purpose_')
            facts = row['state'].get('selection_facts', {}).get(name)
            local[key] = {**question, 'instructions': question['instructions'] + (
                '\nThe selection_facts record for this exact selection (' + name + ') is: ' + json.dumps(facts, separators=(',', ':')) if facts is not None else '')}
        pair = {'time': row['time'], 'answers': {}}
        result['pairs'].append(pair)
        for arm in (['baseline','local'] if i%2 == 0 else ['local','baseline']):
            pair['answers'][arm] = await model.ask(row['state'], row['questions'] if arm == 'baseline' else local)
            result.update(calls=model.calls, cost_usd=model.cost)
            output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({'calls': model.calls, 'cost_usd': model.cost, 'pairs': [{arm: {k:v['choice'] for k,v in answers.items()} for arm,answers in p['answers'].items()} for p in result['pairs']]}))

if __name__ == '__main__':
    asyncio.run(main())
