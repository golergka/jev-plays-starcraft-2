"""Infrastructure-only API lifetime experiment; never updates campaign progress.

Optionally copy a map and disable its trigger script. Such a copy is NOT a
campaign mission and must never be credited as a campaign victory. Requires the
normal player controller to be stopped; this starts a new diagnostic game.
"""
import argparse
import asyncio
import ctypes as c
import json
import shutil
import sys
import tempfile
import time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from jev_sc2.sc2 import SC2
from s2clientprotocol import sc2api_pb2 as sc


def diagnostic_copy(source, destination, storm):
    if destination.exists():raise FileExistsError(destination)
    shutil.copy2(source,destination)
    library=c.CDLL(str(storm));pointer=c.c_void_p;uint=c.c_uint32
    for name,arguments in [('SFileOpenArchive',[c.c_char_p,uint,uint,c.POINTER(pointer)]),
        ('SFileAddFileEx',[pointer,c.c_char_p,c.c_char_p,uint,uint,uint]),
        ('SFileCloseArchive',[pointer])]:
        function=getattr(library,name);function.argtypes=arguments;function.restype=c.c_bool
    handle=pointer()
    if not library.SFileOpenArchive(str(destination).encode(),0,0,c.byref(handle)):
        raise RuntimeError('Cannot open diagnostic copy')
    try:
        with tempfile.TemporaryDirectory(prefix='jev-lifetime-') as directory:
            script=Path(directory)/'MapScript.galaxy';script.write_text('void InitMap () {}\n')
            if not library.SFileAddFileEx(handle,str(script).encode(),b'MapScript.galaxy',0x80000200,2,2):
                raise RuntimeError('Cannot replace diagnostic trigger script')
    finally:library.SFileCloseArchive(handle)


async def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('map',type=Path)
    parser.add_argument('--without-triggers-copy',type=Path)
    parser.add_argument('--storm',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--samples',type=int,default=65)
    args=parser.parse_args()
    if args.samples<1:parser.error('samples must be positive')
    if args.output.exists():raise FileExistsError(args.output)
    map_path=args.map
    if args.without_triggers_copy:
        if not args.storm:parser.error('--storm required for trigger-free copy')
        diagnostic_copy(map_path,args.without_triggers_copy,args.storm)
        map_path=args.without_triggers_copy
    client=await SC2.connect(5001)
    try:
        await client.request('ping',sc.RequestPing())
        await client.start(map_path)
        with args.output.open('x') as output:
            for index in range(args.samples):
                observation=await client.observe()
                record={'time':time.time(),'status':sc.Status.Name(client.status),
                    'loop':observation.observation.game_loop,
                    'owned':sum(u.alliance==1 for u in observation.observation.raw_data.units),
                    'results':[(r.player_id,sc.Result.Name(r.result)) for r in observation.player_result]}
                line=json.dumps(record);output.write(line+'\n');output.flush();print(line,flush=True)
                if client.status==sc.ended:break
                if index+1<args.samples:await asyncio.sleep(10)
    finally:await client.ws.close()

if __name__=='__main__':asyncio.run(main())
