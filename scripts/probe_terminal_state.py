"""Read-only probe for disagreement between API termination and simulation clock.

Run only after the controller exits: this opens its own API connection.
No actions, game resets, hidden state or debug commands are requested.
"""
import argparse
import asyncio
import json
import sys
import time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from jev_sc2.sc2 import SC2
from s2clientprotocol import sc2api_pb2 as sc

async def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--samples',type=int,default=7)
    parser.add_argument('--interval',type=float,default=10)
    args=parser.parse_args()
    if args.samples<1 or not 0<args.interval<=60:
        parser.error('samples must be positive; interval must be in (0,60]')
    client=await SC2.connect(5001)
    try:
        with args.output.open('x') as output:
            for index in range(args.samples):
                observation=await client.observe()
                entry={'time':time.time(),'status':sc.Status.Name(client.status),
                       'loop':observation.observation.game_loop,
                       'players':[{'player':r.player_id,'result':sc.Result.Name(r.result)}
                                  for r in observation.player_result],
                       'owned_units':sum(u.alliance==1 for u in observation.observation.raw_data.units)}
                output.write(json.dumps(entry)+'\n');output.flush()
                print(json.dumps(entry),flush=True)
                if index+1<args.samples:await asyncio.sleep(args.interval)
    finally:await client.ws.close()

if __name__=='__main__':asyncio.run(main())
