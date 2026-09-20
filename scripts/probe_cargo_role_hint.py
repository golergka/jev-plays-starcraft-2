"""Paired test of explicit persistent cargo semantics for continuation."""
import asyncio
import copy
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from dotenv import load_dotenv
from jev_sc2.jev import Jev

async def main():
    source,output=map(Path,sys.argv[1:3])
    events=[json.loads(l) for l in source.read_text().splitlines()]
    rows=[e for e in events if e['event']=='jev' and 'Bunker' in e.get('questions',{})
          and e['state']['selection_facts']['Bunker'].get('cargo_slots_used',0)>0
          and 'continue' in e['questions']['Bunker']['criteria']]
    if len(rows)<3:raise ValueError('Need three occupied bunker states')
    load_dotenv(Path(__file__).resolve().parents[1]/'.env')
    jev=Jev(lambda *a,**k:None,'cargo-role-hint-probe',max_calls=6)
    result={'source':str(source),'pairs':[],'method':'First/middle/last occupied Bunker concrete decisions. Same full states and batches; only removes the prior Use another available ability role sentence from the concrete question. All alternatives retained, alternating arms. No gameplay or claim of improved survival.'}
    for i,row in enumerate([rows[0],rows[len(rows)//2],rows[-1]]):
        q=copy.deepcopy(row['questions']);f=row['state']['selection_facts']['Bunker']
        q['Bunker']['instructions']=q['Bunker']['instructions'].replace(' Jev selected this contribution: Use another available ability.', '')
        pair={'loop':row['state'].get('game_loop'),'passengers':f['passengers_by_type'],
              'treatment_instructions':q['Bunker']['instructions'],'answers':{}}
        result['pairs'].append(pair)
        for arm in (['baseline','without_role_hint'] if i%2==0 else ['without_role_hint','baseline']):
            pair['answers'][arm]=await jev.ask(row['state'],row['questions'] if arm=='baseline' else q)
            result.update(calls=jev.calls,cost_usd=jev.cost)
            output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'calls':jev.calls,'cost_usd':jev.cost,'pairs':[{'loop':p['loop'],**{k:v['Bunker']['choice'] for k,v in p['answers'].items()}} for p in result['pairs']]}))

if __name__=='__main__':asyncio.run(main())
