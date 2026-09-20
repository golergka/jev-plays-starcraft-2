"""Offline sizing of already Jev-selected training commitments."""
import asyncio
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from dotenv import load_dotenv
from jev_sc2.jev import Jev

async def main():
    load_dotenv(Path(__file__).resolve().parents[1]/'.env')
    source, output=map(Path,sys.argv[1:3])
    rows=[json.loads(l) for l in source.read_text().splitlines()]
    cases=[];latest=None
    for row in rows:
        if row['event']=='jev' and 'investment' in row['questions']:latest=row
        if row['event']=='production_batch_chosen' and latest:
            cases.append((row,latest))
    if not cases:raise ValueError('No chosen batches')
    selected=cases if len(cases)<=6 else [cases[round(i*(len(cases)-1)/5)] for i in range(6)]
    model=Jev(lambda *a,**k:None,'batch-size-probe',max_calls=6)
    result={'source':str(source),'method':'Up to six already chosen training batches. Ask size conditional on recorded Jev-selected type; no added type duplicates, no commands, no deployment.','cases':[]}
    for event,prior in selected:
        name=event['target_project'];catalog=prior['state']['unit_type_facts'][name]
        costs={'minerals':catalog['mineral_cost'],'vespene':catalog['gas_cost'],'supply':catalog['supply_required']}
        criteria={'cancel':'Cancel this training commitment; keep resources for another decision.'}
        for n in [1,3,6,12]:
            total={k:v*n for k,v in costs.items()}
            criteria[f'requests_{n}']=f'Authorize at most {n} training requests for {name} within 2016 game loops. Maximum aggregate listed costs if all requests execute: {total}. This is a request allowance, not guaranteed completed units.'
        question={'type':'choice','instructions':f'Jev has selected a training commitment for {name}. Choose its size given current resources, force, objective, and priorities. The producer is chosen separately and remains fixed. Requests execute only while affordable and legal, at least112loops apart, and stop when the allowance ends, 2016loops pass, the producer disappears, or strategic priority changes. This commitment has priority over other new purchases while active. Rejected/stale requests consume attempts. You may cancel.','criteria':criteria}
        answer=(await model.ask(prior['state'],{'batch_size':question}))['batch_size']
        if answer.get('choice') not in criteria:raise ValueError('Invalid batch size')
        result['cases'].append({'loop':event['loop'],'type':name,'question':question,'answer':answer})
        result.update(calls=model.calls,cost=model.cost)
        output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'calls':model.calls,'cost':model.cost,'choices':[(c['type'],c['answer']['choice']) for c in result['cases']]}))

if __name__=='__main__':asyncio.run(main())
