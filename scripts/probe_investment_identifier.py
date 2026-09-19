"""Six-call paired identifier probe on recorded investments; no game commands."""
import asyncio
import copy
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from dotenv import load_dotenv
from jev_sc2.jev import Jev

async def main():
    root=Path(__file__).resolve().parents[1]
    load_dotenv(root/'.env')
    source,output=map(Path,sys.argv[1:3])
    eligible=[]
    for line in source.read_text().splitlines():
        row=json.loads(line)
        if row['event']!='jev' or 'investment' not in row['questions']:continue
        if row['state'].get('resources',{}).get('minerals',0)<500:continue
        if row['response']['answers'].get('investment',{}).get('choice')!='save':continue
        if 'save' in row['questions']['investment']['criteria']:eligible.append(row)
    if len(eligible)<3:raise ValueError('Need three high-balance recorded save decisions')
    samples=[eligible[i] for i in (0,len(eligible)//2,len(eligible)-1)]
    model=Jev(lambda *a,**k:None,'investment-identifier-probe',max_calls=6)
    result={'source':str(source),'method':'First/middle/last eligible recorded save decisions with >=500 minerals. Identical state, descriptions and option order; rename only save to option_0. Alternate request order. Six calls maximum. No gameplay commands. Single draws, not statistical evidence.','pairs':[]}
    for index,row in enumerate(samples):
        original=row['questions']['investment'];changed=copy.deepcopy(original)
        assert 'option_0' not in original['criteria']
        changed['criteria']={('option_0' if k=='save' else k):v for k,v in original['criteria'].items()}
        variants=[('original',original),('renamed',changed)]
        if index%2:variants.reverse()
        pair={'recorded_time':row['time'],'resources':row['state']['resources']}
        for label,question in variants:
            answer=(await model.ask(row['state'],{'investment':question}))['investment']
            key='save' if label=='original' else 'option_0'
            pair[label]={'choice':answer.get('choice'),'no_purchase_probability':answer.get('probabilities',{}).get(key),'answer':answer}
        result['pairs'].append(pair)
        result.update(calls=model.calls,cost=model.cost)
        output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'calls':model.calls,'cost':model.cost,'pairs':[{k:v for k,v in p.items() if k!='resources'} for p in result['pairs']]},indent=2))

if __name__=='__main__':asyncio.run(main())
