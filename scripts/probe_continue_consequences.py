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
    samples=[r for r in rows if r['event']=='jev' and key in r['questions'] and r['state'].get('selection_facts',{}).get(key.removeprefix('purpose_'),{}).get('idle_count',0)>0][:3]
    jev=Jev(lambda *args,**kwargs:None,'strategy-hint-probe',max_calls=6)
    pairs=[]
    for i,row in enumerate(samples):
        kind=key.removeprefix('purpose_')
        original=row['questions'][key]
        clarified=copy.deepcopy(original)
        facts=row['state']['selection_facts'][kind]
        clarified['criteria']['continue'] += f" This selection currently has {facts['idle_count']} idle units out of {facts['count']}. No new task is assigned to those idle units; existing automatic behavior may continue. Current orders: {facts['current_order_counts']}."
        variants=[('original',original),('clarified',clarified)]
        if i%2: variants.reverse()
        result={'sample':i,'idle_count':facts['idle_count'],'count':facts['count']}
        for name,question in variants:
            result[name]=(await jev.ask(row['state'],{key:question}))[key]
        pairs.append(result)
    payload={'source':str(source),'question':key,'pairs':pairs,'calls':jev.calls,'cost':jev.cost,
             'method':'First three recorded states with idle units. Append observed idle count and current orders to continue description; state and all other choices identical. Alternate pair order; no game commands.'}
    output.write_text(json.dumps(payload,indent=2)+'\n');print(json.dumps(payload,indent=2))


if __name__=='__main__':asyncio.run(main())
