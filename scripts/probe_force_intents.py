"""Offline task-structure probe: immediate investment versus qualitative production intentions."""
import asyncio
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from dotenv import load_dotenv
from jev_sc2.jev import Jev


def target_questions(state):
    types=sorted({label[6:] for labels in state.get('observed_capabilities_by_type',{}).values()
                  for label in labels if label.startswith('Train ') and label[6:] in state.get('unit_type_facts',{})})
    questions={}
    for index,name in enumerate(types):
        current=state.get('selection_facts',{}).get(name,{}).get('count',0)
        questions[f'target_{index}']={'type':'choice',
            'instructions':f'Choose a production intent for {name} during the next 2016 game loops to help complete the primary mission objective. Currently observed count: {current}. This is a hypothetical goal, not an order. Shared resources and production capacity must be allocated separately across types.',
            'criteria':{
                'expand':f'Increase the number of owned {name} above the current count. Seek additional units of this type when resources and production allow.',
                'replace':f'Maintain the current number of {name}; replace observed losses but do not expand this type above the current count.',
                'stop':f'Do not produce more {name} during this horizon, including replacements. Existing units remain available.'}}

    return questions

async def main():
    load_dotenv(Path(__file__).resolve().parents[1]/'.env')
    source,output=map(Path,sys.argv[1:3])
    rows=[json.loads(l) for l in source.read_text().splitlines()]
    eligible=[r for r in rows if r['event']=='jev' and set(r['questions'])=={'investment'} and r['state'].get('resources',{}).get('minerals',0)>=300 and target_questions(r['state'])]
    if len(eligible)<3:raise ValueError('Need three eligible investment states')
    model=Jev(lambda *a,**k:None,'force-intent-probe',max_calls=6)
    result={'source':str(source),'method':'First/middle/last investment states with at least300minerals and observed Train capability. Immediate investment versus qualitative expand/replace/stop intentions; not equivalent questions or proof of better play. Alternate arm order. No commands.','pairs':[]}
    for i in (0,len(eligible)//2,len(eligible)-1):
        row=eligible[i];q=target_questions(row['state']);pair={'time':row['time'],'target_questions':q,'observed_counts':{k:v.get('count') for k,v in row['state']['selection_facts'].items()}}
        for arm in (['investment','targets'] if len(result['pairs'])%2==0 else ['targets','investment']):
            questions=row['questions'] if arm=='investment' else q
            pair[arm]=await model.ask(row['state'],questions)
            for key,question in questions.items():
                if pair[arm].get(key,{}).get('choice') not in question['criteria']:raise ValueError('Invalid choice')
        result['pairs'].append(pair);result.update(calls=model.calls,cost=model.cost)
        output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'calls':model.calls,'cost':model.cost,'choices':[{arm:{k:v['choice'] for k,v in p[arm].items()} for arm in ['investment','targets']} for p in result['pairs']]}))

if __name__=='__main__':asyncio.run(main())
