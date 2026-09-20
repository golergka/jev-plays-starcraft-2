"""Recorded-order ablation of explicit primary/bonus objective semantics."""
import asyncio
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from dotenv import load_dotenv
from jev_sc2.jev import Jev

GUIDANCE = (' The mission context marks primary objectives separately from bonus objectives. '
            'Choose for completion of the primary objective; bonus progress alone is not mission completion. '
            'Use the actual objective names and descriptions to distinguish their targets. '
            'A collectible is not necessarily the primary objective target. '
            'Decide whether any optional progress is worth its effect on completing the primary objective.')


async def main():
    source,output=map(Path,sys.argv[1:3])
    rows=[json.loads(line) for line in source.read_text().splitlines()]
    samples=[(e,k) for e in rows if e['event']=='jev' for k in e.get('questions',{})
             if k in ('MobileCombat','Marauder') and e['state'].get('mission_context',{}).get('objectives')]
    if len(samples)<3:raise ValueError('Need three recorded combat menus with objective context')
    load_dotenv(Path(__file__).resolve().parents[1]/'.env')
    model=Jev(lambda *a,**k:None,'objective-priority-probe',max_calls=6)
    result={'source':str(source),'method':'First/middle/last recorded MobileCombat or Marauder menu. Same state and every criterion; append only general primary/bonus semantics to instructions. Alternate arm order. No gameplay commands; six-call cap.','guidance':GUIDANCE,'pairs':[]}
    for index in (0,len(samples)//2,len(samples)-1):
        row,key=samples[index];q=row['questions'][key]
        pair={'time':row['time'],'selection':key,'objectives':row['state']['mission_context']['objectives']}
        result['pairs'].append(pair)
        for arm in (['baseline','explicit_priority'] if len(result['pairs'])%2 else ['explicit_priority','baseline']):
            question=q if arm=='baseline' else {**q,'instructions':q['instructions']+GUIDANCE}
            answer=(await model.ask(row['state'],{key:question}))[key]
            pair[arm]={'answer':answer,'chosen_description':q['criteria'].get(answer['choice'])}
            result.update(calls=model.calls,cost_usd=model.cost)
            output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'calls':model.calls,'cost_usd':model.cost,'choices':[{a:p[a]['answer']['choice'] for a in ('baseline','explicit_priority')} for p in result['pairs']]}))


if __name__=='__main__':asyncio.run(main())
