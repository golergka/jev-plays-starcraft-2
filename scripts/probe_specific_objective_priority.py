"""Bounded test of a narrower objective-interaction strategy description."""
import asyncio
import copy
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dotenv import load_dotenv
from jev_sc2.jev import Jev

OBJECTIVE_PRIORITY = ('Use existing forces to perform an identified mission-objective interaction or move toward its known location. '
                      'This priority does not include producing additional forces, assembling a force, or scouting to discover an unknown objective location; those have separate priorities.')

async def main():
    source, output = map(Path, sys.argv[1:3])
    rows = [json.loads(line) for line in source.read_text().splitlines()]
    samples = [r for r in rows if r['event']=='jev' and 'strategy' in r.get('questions', {})]
    if len(samples)<3: raise ValueError('Need three strategic requests')
    load_dotenv(Path(__file__).resolve().parents[1]/'.env')
    model = Jev(lambda *a, **k: None, 'specific-objective-priority-probe', max_calls=6)
    result = {'source':str(source), 'method':'First/middle/last strategic requests; identical full question batch and state, replace only the broad pursue_objective description with a specific existing-force interaction/movement priority. Alternate arm order. Six calls maximum; no game commands.', 'criterion':OBJECTIVE_PRIORITY, 'pairs':[]}
    for index in (0,len(samples)//2,len(samples)-1):
        row=samples[index]; pair={'time':row['time']}; result['pairs'].append(pair)
        for arm in (['baseline','specific_priority'] if len(result['pairs'])%2 else ['specific_priority','baseline']):
            questions=copy.deepcopy(row['questions'])
            if arm=='specific_priority': questions['strategy']['criteria']['pursue_objective']=OBJECTIVE_PRIORITY
            pair[arm]=await model.ask(row['state'],questions)
            result.update(calls=model.calls,cost_usd=model.cost)
            output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'calls':model.calls,'cost_usd':model.cost,'choices':[{a:p[a]['strategy']['choice'] for a in ('baseline','specific_priority')} for p in result['pairs']]}))

if __name__=='__main__': asyncio.run(main())
