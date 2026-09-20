"""Extract opening combat decisions and observed membership, without API calls."""
import json
import sys
from pathlib import Path

def audit(run, limit=1600):
    events=[json.loads(line) for line in (run/'events.jsonl').read_text().splitlines()]
    ticks=[e for e in events if e['event']=='tick' and e['loop']<limit]
    if not ticks: raise ValueError('No opening ticks')
    end=ticks[-1]['time']
    decisions=[]
    for e in events:
        if e['event']!='jev' or e['time']>end or 'MobileCombat' not in e.get('questions',{}):continue
        answer=e['response']['answers']['MobileCombat']
        decisions.append({'time':e['time'],'choice':answer['choice'],
                          'criterion':e['questions']['MobileCombat']['criteria'].get(answer['choice']),
                          'selection_facts':e['state'].get('selection_facts',{}).get('MobileCombat')})
    return {'run':str(run),'loop_limit':limit,'decisions':decisions,
            'ticks':[{'loop':e['loop'],'time':e['time'],
                      'combat_units':[u for u in e['units'] if u['type'] in ('Marine','Medic','Marauder','Firebat')],
                      'submitted_actions':e.get('submitted_actions',[])} for e in ticks],
            'limits':'Opening Terran audit only, not general policy. Missing units are observation disappearances, not attributed deaths. Shared map-point orders do not reveal the engine path. Count stability can conceal member replacement. No causal counterfactual or hidden enemy information.'}

if __name__=='__main__':
    run,output=map(Path,sys.argv[1:3]);output.write_text(json.dumps(audit(run),indent=2)+'\n')
