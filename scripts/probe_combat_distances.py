"""Recorded-state ablation of mechanically derived type-to-type distances."""
import asyncio
import json
import math
import sys
from collections import defaultdict
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from dotenv import load_dotenv
from jev_sc2.jev import Jev


def distances(state):
    encoded = state['units']
    own = [dict(zip(encoded['columns'], row)) for row in encoded['rows']]
    by_type = defaultdict(list)
    for unit in own:
        by_type[unit['type']].append(unit)
    enemies = defaultdict(list)
    visible = state['visible_entities']
    if isinstance(visible,dict):
        visible = [dict(zip(visible['columns'],row)) for row in visible['rows']]
    for unit in visible:
        if unit['alliance'] == 'Enemy':
            enemies[unit['type']].append(unit)
    pairs = []
    for owned_type, members in sorted(by_type.items()):
        for enemy_type, targets in sorted(enemies.items()):
            pairs.append({'owned_type': owned_type, 'owned_count':len(members),
                          'visible_enemy_type': enemy_type, 'visible_enemy_count':len(targets),
                          'minimum_center_distance':round(min(math.dist(u['position'],e['position']) for u in members for e in targets),2)})
    return {'pairs':pairs,'scope':'Euclidean distances between observed centers only. Not path lengths, attack legality, predicted damage, target priority, or a recommendation. Catalog weapon ranges remain separately available; radii, upgrades, terrain, and movement affect actual engagement.'}


async def main():
    load_dotenv(Path(__file__).resolve().parents[1]/'.env')
    source, output = map(Path,sys.argv[1:3])
    rows=[json.loads(l) for l in source.read_text().splitlines()]
    eligible=[r for r in rows if r['event']=='jev' and r['questions'] and
              all(q.get('type')=='score' and 'Order kind: ' in q.get('instructions','') for q in r['questions'].values()) and
              any(f.get('nearest_visible_enemy_distance') is not None and f['nearest_visible_enemy_distance']<12 for f in r['state'].get('selection_facts',{}).values())]
    if len(eligible)<3:raise ValueError('Need three recorded close-enemy states')
    model=Jev(lambda *a,**k:None,'combat-distance-ablation',max_calls=6)
    result={'source':str(source),'selection':'First/middle/last recorded kind-score requests with an enemy within 12 of any reported selection; this threshold only selects offline samples, never gameplay actions.','pairs':[]}
    for index in (0,len(eligible)//2,len(eligible)-1):
        row=eligible[index];extra=distances(row['state']);pair={'time':row['time'],'added_facts':extra}
        for arm in (['baseline','distances'] if len(result['pairs'])%2==0 else ['distances','baseline']):
            state=row['state'] if arm=='baseline' else {**row['state'],'observed_type_distances':extra}
            pair[arm]=await model.ask(state,row['questions'])
        result['pairs'].append(pair);result.update(calls=model.calls,cost=model.cost)
        output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'calls':model.calls,'cost':model.cost,'tops':[{arm:max(p[arm],key=lambda k:p[arm][k]['score']) for arm in ['baseline','distances']} for p in result['pairs']]}))

if __name__=='__main__':asyncio.run(main())
