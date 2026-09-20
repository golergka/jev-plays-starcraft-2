"""Generic purchase-dependency assessment before unchanged investment choice."""
import asyncio,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from dotenv import load_dotenv
from jev_sc2.jev import Jev
CRITERIA={
 'self_contained':'After completion, the purchased entity can supply a relevant capability using its own abilities and existing resources; no additional unit purchase or passenger loading is needed. Ordinary orders may still be needed.',
 'complementary':'The relevant capability depends on additional unit production, passenger loading, or another complementary entity/action beyond ordinary use of this purchased entity.',
 'unclear':'The supplied facts do not establish the relevant dependency.'}
async def main():
    source,output=map(Path,sys.argv[1:3]);E=[json.loads(l) for l in source.read_text().splitlines()]
    eligible=[]
    for e in E:
        if e['event']=='jev' and 'investment' in e.get('questions',{}):
            q=e['questions']['investment'];a=e['response']['answers']['investment']['choice']
            if q['criteria'].get(a,'').startswith('Purchase one Bunker.'):eligible.append(e)
    load_dotenv(Path(__file__).resolve().parents[1]/'.env');m=Jev(lambda *a,**k:None,'general-purchase-dependency',max_calls=6)
    out={'source':str(source),'method':'Same first/middle/last recorded Bunker-top states. Assess every project option with the same dependency question, then feed Jev answers into unchanged investment question. No filtering or preferred unit. Historical baseline, six-call ceiling, offline only.','reviews':[]}
    for e in [eligible[0],eligible[len(eligible)//2],eligible[-1]]:
        options={k:v for k,v in e['questions']['investment']['criteria'].items() if k.startswith('project_')}
        questions={k:{'type':'choice','instructions':'Classify the dependency of this purchase for addressing the current mission situation and your stated bottleneck. This is a factual assessment, not a purchase recommendation. Purchase: '+v,'criteria':CRITERIA} for k,v in options.items()}
        assessment=await m.ask(e['state'],questions)
        for k in options:
            if assessment.get(k,{}).get('choice') not in CRITERIA:raise ValueError('Invalid dependency assessment')
        state={**e['state'],'your_purchase_dependency_assessments':{'assessments':{k:{'purchase':options[k],'assessment':CRITERIA[assessment[k]['choice']]} for k in options},'meaning':'Your dependency assessment; not a usefulness ranking. Complementary purchases may be valuable. All original options remain available.'}}
        a=(await m.ask(state,e['questions']))['investment']
        out['reviews'].append({'loop':e['state']['game_loop'],'assessments':assessment,'answer':a,'description':e['questions']['investment']['criteria'].get(a['choice'])});out.update(calls=m.calls,cost_usd=m.cost);output.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({'calls':m.calls,'cost':m.cost,'reviews':[{'loop':r['loop'],'description':r['description'][:100]} for r in out['reviews']]}))
if __name__=='__main__':asyncio.run(main())
