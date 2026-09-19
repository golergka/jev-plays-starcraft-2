"""Offline paired test of per-selection context filtering on contribution decisions."""
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
    samples=[r for r in rows if r['event']=='jev' and key in r['questions'] and r['state'].get('strategy_chosen_by_jev')][:3]
    jev=Jev(lambda *args,**kwargs:None,'strategy-hint-probe',max_calls=6)
    pairs=[]
    for i,row in enumerate(samples):
        kind=key.removeprefix('purpose_')
        scoped={**row['state']}
        for field in ('selection_facts','type_selection_facts','unit_type_facts','observed_capabilities_by_type'):
            scoped[field]={kind:row['state'].get(field,{}).get(kind)}
        variants=[('original',row['state']),('scoped',scoped)]
        if i%2: variants.reverse()
        result={'original_state_chars':len(json.dumps(row['state'])),'scoped_state_chars':len(json.dumps(scoped)),'sample':i,'recorded_strategy':row['state']['strategy_chosen_by_jev']}
        for name,state in variants:
            result[name]=(await jev.ask(state,{key:row['questions'][key]}))[key]
        pairs.append(result)
    payload={'source':str(source),'question':key,'pairs':pairs,'calls':jev.calls,'cost':jev.cost,
             'method':'First three recorded states. Restrict selection/type/capability dictionaries to the selection being asked about; retain all other fields and exact question. Alternate pair order; no game commands.'}
    output.write_text(json.dumps(payload,indent=2)+'\n');print(json.dumps(payload,indent=2))


if __name__=='__main__':asyncio.run(main())
