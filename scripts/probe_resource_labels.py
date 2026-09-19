"""Offline paired resource-context placement probe; emits no game commands."""
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
    source,output=map(Path,sys.argv[1:3])
    samples=[]
    for line in source.read_text().splitlines():
        row=json.loads(line)
        if row['event']!='jev' or not row['state'].get('resources'): continue
        for key,q in row['questions'].items():
            if any(isinstance(d,str) and 'Gather vespene gas' in d for d in q.get('criteria',{}).values()):
                samples.append((row,key));break
    samples=samples[-3:]
    model=Jev(lambda *a,**k:None,'resource-label-probe',max_calls=6)
    pairs=[]
    for i,(row,key) in enumerate(samples):
        question=row['questions'][key]; changed=copy.deepcopy(question)
        for option,description in changed['criteria'].items():
            if not isinstance(description,str): continue
            resource='minerals' if 'Gather minerals' in description else 'vespene' if 'Gather vespene gas' in description else None
            if resource:
                changed['criteria'][option]=description+f'; increases {resource} balance (currently {row["state"]["resources"][resource]}). Does not increase the other resource balance.'
        variants=[('original',question),('inline_balance',changed)]
        if i%2: variants.reverse()
        result={'question':key,'resources':row['state']['resources']}
        for label,q in variants:result[label]=(await model.ask(row['state'],{key:q}))[key]
        pairs.append(result)
    result={'source':str(source),'pairs':pairs,'calls':model.calls,'cost':model.cost,
            'method':'Last three recorded gas-gather menus. Same state and choices; append observed relevant balance and literal single-resource effect. Alternate pair order. No gameplay commands.'}
    output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__':asyncio.run(main())
