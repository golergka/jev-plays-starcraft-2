import asyncio
import subprocess
import pytest
from s2clientprotocol import raw_pb2 as raw, sc2api_pb2 as sc
from jev_sc2.reload import PlayerLoader
from jev_sc2.sc2 import SC2, find_executable
from jev_sc2.view import validate_commands, make_view


def test_reload_uses_commit_and_retains_good_policy(tmp_path):
    def git(*args):
        return subprocess.check_output(['git','-C',str(tmp_path),*args],text=True)
    git('init','-q')
    git('config','user.name','Test')
    git('config','user.email','test@example.invalid')
    source=tmp_path/'player.py'
    source.write_text('async def decide(*args): return [1]\n')
    git('add','player.py'); git('commit','-qm','first')
    loader=PlayerLoader(tmp_path); loader.refresh()
    first=loader.revision
    source.write_text('async def decide(*args): return [2]\n')
    assert loader.refresh() is None
    assert asyncio.run(loader.module.decide()) == [1]
    git('add','player.py'); git('commit','-qm','second')
    assert loader.refresh() != first
    assert asyncio.run(loader.module.decide()) == [2]
    source.write_text('broken syntax!')
    git('add','player.py'); git('commit','-qm','broken')
    with pytest.raises(SyntaxError): loader.refresh()
    assert asyncio.run(loader.module.decide()) == [2]
    assert loader.refresh() is None


def test_rejects_hidden_targets_unowned_units_and_unoffered_commands():
    observation=sc.ResponseObservation()
    units=observation.observation.raw_data.units
    units.add(tag=1,alliance=raw.Self,display_type=raw.Visible)
    units.add(tag=2,alliance=raw.Enemy,display_type=raw.Hidden)
    cmd={'unit_tag':1,'ability_id':23,'target_tag':2}
    view={'self':[{'candidates':[{'command':cmd}]}]}
    assert validate_commands([cmd],view,observation)==[]
    units[1].display_type=raw.Visible
    assert len(validate_commands([cmd,cmd],view,observation))==1
    assert validate_commands([{**cmd,'ability_id':999}],view,observation)==[]
    units[0].alliance=raw.Enemy
    assert validate_commands([cmd],view,observation)==[]


def test_debug_is_unavailable():
    with pytest.raises(ValueError,match='Forbidden'):
        asyncio.run(SC2(None).request('debug',None))


def test_latest_build_numerically(tmp_path):
    for version in [9,100]:
        p=tmp_path/f'Versions/Base{version}/SC2.app/Contents/MacOS/SC2'
        p.parent.mkdir(parents=True); p.touch()
    assert 'Base100' in str(find_executable(tmp_path))


def test_real_websocket_protocol_roundtrip(tmp_path):
    from websockets.asyncio.server import serve
    map_path = tmp_path/'test.SC2Map'
    map_path.write_bytes(b'fixture-map-bytes')
    async def scenario():
        requests=[]
        async def server(ws):
            async for payload in ws:
                request=sc.Request.FromString(payload)
                requests.append(request)
                kind=request.WhichOneof('request')
                status={'ping':sc.launched,'create_game':sc.init_game,
                        'join_game':sc.in_game,'observation':sc.in_game}[kind]
                reply=sc.Response(id=request.id,status=status)
                getattr(reply,kind).SetInParent()
                if kind=='ping': reply.ping.game_version='fixture'
                await ws.send(reply.SerializeToString())
        async with serve(server,'127.0.0.1',0) as service:
            port=service.sockets[0].getsockname()[1]
            client=await SC2.connect(port)
            assert (await client.request('ping',sc.RequestPing())).game_version=='fixture'
            await client.start(map_path)
            await client.observe()
            await client.ws.close()
        assert [r.WhichOneof('request') for r in requests]==['ping','create_game','join_game','observation']
        assert requests[1].create_game.realtime
        assert requests[1].create_game.local_map.map_data == b'fixture-map-bytes'
        assert not requests[1].create_game.disable_fog
        assert requests[1].create_game.player_setup[0].type==sc.Participant
        assert not requests[2].join_game.HasField('observed_player_id')
        assert not requests[3].observation.disable_fog
    asyncio.run(scenario())


