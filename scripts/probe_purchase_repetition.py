"""Six-call paired ablation of repeated capability prose in purchase choices."""
import asyncio
import copy
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from dotenv import load_dotenv
from jev_sc2.jev import Jev

async def main():
    root=Path(__file__).resolve().parents[1];load_dotenv(root/'.env')
    source,output=map(Path,sys.argv[1:3])
    rows=[json.loads(s) for s in source.read_text().splitlines()]
    eligible=[r for r in rows if r['event']=='jev' and 'investment' in r['questions']
              and r['state'].get('resources',{}).get('minerals',0)>=500
              and any('Purchase one Marine.' in v for v in r['questions']['investment']['criteria'].values())]
    if len(eligible)<3:raise ValueError('Need three high-balance investment requests with Marine offered')
    model=Jev(lambda *a,**k:None,'purchase-repetition-probe',max_calls=6)
    result={'source':str(source),'method':'First/middle/last eligible >=500 mineral requests with Marine offered. Remove only repeated Adds another unit able to prose from all purchase criteria; full observed_capabilities_by_type remains unchanged in shared state. Alternate pair order. No game commands; three samples cannot establish tactical quality.','pairs':[]}
    for i in (0,len(eligible)//2,len(eligible)-1):
        row=eligible[i];q=copy.deepcopy(row['questions']['investment'])
        for key,text in q['criteria'].items():
            for caps in row['state'].get('observed_capabilities_by_type',{}).values():
                if caps:text=text.replace('Adds another unit able to: '+', '.join(caps)+'. ','Capabilities remain listed in observed_capabilities_by_type. ')
            q['criteria'][key]=text
        pair={'recorded_time':row['time'],'original_chars':len(json.dumps(row['questions']['investment'])),'reduced_chars':len(json.dumps(q))}
        variants=[('original',row['questions']['investment']),('deduplicated',q)]
        if len(result['pairs'])%2:variants.reverse()
        for label,question in variants:
            answer=(await model.ask(row['state'],{'investment':question}))['investment']
            pair[label]={'answer':answer,'chosen_description':question['criteria'].get(answer.get('choice'))}
        result['pairs'].append(pair);result.update(calls=model.calls,cost=model.cost)
        output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'calls':model.calls,'cost':model.cost}))

if __name__=='__main__':asyncio.run(main())
