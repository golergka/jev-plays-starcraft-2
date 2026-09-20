"""Offline geometry probe for offered six-unit cardinal moves."""
import asyncio
import copy
import json
import math
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from dotenv import load_dotenv
from jev_sc2.jev import Jev

async def main():
    source,output=map(Path,sys.argv[1:3]); rows=[]
    for line in source.read_text().splitlines():
        e=json.loads(line)
        if e['event']!='jev':continue
        q=e.get('questions',{}).get('MobileCombat',{})
        f=e['state'].get('selection_facts',{}).get('MobileCombat',{})
        if (f.get('count',99)<=2 and f.get('visible_enemies_within_12_of_any_member')
            and any(k.startswith('group_map_') for k in q.get('criteria',{}))):
            rows.append(e)
    if len(rows)<3:raise ValueError('Need three eligible concrete menus')
    load_dotenv(Path(__file__).resolve().parents[1]/'.env')
    model=Jev(lambda *a,**k:None,'cardinal-geometry-probe',max_calls=6)
    result={'source':str(source),'eligible':len(rows),'pairs':[], 'method':'First/middle/last concrete MobileCombat menus with at most two members, nearby visible enemies and map destinations. Same full state and every option; append per-member nearest-visible-enemy before/endpoint distances for cardinal options only. Alternate arms; no game commands, forced retreat or action filtering.'}
    for i,e in enumerate([rows[0],rows[len(rows)//2],rows[-1]]):
        qs=copy.deepcopy(e['questions'])
        def records(value):
            return [dict(zip(value['columns'],row)) for row in value['rows']] if isinstance(value,dict) else value
        units={u['tag']:u for u in records(e['state']['units'])}
        enemies=[u for u in records(e['state']['visible_entities']) if u['alliance']=='Enemy']
        members=e['state']['selection_facts']['MobileCombat']['members']
        geometry={}
        for direction,(dx,dy) in {'north':(0,6),'south':(0,-6),'east':(6,0),'west':(-6,0)}.items():
            for key in ('group_'+direction,'group_attack_move_'+direction):
                if key not in qs['MobileCombat']['criteria']:continue
                distances=[]
                for member in members:
                    pos=units[member['tag']]['position']
                    before=min(math.dist(pos,x['position']) for x in enemies)
                    after=min(math.dist([pos[0]+dx,pos[1]+dy],x['position']) for x in enemies)
                    distances.append({'tag':member['tag'],'before':round(before,1),'endpoint':round(after,1)})
                geometry[key]=distances
                qs['MobileCombat']['criteria'][key]+='; per-member nearest current-visible-enemy distance before and at endpoint: '+json.dumps(distances)+'. Uses rounded observed coordinates, assumes enemies stay still; nearest enemy identity may change. Does not assess weapon range, damage, actual route, or safety; some enemy entities cannot attack.'
        p={'loop':e['state']['game_loop'],'geometry':geometry,'answers':{}};result['pairs'].append(p)
        for arm in (['baseline','local'] if i%2==0 else ['local','baseline']):
            q=e['questions'] if arm=='baseline' else qs
            a=(await model.ask(e['state'],q))['MobileCombat']
            p['answers'][arm]={'answer':a,'description':q['MobileCombat']['criteria'].get(a['choice'])}
            result.update(calls=model.calls,cost_usd=model.cost);output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'calls':model.calls,'cost':model.cost,'pairs':[{'loop':p['loop'],**{k:v['answer']['choice'] for k,v in p['answers'].items()}} for p in result['pairs']]}))

if __name__=='__main__':asyncio.run(main())
