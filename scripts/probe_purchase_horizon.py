"""Test an explicit planning horizon on recorded purchase choices; no game actions."""
import asyncio,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from dotenv import load_dotenv
from jev_sc2.jev import Jev

async def main():
    source,output=map(Path,sys.argv[1:3]);loops=set(map(int,sys.argv[3:]))
    if output.exists():raise FileExistsError(output)
    selected=[e for line in source.read_text().splitlines() if (e:=json.loads(line))['event']=='jev' and 'investment' in e.get('questions',{}) and e['state'].get('game_loop') in loops]
    assert len(selected)==len(loops)
    load_dotenv(Path(__file__).resolve().parents[1]/'.env')
    model=Jev(lambda *a,**k:None,'purchase-horizon-probe',max_calls=len(selected));results=[]
    extra=' Evaluate the consequences over the next 2016 game loops, including capabilities that require subsequent production or other actions. Compare that with continuing current operations without this purchase. Choose only the next purchase here; future purchases and actions remain separate decisions. Do not assume resources or outcomes not supported by observations.'
    for e in selected:
        q=e['questions']['investment'];modified={**q,'instructions':q['instructions']+extra}
        answer=await model.ask(e['state'],{'investment':modified})
        choice=answer['investment']['choice']
        if choice not in q['criteria']:raise ValueError('Invalid purchase choice')
        results.append({'loop':e['state']['game_loop'],'original':e['response']['answers']['investment'],'horizon':answer['investment'],'selected_description':q['criteria'][choice]})
    output.write_text(json.dumps({'source':str(source),'method':'Same recorded state and full purchase menu; append general2016-loop consequence comparison. Historical original, not contemporaneous control. No gameplay actions.','added_instruction':extra,'results':results,'calls':model.calls,'cost':model.cost},indent=2)+'\n')
    print(json.dumps({'calls':model.calls,'cost':model.cost,'choices':[(x['loop'],x['horizon']['choice']) for x in results]}))
if __name__=='__main__':asyncio.run(main())
