"""Compare investment choices with explicit observed producer relationships."""
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
    rows=[e for e in events if e['event']=='jev' and 'investment' in e.get('questions',{})
          and e['state'].get('jev_production_intentions')
          and not e['state'].get('selection_facts',{}).get('Barracks',{}).get('count',0)]
    if len(rows)<3:raise ValueError('Need three eligible states')
    load_dotenv(Path(__file__).resolve().parents[1]/'.env')
    model=Jev(lambda *a,**k:None,'producer-dependency-probe',max_calls=6)
    result={'source':str(source),'pairs':[],'method':'First/middle/last investment states without observed Barracks and with Jev goals. Same full questions and state; treatment adds factual reverse index of previously observed Train controls, current producer counts and incomplete counts for all known producers. No forced rebuild or action filtering. Alternating arms; exploratory only.'}
    for i,e in enumerate([rows[0],rows[len(rows)//2],rows[-1]]):
        state=copy.deepcopy(e['state']);relationships=[]
        for producer,labels in state.get('observed_capabilities_by_type',{}).items():
            targets=sorted({label[6:] for label in labels if label.startswith('Train ')})
            if targets:
                f=state.get('selection_facts',{}).get(producer,{})
                relationships.append({'producer_type':producer,'previously_observed_training_controls':targets,
                    'currently_observed_producer_count':f.get('count',0),'currently_incomplete_count':f.get('incomplete_count',0)})
        state['observed_production_relationships']={'relationships':relationships,'limits':'Historical training controls, not current legality. A missing producer cannot execute its training controls; constructing it may still leave other prerequisites unmet. No purchase is selected by this table.'}
        pair={'loop':state.get('game_loop'),'relationships':relationships,'answers':{}};result['pairs'].append(pair)
        for arm in (['baseline','dependencies'] if i%2==0 else ['dependencies','baseline']):
            answers=await model.ask(e['state'] if arm=='baseline' else state,e['questions'])
            choice=answers['investment']['choice']
            pair['answers'][arm]={'answer':answers['investment'],'description':e['questions']['investment']['criteria'].get(choice)}
            result.update(calls=model.calls,cost_usd=model.cost);output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'calls':model.calls,'cost':model.cost,'pairs':[{'loop':p['loop'],**{k:v['description'][:100] for k,v in p['answers'].items()}} for p in result['pairs']]}))

if __name__=='__main__':asyncio.run(main())
