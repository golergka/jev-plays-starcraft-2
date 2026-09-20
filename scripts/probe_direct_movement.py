"""Replay direct combat questions with explicit Move versus Attack-move semantics."""
import asyncio
import copy
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
    samples=[r for r in rows if r['event']=='jev' and key in r['questions'] and r['state'].get('strategy_chosen_by_jev')][:3]
    jev=Jev(lambda *args,**kwargs:None,'direct-movement-semantics-probe',max_calls=6)
    pairs=[]
    for i,row in enumerate(samples):
        kind=key.removeprefix('purpose_')
        original=row['questions'][key]
        clarified=copy.deepcopy(original)
        clarified['instructions'] += ' Ordinary Move changes location only: moving near a resource does not harvest it, moving near a building does not repair or enter it, and ordinary Move does not attack along the route.'
        variants=[('original',original),('clarified',clarified)]
        if i%2: variants.reverse()
        result={'sample':i}
        for name,question in variants:
            result[name]=(await jev.ask(row['state'],{key:question}))[key]
        pairs.append(result)
    payload={'source':str(source),'question':key,'pairs':pairs,'calls':jev.calls,'cost':jev.cost,
             'method':'First three recorded states. Append literal Move semantics to the direct order instruction; keep state and all other choices identical. Alternate pair order; no game commands.'}
    output.write_text(json.dumps(payload,indent=2)+'\n');print(json.dumps({'calls':jev.calls,'cost':jev.cost,'choices':[{k:v.get('choice') for k,v in p.items() if isinstance(v,dict)} for p in pairs]}))


if __name__=='__main__':asyncio.run(main())
