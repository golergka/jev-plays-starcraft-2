"""Feed recorded Jev factual assessment back into unchanged purchase questions."""
import asyncio,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from dotenv import load_dotenv
from jev_sc2.jev import Jev
async def main():
    source,assessments,output=map(Path,sys.argv[1:4]);events=[json.loads(l) for l in source.read_text().splitlines()]
    facts=json.loads(assessments.read_text());load_dotenv(Path(__file__).resolve().parents[1]/'.env');m=Jev(lambda *a,**k:None,'purchase-self-assessment',max_calls=3)
    out={'source':str(source),'assessments':str(assessments),'method':'Original purchase state/questions plus Jev factual dependency answer from505. Historical baseline choices retained for comparison, not contemporaneous randomized controls. Offline only.','answers':[]}
    for r in facts['answers']:
        e=next(e for e in events if e['event']=='jev' and e['state'].get('game_loop')==r['loop'] and 'investment' in e['questions'])
        state={**e['state'],'your_factual_dependency_assessment':{'candidate':'Bunker','question':'Does a newly constructed empty Bunker itself add an independent weapon before passenger-loading decisions?','answer':r['answer']['dependency'],'choice_meanings':{'passengers':'No independent weapon is established on the empty structure; documented combat benefit concerns loaded infantry and requires separate loading.'},'meaning':'Your factual assessment, not a purchase recommendation. All original choices remain available.'}}
        a=(await m.ask(state,e['questions']))['investment'];out['answers'].append({'loop':r['loop'],'baseline':e['response']['answers']['investment']['choice'],'answer':a,'description':e['questions']['investment']['criteria'].get(a['choice'])});out.update(calls=m.calls,cost_usd=m.cost);output.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({'calls':m.calls,'cost':m.cost,'answers':[{'loop':r['loop'],'description':r['description'][:100]} for r in out['answers']]}))
if __name__=='__main__':asyncio.run(main())
