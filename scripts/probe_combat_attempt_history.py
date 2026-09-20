"""Paired replay: expose existing verified attempt summaries to combat choices."""
import asyncio,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from dotenv import load_dotenv
from jev_sc2.jev import Jev

async def main():
    load_dotenv(Path(__file__).resolve().parents[1]/'.env')
    source,output=map(Path,sys.argv[1:3])
    events=[json.loads(s) for s in source.read_text().splitlines()]
    eligible=[e for e in events if e['event']=='jev' and 'MobileCombat' in e.get('questions',{}) and e['state']['selection_facts']['MobileCombat']['count']==1]
    if len(eligible)<3:raise ValueError('Need three single-unit decisions')
    samples=[eligible[i] for i in (0,len(eligible)//2,len(eligible)-1)]
    prior_attempts=next(e['state']['previous_attempts'] for e in events if e['event']=='jev' and e.get('state',{}).get('previous_attempts'))
    model=Jev(lambda *a,**k:None,'combat-attempt-history-probe',max_calls=6);pairs=[]
    for i,e in enumerate(samples):
        loop=e['state']['game_loop']
        variants=[('original',e['state']),('with_history',{**e['state'],'previous_attempts':prior_attempts})]
        if i%2:variants.reverse()
        pair={'loop':loop}
        for name,state in variants:pair[name]=(await model.ask(state,{'MobileCombat':e['questions']['MobileCombat']}))['MobileCombat']
        pairs.append(pair)
    result={'source':str(source),'method':'First/middle/last single-unit MobileCombat records; identical menus, alternate pair order; add existing verified previous-attempt summaries. No game actions.','previous_attempts':prior_attempts,'pairs':pairs,'calls':model.calls,'cost':model.cost}
    output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'cost':model.cost,'choices':[(p['loop'],p['original']['choice'],p['with_history']['choice']) for p in pairs]}))
if __name__=='__main__':asyncio.run(main())
