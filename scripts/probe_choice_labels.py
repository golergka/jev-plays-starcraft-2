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
    parser.add_argument('--question',default='strategy')
    parser.add_argument('--from-key',default='hold')
    parser.add_argument('--to-key',default='continue_operations')
    args=parser.parse_args()
    load_dotenv(Path(__file__).resolve().parents[1]/'.env')
    rows=[json.loads(line) for line in args.events.read_text().splitlines()]
    recorded=[r for r in rows if r['event']=='jev' and args.question in r['questions'] and args.from_key in r['questions'][args.question]['criteria']][:args.samples]
    log=[]
    jev=Jev(lambda event,**fields:log.append({'event':event,**fields}), 'choice-label-probe',max_calls=2*len(recorded))
    pairs=[]
    for index,row in enumerate(recorded):
        original=row['questions'][args.question]
        if args.from_key not in original['criteria']:
            continue
        renamed={**original,'criteria':{(args.to_key if k==args.from_key else k):v for k,v in original['criteria'].items()}}
        order=[('original',original),('renamed',renamed)]
        if index%2:
            order.reverse()
        results={}
        for label,question in order:
            answer=await jev.ask(row['state'],{args.question:question})
            results[label]=answer[args.question]
        pairs.append({'sample':index,'recorded_choice':row['response']['answers'][args.question],**results})
    args.output.write_text(json.dumps({'source':str(args.events),'pairs':pairs,'calls':jev.calls,'cost':jev.cost,
        'method':f'Only {args.from_key} key renamed to {args.to_key} in {args.question}; all descriptions and recorded state unchanged. Pair order alternates. Small sequential probe, not a gameplay performance claim.'},indent=2)+'\n')
    print(json.dumps({'calls':jev.calls,'cost':jev.cost,'pairs':pairs},indent=2))


if __name__=='__main__':
    asyncio.run(main())
