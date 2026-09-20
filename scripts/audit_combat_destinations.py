"""Join concrete combat menus to sampled orders without inferring paths or deaths."""
import json
import sys
from collections import Counter
from pathlib import Path

def audit(source):
    rows=[]; pending={}
    for line in source.read_text().splitlines():
        e=json.loads(line)
        if e['event']=='jev':
            for selection,q in e.get('questions',{}).items():
                criteria=q.get('criteria',{})
                # A concrete spatial menu, not the preceding family question.
                if not any(k.startswith(('group_map_','group_last_known_','group_move_','group_attack_move_')) for k in criteria):
                    continue
                facts=e['state'].get('selection_facts',{}).get(selection,{})
                if not facts or facts.get('some_can_harvest_minerals') or facts.get('some_can_construct_buildings'):
                    continue
                loop=e['state'].get('game_loop');answer=e['response']['answers'][selection]
                row={'loop':loop,'selection':selection,'facts':facts,'top_choice':answer.get('choice'),
                     'top_description':criteria.get(answer.get('choice')),'selected_choice':None,
                     'selected_description':None}
                rows.append(row);pending[(loop,selection)]=(row,criteria)
        elif e['event']=='group_choice' and (e.get('loop'),e.get('cohort')) in pending:
            row,criteria=pending[(e['loop'],e['cohort'])]
            row['selected_choice']=e['choice'];row['selected_description']=criteria.get(e['choice'])
    return {'source':str(source),'limits':'Recorded selected orders, not evidence of engine acceptance, actual route, arrival or death. Selection may combine support/transport with armed units. No hidden map information.',
            'top_choices':dict(Counter(r['top_choice'] for r in rows)),
            'selected_choices':dict(Counter(r['selected_choice'] for r in rows)), 'reviews':rows}

if __name__=='__main__':
    result=audit(Path(sys.argv[1]));Path(sys.argv[2]).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'reviews':len(result['reviews']),'selected_choices':result['selected_choices'],
                      'sampled_differences':sum(r['top_choice']!=r['selected_choice'] for r in result['reviews'])}))
