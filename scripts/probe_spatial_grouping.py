"""Bounded recorded-state test of an optional spatial grouping mode."""
import asyncio
import copy
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dotenv import load_dotenv
from jev_sc2.jev import Jev

GROUPING_DESCRIPTION = ('Separate mobile non-worker units into local groups connected by distances of at most 12 map units. Each group receives independent Jev order decisions. Workers and other units retain their existing grouping. This changes selection organization only; it does not choose destinations, attacks, or regrouping orders.')

async def main():
    source, output = map(Path, sys.argv[1:3])
    rows = [json.loads(line) for line in source.read_text().splitlines()]
    samples = [r for r in rows if r['event']=='jev' and 'coordination' in r.get('questions', {})]
    if '--dispersed' in sys.argv:
        samples = [r for r in samples if r['state'].get('selection_facts',{}).get('MobileCombat',{}).get('max_separation',0)>12]
    if len(samples)<3: raise ValueError('Need three strategic requests')
    load_dotenv(Path(__file__).resolve().parents[1]/'.env')
    model = Jev(lambda *a, **k: None, 'spatial-grouping-probe', max_calls=6)
    result = {'source':str(source), 'method':'First/middle/last strategic requests; identical full question batch and state, add a spatial grouping mode without removing existing modes. Alternate arm order. Six calls maximum; no game commands.', 'criterion':GROUPING_DESCRIPTION, 'pairs':[]}
    for index in (0,len(samples)//2,len(samples)-1):
        row=samples[index]; pair={'time':row['time'],'loop':row['state'].get('game_loop')}; result['pairs'].append(pair)
        for arm in (['baseline','spatial_option'] if len(result['pairs'])%2 else ['spatial_option','baseline']):
            questions=copy.deepcopy(row['questions'])
            if arm=='spatial_option': questions['coordination']['criteria']['by_proximity']=GROUPING_DESCRIPTION
            pair[arm]=await model.ask(row['state'],questions)
            result.update(calls=model.calls,cost_usd=model.cost)
            output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'calls':model.calls,'cost_usd':model.cost,'choices':[{a:p[a]['coordination']['choice'] for a in ('baseline','spatial_option')} for p in result['pairs']]}))

if __name__=='__main__': asyncio.run(main())
