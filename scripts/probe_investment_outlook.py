"""Nine-call test of Jev's own no-purchase outlook feeding investment choice."""
import asyncio
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
    eligible=[r for r in rows if r['event']=='jev' and 'investment' in r['questions'] and r['state'].get('resources',{}).get('minerals',0)>=500]
    if len(eligible)<3:raise ValueError('Need three high-balance requests')
    model=Jev(lambda *a,**k:None,'investment-outlook-probe',max_calls=9)
    result={'source':str(source),'method':'First/middle/last >=500 mineral investment requests. Compare original to identical question with separate Jev-generated no-new-purchase outlook added to state. Outlook is a model estimate, not observation. Alternate baseline/enriched order. Nine calls maximum; no gameplay commands.','pairs':[]}
    for i in (0,len(eligible)//2,len(eligible)-1):
        row=eligible[i];q={'investment':row['questions']['investment']};pair={'recorded_time':row['time']}
        if not len(result['pairs'])%2:pair['original']=await model.ask(row['state'],q)
        outlook=await model.ask(row['state'],{'outlook':{'type':'choice','instructions':'Estimate the mission outlook if no further new units, structures or upgrades are purchased. Existing queues finish and currently owned units can still receive orders. Use only the supplied observations; hidden future events are unknown. This is an uncertain forecast, not a command.','criteria':{'likely_success':'The existing force and queued production are likely sufficient to complete the objective without further purchases.','unlikely_success':'The existing force and queued production are unlikely to complete the objective without further purchases.','uncertain':'The supplied evidence does not support either outlook confidently.'}}})
        pair['outlook']=outlook
        pair['with_outlook']=await model.ask({**row['state'],'jev_no_new_purchase_outlook':{'estimate':outlook,'interpretation':'Jev-generated uncertain forecast, not an observed result or instruction. Choose investment independently using current facts.'}},q)
        if len(result['pairs'])%2:pair['original']=await model.ask(row['state'],q)
        result['pairs'].append(pair);result.update(calls=model.calls,cost=model.cost)
        output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'calls':model.calls,'cost':model.cost}))

if __name__=='__main__':asyncio.run(main())
