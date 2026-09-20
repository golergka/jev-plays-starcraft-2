"""Offline latency and decision audit for observed changes during pacing."""
import json
import statistics
import sys
from collections import Counter
from pathlib import Path


def audit(run):
    events=[json.loads(l) for l in (run/'events.jsonl').read_text().splitlines()]
    known={};pending_early=None;reviews=[]
    for i,e in enumerate(events):
        if e['event']=='tick':known.update({u['tag']:u['type'] for u in e['units']})
        if e['event']=='early_event_review':pending_early=e
        if e['event']!='decision_wait_events':continue
        following=[]
        for r in events[i+1:]:
            if r['event']=='decision_wait_events':break
            following.append(r)
            if r['event']=='tick':break
        tick=next((r for r in following if r['event']=='tick'),None)
        details=[]
        for change in e['events']:
            details.append({'loop':change['loop'],'wait_game_loops':e['review_loop']-change['loop'],
                            'damaged_types':dict(Counter(known.get(t,'unidentified') for t in change['damaged_tags'])),
                            'disappeared_types':dict(Counter(known.get(t,'unidentified') for t in change['disappeared_tags'])),
                            'new_nearby_enemy_count':len(change['new_nearby_enemy_tags'])})
        reviews.append({'review_loop':e['review_loop'],'early':bool(pending_early and pending_early['loop']==e['review_loop']),
                        'borrowed_seconds':pending_early['borrowed_seconds'] if pending_early and pending_early['loop']==e['review_loop'] else 0,
                        'changes':details,'completed_tick':tick['loop'] if tick else None,
                        'combat_choices':[{'cohort':r['cohort'],'choice':r['choice']} for r in following if r['event']=='group_choice' and r['cohort']=='MobileCombat']})
        pending_early=None
    def summary(early):
        selected=[r for r in reviews if r['early']==early]
        waits=[c['wait_game_loops'] for r in selected for c in r['changes']]
        return {'reviews':len(selected),'change_observations':len(waits),'median_wait_game_loops':statistics.median(waits) if waits else None,'max_wait_game_loops':max(waits,default=None)}
    return {'run':str(run),'summary':{'early':summary(True),'ordinary':summary(False)},'reviews':reviews,
            'limits':'Observed changes only; bounded logs may omit older changes. Types use previously observed own tags. Repeated damage is multiple observations, not independent encounters. Early and ordinary reviews have different triggers and debt; their latency difference is not causal performance evidence. No missing unit is assumed dead. No new API calls.'}

if __name__=='__main__':
    run,output=map(Path,sys.argv[1:3]);result=audit(run);output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result['summary']))
