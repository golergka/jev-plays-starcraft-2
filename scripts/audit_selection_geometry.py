"""Attribute selection diameter to observed members without inferring combat power."""
import json
import math
import sys
from pathlib import Path

def audit(run):
    events = [json.loads(l) for l in (run/'events.jsonl').read_text().splitlines()]
    ticks = {e['loop']: {u['tag']:u for u in e['units']} for e in events if e['event']=='tick'}
    rows = []
    for e in events:
        if e['event'] != 'jev': continue
        state = e.get('state', {})
        loop = state.get('game_loop')
        observed = ticks.get(loop, {})
        for key, q in e.get('questions', {}).items():
            facts = state.get('selection_facts', {}).get(key, {})
            members = facts.get('members', [])
            if len(members)<2 or not all(m['tag'] in observed for m in members): continue
            pairs = [(a,b,math.dist(observed[a['tag']]['position'],observed[b['tag']]['position']))
                     for i,a in enumerate(members) for b in members[i+1:]]
            a,b,d = max(pairs,key=lambda p:p[2])
            rows.append({'loop':loop,'selection':key,'diameter':round(d,1),'diameter_members':[a,b],
                         'diameter_excluding_each_type':{t:round(max((distance for a,b,distance in pairs if a['type']!=t and b['type']!=t),default=0),1) for t in sorted({m['type'] for m in members})},
                         'regroup_options':sum('join_' in k for k in q.get('criteria',{}))})
    return {'run':str(run),'rows':rows,'limits':'Same-loop observed positions; exclusion is diagnostic, not a proposed control rule. Zero diameter can mean fewer than two remaining members. No path or combat effectiveness inference.'}

if __name__=='__main__':
    result=audit(Path(sys.argv[1]))
    Path(sys.argv[2]).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
