"""Recorded-state comparison of catalog-weapon subgroup geometry."""
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
    source, output = map(Path,sys.argv[1:3])
    events=[json.loads(l) for l in source.read_text().splitlines()]
    ticks={e['loop']:{u['tag']:u for u in e['units']} for e in events if e['event']=='tick'}
    rows=[e for e in events if e['event']=='jev' and 'MobileCombat' in e.get('questions',{})
          and e['state']['selection_facts']['MobileCombat']['count']>1]
    samples=[rows[0],rows[len(rows)//2],rows[-1]]
    load_dotenv(Path(__file__).resolve().parents[1]/'.env')
    jev=Jev(lambda *a,**k:None,'weapon-geometry-probe',max_calls=6)
    result={'source':str(source),'pairs':[],'method':'First/middle/last multi-member MobileCombat order states. Same original question batch, all choices preserved. Treatment adds subgroup geometry derived from same-loop own positions and supplied catalog weapons. Alternating arms; no game commands, causal inference or claim that empty weapons means harmless.'}
    for i,e in enumerate(samples):
        state=copy.deepcopy(e['state']); loop=state['game_loop']; observed=ticks[loop]
        members=state['selection_facts']['MobileCombat']['members']; catalog=state['unit_type_facts']
        geometry={}
        for label,predicate in [('catalog_weapon_present',lambda w:bool(w)),('catalog_weapon_empty',lambda w:w==[])]:
            group=[observed[m['tag']] for m in members if predicate(catalog.get(m['type'],{}).get('catalog_weapons'))]
            geometry[label]={'count':len(group),'members':[{'tag':u['tag'],'type':u['type']} for u in group],
                'max_straight_line_separation':round(max((math.dist(a['position'],b['position']) for a in group for b in group),default=0),1) if group else None}
        geometry['limits']='Catalog weapons only, not effective fighting strength; empty catalog weapons does not exclude abilities, passengers or support. Straight-line separation is not path distance.'
        state['selection_facts']['MobileCombat']['catalog_weapon_subgroups']=geometry
        pair={'loop':loop,'added_facts':geometry,'answers':{}};result['pairs'].append(pair)
        for arm in (['baseline','geometry'] if i%2==0 else ['geometry','baseline']):
            pair['answers'][arm]=await jev.ask(e['state'] if arm=='baseline' else state,e['questions'])
            result.update(calls=jev.calls,cost_usd=jev.cost)
            output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'cost_usd':jev.cost,'pairs':[{'loop':p['loop'],**{a:v['MobileCombat']['choice'] for a,v in p['answers'].items()}} for p in result['pairs']]}))

if __name__=='__main__':asyncio.run(main())
