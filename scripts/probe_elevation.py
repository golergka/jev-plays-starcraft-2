"""Paired recorded-state elevation ablation; no game actions."""
import asyncio,copy,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from dotenv import load_dotenv
from jev_sc2.jev import Jev

def strip_z(value):
    if isinstance(value,list):return [strip_z(v) for v in value]
    if not isinstance(value,dict):return value
    value={k:strip_z(v) for k,v in value.items() if k not in ('observed_world_z','coordinate_note')}
    if 'observed_world_z' in value.get('columns',[]):
        index=value['columns'].index('observed_world_z')
        value['columns']=[c for i,c in enumerate(value['columns']) if i!=index]
        value['rows']=[[v for i,v in enumerate(row) if i!=index] for row in value['rows']]
    return value

async def main():
    source,output=map(Path,sys.argv[1:3])
    if output.exists():raise FileExistsError(output)
    selected=[e for s in source.read_text().splitlines() if (e:=json.loads(s))['event']=='jev' and 'MobileCombat' in e.get('questions',{}) and e['state'].get('game_loop') in (47,418,1198)]
    assert len(selected)==3
    load_dotenv(Path.cwd()/'.env');model=Jev(lambda *a,**k:None,'elevation-probe',max_calls=6);pairs=[]
    for i,e in enumerate(selected):
        pair={'loop':e['state']['game_loop']}
        for mode in (['with_z','without_z'] if i%2==0 else ['without_z','with_z']):
            state=copy.deepcopy(e['state']) if mode=='with_z' else strip_z(e['state'])
            answer=await model.ask(state,{'MobileCombat':e['questions']['MobileCombat']});pair[mode]=answer['MobileCombat']
        pairs.append(pair)
    output.write_text(json.dumps({'source':str(source),'method':'Three paired states, alternating order; only observed_world_z and coordinate_note removed. Identical menus; no game actions.','pairs':pairs,'calls':model.calls,'cost':model.cost},indent=2)+'\n');print(json.dumps({'cost':model.cost,'choices':[(p['loop'],p['with_z']['choice'],p['without_z']['choice']) for p in pairs]}))
if __name__=='__main__':asyncio.run(main())
