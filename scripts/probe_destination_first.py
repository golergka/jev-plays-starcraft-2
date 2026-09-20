"""Offline exact-destination-first decomposition; all original orders retained."""
import asyncio
import json
import re
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dotenv import load_dotenv
from jev_sc2.jev import Jev


def destination(key):
    for pattern, label in (
        (r'group_map_(?:attack_move|move)_(.+)', 'sector_'),
        (r'group_last_known_(?:attack_move|move)_(.+)', 'remembered_'),
        (r'group_(?:attack_move_)?(north|south|east|west)', 'relative_'),
        (r'group_(?:attack_move_join|attack_move|move|attack|join)_(\d+)', 'entity_'),
    ):
        match = re.fullmatch(pattern, key)
        if match:
            return label + match.group(1)
    return 'order_' + key

async def main():
    source, output = map(Path, sys.argv[1:3])
    events = [json.loads(l) for l in source.read_text().splitlines()]
    rows = [e for e in events if e['event']=='jev' and
            'MobileCombat' in e.get('questions', {}) and e['state'].get('game_loop',0)>=1500][:3]
    if len(rows)!=3: raise ValueError('Need three recorded concrete menus')
    load_dotenv(Path(__file__).resolve().parents[1]/'.env')
    model = Jev(lambda *a, **k: None, 'destination-first-probe', max_calls=9)
    result = {'source':str(source), 'method':'Three first concrete menus after loop1500. Fresh full-menu baseline versus exact destination then original order. All options partitioned, no preferred destination. Alternating arms; at most nine calls; offline only.', 'pairs':[]}
    for i,e in enumerate(rows):
        q=e['questions']['MobileCombat']; groups={}
        for key,description in q['criteria'].items():
            groups.setdefault(destination(key),{})[key]=description
        assert {k:v for g in groups.values() for k,v in g.items()}==q['criteria']
        pair={'loop':e['state']['game_loop'],'original_count':len(q['criteria']), 'destination_count':len(groups),'answers':{}}
        result['pairs'].append(pair)
        async def baseline():
            pair['answers']['baseline']=(await model.ask(e['state'],e['questions']))['MobileCombat']
        async def staged():
            query={**q,'instructions':q['instructions']+' First select the exact destination or nonspatial order. Available execution modes are listed together; choose one of those modes next. No option is a recommendation.',
                   'criteria':{k:'Available original orders at this destination: '+' | '.join(g.values()) for k,g in groups.items()}}
            answer=(await model.ask(e['state'],{'MobileCombat':query}))['MobileCombat']
            if answer['choice'] not in groups:raise ValueError('Invalid destination')
            pair['destination']=answer
            qs={**e['questions'],'MobileCombat':{**q,'criteria':groups[answer['choice']]}}
            pair['answers']['destination_first']=(await model.ask(e['state'],qs))['MobileCombat']
        for fn in ([baseline,staged] if i%2==0 else [staged,baseline]):await fn()
        for arm,a in pair['answers'].items():
            if a['choice'] not in q['criteria']:raise ValueError('Invalid order')
            a['description']=q['criteria'][a['choice']]
        result.update(calls=model.calls,cost_usd=model.cost)
        output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'calls':model.calls,'cost':model.cost,'pairs':[{'loop':p['loop'],**{a:v['choice'] for a,v in p['answers'].items()}} for p in result['pairs']]}))

if __name__=='__main__':asyncio.run(main())
