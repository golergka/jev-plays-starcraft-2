"""Compare full combat menus with Jev-selected order kind then exact order."""
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
    model=Jev(lambda *a,**k:None,'order-kind-probe',max_calls=9)
    descriptions={'attack':'Attack a currently visible enemy unit.',
        'attack_move':'Move to a selected location, engaging enemies encountered along the route.',
        'move':'Move to a selected location without attacking along the route.',
        'hold':'Hold position instead of moving.', 'stop':'Stop current orders.',
        'continue':'Keep existing orders unchanged.', 'individual':'Ask Jev to choose separate individual orders.'}
    def family(key):
        if key in ('continue','individual'):return key
        if 'attack_move' in key:return 'attack_move'
        if key.startswith('group_attack_'):return 'attack'
        if key=='group_hold_position':return 'hold'
        if key=='group_stop':return 'stop'
        return 'move'
    result={'source':str(source),'method':'First/middle/last exact reconstructed Marine menus; full direct Choice versus order-kind Choice followed by exact within-kind Choice. All options retained. Alternate arm order, nine-call ceiling. No game commands.','pairs':[]}
    for index in (0,len(eligible)//2,len(eligible)-1):
        event,state,full=eligible[index]
        groups={}
        for key,value in full['criteria'].items():groups.setdefault(family(key),{})[key]=value
        pair={'time':event['time'],'options':event['options'],'groups':{k:len(v) for k,v in groups.items()}}
        async def direct():
            pair['full']=(await model.ask(state,{'Marine':full}))['Marine']
        async def staged():
            q={'type':'choice','instructions':full['instructions']+' First choose the kind of order; its exact target or destination will be chosen separately.',
               'criteria':{k:descriptions[k] for k in groups}}
            pair['kind']=(await model.ask(state,{'Marine':q}))['Marine']
            selected=pair['kind']['choice']
            if selected not in groups:raise ValueError('Invalid order kind')
            pair['staged']=(await model.ask(state,{'Marine':{**full,'criteria':groups[selected]}}))['Marine']
        for action in ([staged,direct] if len(result['pairs'])%2 else [direct,staged]):await action()
        result['pairs'].append(pair);result.update(calls=model.calls,cost=model.cost)
        output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'calls':model.calls,'cost':model.cost,'choices':[{k:p[k]['choice'] for k in ('full','kind','staged')} for p in result['pairs']]}))

if __name__=='__main__':asyncio.run(main())
