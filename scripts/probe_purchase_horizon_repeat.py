"""Repeated paired planning-horizon diagnostic, without gameplay actions."""
import asyncio,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from dotenv import load_dotenv
from jev_sc2.jev import Jev
async def main():
    output=Path('docs/experiments/617-purchase-horizon-repeat.json')
    if output.exists():raise FileExistsError(output)
    previous=json.loads(Path('docs/experiments/616-purchase-horizon-probe.json').read_text())
    rows=[json.loads(s) for s in Path(previous['source']).read_text().splitlines()]
    e=next(e for e in rows if e['event']=='jev' and e.get('state',{}).get('game_loop')==8744 and 'investment' in e.get('questions',{}))
    load_dotenv(Path.cwd()/'.env');model=Jev(lambda *a,**k:None,'horizon-repeat',max_calls=6);pairs=[]
    for i in range(3):
        pair={}
        for variant in (['original','horizon'] if i%2==0 else ['horizon','original']):
            q=dict(e['questions']['investment'])
            if variant=='horizon':q['instructions']+=previous['added_instruction']
            answer=(await model.ask(e['state'],{'investment':q}))['investment']
            if answer['choice'] not in q['criteria']:raise ValueError('Invalid choice')
            pair[variant]=answer
        pairs.append(pair)
    result={'source':previous['source'],'loop':8744,'method':'Three paired repetitions with alternating call order; identical state and menu. No game actions. One selected state, not broad generalization.','pairs':pairs,'calls':model.calls,'cost':model.cost}
    output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'cost':model.cost,'choices':[(p['original']['choice'],p['horizon']['choice']) for p in pairs]}))
if __name__=='__main__':asyncio.run(main())
