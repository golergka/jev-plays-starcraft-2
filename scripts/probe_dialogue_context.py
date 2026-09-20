"""Compare identical recorded combat decisions with/without captured dialogue."""
import asyncio
import copy
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from dotenv import load_dotenv
from jev_sc2.jev import Jev

async def main():
    source, output = map(Path,sys.argv[1:3])
    if output.exists(): raise FileExistsError(output)
    load_dotenv(Path(__file__).resolve().parents[1]/'.env')
    rows=[json.loads(line) for line in source.read_text().splitlines()]
    eligible=[e for e in rows if e['event']=='jev' and 'MobileCombat' in e.get('questions',{})
              and e['state'].get('mission_context',{}).get('dialogue_history',{}).get('messages')]
    if len(eligible)<3:raise ValueError('Need at least three dialogue-bearing combat states')
    model=Jev(lambda *a,**k:None,'dialogue-context-probe',max_calls=6)
    pairs=[]
    for i,index in enumerate((0,len(eligible)//2,len(eligible)-1)):
        event=eligible[index];pair={'loop':event['state']['game_loop']}
        variants=['with_dialogue','without_dialogue']
        if i%2:variants.reverse()
        for variant in variants:
            state=copy.deepcopy(event['state'])
            if variant=='without_dialogue':state['mission_context'].pop('dialogue_history')
            answer=await model.ask(state,{'MobileCombat':event['questions']['MobileCombat']})
            pair[variant]=answer['MobileCombat']
        pairs.append(pair)
    result={'source':str(source),'method':'First/middle/last eligible recorded combat states; identical menus and state except dialogue_history. Alternating pair order; no game actions.','pairs':pairs,'calls':model.calls,'cost':model.cost}
    output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'cost':model.cost,'choices':[(p['loop'],p['with_dialogue']['choice'],p['without_dialogue']['choice']) for p in pairs]}))
if __name__=='__main__':asyncio.run(main())
