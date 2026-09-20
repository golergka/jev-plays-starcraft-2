"""Bounded infrastructure diagnostic, no gameplay orders or campaign credit."""
import asyncio
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from jev_sc2.sc2 import SC2
from scripts.probe_api_lifetime import advance_diagnostic
from s2clientprotocol import sc2api_pb2 as sc, common_pb2 as common, query_pb2 as query, error_pb2

async def main():
    map_path, output = map(Path, sys.argv[1:3])
    result = {'mode': 'live stepped diagnostic; fog enabled; no action requests; no campaign credit', 'samples': []}
    client = await SC2.connect(5001)
    try:
        await client.request('ping', sc.RequestPing())
        if client.status in (sc.in_game, sc.in_replay):
            await client.request('leave_game', sc.RequestLeaveGame())
        await client.request('create_game', sc.RequestCreateGame(
            local_map=sc.LocalMap(map_path=map_path.name, map_data=map_path.read_bytes()),
            player_setup=[sc.PlayerSetup(type=sc.Participant)], disable_fog=False, realtime=False))
        await client.request('join_game', sc.RequestJoinGame(race=common.Terran, player_name='Placement diagnostic',
            options=sc.InterfaceOptions(raw=True, raw_crop_to_playable_area=True)))
        data = await client.request('data', sc.RequestData(unit_type_id=True, ability_id=True))
        names = {u.unit_id: u.name for u in data.units}
        for index in range(9):
            obs = await client.observe()
            own = [u for u in obs.observation.raw_data.units if u.alliance == 1]
            producers = [u for u in own if names.get(u.unit_type) in ('Barracks', 'SCV')]
            row = {'loop': obs.observation.game_loop, 'queries': []}
            result['samples'].append(row)
            for u in producers:
                if names[u.unit_type] == 'SCV' and any(r['type']=='SCV' for r in row['queries']): continue
                ability = 421 if names[u.unit_type]=='Barracks' else 319
                variants = [('omitted', None), ('center', (u.pos.x,u.pos.y)), ('east6', (u.pos.x+6,u.pos.y)), ('west6',(u.pos.x-6,u.pos.y))]
                placements=[]
                for _, point in variants:
                    p=query.RequestQueryBuildingPlacement(ability_id=ability, placing_unit_tag=u.tag)
                    if point: p.target_pos.x,p.target_pos.y=point
                    placements.append(p)
                answer=await client.request('query', query.RequestQuery(placements=placements, ignore_resource_requirements=True,
                    abilities=[query.RequestQueryAvailableAbilities(unit_tag=u.tag)]))
                row['queries'].append({'tag':u.tag,'type':names[u.unit_type], 'position':[u.pos.x,u.pos.y], 'ability':ability,
                    'available_abilities':[a.ability_id for item in answer.abilities for a in item.abilities],
                    'placements':[{ 'variant':n,'result':error_pb2.ActionResult.Name(r.result)} for (n,_),r in zip(variants,answer.placements)]})
            output.write_text(json.dumps(result,indent=2)+'\n')
            if any(names.get(u.unit_type)=='Barracks' for u in producers):break
            if index<8: await advance_diagnostic(client,256)
        print(json.dumps(result))
    except Exception as exc:
        result['error']=str(exc); output.write_text(json.dumps(result,indent=2)+'\n'); raise
    finally: await client.ws.close()

if __name__=='__main__':asyncio.run(main())
