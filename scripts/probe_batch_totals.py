"""Replay batch investments with mechanically computed total costs and output."""
import asyncio
import copy
import ast
import re
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from dotenv import load_dotenv
from jev_sc2.jev import Jev


async def main():
    load_dotenv(Path(__file__).resolve().parents[1]/'.env')
    source=Path(sys.argv[1]); output=Path(sys.argv[2]); key=sys.argv[3]
    rows=[json.loads(line) for line in source.read_text().splitlines()]
    eligible=[r for r in rows if r['event']=='jev' and key in r['questions'] and r['state'].get('resources',{}).get('minerals',0)>=1000 and any(k.startswith('batch_') for k in r['questions'][key]['criteria'])]
    if len(eligible)<3:raise ValueError('Need three high-resource batch states')
    samples=[eligible[i] for i in (0,len(eligible)//2,len(eligible)-1)]
    jev=Jev(lambda *args,**kwargs:None,'batch-total-probe',max_calls=6)
    pairs=[]
    for i,row in enumerate(samples):
        kind=key.removeprefix('purpose_')
        original=row['questions'][key]
        clarified=copy.deepcopy(original)
        for option,description in clarified['criteria'].items():
            if not option.startswith('batch_'):continue
            match=re.search(r'Cost/effects: (\{.*?\})\. Already owned:',description)
            if not match:raise ValueError('Missing exact project cost')
            project=ast.literal_eval(match.group(1))
            description += f" Three completed units would add three {project['type']} units, costing {3*project['minerals']} minerals and {3*project['vespene']} gas in total, with {3*project['supply']} total supply used. These totals assume all three requests complete; completion is not guaranteed."
            clarified['criteria'][option]=description

        variants=[('original',original),('clarified',clarified)]
        if i%2: variants.reverse()
        result={'sample':i}
        for name,question in variants:
            result[name]=(await jev.ask(row['state'],{key:question}))[key]
        pairs.append(result)
    payload={'source':str(source),'question':key,'pairs':pairs,'calls':jev.calls,'cost':jev.cost,
             'method':'First/middle/last >=1000mineral batch states. Append computed total cost/supply and three-unit output to existing batches; other options and state unchanged. Alternate pair order; no game commands.'}
    output.write_text(json.dumps(payload,indent=2)+'\n');print(json.dumps({'calls':jev.calls,'cost':jev.cost,'choices':[{k:v.get('choice') for k,v in p.items() if isinstance(v,dict)} for p in pairs]}))


if __name__=='__main__':asyncio.run(main())