@pytest.mark.parametrize("stationary_abilities", [(), (3665,3793)])
def test_view_excludes_hidden_and_snapshot_enemies_and_uses_queried_ids(stationary_abilities):
    from s2clientprotocol import query_pb2 as query
    class Client:
        async def request(self,name,body):
            assert name=='query' and not body.ignore_resource_requirements
            result=query.ResponseQuery()
            abilities=result.abilities.add(unit_tag=1)
            abilities.abilities.add(ability_id=3794)
            abilities.abilities.add(ability_id=3674)
            for ability in stationary_abilities:
                abilities.abilities.add(ability_id=ability)
            return result
    obs=sc.ResponseObservation()
    own=obs.observation.raw_data.units.add(tag=1,unit_type=48,alliance=raw.Self,health=45,health_max=45)
    own.pos.x=10; own.pos.y=10
    for tag, display in [(2,raw.Visible),(3,raw.Hidden),(4,raw.Snapshot)]:
        enemy=obs.observation.raw_data.units.add(tag=tag,unit_type=105,alliance=raw.Enemy,display_type=display)
        enemy.pos.x=12; enemy.pos.y=12
        enemy.orders.add(ability_id=999)
    info=sc.ResponseGameInfo()
    info.start_raw.playable_area.p1.x=32; info.start_raw.playable_area.p1.y=32
    result=asyncio.run(make_view(Client(),obs,sc.ResponseData(),info,'combat test'))
    unit=result['self'][0]
    assert [u['tag'] for u in unit['surroundings']]==[2]
    assert 'orders' not in unit['surroundings'][0]
    assert {c['command']['ability_id'] for c in unit['candidates']}=={3794,3674,*stationary_abilities}
    for candidate in unit['candidates']:
        if candidate['id'] in {'stop','hold_position'}:
            assert set(candidate['command']) == {'unit_tag','ability_id'}


def test_multistage_decision_cannot_exceed_call_budget(monkeypatch):
    from types import SimpleNamespace
    from unittest.mock import AsyncMock
    import jev_sc2.jev as module
    response = SimpleNamespace(usage=SimpleNamespace(cost=0),
                               model_dump=lambda **kwargs: {'answers': {}})
    request = AsyncMock(return_value=response)
    monkeypatch.setenv('OPENROUTER_API_KEY', 'test-key-not-a-credential')
    monkeypatch.setattr(module, 'OpenRouter', lambda **kwargs: SimpleNamespace(
        alpha=SimpleNamespace(decisions=SimpleNamespace(create_async=request))))
    model = module.Jev(lambda *a, **k: None, 'test', max_calls=1)
    async def two_stages():
        await model.ask({}, {})
        with pytest.raises(module.CallBudgetReached):
            await model.ask({}, {})
    asyncio.run(two_stages())
    assert request.await_count == 1


def test_terrain_is_masked_by_current_player_visibility():
    from s2clientprotocol.common_pb2 import ImageData
    from jev_sc2.view import visible_terrain
    visibility = ImageData(bits_per_pixel=8, data=bytes([0,1,2,2]))
    visibility.size.x, visibility.size.y = 4, 1
    pathing = ImageData(bits_per_pixel=1, data=bytes([0b10100000]))
    pathing.size.x, pathing.size.y = 4, 1
    assert visible_terrain(visibility,pathing,0,0).startswith('unknown')
    assert visible_terrain(visibility,pathing,1,0).startswith('unknown')
    assert visible_terrain(visibility,pathing,2,0) == 'walkable static terrain'
    assert visible_terrain(visibility,pathing,3,0) == 'blocked static terrain'
    assert visible_terrain(visibility,pathing,9,0).startswith('unknown')
