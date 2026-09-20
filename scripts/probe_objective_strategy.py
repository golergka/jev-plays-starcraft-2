"""Bounded recorded-state test of an objective-directed strategic option."""
import asyncio
import copy
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dotenv import load_dotenv
from jev_sc2.jev import Jev

OBJECTIVE_PRIORITY = ('Commit effort to completing the active primary mission objectives described in mission_context. '
                      'Further decisions choose the necessary movement, interactions, combat or preparation; '
                      'this priority does not assume the objective is destruction of an enemy base.')

async def main():
    source, output = map(Path, sys.argv[1:3])
    rows = [json.loads(line) for line in source.read_text().splitlines()]
    samples = [r for r in rows if r['event']=='jev' and 'strategy' in r.get('questions', {})]
    if len(samples)<3: raise ValueError('Need three strategic requests')
    load_dotenv(Path(__file__).resolve().parents[1]/'.env')
    model = Jev(lambda *a, **k: None, 'objective-strategy-probe', max_calls=6)
    result = {'source':str(source), 'method':'First/middle/last strategic requests; identical full question batch and state, add one general primary-objective priority. Alternate arm order. Six calls maximum; no game commands.', 'criterion':OBJECTIVE_PRIORITY, 'pairs':[]}
    for index in (0,len(samples)//2,len(samples)-1):
        row=samples[index]; pair={'time':row['time']}; result['pairs'].append(pair)
        for arm in (['baseline','objective_option'] if len(result['pairs'])%2 else ['objective_option','baseline']):
            questions=copy.deepcopy(row['questions'])
            if arm=='objective_option': questions['strategy']['criteria']['pursue_objective']=OBJECTIVE_PRIORITY
            pair[arm]=await model.ask(row['state'],questions)
            result.update(calls=model.calls,cost_usd=model.cost)
            output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'calls':model.calls,'cost_usd':model.cost,'choices':[{a:p[a]['strategy']['choice'] for a in ('baseline','objective_option')} for p in result['pairs']]}))

if __name__=='__main__': asyncio.run(main())
