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
            if len(sys.argv)>3 and key != sys.argv[3]: continue
            if any(isinstance(d,str) and 'Gather vespene gas' in d for d in q.get('criteria',{}).values()):
                samples.append((row,key));break
    samples=samples[-3:]
    model=Jev(lambda *a,**k:None,'resource-label-probe',max_calls=6)
    pairs=[]
    for i,(row,key) in enumerate(samples):
        question=row['questions'][key]; changed=copy.deepcopy(question)
        changed['criteria']={
            'gather_minerals':'Gather minerals using one of the offered mineral-field targets; a later choice selects the field.',
            'gather_vespene':'Gather vespene gas using one of the offered gas targets; a later choice selects the target.',
            'continue':'Keep existing orders unchanged.'}
        variants=[('original',question),('resource_category',changed)]
        if i%2: variants.reverse()
        result={'question':key,'resources':row['state']['resources']}
        for label,q in variants:result[label]=(await model.ask(row['state'],{key:q}))[key]
        pairs.append(result)
    result={'source':str(source),'question_filter':sys.argv[3] if len(sys.argv)>3 else None,'pairs':pairs,'calls':model.calls,'cost':model.cost,
            'method':'Last three filtered gas-gather menus. Same state; replace individual resource locations with one mineral and one gas category plus continue. Later target decision not run. Alternate pair order; no gameplay commands.'}
    output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__':asyncio.run(main())
