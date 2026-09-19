"""Recorded-state test of optional independent worker decisions; no game commands."""
import asyncio
import copy
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from dotenv import load_dotenv
from jev_sc2.jev import Jev

DESCRIPTION = ('Give each observed harvesting/building worker its own contribution and order decisions, allowing mixed assignments even when workers currently share one job. Other units remain grouped by type. This requires more model decisions.')

async def main():
    source, output = map(Path,sys.argv[1:3])
    if output.exists():raise FileExistsError(output)
    samples=[]
    for line in source.read_text().splitlines():
        row=json.loads(line)
        if row['event']!='jev' or 'coordination' not in row['questions']:continue
        facts=row['state'].get('selection_facts',{})
        if sum(f.get('count',0) for f in facts.values() if f.get('some_can_harvest_minerals'))>=4:
            samples.append(row)
    if not samples:raise ValueError('No states with multiple observed harvesting workers')
    selected=[samples[i] for i in sorted({0,len(samples)//2,len(samples)-1})]
    load_dotenv(Path(__file__).resolve().parents[1]/'.env')
    model=Jev(lambda *a,**k:None,'worker-grouping-probe',max_calls=6)
    results=[]
    for i,row in enumerate(selected):
        original=copy.deepcopy(row['questions'])
        original['coordination']['criteria'].pop('individual_workers',None)
        expanded=copy.deepcopy(original)
        expanded['coordination']['criteria']['individual_workers']=DESCRIPTION
        variants=[('original',original),('expanded',expanded)]
        if i%2:variants.reverse()
        result={'recorded_time':row['time'],'resources':row['state'].get('resources')}
        for label,questions in variants:
            result[label]=await model.ask(row['state'],questions)
        results.append(result)
    payload={'source':str(source),'method':'First/middle/last qualifying strategy request with at least four observed harvesting workers; identical state and existing choices; add individual worker grouping; alternate request order. No commands, single trials.', 'results':results,'calls':model.calls,'cost':model.cost}
    output.write_text(json.dumps(payload,indent=2)+'\n')
    print(json.dumps({'calls':model.calls,'cost':model.cost,'choices':[{k:v['coordination']['choice'] for k,v in r.items() if k in ('original','expanded')} for r in results]}))

if __name__=='__main__':asyncio.run(main())
