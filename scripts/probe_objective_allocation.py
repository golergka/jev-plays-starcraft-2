"""Recorded-state comparison of objective-linked purchase instructions."""
import asyncio
import copy
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dotenv import load_dotenv
from jev_sc2.jev import Jev

EXTRA = (' Evaluate this purchase by how it helps complete the active primary mission objective. '
         'Consider what the force currently lacks to finish that objective, the time needed to obtain it, '
         'and the opportunity cost of spending on another project or waiting. '
         'Survival, resource income and expansion are means toward the mission objective; '
         'they are not automatically evidence of progress toward completing it.')

async def main():
    source, output = map(Path, sys.argv[1:3])
    rows = [json.loads(line) for line in source.read_text().splitlines()]
    rows = [r for r in rows if r['event']=='jev' and 'investment' in r.get('questions',{})]
    if len(rows)<3: raise ValueError('Need three investment states')
    load_dotenv(Path(__file__).resolve().parents[1]/'.env')
    model=Jev(lambda *a,**k:None,'objective-allocation-probe',max_calls=6)
    result={'source':str(source),'method':'First/middle/last eligible recorded requests. Full original state and questions retained; treatment adds general primary-objective and opportunity-cost wording; no unit, route or build-order recommendation. Alternating order, one pair per state. No gameplay commands; descriptive comparison, not causal performance evidence.','pairs':[]}
    for i,row in enumerate([rows[0],rows[len(rows)//2],rows[-1]]):
        questions=copy.deepcopy(row['questions'])
        questions['investment']['instructions'] += EXTRA
        pair={'time':row['time']};result['pairs'].append(pair)
        for arm in (['baseline','explicit'] if i%2==0 else ['explicit','baseline']):
            pair[arm]=await model.ask(row['state'], row['questions'] if arm=='baseline' else questions)
            result.update(calls=model.calls,cost_usd=model.cost)
            output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'calls':model.calls,'cost_usd':model.cost,'choices':[{a:{k:v['choice'] for k,v in p[a].items()} for a in ('baseline','explicit')} for p in result['pairs']]}))

if __name__=='__main__':asyncio.run(main())
