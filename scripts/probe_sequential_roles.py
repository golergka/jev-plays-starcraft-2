"""Small recorded-state probe: independent versus sequential worker role choices."""
import asyncio
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dotenv import load_dotenv
from jev_sc2.jev import Jev

async def main():
    source, output = map(Path,sys.argv[1:3])
    rows=[json.loads(line) for line in source.read_text().splitlines()]
    for row in rows:
        if row['event']!='jev': continue
        questions={k:q for k,q in row.get('questions',{}).items()
                   if k.startswith('purpose_') and 'income' in q.get('criteria',{})}
        if 2<=len(questions)<=5: break
    else: raise ValueError('No bounded multi-worker role state')
    facts=row['state'].get('selection_facts',{})
    if any(facts.get(k.removeprefix('purpose_'),{}).get('count')!=1 for k in questions):
        raise ValueError('Expected one worker per selection')
    load_dotenv(Path(__file__).resolve().parents[1]/'.env')
    model=Jev(lambda *a,**k:None,'sequential-role-probe',max_calls=6)
    result={'source':str(source),'recorded_time':row['time'],
            'method':'First eligible 2-5-worker state. One independent batch then identical individual role questions in sorted-key order with earlier peer choices appended. No sampling, concrete commands, game actions, or claim that order is neutral. One unreplicated comparison; not a win-rate test.',
            'independent':await model.ask(row['state'],questions),'sequential':{},'order':sorted(questions)}
    peer_choices=[]
    for key in sorted(questions):
        answer=await model.ask({**row['state'],'roles_chosen_for_other_selections_this_review':peer_choices}, {key:questions[key]})
        result['sequential'][key]=answer[key]
        choice=answer[key]['choice']
        peer_choices.append({'selection':key.removeprefix('purpose_'),'chosen_role':choice,
                             'meaning':questions[key]['criteria'][choice]})
        result.update(calls=model.calls,cost_usd=model.cost)
        output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'calls':model.calls,'cost_usd':model.cost,'choices':{arm:{k:v['choice'] for k,v in result[arm].items()} for arm in ('independent','sequential')}}))

if __name__=='__main__':asyncio.run(main())
