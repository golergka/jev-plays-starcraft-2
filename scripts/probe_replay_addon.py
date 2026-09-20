"""Read-only player-POV replay diagnostic; never credits campaign progress."""
import asyncio
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from jev_sc2.sc2 import SC2
from s2clientprotocol import sc2api_pb2 as sc, query_pb2 as query, error_pb2

async def diagnostic_request(client,name,body):
    assert name in ('start_replay','step')
    async with client.lock:
        client.counter+=1
        await client.ws.send(sc.Request(id=client.counter,**{name:body}).SerializeToString())
        reply=sc.Response.FromString(await asyncio.wait_for(client.ws.recv(),60))
        if reply.id!=client.counter or reply.error:raise RuntimeError(str(reply.error))
        client.status=reply.status
        result=getattr(reply,name)
        if 'error' in result.DESCRIPTOR.fields_by_name and result.HasField('error'):raise RuntimeError(str(result))
        return result

async def main():
    replay,output,map_path=map(Path,sys.argv[1:4]);result={'replay':str(replay),'mode':'player1 replay; fog enabled; no action requests','samples':[]}
    client=await SC2.connect(5001)
    try:
        await client.request('ping',sc.RequestPing())
        if client.status==sc.in_game:await client.request('leave_game',sc.RequestLeaveGame())
        await diagnostic_request(client,'start_replay',sc.RequestStartReplay(replay_path=str(replay.resolve()),map_data=map_path.read_bytes(),observed_player_id=1,disable_fog=False,realtime=False,options=sc.InterfaceOptions(raw=True, raw_crop_to_playable_area=True)))
        data=await client.request('data',sc.RequestData(unit_type_id=True,ability_id=True))
        names={u.unit_id:u.name for u in data.units}
        obs=await client.observe()
        for target_loop in (21188,21190,21688,21690,22479):
            delta=target_loop-obs.observation.game_loop
            if delta>0:await diagnostic_request(client,'step',sc.RequestStep(count=delta))
            obs=await client.observe()
            owned=[u for u in obs.observation.raw_data.units if u.alliance==1]
            row={'loop':obs.observation.game_loop,'producers':[{'tag':u.tag,'type':names.get(u.unit_type),'position':[u.pos.x,u.pos.y],'addon_tag':u.add_on_tag,'orders':[{'ability':o.ability_id,'progress':o.progress} for o in u.orders]} for u in owned if names.get(u.unit_type,'').startswith('Barracks')], 'queries':[]}
            result['samples'].append(row);output.write_text(json.dumps(result,indent=2)+'\n')
            for u in owned:
                if names.get(u.unit_type)!='Barracks':continue
                tests=[]
                for name,point in [('omitted',None),('producer_center',(u.pos.x,u.pos.y))]:
                    p=query.RequestQueryBuildingPlacement(ability_id=421,placing_unit_tag=u.tag)
                    if point:p.target_pos.x,p.target_pos.y=point
                    tests.append((name,p))
                try:
                    answer=await client.request('query',query.RequestQuery(placements=[p for _,p in tests]))
                    row['queries'].append({'tag':u.tag,'results':[{ 'variant':n,'result':error_pb2.ActionResult.Name(r.result)} for (n,_),r in zip(tests,answer.placements)]})
                except Exception as exc:row['queries'].append({'error':str(exc)})
            output.write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps(result))
    except Exception as exc:
        result['error']=str(exc)
        output.write_text(json.dumps(result,indent=2)+'\n')
        raise
    finally:await client.ws.close()

if __name__=='__main__':asyncio.run(main())
