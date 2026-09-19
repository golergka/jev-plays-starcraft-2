"""Offline paired test of continuation consequences, without gameplay commands."""
import asyncio
import copy
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from dotenv import load_dotenv
from jev_sc2.jev import Jev


async def main():
    load_dotenv(Path(__file__).resolve().parents[1]/'.env')
    source=Path(sys.argv[1]); output=Path(sys.argv[2]); key=sys.argv[3]
    rows=[json.loads(line) for line in source.read_text().splitlines()]
    samples=[]
    for row in rows:
        if row['event']!='jev' or row['state'].get('resources',{}).get('minerals',50)>=50: continue
        for candidate in row['questions']:
            if candidate.startswith(key) and row['state'].get('selection_facts',{}).get(candidate.removeprefix('purpose_'),{}).get('idle_count',0)>0:
                samples.append((row,candidate));break
        if len(samples)==3:break
    jev=Jev(lambda *args,**kwargs:None,'strategy-hint-probe',max_calls=6)
    pairs=[]
    for i,(row,key) in enumerate(samples):
        kind=key.removeprefix('purpose_')
        original=row['questions'][key]
        clarified=copy.deepcopy(row['state'])
        resources=clarified['resources']
        observed={label.split(' ',1)[1].split(' on visible')[0]
                  for labels in clarified.get('observed_capabilities_by_type',{}).values()
                  for label in labels if label.startswith(('Train ','Build '))}
        deficits={}
        for name in sorted(observed):
            cost=clarified.get('unit_type_facts',{}).get(name)
            if cost is None: continue
            deficits[name]={'additional_minerals':max(0,cost['mineral_cost']-resources['minerals']),
                            'additional_vespene':max(0,cost['gas_cost']-resources['vespene'])}
        clarified['catalog_resource_shortfalls_for_observed_production']=deficits
        clarified['shortfall_note']='Arithmetic only. Catalog costs may differ from actual ability costs; zero shortfall does not establish tech, producer, placement or supply eligibility.'
        variants=[('original',row['state']),('computed_shortfalls',clarified)]
        if i%2: variants.reverse()
        result={'sample':i,'question':key,'resources':resources,'shortfalls':deficits}
        for name,state in variants:
            result[name]=(await jev.ask(state,{key:original}))[key]
        pairs.append(result)
    payload={'source':str(source),'question':key,'pairs':pairs,'calls':jev.calls,'cost':jev.cost,
             'method':'First three recorded states with idle units and fewer than50minerals. Same question; add computed catalog resource shortfalls for previously observed Train/Build products. Catalog arithmetic does not certify legal ability cost or eligibility. Alternate pair order; no game commands.'}
    output.write_text(json.dumps(payload,indent=2)+'\n');print(json.dumps(payload,indent=2))


if __name__=='__main__':asyncio.run(main())
