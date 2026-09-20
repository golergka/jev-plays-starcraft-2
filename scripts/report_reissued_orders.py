"""Measure repeated accepted command payloads, not actual interrupted work."""
import json
import sys
from collections import Counter
from pathlib import Path

source=Path(sys.argv[1])
rows=[json.loads(line) for line in source.read_text().splitlines()]
last={};counts=Counter();repeated=Counter();gaps=[];skipped=0
for row in rows:
    if row.get('event')!='tick':continue
    commands=row.get('commands',[]);results=row.get('action_results',[])
    # Fresh-state filtering may remove commands. Do not guess command/result
    # correspondence when logs cannot establish a one-to-one pairing.
    if row.get('submitted')!=len(commands) or len(results)!=len(commands):
        skipped+=1
        last.clear()
        continue
    for command,result in zip(commands,results):
        tag=command['unit_tag']
        if result!=1:
            last.pop(tag,None)
            continue
        ability=str(command['ability_id'])
        counts[ability]+=1
        payload=json.dumps(command,sort_keys=True)
        prior=last.get(tag)
        if prior and prior[0]==payload and row['loop']>=prior[1]:
            repeated[ability]+=1
            gaps.append(row['loop']-prior[1])
        last[tag]=(payload,row['loop'])
result={'source':str(source),'accepted_commands_in_unambiguous_ticks':sum(counts.values()),
        'exact_reissues':sum(repeated.values()),'accepted_by_ability':dict(counts),
        'reissued_by_ability':dict(repeated),'ambiguous_ticks_excluded':skipped,
        'scope':'Same serialized command as the previous accepted command for that unit in unambiguous tick logs. Not proof of interrupted work or wasted actions: unit state may change, and background jobs are not included. No semantic remapping or coordinate tolerance applied.'}
if len(sys.argv)>2:Path(sys.argv[2]).write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
