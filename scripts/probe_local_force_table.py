"""Summarize existing visible force facts, without choosing an action."""
import asyncio,copy,json,math,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from dotenv import load_dotenv
from jev_sc2.jev import Jev

def records(value):
    if isinstance(value,dict) and 'columns' in value:
        return [dict(zip(value['columns'],row)) for row in value['rows']]
    return value or []

def summarize(state,key):
    members={m['tag'] for m in state['selection_facts'][key]['members']}
    own=[u for u in records(state['units']) if u['tag'] in members]
    enemies=[u for u in records(state['visible_entities']) if u['alliance']=='Enemy'
             and any(math.dist(u['position'],v['position'])<=12 for v in own)]
    catalog=state['unit_type_facts']
    if 'columns' in catalog:catalog={r['type_name']:r for r in records(catalog)}
    def table(units):
        rows={}
        for u in units:
            row=rows.setdefault(u['type'],{'count':0,'observed_health_plus_shields':0,
                'catalog_weapons':catalog.get(u['type'],{}).get('catalog_weapons',[])})
            row['count']+=1;row['observed_health_plus_shields']+=u.get('health',0)+u.get('shield',0)
        return rows
    return {'selection':table(own),'visible_enemies_within_12_of_any_member':table(enemies),
            'limits':'Aggregation of supplied visible facts only. This is not a battle prediction: range, terrain, dispersion, armor, bonuses, abilities, passengers and reinforcements affect outcomes. Empty catalog weapons does not establish harmlessness.'}

async def main():
    load_dotenv(Path(__file__).resolve().parents[1]/'.env')
    source,output=map(Path,sys.argv[1:3]);key='MobileCombat'
    es=[json.loads(s) for s in source.read_text().splitlines()]
    eligible=[e for e in es if e['event']=='jev' and key in e['questions'] and summarize(e['state'],key)['visible_enemies_within_12_of_any_member']]
    if len(eligible)<3:raise ValueError('Need three threatened selections')
    samples=[eligible[i] for i in (0,len(eligible)//2,len(eligible)-1)]
    jev=Jev(lambda *a,**k:None,'local-force-table-probe',max_calls=6);pairs=[]
    for i,e in enumerate(samples):
        addition=summarize(e['state'],key);state=copy.deepcopy(e['state']);state['local_force_table']=addition
        variants=[('original',e['state']),('summary',state)]
        if i%2:variants.reverse()
        pair={'loop':e['state']['game_loop'],'added_facts':addition}
        for name,s in variants:pair[name]=(await jev.ask(s,{key:e['questions'][key]}))[key]
        pairs.append(pair)
    out={'source':str(source),'method':'First/middle/last threatened MobileCombat records, identical menu insertion order in both arms, alternating request order. Add only aggregates of existing facts. No gameplay actions.','pairs':pairs,'calls':jev.calls,'cost':jev.cost}
    output.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({'cost':jev.cost,'choices':[(p['loop'],p['original']['choice'],p['summary']['choice']) for p in pairs]}))
if __name__=='__main__':asyncio.run(main())
