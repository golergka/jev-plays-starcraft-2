"""Six-call recorded-state probe: each executable purchase versus waiting."""
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
              and r['response']['answers'].get('investment',{}).get('choice')=='save']
    if len(eligible)<3:raise ValueError('Need three eligible states')
    samples=[eligible[i] for i in (0,len(eligible)//2,len(eligible)-1)]
    model=Jev(lambda *a,**k:None,'investment-pairwise-probe',max_calls=6)
    result={'source':str(source),'method':'First/middle/last high-balance top-save states. Original menu versus independent pairwise comparisons of every executable purchase with unchanged save description. Identical observations, alternating variant order. Pairwise choices do not authorize simultaneous purchases; probabilities across pairs are not a joint distribution. No game actions; three samples cannot establish significance.','pairs':[]}
    for i,row in enumerate(samples):
        q=row['questions']['investment']
        projects={k:v for k,v in q['criteria'].items() if k.startswith(('project_','batch_'))}
        pair={'recorded_time':row['time'],'resources':row['state']['resources'],'projects':projects}
        for variant in (['original','pairwise'] if i%2==0 else ['pairwise','original']):
            questions=({'investment':q} if variant=='original' else {
                k:{'type':'choice','instructions':'Compare these two mutually exclusive alternatives for this review. Which better contributes to the mission objective given current resources, force and existing work? Each question is an independent comparison, not authorization to purchase multiple projects.',
                   'criteria':{'purchase':v,'wait':q['criteria']['save']}} for k,v in projects.items()})
            pair[variant]=await model.ask(row['state'],questions)
        result['pairs'].append(pair)
        result.update(calls=model.calls,cost=model.cost)
        output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'calls':model.calls,'cost':model.cost,'pairs':[{
        'original':p['original']['investment']['choice'],
        'purchase_choices':[k for k,v in p['pairwise'].items() if v['choice']=='purchase'],
        'purchase_probabilities':{k:v['probabilities'].get('purchase') for k,v in p['pairwise'].items()}}
        for p in result['pairs']]},indent=2))

if __name__=='__main__':asyncio.run(main())
