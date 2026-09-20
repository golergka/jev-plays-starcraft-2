"""Trace offered boarding controls, chosen actions and observed cargo."""
import json
import sys
from pathlib import Path

def audit(source, selection):
    rows=[]
    for line in source.read_text().splitlines():
        e=json.loads(line)
        if e['event']!='jev' or selection not in e.get('questions',{}):continue
        q=e['questions'][selection]; answer=e['response']['answers'][selection]
        facts=e['state'].get('selection_facts',{}).get(selection,{})
        if 'cargo_slots_used' not in facts:continue
        choice=answer.get('choice')
        rows.append({'loop':e['state'].get('game_loop'),'choice':choice,
            'description':q['criteria'].get(choice),'passengers':facts.get('passengers_by_type'),
            'cargo_slots_used':facts['cargo_slots_used'],
            'offered_loading_options':{k:v for k,v in q['criteria'].items() if 'load into this unit' in v},
            'continue_description':q['criteria'].get('continue')})
    return {'source':str(source),'selection':selection,'rows':rows,
        'limits':'Selections and observed cargo, not proof every submitted order completed. Sparse samples can miss intervening events. No gameplay or paid API calls.'}

if __name__=='__main__':
    result=audit(Path(sys.argv[1]),sys.argv[2]);Path(sys.argv[3]).write_text(json.dumps(result,indent=2)+'\n')
    print('audited',len(result['rows']),'decisions')
