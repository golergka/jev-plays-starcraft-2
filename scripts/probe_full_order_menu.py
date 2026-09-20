"""Compare reconstructed full menus with recorded tournament finalists; no commands."""
import asyncio
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from dotenv import load_dotenv
from jev_sc2.jev import Jev

async def main():
    load_dotenv(Path(__file__).resolve().parents[1]/'.env')
    source, output = map(Path,sys.argv[1:3])
    rows=[json.loads(l) for l in source.read_text().splitlines()]
    eligible=[]
    for i,row in enumerate(rows):
        if row['event']!='order_menu_tournament' or row.get('question')!='Marine': continue
        preceding=[r for r in rows[:i] if r['event']=='jev' and 'Marine' in r['questions']][-2:]
        if len(preceding)!=2 or preceding[0]['state']!=preceding[1]['state']:continue
        criteria={k:v for r in preceding for k,v in r['questions']['Marine']['criteria'].items()}
        if len(criteria)!=row['options']:continue
        q={**preceding[0]['questions']['Marine'],'criteria':criteria}
        eligible.append((row,preceding[0]['state'],q))
    if len(eligible)<3:raise ValueError('Cannot reconstruct three exact full menus')
    model=Jev(lambda *a,**k:None,'full-order-menu-probe',max_calls=6)
    result={'source':str(source),'method':'First/middle/last exactly reconstructed two-part Marine tournaments. Same state, full criteria vs original finalists; alternate order. No game commands. Six-call cap.','pairs':[]}
    for index in (0,len(eligible)//2,len(eligible)-1):
        event,state,full=eligible[index]
        final={**full,'criteria':{k:full['criteria'][k] for k in event['finalists']}}
        pair={'time':event['time'],'options':event['options'],'recorded_finalists':event['finalists']}
        variants=[('full',full),('finalists',final)]
        if len(result['pairs'])%2:variants.reverse()
        for label,q in variants:pair[label]=(await model.ask(state,{'Marine':q}))['Marine']
        result['pairs'].append(pair);result.update(calls=model.calls,cost=model.cost)
        output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'calls':model.calls,'cost':model.cost,'choices':[{k:p[k]['choice'] for k in ('full','finalists')} for p in result['pairs']]}))

if __name__=='__main__':asyncio.run(main())
