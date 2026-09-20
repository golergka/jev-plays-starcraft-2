"""Paired replay of criterion keys; retain descriptions and insertion order."""
import asyncio,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from dotenv import load_dotenv
from jev_sc2.jev import Jev

async def main():
    load_dotenv(Path(__file__).resolve().parents[1]/'.env')
    source,output=map(Path,sys.argv[1:3])
    events=[json.loads(s) for s in source.read_text().splitlines()]
    eligible=[e for e in events if e['event']=='jev' and 'MobileCombat' in e.get('questions',{}) and e['state']['selection_facts']['MobileCombat']['count']==1]
    if len(eligible)<3:raise ValueError('Need three eligible records')
    model=Jev(lambda *a,**k:None,'opaque-combat-keys-probe',max_calls=6);pairs=[]
    for i,e in enumerate(eligible[j] for j in (0,len(eligible)//2,len(eligible)-1)):
        q=e['questions']['MobileCombat'];mapping={f'option_{j:03d}':key for j,key in enumerate(q['criteria'])}
        opaque={**q,'criteria':{alias:q['criteria'][key] for alias,key in mapping.items()}}
        variants=[('original',q),('opaque',opaque)]
        if i%2:variants.reverse()
        pair={'loop':e['state']['game_loop'],'mapping':mapping}
        for name,question in variants:
            answer=(await model.ask(e['state'],{'MobileCombat':question}))['MobileCombat']
            pair[name]=answer
        pair['decoded_opaque_choice']=mapping[pair['opaque']['choice']]
        pairs.append(pair)
    result={'source':str(source),'method':'First/middle/last single-unit combat states. Replace only criterion keys with ordinal aliases preserving insertion order and descriptions; alternate pair order. State references remain unchanged, so this tests the presentation as a whole, not isolated token causality. No game actions.','pairs':pairs,'calls':model.calls,'cost':model.cost}
    output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'cost':model.cost,'choices':[(p['loop'],p['original']['choice'],p['decoded_opaque_choice']) for p in pairs]}))
if __name__=='__main__':asyncio.run(main())
