"""Experimental replay recovery using fields verified in installed SC2 schema.

Run only with the controller stopped and the current mission finished. Does not
change campaign progress or issue gameplay actions. Never disables fog.
"""
import argparse
import asyncio
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from google.protobuf import descriptor_pb2, descriptor_pool, message_factory
from s2clientprotocol import sc2api_pb2 as sc
from jev_sc2.sc2 import SC2


def protocol_types():
    fd=descriptor_pb2.FileDescriptorProto(name='warmstart_probe.proto',package='probe',syntax='proto2')
    body=fd.message_type.add(name='Warmstart')
    for name,number,kind in [('replay_data',1,12),('player_id',2,5),('disable_fog',3,8),('is_host',4,8),('map_data',5,12)]:
        body.field.add(name=name,number=number,type=kind,label=1)
    request=fd.message_type.add(name='Request')
    request.field.add(name='warmstart_game',number=23,type=11,type_name='.probe.Warmstart',label=1)
    request.field.add(name='id',number=97,type=13,label=1)
    result=fd.message_type.add(name='WarmstartResponse')
    result.field.add(name='error',number=1,type=5,label=1)
    result.field.add(name='error_details',number=2,type=9,label=1)
    response=fd.message_type.add(name='Response')
    response.field.add(name='warmstart_game',number=23,type=11,type_name='.probe.WarmstartResponse',label=1)
    pool=descriptor_pool.DescriptorPool();pool.Add(fd)
    factory=message_factory.MessageFactory(pool)
    return tuple(factory.GetPrototype(pool.FindMessageTypeByName('probe.'+name)) for name in ('Request','Response'))


async def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('replay',type=Path);parser.add_argument('map',type=Path)
    parser.add_argument('--player-id',type=int,default=1)
    args=parser.parse_args()
    Request,Response=protocol_types()
    request=Request(id=1)
    request.warmstart_game.replay_data=args.replay.read_bytes()
    request.warmstart_game.map_data=args.map.read_bytes()
    request.warmstart_game.player_id=args.player_id
    request.warmstart_game.disable_fog=False
    request.warmstart_game.is_host=True
    client=await SC2.connect(5001)
    try:
        await client.request('ping',sc.RequestPing())
        if client.status!=sc.ended:raise RuntimeError('Probe requires ended API state')
        request.id=client.counter+1;client.counter+=1
        await client.ws.send(request.SerializeToString())
        raw=await asyncio.wait_for(client.ws.recv(),120)
        reply=sc.Response.FromString(raw)
        detail=Response.FromString(raw).warmstart_game
        print(json.dumps({'warmstart_error':detail.error if detail.HasField('error') else None,
                          'warmstart_error_details':detail.error_details,'response_bytes':len(raw),'status':sc.Status.Name(reply.status),
                          'errors':list(reply.error),'id':reply.id}),flush=True)
        # Preserve raw protocol evidence locally for unknown response field23.
        target=args.replay.parent/'warmstart-response.bin'
        with target.open('xb') as f:f.write(raw)
        if reply.error or detail.HasField('error'):return
        observation=await client.observe()
        print(json.dumps({'status':sc.Status.Name(client.status),'loop':observation.observation.game_loop,
                          'player_id':observation.observation.player_common.player_id,
                          'owned_units':sum(u.alliance==1 for u in observation.observation.raw_data.units),
                          'players':[(r.player_id,sc.Result.Name(r.result)) for r in observation.player_result]}),flush=True)
    finally:await client.ws.close()

if __name__=='__main__':asyncio.run(main())
