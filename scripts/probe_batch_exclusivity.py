"""Recorded-state comparison of actual purchase reservation semantics."""
import asyncio
import copy
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dotenv import load_dotenv
from jev_sc2.jev import Jev

OLD = 'Prioritize this batch over other new purchases until it finishes, expires, or your strategic priority changes.'
NEW = ('No other new unit, structure or upgrade purchase is allowed while this batch is active, '
       'including while waiting for resources or an available training control. '
       'This exclusive reservation ends when the batch finishes, expires, or your strategic priority changes.')

async def main():
    source, output = map(Path, sys.argv[1:3])
    rows = [json.loads(line) for line in source.read_text().splitlines()]
    rows = [r for r in rows if r['event']=='jev' and any(OLD in text for q in r.get('questions',{}).values() for text in q.get('criteria',{}).values())]
    if len(rows)<3: raise ValueError('Need three investment states with batch options')
    load_dotenv(Path(__file__).resolve().parents[1]/'.env')
    model=Jev(lambda *a,**k:None,'batch-exclusivity-probe',max_calls=6)
    result={'source':str(source),'method':'First/middle/last eligible recorded requests. Full original state and questions retained; treatment describes actual exclusive purchase reservation. Alternating order, one pair per state. No gameplay commands; descriptive comparison, not causal performance evidence.','pairs':[]}
    for i,row in enumerate([rows[0],rows[len(rows)//2],rows[-1]]):
        questions=copy.deepcopy(row['questions'])
        for q in questions.values():
            q['criteria']={k:v.replace(OLD,NEW) for k,v in q['criteria'].items()}
        pair={'time':row['time']};result['pairs'].append(pair)
        for arm in (['baseline','explicit'] if i%2==0 else ['explicit','baseline']):
            pair[arm]=await model.ask(row['state'], row['questions'] if arm=='baseline' else questions)
            result.update(calls=model.calls,cost_usd=model.cost)
            output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'calls':model.calls,'cost_usd':model.cost,'choices':[{a:{k:v['choice'] for k,v in p[a].items()} for a in ('baseline','explicit')} for p in result['pairs']]}))

if __name__=='__main__':asyncio.run(main())
