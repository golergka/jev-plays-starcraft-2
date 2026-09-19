"""Nine-call recorded-state probe; ranks a project then asks buy versus wait."""
import asyncio
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
    rows=[json.loads(line) for line in source.read_text().splitlines()]
    eligible=[r for r in rows if r['event']=='jev' and 'investment' in r['questions']
              and r['state'].get('resources',{}).get('minerals',0)>=500
              and r['response']['answers'].get('investment',{}).get('choice')=='save'
              and 'strategy_chosen_by_jev' in r['state']]
    if len(eligible)<3:raise ValueError('Need three eligible recorded states')
    samples=[eligible[i] for i in (0,len(eligible)//2,len(eligible)-1)]
    model=Jev(lambda *a,**k:None,'investment-stages-probe',max_calls=9)
    result={'source':str(source),'method':'First/middle/last high-balance recorded top-save states. Original menu versus project ranking followed by binary authorization. Alternate baseline/staged order. Ranking is conditional, not a purchase authorization. Identical observed state; no gameplay commands. Three single pairs cannot establish significance.','pairs':[]}
    for i,row in enumerate(samples):
        question=row['questions']['investment']
        projects={k:v for k,v in question['criteria'].items() if k.startswith(('project_','batch_'))}
        pair={'recorded_time':row['time'],'resources':row['state']['resources']}
        for variant in (['original','staged'] if i%2==0 else ['staged','original']):
            if variant=='original':
                pair['original']=(await model.ask(row['state'],{'investment':question}))['investment']
                continue
            ranking=(await model.ask(row['state'],{'project':{'type':'choice',
                'instructions':'If making a new investment now, which executable project would contribute most to the mission objective? Rank projects only; a separate decision will choose whether to buy or wait.',
                'criteria':projects}}))['project']
            chosen=ranking.get('choice')
            if chosen not in projects:raise ValueError('Invalid project ranking')
            gate=(await model.ask(row['state'],{'authorize':{'type':'choice',
                'instructions':'Choose whether to authorize this proposed investment now or wait. Consider its marginal benefit, cost, current force and existing work relative to the mission objective. The prior conditional ranking did not authorize spending.',
                'criteria':{'purchase':projects[chosen], 'wait':question['criteria']['save']}}}))['authorize']
            pair['staged']={'ranking':ranking,'proposal':projects[chosen],'authorization':gate}
        result['pairs'].append(pair)
        result.update(calls=model.calls,cost=model.cost)
        output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'calls':model.calls,'cost':model.cost,'pairs':[{'original':p['original']['choice'],'original_save_probability':p['original']['probabilities'].get('save'),'project':p['staged']['ranking']['choice'],'authorization':p['staged']['authorization']} for p in result['pairs']]},indent=2))

if __name__=='__main__':asyncio.run(main())
