"""Six-call paired test of measured decision cadence in investment context."""
import asyncio
import json
import statistics
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from dotenv import load_dotenv
from jev_sc2.jev import Jev

async def main():
    root=Path(__file__).resolve().parents[1];load_dotenv(root/'.env')
    source,output=map(Path,sys.argv[1:3]);rows=[json.loads(s) for s in source.read_text().splitlines()]
    ticks=[r for r in rows if r['event']=='tick']
    eligible=[r for r in rows if r['event']=='jev' and 'investment' in r['questions'] and r['state'].get('resources',{}).get('minerals',0)>=500]
    if len(eligible)<3:raise ValueError('Need three recorded high-balance decisions')
    model=Jev(lambda *a,**k:None,'review-cadence-probe',max_calls=6)
    result={'source':str(source),'method':'First/middle/last >=500mineral investment requests; add only measured trailing decision gaps from earlier tick events. No future samples or timing guarantee. Identical questions, alternating pair order; six calls, no gameplay commands.','pairs':[]}
    for index in (0,len(eligible)//2,len(eligible)-1):
        row=eligible[index];past=[r for r in ticks if r['time']<row['time']][-6:]
        gaps=[b['loop']-a['loop'] for a,b in zip(past,past[1:])]
        seconds=[b['time']-a['time'] for a,b in zip(past,past[1:])]
        cadence={'recent_review_gaps_game_loops':gaps,'median_wall_seconds_between_completed_decisions':round(statistics.median(seconds),2) if seconds else None,'interpretation':'Measured past controller cadence under budget pacing. Reviews are not every frame. Waiting preserves current orders until subsequent decisions; future review timing is not guaranteed.'}
        pair={'recorded_time':row['time'],'cadence':cadence}
        variants=[('original',row['state']),('with_cadence',{**row['state'],'measured_decision_cadence':cadence})]
        if len(result['pairs'])%2:variants.reverse()
        for label,state in variants:pair[label]=await model.ask(state,{'investment':row['questions']['investment']})
        result['pairs'].append(pair);result.update(calls=model.calls,cost=model.cost);output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'calls':model.calls,'cost':model.cost}))

if __name__=='__main__':asyncio.run(main())
