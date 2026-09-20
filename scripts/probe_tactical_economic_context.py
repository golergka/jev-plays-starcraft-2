"""Offline paired test of a economic context on a selected question."""
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
    minimum_loop=int(sys.argv[4]) if len(sys.argv)>4 else 0
    samples=[r for r in rows if r['event']=='jev' and key in r['questions'] and r['state'].get('strategy_chosen_by_jev') and r['state'].get('game_loop',0)>=minimum_loop][:3]
    if len(samples)!=3: raise ValueError('Need three eligible recorded requests')
    jev=Jev(lambda *args,**kwargs:None,'tactical-economic-context-probe',max_calls=6)
    pairs=[]
    for i,row in enumerate(samples):
        removed = {'resources','harvesting_assignments','previous_investment_intent','production_commitment'}
        variants=[('full',row['state']),('without_economy',{k:v for k,v in row['state'].items() if k not in removed})]
        if i%2: variants.reverse()
        result={'sample':i,'loop':row['state'].get('game_loop'),'recorded_strategy':row['state']['strategy_chosen_by_jev']}
        for name,state in variants:
            result[name]=(await jev.ask(state,{key:row['questions'][key]}))[key]
        pairs.append(result)
    payload={'source':str(source),'question':key,'pairs':pairs,'calls':jev.calls,'cost':jev.cost,
             'method':'Remove resources, harvesting_assignments, previous_investment_intent and production_commitment from three recorded states. Retain objective, units, visible and stale entities, terrain, type facts, outcomes and strategy. Same selected question, alternating pair order. No game commands.'}
    output.write_text(json.dumps(payload,indent=2)+'\n');print(json.dumps(payload,indent=2))


if __name__=='__main__':asyncio.run(main())
