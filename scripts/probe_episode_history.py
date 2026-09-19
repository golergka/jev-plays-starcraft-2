"""Paired recorded-state ablation of prior-attempt facts; no game commands."""
import asyncio
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dotenv import load_dotenv
from jev_sc2.jev import Jev


async def main():
    root=Path(__file__).resolve().parents[1]
    load_dotenv(root/'.env')
    source,output=map(Path,sys.argv[1:3])
    rows=[json.loads(line) for line in source.read_text().splitlines()]
    eligible=[r for r in rows if r.get('event')=='jev'
              and 'investment' in r['questions'] and r['state'].get('previous_attempts',{}).get('attempts')]
    indices=sorted({0,len(eligible)//2,len(eligible)-1}) if eligible else []
    if len(indices)!=3:
        raise ValueError('Need at least three recorded history-containing investment states')
    jev=Jev(lambda *args,**kwargs:None,'episode-history-ablation',max_calls=6)
    pairs=[]
    for i,index in enumerate(indices):
        row=eligible[index]
        original=row['state']
        ablated={k:v for k,v in original.items() if k!='previous_attempts'}
        variants=[('with_history',original),('without_history',ablated)]
        if i%2:variants.reverse()
        result={'recorded_time':row['time'],'resources':original.get('resources'),
                'criteria':row['questions']['investment']['criteria']}
        for label,state in variants:
            result[label]=(await jev.ask(state,{'investment':row['questions']['investment']}))['investment']
        pairs.append(result)
    payload={'source':str(source),'pairs':pairs,'calls':jev.calls,'cost':jev.cost,
             'method':'First/middle/last recorded investment states. Remove only previous_attempts; identical questions and other state. Alternate pair order. Six calls, no game commands. Small unreplicated probe; not a survival comparison.'}
    output.write_text(json.dumps(payload,indent=2)+'\n')
    print(json.dumps({'calls':jev.calls,'cost':jev.cost,'pairs':[
        {label:{'choice':p[label].get('choice'),'save_probability':p[label].get('probabilities',{}).get('save')}
         for label in ('with_history','without_history')} for p in pairs]}))


if __name__=='__main__':
    asyncio.run(main())
