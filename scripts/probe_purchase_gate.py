"""Recorded-state diagnostic: Jev chooses spending versus waiting; no game orders."""
import asyncio,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from dotenv import load_dotenv
from jev_sc2.jev import Jev

async def main():
    source,output=map(Path,sys.argv[1:3]);loops=set(map(int,sys.argv[3:]))
    if output.exists():raise FileExistsError(output)
    rows=[json.loads(s) for s in source.read_text().splitlines()]
    selected=[e for e in rows if e['event']=='jev' and 'investment' in e.get('questions',{}) and e['state'].get('game_loop') in loops]
    assert len(selected)==len(loops)
    load_dotenv(Path(__file__).resolve().parents[1]/'.env')
    model=Jev(lambda *a,**k:None,'purchase-gate-probe',max_calls=len(selected));results=[]
    for e in selected:
        options=e['questions']['investment']['criteria']
        state={**e['state'],'available_purchase_menu':options}
        answer=await model.ask(state,{'purchase_gate':{'type':'choice','instructions':'Decide whether to make a new purchase now or defer new spending, using the current observations and available purchase menu. This is a diagnostic choice, not an executed order. A later decision would choose the exact purchase; neither option changes existing queues or repair spending.','criteria':{'purchase':'Make one of the available new purchases or training commitments; a separate Jev decision chooses which.','wait':'Make no new purchase now, leaving resources available for later decisions and ongoing work.'}}})
        results.append({'loop':e['state']['game_loop'],'original':e['response']['answers']['investment'],'gate':answer['purchase_gate']})
    output.write_text(json.dumps({'source':str(source),'method':'One gate call per recorded state; original choice reused from live log, not a contemporaneous paired control. No actions executed. Gate does not select a specific project or prove better play.','results':results,'calls':model.calls,'cost':model.cost},indent=2)+'\n')
    print(json.dumps({'calls':model.calls,'cost':model.cost,'choices':[(x['loop'],x['gate']['choice']) for x in results]}))
if __name__=='__main__':asyncio.run(main())
