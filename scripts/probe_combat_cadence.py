"""Paired replay: expose observed review intervals to concrete combat choices."""
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
    ticks=sorted({e['loop'] for e in events if e['event']=='tick'})
    model=Jev(lambda *a,**k:None,'combat-cadence-probe',max_calls=6);pairs=[]
    for i,e in enumerate(samples):
        loop=e['state']['game_loop'];prior=[t for t in ticks if t<=loop][-5:]
        facts={'recent_review_intervals_game_loops':[b-a for a,b in zip(prior,prior[1:])], 'meaning':'Measured past controller review intervals. The next review time is unknown and may be delayed by spending limits. A chosen order can remain active until another decision; this is not a command to hold it for any specific duration.'}
        variants=[('original',e['state']),('with_cadence',{**e['state'],'concrete_review_timing':facts})]
        if i%2:variants.reverse()
        pair={'loop':loop,'timing':facts}
        for name,state in variants:pair[name]=(await model.ask(state,{'MobileCombat':e['questions']['MobileCombat']}))['MobileCombat']
        pairs.append(pair)
    result={'source':str(source),'method':'First/middle/last single-unit MobileCombat records; identical menus, alternate pair order; add only prior observed review intervals. No game actions.','pairs':pairs,'calls':model.calls,'cost':model.cost}
    output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'cost':model.cost,'choices':[(p['loop'],p['original']['choice'],p['with_cadence']['choice']) for p in pairs]}))
if __name__=='__main__':asyncio.run(main())
