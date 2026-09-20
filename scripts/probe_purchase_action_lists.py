"""Recorded-state comparison of duplicated action-list removal from purchase descriptions."""
import asyncio
import copy
import re
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dotenv import load_dotenv
from jev_sc2.jev import Jev

def shorten(text):
    # Remove duplicated observed action lists only; shared-state facts remain.
    return re.sub(r'Adds another unit able to: .*?\. ', '', text)

async def main():
    source, output = map(Path, sys.argv[1:3])
    rows = [json.loads(line) for line in source.read_text().splitlines()]
    rows = [r for r in rows if r['event']=='jev' and 'investment' in r.get('questions',{})]
    if len(rows)<3: raise ValueError('Need three investment states')
    load_dotenv(Path(__file__).resolve().parents[1]/'.env')
    model=Jev(lambda *a,**k:None,'purchase-action-list-probe',max_calls=6)
    result={'source':str(source),'method':'First/middle/last eligible recorded requests. Full original state retained; treatment removes duplicated Adds another unit able to action lists from option descriptions, retaining them in shared observed_capabilities_by_type. All costs, weapons, prerequisite descriptions and choices remain. Alternating order, one pair per state. No gameplay commands; descriptive comparison, not causal performance evidence.','pairs':[]}
    for i,row in enumerate([rows[0],rows[len(rows)//2],rows[-1]]):
        questions=copy.deepcopy(row['questions'])
        questions['investment']['criteria'] = {k: shorten(v) for k,v in questions['investment']['criteria'].items()}
        pair={'time':row['time'], 'treatment_criteria':questions['investment']['criteria']};result['pairs'].append(pair)
        for arm in (['baseline','explicit'] if i%2==0 else ['explicit','baseline']):
            pair[arm]=await model.ask(row['state'], row['questions'] if arm=='baseline' else questions)
            result.update(calls=model.calls,cost_usd=model.cost)
            output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'calls':model.calls,'cost_usd':model.cost,'choices':[{a:{k:v['choice'] for k,v in p[a].items()} for a in ('baseline','explicit')} for p in result['pairs']]}))

if __name__=='__main__':asyncio.run(main())
