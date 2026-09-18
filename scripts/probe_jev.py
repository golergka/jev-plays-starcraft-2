"""Synthetic spatial/batching probe, explicitly not a StarCraft performance test."""
import asyncio
import json
import sys
import time
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from dotenv import load_dotenv
from jev_sc2.jev import Jev


async def main():
    load_dotenv(Path(__file__).resolve().parent.parent/'.env')
    directory=Path('runs')/('probe-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
    directory.mkdir(parents=True)
    with (directory/'events.jsonl').open('w') as out:
        def log(event,**fields):
            out.write(json.dumps({'time':time.time(),'event':event,**fields})+'\n'); out.flush()
        jev=Jev(log,directory.name)
        cases={
            'case_a':{'enemy_direction':'north','north_offset':2,'east_offset':0},
            'case_b':{'enemy_direction':'south','north_offset':-2,'east_offset':0},
            'case_c':{'enemy_direction':'east','north_offset':0,'east_offset':2},
            'case_d':{'enemy_direction':'west','north_offset':0,'east_offset':-2},
        }
        expected={'case_a':'south','case_b':'north','case_c':'west','case_d':'east'}
        common={'unit':'Marine','health':'critical','weapon':'cooling down',
                'enemy':'melee Zergling within striking distance',
                'terrain':'open ground in every direction',
                'task':'Move directly away from this attacker while the weapon cools down.'}
        results=[]
        for representation in ['named','numeric']:
            states={key:{**common,**({k:v for k,v in case.items() if k=='enemy_direction'}
                                     if representation=='named' else
                                     {k:v for k,v in case.items() if k!='enemy_direction'})}
                    for key,case in cases.items()}
            questions={key:{'type':'choice','instructions':f'For scenario {key}, choose the direction directly away from its enemy.',
                            'criteria':{d:f'Move {d}' for d in ['north','south','east','west']}}
                       for key in cases}
            for batch in [False,True]:
                groups=[list(cases)] if batch else [[key] for key in cases]
                for group in groups:
                    before=time.monotonic()
                    answers=await jev.ask({k:states[k] for k in group},{k:questions[k] for k in group})
                    row={'representation':representation,'batch':batch,'latency_ms':round((time.monotonic()-before)*1000),
                         'answers':answers,'correct':sum(answers[k]['choice']==expected[k] for k in group),'total':len(group)}
                    results.append(row)
                    print(json.dumps(row),flush=True)
        (directory/'summary.json').write_text(json.dumps(results,indent=2))
        print('Synthetic probe saved:',directory)


asyncio.run(main())
