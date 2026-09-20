"""Repeated same-state comparison of full versus worker-only role batches."""
import asyncio
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dotenv import load_dotenv
from jev_sc2.jev import Jev

async def main():
    source, output=map(Path,sys.argv[1:3])
    for line in source.read_text().splitlines():
        row=json.loads(line)
        if row['event']!='jev':continue
        workers={k:q for k,q in row.get('questions',{}).items()
                 if k.startswith('purpose_') and 'income' in q.get('criteria',{})}
        if 2<=len(workers)<=5 and len(workers)<len(row['questions']):break
    else:raise ValueError('No mixed role batch with two to five economic selections')
    load_dotenv(Path(__file__).resolve().parents[1]/'.env')
    model=Jev(lambda *a,**k:None,'role-batch-composition-probe',max_calls=6)
    result={'source':str(source),'time':row['time'],'worker_keys':list(workers),
            'omitted_keys':list(set(row['questions'])-set(workers)),
            'method':'Three paired repeats of one recorded state, full original question batch versus unchanged economic-role subset. Alternating arm order. No peer context, commands or policy changes. Descriptive repeatability probe, not independent states or a performance test.', 'pairs':[]}
    for i in range(3):
        pair={};result['pairs'].append(pair)
        for arm in (['full','subset'] if i%2==0 else ['subset','full']):
            pair[arm]=await model.ask(row['state'],row['questions'] if arm=='full' else workers)
            result.update(calls=model.calls,cost_usd=model.cost)
            output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'calls':model.calls,'cost_usd':model.cost,'choices':[
        {arm:{k:p[arm][k]['choice'] for k in workers} for arm in ('full','subset')} for p in result['pairs']]}))

if __name__=='__main__':asyncio.run(main())
