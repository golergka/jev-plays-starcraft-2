"""Offline Jev pairwise role comparisons; no connection to the game."""
import asyncio
import itertools
import json
import sys
from collections import Counter
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from dotenv import load_dotenv
from jev_sc2.jev import Jev

async def main():
    load_dotenv(Path(__file__).resolve().parents[1]/'.env')
    source,output=map(Path,sys.argv[1:3]); key=sys.argv[3]
    rows=[json.loads(l) for l in source.read_text().splitlines()]
    rows=[r for r in rows if r['event']=='jev' and key in r['questions']
          and r['state'].get('selection_facts',{}).get(key.removeprefix('purpose_'),{}).get('idle_count',0)>0][:3]
    model=Jev(lambda *a,**k:None,'pairwise-role-probe',max_calls=6)
    samples=[]
    for i,row in enumerate(rows):
        question=row['questions'][key]; pairs={}
        for j,(a,b) in enumerate(itertools.combinations(question['criteria'],2)):
            pairs[f'pair_{j}']={**question,'criteria':{a:question['criteria'][a],b:question['criteria'][b]}}
        variants=[('original',{key:question}),('pairwise',pairs)]
        if i%2:variants.reverse()
        results={}
        for name,qs in variants:results[name]=await model.ask(row['state'],qs)
        wins=Counter()
        invalid=[]
        for name,answer in results['pairwise'].items():
            choice=answer.get('choice')
            if choice in pairs[name]['criteria']:wins[choice]+=1
            else:invalid.append(name)
        maximum=max(wins.values(),default=0)
        samples.append({'sample':i,'original':results['original'][key],
            'pairwise_answers':results['pairwise'],'wins':dict(wins),
            'tied_winners':[k for k,v in wins.items() if v==maximum], 'invalid_answers':invalid})
    result={'source':str(source),'question':key,'samples':samples,'calls':model.calls,'cost':model.cost,
            'method':'First three recorded states with idle units. Same state, instructions and role descriptions. Compare original menu with all unordered pairs, counting model-selected pair wins. Ties remain ties. Alternate variant order. No game commands.'}
    output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'calls':model.calls,'cost':model.cost,'samples':[{k:v for k,v in x.items() if k!='pairwise_answers'} for x in samples]},indent=2))

if __name__=='__main__':asyncio.run(main())
