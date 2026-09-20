"""Compare one-step harvest continuation with explicit bounded commitments."""
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
    samples=[]
    for line in source.read_text().splitlines():
        row=json.loads(line)
        if row['event']!='jev':continue
        qs={k:q for k,q in row.get('questions',{}).items()
            if 'gather_minerals' in q.get('criteria',{})}
        if qs:samples.append((row,qs))
    if len(samples)<3:raise ValueError('Need three recorded resource decisions')
    load_dotenv(Path(__file__).resolve().parents[1]/'.env')
    model=Jev(lambda *a,**k:None,'harvest-commitment-probe',max_calls=6)
    result={'source':str(source),'method':'First/middle/last resource-category question subsets. Identical state; optional explicit continuation durations. Alternate arm order. No actions or executor deployed; not a savings or success measurement.','pairs':[]}
    for i in (0,len(samples)//2,len(samples)-1):
        row,questions=samples[i];pair={'time':row['time']};result['pairs'].append(pair)
        for arm in (['baseline','commitments'] if len(result['pairs'])%2 else ['commitments','baseline']):
            qs=copy.deepcopy(questions)
            if arm=='commitments':
                for q in qs.values():
                    for loops in (112,672,2016):
                        q['criteria'][f'continue_{loops}']=f'Keep this selection on its currently observed harvesting job for up to {loops} game loops without another resource-location decision. Only applicable when already gathering or returning resources. No new workers or resources are assigned. End early if the role or strategic priority changes, membership changes, a worker stops harvesting or takes damage, or a newly visible enemy appears. Existing visible enemies remain known risks you accept for this commitment. Other decisions continue normally.'
            pair[arm]=await model.ask(row['state'],qs)
            result.update(calls=model.calls,cost_usd=model.cost)
            output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'calls':model.calls,'cost_usd':model.cost,'choices':[{a:{k:v['choice'] for k,v in p[a].items()} for a in ('baseline','commitments')} for p in result['pairs']]}))

if __name__=='__main__':asyncio.run(main())
