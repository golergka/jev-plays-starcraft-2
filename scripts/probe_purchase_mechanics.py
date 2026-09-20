"""Offline salience probe: repeat supplied mechanics beside matching purchases."""
import asyncio,copy,json,re,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from dotenv import load_dotenv
from jev_sc2.jev import Jev

async def main():
    source,output=map(Path,sys.argv[1:3]);eligible=[]
    for line in source.read_text().splitlines():
        e=json.loads(line)
        if e['event']!='jev' or 'investment' not in e.get('questions',{}):continue
        q=e['questions']['investment'];choice=e['response']['answers']['investment']['choice']
        desc=q['criteria'].get(choice,'')
        if desc.startswith('Purchase one Bunker.') and e['state'].get('unit_type_facts',{}).get('Bunker',{}).get('documented_mechanics'):eligible.append(e)
    if len(eligible)<3:raise ValueError('Need three recorded Bunker top choices')
    load_dotenv(Path(__file__).resolve().parents[1]/'.env');model=Jev(lambda *a,**k:None,'purchase-mechanics-probe',max_calls=6)
    out={'source':str(source),'eligible':len(eligible),'method':'First/middle/last recorded Bunker-top investment states. All original state/options retained. Treatment repeats existing documented mechanics beside every matching purchase; no new tactical guidance. Alternating arms, six calls, offline only.','pairs':[]}
    for i,e in enumerate([eligible[0],eligible[len(eligible)//2],eligible[-1]]):
        changed=copy.deepcopy(e['questions'])
        for key,desc in changed['investment']['criteria'].items():
            m=re.match(r'^Purchase one ([^.]+)\.',desc)
            fact=(e['state'].get('unit_type_facts',{}).get(m.group(1),{}).get('documented_mechanics',{}) if m else {}).get('fact')
            if fact:changed['investment']['criteria'][key]+=' Documented mechanic: '+fact
        row={'loop':e['state']['game_loop'],'answers':{}};out['pairs'].append(row)
        for arm in (['baseline','adjacent'] if i%2==0 else ['adjacent','baseline']):
            q=e['questions'] if arm=='baseline' else changed
            a=(await model.ask(e['state'],q))['investment'];row['answers'][arm]={'answer':a,'description':q['investment']['criteria'].get(a['choice'])}
            out.update(calls=model.calls,cost_usd=model.cost);output.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({'calls':model.calls,'cost':model.cost,'pairs':[{'loop':r['loop'],**{k:v['description'][:100] for k,v in r['answers'].items()}} for r in out['pairs']]}))
if __name__=='__main__':asyncio.run(main())
