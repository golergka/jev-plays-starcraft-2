"""Trace observed unit membership and submitted orders, without attributing deaths."""
import json
import sys
from pathlib import Path

def audit(run, unit_type):
    events=[json.loads(l) for l in (run/'events.jsonl').read_text().splitlines()]
    ticks=[e for e in events if e['event']=='tick']
    initial={u['tag'] for u in ticks[0]['units']}
    units={}
    for index,tick in enumerate(ticks):
        for u in tick['units']:
            if u['type']!=unit_type: continue
            row=units.setdefault(u['tag'],{'tag':u['tag'],'initial':u['tag'] in initial,'observations':[],'submitted_orders':[]})
            row['observations'].append({'loop':tick['loop'],'position':u['position'],'health':u['health']})
    for row in units.values():
        last=row['observations'][-1]['loop']
        later=next((t for t in ticks if t['loop']>last),None)
        row['next_tick_without_tag']=later['loop'] if later else None
        for e in events:
            for a in e.get('submitted_actions',[]):
                if row['tag'] in a.get('unit_tags',[]):row['submitted_orders'].append({'loop':e.get('loop'),'time':e['time'],**a})
    return {'run':str(run),'unit_type':unit_type,'units':list(units.values()),'limits':'First appearance is not proven production; last appearance and missing next tick are not proven death. Observations are sparse. Accepted orders do not prove execution, completion, or exact path. No gameplay/API calls.'}

if __name__=='__main__':
    run,kind,output=sys.argv[1:]
    result=audit(Path(run),kind);Path(output).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps([{'tag':u['tag'],'initial':u['initial'],'loops':[o['loop'] for o in u['observations']],'orders':[(a['loop'],a['ability_id'],a['result']) for a in u['submitted_orders']]} for u in result['units']]))
