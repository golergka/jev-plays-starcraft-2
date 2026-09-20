"""Jev assesses consequences of its own choice, then revisits the same menu."""
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
    rows=[json.loads(l) for l in source.read_text().splitlines()]
    rows=[r for r in rows if r['event']=='jev' and 'MobileCombat' in r.get('questions',{})][:3]
    if len(rows)!=3:raise ValueError('Need three combat decision states')
    load_dotenv(Path(__file__).resolve().parents[1]/'.env')
    model=Jev(lambda *a,**k:None,'combat-outlook-probe',max_calls=9)
    result={'source':str(source),'method':'First three concrete MobileCombat states. Fresh full-batch baseline, Jev consequence assessment of its own chosen order, then identical full batch with explicitly uncertain model assessment. No root selected alternative or game commands. Fixed order; extra context and call variation confound causality.','samples':[]}
    for row in rows:
        sample={'time':row['time']};result['samples'].append(sample)
        sample['baseline']=await model.ask(row['state'],row['questions'])
        choice=sample['baseline']['MobileCombat']['choice']
        description=row['questions']['MobileCombat']['criteria'][choice]
        hypothetical={'selection':'MobileCombat','order':description,'horizon_game_loops':672}
        predicates={'loss':'Several members of this selection will be lost within the horizon.',
                    'progress':'This order will make useful progress toward completing the primary mission objective within the horizon.',
                    'cohesion':'The selection will remain close enough together to support each other within the horizon.'}
        questions={k:{'type':'choice','instructions':'Assess this prediction if the proposed order is issued. Use only observed state and known controls; engine routes and unseen enemies are unknown. Do not assume a future rescue order. Prediction: '+v,
                      'criteria':{'likely':'The supplied evidence supports this prediction.','unlikely':'The supplied evidence argues against this prediction.','uncertain':'The supplied evidence is insufficient to judge.'}} for k,v in predicates.items()}
        sample['assessment']=await model.ask({**row['state'],'hypothetical_order':hypothetical},questions)
        state=copy.deepcopy(row['state']);state['jev_order_assessment']={'hypothetical_order':hypothetical,'predictions':predicates,'answers':sample['assessment'],'provenance':'Uncertain Jev predictions, not measured outcomes or instructions. Original observed state remains authoritative.'}
        sample['reconsidered']=await model.ask(state,row['questions'])
        result.update(calls=model.calls,cost_usd=model.cost);output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'calls':model.calls,'cost_usd':model.cost,'samples':[{'baseline':s['baseline']['MobileCombat']['choice'],'assessment':{k:v['choice'] for k,v in s['assessment'].items()},'reconsidered':s['reconsidered']['MobileCombat']['choice']} for s in result['samples']]}))

if __name__=='__main__':asyncio.run(main())
