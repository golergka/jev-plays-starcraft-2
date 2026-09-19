"""Six-call paired compact investment-state probe on recorded investments; no game commands."""
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
        if 'strategy_chosen_by_jev' in row['state']:eligible.append(row)
    if len(eligible)<3:raise ValueError('Need three high-balance recorded save decisions')
    samples=[eligible[i] for i in (0,len(eligible)//2,len(eligible)-1)]
    model=Jev(lambda *a,**k:None,'investment-compact-state-probe',max_calls=6)
    result={'source':str(source),'method':'First/middle/last eligible recorded save decisions with >=500 minerals. Identical questions; compact variant omits catalog, duplicate project lists, spatial detail, and raw action feedback while retaining objective, resources, force counts/health/orders/cargo, capabilities, outcome history and strategy. Lossy context ablation, not equivalent facts. Alternate request order. Six calls maximum. No gameplay commands. Single draws, not statistical evidence.','pairs':[]}
    for index,row in enumerate(samples):
        original=row['state'];changed=copy.deepcopy(original)
        for key in ('unit_type_facts','recent_action_feedback'):
            changed.pop(key,None)
        omit={'center','max_separation','largest_distance_to_nearest_selection_member','available_build_abilities','available_projects','available_support_abilities'}
        changed['selection_facts']={k:{f:v for f,v in facts.items() if f not in omit} for k,facts in changed['selection_facts'].items()}
        variants=[('original',original),('compact',changed)]
        if index%2:variants.reverse()
        pair={'recorded_time':row['time'],'resources':row['state']['resources'],'state_chars':{'original':len(json.dumps(original)),'compact':len(json.dumps(changed))}}
        for label,state in variants:
            answer=(await model.ask(state,{'investment':row['questions']['investment']}))['investment']
            key='save'
            pair[label]={'choice':answer.get('choice'),'no_purchase_probability':answer.get('probabilities',{}).get(key),'answer':answer}
        result['pairs'].append(pair)
        result.update(calls=model.calls,cost=model.cost)
        output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'calls':model.calls,'cost':model.cost,'pairs':[{k:v for k,v in p.items() if k!='resources'} for p in result['pairs']]},indent=2))

if __name__=='__main__':asyncio.run(main())
