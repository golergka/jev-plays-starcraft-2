"""Diagnostic comprehension question, not a gameplay policy or order."""
import asyncio,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from dotenv import load_dotenv
from jev_sc2.jev import Jev
async def main():
    source,output=map(Path,sys.argv[1:3]);chosen=[]
    for l in source.read_text().splitlines():
        e=json.loads(l)
        if e['event']=='jev' and 'investment' in e.get('questions',{}):
            q=e['questions']['investment'];a=e['response']['answers']['investment']['choice']
            if q['criteria'].get(a,'').startswith('Purchase one Bunker.'):chosen.append(e)
    load_dotenv(Path(__file__).resolve().parents[1]/'.env');m=Jev(lambda *a,**k:None,'purchase-dependency-probe',max_calls=3)
    out={'source':str(source),'method':'Same first/middle/last Bunker-top states as503/504. Diagnostic comprehension only: explicit candidate named, no replacement purchase or game orders. Full recorded state preserved.','answers':[]}
    for e in [chosen[0],chosen[len(chosen)//2],chosen[-1]]:
        q={'dependency':{'type':'choice','instructions':'Based on the supplied catalog and documented mechanics, does purchasing one new Bunker itself add an independent weapon, before any separate passenger-loading decisions? This is a factual dependency check, not a recommendation to buy or avoid anything.','criteria':{'independent':'Yes, the newly constructed empty structure itself supplies an independent weapon.','passengers':'No independent weapon is established on the empty structure; the documented combat benefit concerns loaded infantry and requires separate loading.','unknown':'The supplied facts do not establish either conclusion.'}}}
        a=await m.ask(e['state'],q);out['answers'].append({'loop':e['state']['game_loop'],'answer':a});out.update(calls=m.calls,cost_usd=m.cost);output.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out))
if __name__=='__main__':asyncio.run(main())
