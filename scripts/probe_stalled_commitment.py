"""Offline test of Jev reconsidering its own stalled production commitment."""
import asyncio,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from dotenv import load_dotenv
from jev_sc2.jev import Jev

async def main():
    source,output=map(Path,sys.argv[1:3]);events=[json.loads(l) for l in source.read_text().splitlines()]
    # Recorded job context only; no later outcome enters the question.
    job=None;eligible=[];seen=set()
    for e in events:
        if e['event']=='production_job_armed':job=dict(e['job'])
        elif e['event']=='production_job_request' and job:
            job.update(remaining=e['remaining_attempts'],last_request_loop=e['loop'])
        elif e['event']=='production_job_released':job=None
        elif e['event']=='jev' and job and job['remaining']>0:
            s=e['state'];loop=s.get('game_loop',0)
            if loop-job['last_request_loop']>=224 and loop not in seen:
                eligible.append((s,dict(job)));seen.add(loop)
    if len(eligible)<3:raise ValueError('Need three stalled states')
    load_dotenv(Path(__file__).resolve().parents[1]/'.env')
    model=Jev(lambda *a,**k:None,'stalled-commitment-probe',max_calls=3)
    result={'source':str(source),'method':'First/middle/last distinct recorded states with an active batch and no further request for at least224loops. No future observations or mission-specific advice. Offline only, no orders.','reviews':[]}
    q={'commitment_review':{'type':'choice','instructions':'Review your existing production commitment using current observations. Decide whether to keep its exclusive purchase reservation or release it so you can reconsider purchases. Releasing does not cancel already submitted training orders and does not select a replacement purchase.', 'criteria':{'keep':'Keep waiting for the remaining training requests until the existing deadline; no other new purchases may occur during this reservation.','release':'Release the remaining unsubmitted training requests and their purchase reservation; reconsider all currently offered purchases at a separate decision.'}}}
    for s,j in [eligible[0],eligible[len(eligible)//2],eligible[-1]]:
        answer=await model.ask({**s,'existing_production_commitment':j},q)
        result['reviews'].append({'loop':s['game_loop'],'resources':s.get('resources'),'job':j,'answer':answer})
        result.update(calls=model.calls,cost_usd=model.cost);output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))
if __name__=='__main__':asyncio.run(main())
