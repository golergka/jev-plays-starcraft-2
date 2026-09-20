"""Six-call comparison of categorical investment choice and independent ratings."""
import asyncio
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from dotenv import load_dotenv
from jev_sc2.jev import Jev

async def main():
    root=Path(__file__).resolve().parents[1];load_dotenv(root/'.env')
    source,output=map(Path,sys.argv[1:3]);rows=[json.loads(s) for s in source.read_text().splitlines()]
    eligible=[r for r in rows if r['event']=='jev' and 'investment' in r['questions'] and r['state'].get('resources',{}).get('minerals',0)>=500]
    if len(eligible)<3:raise ValueError('Need three eligible recorded states')
    model=Jev(lambda *a,**k:None,'investment-score-probe',max_calls=6)
    result={'source':str(source),'method':'First/middle/last >=500mineral investment states. Compare original Choice with one Score per exact offered option, including save. Identical shared state, alternating order. Scores describe usefulness, not win probabilities or calibrated utility. Six-call cap; no game commands.','pairs':[]}
    for i in (0,len(eligible)//2,len(eligible)-1):
        row=eligible[i];options=row['questions']['investment']['criteria']
        scored={key:{'type':'score','instructions':'Rate how useful this specific action is for completing the stated mission objective in the current observed situation. Account for costs, existing forces, current queues and known threats. Evaluate the action itself, including waiting when offered. Action: '+description,'criteria':['Actively undermines progress toward the objective.','Offers little useful progress in the current situation.','Offers some useful progress but limited immediate value.','Offers substantial useful progress in the current situation.','Offers exceptionally important progress toward the objective now.']} for key,description in options.items()}
        pair={'recorded_time':row['time'],'options':options}
        variants=[('choice',{'investment':row['questions']['investment']}),('scores',scored)]
        if len(result['pairs'])%2:variants.reverse()
        for label,questions in variants:pair[label]=await model.ask(row['state'],questions)
        pair['ranking']=sorted(pair['scores'],key=lambda k:pair['scores'][k]['score'],reverse=True)
        result['pairs'].append(pair);result.update(calls=model.calls,cost=model.cost);output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'calls':model.calls,'cost':model.cost}))

if __name__=='__main__':asyncio.run(main())
