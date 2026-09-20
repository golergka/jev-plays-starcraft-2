"""Offline destination-category decomposition; preserves all concrete options."""
import asyncio
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from dotenv import load_dotenv
from jev_sc2.jev import Jev


def category(key):
    if key.startswith('group_map_'):return 'sector'
    if key.startswith('group_last_known_'):return 'remembered'
    if key in {'group_'+d for d in ('north','south','east','west')} | {'group_attack_move_'+d for d in ('north','south','east','west')}:return 'local'
    if key.startswith(('group_move_','group_attack_move_')):return 'visible'
    return 'other'

async def main():
    source,output=map(Path,sys.argv[1:3]);rows=[]
    for line in source.read_text().splitlines():
        e=json.loads(line)
        if e['event']!='jev':continue
        q=e.get('questions',{}).get('MobileCombat',{});f=e['state'].get('selection_facts',{}).get('MobileCombat',{})
        if f.get('count',99)<=2 and f.get('visible_enemies_within_12_of_any_member') and any(k.startswith('group_map_') for k in q.get('criteria',{})):rows.append(e)
    if len(rows)<3:raise ValueError('Need three eligible states')
    load_dotenv(Path(__file__).resolve().parents[1]/'.env')
    model=Jev(lambda *a,**k:None,'destination-category-probe',max_calls=9)
    result={'source':str(source),'pairs':[],'method':'Same first/middle/last small-force threatened concrete menus as474. Baseline full menu versus Jev destination category then exact choice. Every original option appears in exactly one category. Same observed state; alternating arms. No commands or forced local movement.'}
    labels={'sector':'A map-sector destination. Distance and observed terrain vary; this is not necessarily an objective location or safe route.', 'remembered':'A last-known entity location under fog; current presence is unknown.', 'local':'A six-map-unit cardinal step from each unit position; terrain and nearby threats still matter.', 'visible':'A currently visible entity or its observed location; affiliation, distance and utility vary.', 'other':'Another originally offered order.'}
    for i,e in enumerate([rows[0],rows[len(rows)//2],rows[-1]]):
        q=e['questions']['MobileCombat'];groups={}
        for k,v in q['criteria'].items():groups.setdefault(category(k),{})[k]=v
        assert sum(map(len,groups.values()))==len(q['criteria'])
        p={'loop':e['state']['game_loop'],'category_sizes':{k:len(v) for k,v in groups.items()},'answers':{}};result['pairs'].append(p)
        async def baseline():
            p['answers']['baseline']=(await model.ask(e['state'],e['questions']))['MobileCombat']
        async def staged():
            cq={'type':'choice','instructions':q['instructions']+' First choose which kind of destination to use; the exact original destination will be selected next.', 'criteria':{k:labels[k] for k in groups}}
            a=(await model.ask(e['state'],{'MobileCombat':cq}))['MobileCombat'];p['category_answer']=a
            if a['choice'] not in groups:raise ValueError('Invalid category')
            qs={**e['questions'],'MobileCombat':{**q,'criteria':groups[a['choice']]}}
            p['answers']['staged']=(await model.ask(e['state'],qs))['MobileCombat']
        for action in ([baseline,staged] if i%2==0 else [staged,baseline]):await action()
        result.update(calls=model.calls,cost_usd=model.cost);output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'calls':model.calls,'cost':model.cost,'pairs':[{'loop':p['loop'],'category':p['category_answer']['choice'],**{k:v['choice'] for k,v in p['answers'].items()}} for p in result['pairs']]}))

if __name__=='__main__':asyncio.run(main())
