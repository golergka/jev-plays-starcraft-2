"""Inspect recorded order distributions; category totals are diagnostics only."""
import json
import sys
from pathlib import Path


def audit(source, selection):
    rows = []
    for line in source.read_text().splitlines():
        e = json.loads(line)
        if e['event'] != 'jev' or selection not in e.get('questions', {}):
            continue
        q = e['questions'][selection]
        a = e['response']['answers'][selection]
        probabilities = a.get('probabilities', {})
        regroup = {k:v for k,v in probabilities.items() if 'join_' in k}
        top = sorted(probabilities.items(), key=lambda kv:-kv[1])[:5]
        rows.append({'loop':e['state'].get('game_loop'),'choice':a.get('choice'),
                     'choice_probability':probabilities.get(a.get('choice')),
                     'probability_sum':sum(probabilities.values()),
                     'option_count':len(q['criteria']),
                     'regroup_option_count':sum('join_' in k for k in q['criteria']),
                     'regroup_probability_sum':sum(regroup.values()),
                     'largest_regroup_probability':max(regroup.values(),default=0),
                     'top_five':[{'choice':k,'probability':v,'description':q['criteria'].get(k)} for k,v in top]})
    return {'source':str(source),'selection':selection,'rows':rows,
            'limits':'Returned rounded probabilities are not calibrated utilities. Summing options does not establish the best tactic; category size and overlapping semantics matter. No resampling, policy changes or API calls.'}

if __name__ == '__main__':
    result=audit(Path(sys.argv[1]),sys.argv[2])
    Path(sys.argv[3]).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps([{k:r[k] for k in ('loop','choice_probability','regroup_probability_sum','largest_regroup_probability')} for r in result['rows']]))
