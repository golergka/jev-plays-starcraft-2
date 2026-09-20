"""Offline wording probe of concrete movement under observed nearby threats."""
import asyncio
import copy
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from dotenv import load_dotenv
from jev_sc2.jev import Jev

async def main():
    source,output=map(Path,sys.argv[1:3]); rows=[]
    for line in source.read_text().splitlines():
        e=json.loads(line)
        if e['event']!='jev':continue
        q=e.get('questions',{}).get('MobileCombat',{})
        f=e['state'].get('selection_facts',{}).get('MobileCombat',{})
        if (f.get('count',99)<=2 and f.get('visible_enemies_within_12_of_any_member')
            and any(k.startswith('group_map_') for k in q.get('criteria',{}))):
            rows.append(e)
    if len(rows)<3:raise ValueError('Need three eligible concrete menus')
    load_dotenv(Path(__file__).resolve().parents[1]/'.env')
    model=Jev(lambda *a,**k:None,'local-commitment-probe',max_calls=6)
    result={'source':str(source),'eligible':len(rows),'pairs':[], 'method':'First/middle/last concrete MobileCombat menus with at most two members, nearby visible enemies and map destinations. Same full state and every option; append local-versus-distant evaluation instructions. Alternate arms; no game commands, forced retreat or action filtering.'}
    for i,e in enumerate([rows[0],rows[len(rows)//2],rows[-1]]):
        qs=copy.deepcopy(e['questions'])
        qs['MobileCombat']['instructions']+=' Evaluate what happens to these particular units before they reach a distant destination. Compare their current health, nearby visible threats and existing orders with the value of reaching that destination. Choose whether to address the local situation or continue distant travel; neither advancing nor retreating is mandatory. Straight-line distance does not establish a safe or traversable route.'
        p={'loop':e['state']['game_loop'],'instructions':qs['MobileCombat']['instructions'],'answers':{}};result['pairs'].append(p)
        for arm in (['baseline','local'] if i%2==0 else ['local','baseline']):
            q=e['questions'] if arm=='baseline' else qs
            a=(await model.ask(e['state'],q))['MobileCombat']
            p['answers'][arm]={'answer':a,'description':q['MobileCombat']['criteria'].get(a['choice'])}
            result.update(calls=model.calls,cost_usd=model.cost);output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'calls':model.calls,'cost':model.cost,'pairs':[{'loop':p['loop'],**{k:v['answer']['choice'] for k,v in p['answers'].items()}} for p in result['pairs']]}))

if __name__=='__main__':asyncio.run(main())
