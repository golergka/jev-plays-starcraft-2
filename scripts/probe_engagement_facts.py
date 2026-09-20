"""Pair observed member/enemy geometry with existing catalog weapon facts."""
import asyncio
import json
import math
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from dotenv import load_dotenv
from jev_sc2.jev import Jev

def decode(value):
    return [dict(zip(value['columns'],r)) for r in value['rows']] if isinstance(value,dict) else value

def facts(state):
    tags={m['tag'] for m in state['selection_facts']['MobileCombat']['members']}
    enemies=[u for u in decode(state['visible_entities']) if u['alliance']=='Enemy']
    catalog=state['unit_type_facts'];pairs=[]
    for u in decode(state['units']):
        if u['tag'] not in tags or not enemies:continue
        e=min(enemies,key=lambda e:math.dist(u['position'],e['position']))
        pairs.append({'member':{'tag':u['tag'],'type':u['type'],'health':u['health']},
                      'nearest_visible_enemy':e,'center_distance':round(math.dist(u['position'],e['position']),2),
                      'member_catalog_weapons':catalog.get(u['type'],{}).get('catalog_weapons',[]),
                      'enemy_catalog_weapons':catalog.get(e['type'],{}).get('catalog_weapons',[])})
    return {'pairs':pairs,'scope':'Nearest by center distance, not greatest threat. Catalog weapons are not current attack legality; radii, target class, terrain, upgrades and abilities matter. Empty weapons do not prove harmless. No predicted damage, hidden enemies, recommended action or route.'}

async def main():
    source,output=map(Path,sys.argv[1:3]);rows=[json.loads(l) for l in source.read_text().splitlines()]
    rows=[r for r in rows if r['event']=='jev' and 'MobileCombat' in r.get('questions',{}) and (r['state'].get('selection_facts',{}).get('MobileCombat',{}).get('nearest_visible_enemy_distance') or 999)<12]
    if len(rows)<3:raise ValueError('Need three close-enemy concrete combat states')
    load_dotenv(Path(__file__).resolve().parents[1]/'.env');model=Jev(lambda *a,**k:None,'engagement-facts-probe',max_calls=6)
    result={'source':str(source),'method':'First/middle/last eligible concrete combat requests. Same full questions and state; treatment adds nearest-enemy geometry beside existing weapons. Alternating order; one pair/state, no performance claim.','pairs':[]}
    for i,row in enumerate([rows[0],rows[len(rows)//2],rows[-1]]):
        added=facts(row['state']);pair={'time':row['time'],'added_facts':added};result['pairs'].append(pair)
        for arm in (['baseline','paired'] if i%2==0 else ['paired','baseline']):
            state=row['state'] if arm=='baseline' else {**row['state'],'engagement_facts':added}
            pair[arm]=await model.ask(state,row['questions']);result.update(calls=model.calls,cost_usd=model.cost);output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'calls':model.calls,'cost_usd':model.cost,'choices':[{a:p[a]['MobileCombat']['choice'] for a in ('baseline','paired')} for p in result['pairs']]}))

if __name__=='__main__':asyncio.run(main())
