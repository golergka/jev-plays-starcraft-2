"""Paired offline Jev calls: rename a choice key, preserving every description.

Uses recorded fair states. Never connects to SC2 or emits game commands.
"""
import argparse
import asyncio
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from dotenv import load_dotenv
from jev_sc2.jev import Jev


async def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('events',type=Path)
    parser.add_argument('--samples',type=int,default=3)
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args()
    load_dotenv(Path(__file__).resolve().parents[1]/'.env')
    rows=[json.loads(line) for line in args.events.read_text().splitlines()]
    recorded=[r for r in rows if r['event']=='jev' and 'strategy' in r['questions']][:args.samples]
    log=[]
    jev=Jev(lambda event,**fields:log.append({'event':event,**fields}), 'choice-label-probe',max_calls=2*len(recorded))
    pairs=[]
    for index,row in enumerate(recorded):
        original=row['questions']['strategy']
        if 'hold' not in original['criteria']:
            continue
        renamed={**original,'criteria':{('continue_operations' if k=='hold' else k):v for k,v in original['criteria'].items()}}
        order=[('original',original),('renamed',renamed)]
        if index%2:
            order.reverse()
        results={}
        for label,question in order:
            answer=await jev.ask(row['state'],{'strategy':question})
            results[label]=answer['strategy']
        pairs.append({'sample':index,'recorded_choice':row['response']['answers']['strategy'],**results})
    args.output.write_text(json.dumps({'source':str(args.events),'pairs':pairs,'calls':jev.calls,'cost':jev.cost,
        'method':'Only hold key renamed to continue_operations; all descriptions and recorded state unchanged. Pair order alternates. Small sequential probe, not a gameplay performance claim.'},indent=2)+'\n')
    print(json.dumps({'calls':jev.calls,'cost':jev.cost,'pairs':pairs},indent=2))


if __name__=='__main__':
    asyncio.run(main())
