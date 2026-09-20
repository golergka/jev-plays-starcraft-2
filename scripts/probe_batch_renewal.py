"""Replay first investment after each completed request allowance; no commands."""
import asyncio
import copy
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from dotenv import load_dotenv
from jev_sc2.jev import Jev

async def main():
    load_dotenv(Path(__file__).resolve().parents[1]/'.env')
    source,output=map(Path,sys.argv[1:3])
    rows=[json.loads(l) for l in source.read_text().splitlines()]
    samples=[]
    for index,event in enumerate(rows):
        if event['event']!='production_job_released' or event['reason']!='completed request allowance':continue
        target=event['job']['target_project']
        row=next((r for r in rows[index+1:] if r['event']=='jev' and 'investment' in r['questions']),None)
        if row is None:continue
        matches=[k for k,v in row['questions']['investment']['criteria'].items()
                 if k.startswith('batch_') and f'training requests for {target} over' in v]
        if len(matches)==1:samples.append((event,row,matches[0]))
        if len(samples)==3:break
    if len(samples)!=3:raise ValueError('Need three exact post-commitment states')
    model=Jev(lambda *a,**k:None,'batch-renewal-probe',max_calls=6)
    result={'source':str(source),'method':'First investment after each of first three completed request allowances. Treatment adds observed previous job summary and labels existing matching batch as renewal. No new options or automatic renewal; all choices remain. Alternating order.','pairs':[]}
    for event,row,key in samples:
        q=copy.deepcopy(row['questions'])
        q['investment']['criteria'][key]='Renew the previous training commitment with a new bounded batch. '+q['investment']['criteria'][key]
        state={**row['state'],'previous_training_commitment':{'target':event['job']['target_project'],'release_reason':event['reason'],'note':'The previous request allowance was exhausted. This does not prove completed units. No requests remain authorized. Renewal is optional.'}}
        pair={'time':row['time'],'target':event['job']['target_project'],'renewal_key':key}
        variants=[('original',row['state'],row['questions']),('renewal',state,q)]
        if len(result['pairs'])%2:variants.reverse()
        for label,s,questions in variants:pair[label]=(await model.ask(s,questions))['investment']
        result['pairs'].append(pair);result.update(calls=model.calls,cost=model.cost)
        output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'calls':model.calls,'cost':model.cost,'choices':[{k:p[k]['choice'] for k in ('original','renewal')} for p in result['pairs']]}))

if __name__=='__main__':asyncio.run(main())
