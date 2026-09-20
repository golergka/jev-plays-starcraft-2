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
    for row in rows:
        if row['event']!='jev' or 'MobileCombat' not in row.get('questions',{}): continue
        facts=row['state']['selection_facts']['MobileCombat']
        if facts.get('max_separation',0)<=10: continue
        q=row['questions']['MobileCombat']
        eligible.append(({'time':row['time'],'options':len(q['criteria'])},row['state'],q))
    if len(eligible)<3:raise ValueError('Need three dispersed selection states')
    model=Jev(lambda *a,**k:None,'order-destination-family-probe',max_calls=9)
    descriptions={'regroup':'Gather at a chosen friendly unit or structure, using Move or attack-move. Jev chooses the anchor and movement mode next; this does not guarantee a safe route.', 'support':'Use an offered support ability with its specified executor.', 'other':'Use another offered order.', 'attack':'Attack a currently visible enemy unit.',
        'attack_move':'Move to a selected location, engaging enemies encountered along the route.',
        'move':'Move to a selected location without attacking along the route.',
        'hold':'Hold position instead of moving.', 'stop':'Stop current orders.',
        'continue':'Keep existing orders unchanged.', 'individual':'Ask Jev to choose separate individual orders.'}
    def family(key):
        if key in ('continue','individual'):return key
        if 'join_' in key:return 'regroup'
        if key.startswith('support_'):return 'support'
        if 'attack_move' in key:return 'attack_move'
        if key.startswith('group_attack_'):return 'attack'
        if key=='group_hold_position':return 'hold'
        if key=='group_stop':return 'stop'
        return 'move'
    result={'source':str(source),'method':'First/middle/last MobileCombat menus with max separation >10. Full Choice versus family then exact order. Unlike326, friendly destinations form one regroup family spanning Move and attack-move; support remains explicit. Every original option retained. Alternate arm order, nine-call ceiling. Exploratory, no game commands.','pairs':[]}
    for index in (0,len(eligible)//2,len(eligible)-1):
        event,state,full=eligible[index]
        groups={}
        for key,value in full['criteria'].items():groups.setdefault(family(key),{})[key]=value
        pair={'time':event['time'],'options':event['options'],'groups':{k:len(v) for k,v in groups.items()}}
        async def direct():
            pair['full']=(await model.ask(state,{'MobileCombat':full}))['MobileCombat']
        async def staged():
            q={'type':'choice','instructions':full['instructions']+' First choose the kind of order; its exact target or destination will be chosen separately.',
               'criteria':{k:descriptions[k] for k in groups}}
            pair['kind']=(await model.ask(state,{'MobileCombat':q}))['MobileCombat']
            selected=pair['kind']['choice']
            if selected not in groups:raise ValueError('Invalid order kind')
            pair['staged']=(await model.ask(state,{'MobileCombat':{**full,'criteria':groups[selected]}}))['MobileCombat']
        for action in ([staged,direct] if len(result['pairs'])%2 else [direct,staged]):await action()
        result['pairs'].append(pair);result.update(calls=model.calls,cost=model.cost)
        output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'calls':model.calls,'cost':model.cost,'choices':[{k:p[k]['choice'] for k in ('full','kind','staged')} for p in result['pairs']]}))

if __name__=='__main__':asyncio.run(main())
