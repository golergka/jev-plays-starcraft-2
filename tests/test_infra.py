import asyncio
import subprocess
import pytest
from s2clientprotocol import raw_pb2 as raw, sc2api_pb2 as sc
from jev_sc2.reload import PlayerLoader
from jev_sc2.sc2 import SC2, find_executable
from jev_sc2.view import validate_commands, make_view


def test_jev_group_order_maps_only_shared_offered_actions():
    import player
    class Model:
        def log(self,*args,**kwargs): pass
        async def ask(self,state,questions):
            if 'strategy' in questions:
                return {'strategy':{'choice':'strengthen'}}
            if 'purpose_Marine' in questions:
                return {'purpose_Marine':{'choice':'positioning'}}
            options=questions['Marine']['criteria']
            assert 'group_north' in options and 'group_only_one_unit' not in options
            return {'Marine':{'choice':'group_north'}}
    commands=[{'unit_tag':i,'ability_id':16,'point':[i,6]} for i in (1,2)]
    units=[{'tag':i,'type':'Marine','position':[i,0], 'candidates':[{'id':'north','description':'Move north','command':c}]}
           for i,c in zip((1,2),commands)]
    units[0]['candidates'].append({'id':'only_one_unit','description':'unshared','command':{}})
    assert asyncio.run(player.decide({'self':units,'loop':1},Model(),{}))==commands


def test_spending_conflict_is_chosen_by_jev_not_command_order():
    import player
    commands=[{'unit_tag':i,'ability_id':524 if i==1 else 560} for i in (1,2)]
    units=[{'candidates':[{'command':cmd,'description':'Train unit',
                          'resource_cost':{'minerals':50,'vespene':0,'supply':1}}]} for cmd in commands]
    class Model:
        def log(self,*args,**kwargs): pass
        async def ask(self,state,questions):
            assert state['proposed_total_cost']['minerals']==100
            assert set(questions['spending']['criteria'])=={'defer','buy_0','buy_1'}
            return {'spending':{'choice':'buy_1'}}
    view={'self':units,'loop':1,'resources':{'minerals':50,'vespene':0,'supply_remaining':2}}
    assert asyncio.run(player.arbitrate_spending(commands,view,{},Model()))==[commands[1]]


def test_jev_can_select_one_builder_without_shared_build_ability():
    import player
    command={'unit_tag':1,'ability_id':319,'point':[5,5]}
    units=[{'tag':1,'type':'SCV','position':[1,1],'candidates':[{'id':'build_319_north','description':'Build SupplyDepot','command':command}]},
           {'tag':2,'type':'SCV','position':[2,2],'candidates':[]}]
    class Model:
        def log(self,*args,**kwargs): pass
        async def ask(self,state,questions):
            if 'strategy' in questions: return {'strategy':{'choice':'strengthen'}}
            assert set(questions['investment']['criteria'])=={'save','project_0'}
            return {'investment':{'choice':'project_0'}}
    assert asyncio.run(player.decide({'self':units,'loop':1},Model(),{}))==[command]


def test_map_overview_masks_unexplored_terrain_and_preserves_north_orientation():
    from s2clientprotocol import common_pb2 as common
    from jev_sc2.view import explored_map
    area=common.RectangleI(p0=common.PointI(x=0,y=0),p1=common.PointI(x=2,y=2))
    visibility=common.ImageData(bits_per_pixel=8,size=common.Size2DI(x=2,y=2),data=bytes([0,3,1,2]))
    pathing=common.ImageData(bits_per_pixel=8,size=common.Size2DI(x=2,y=2),data=bytes([0,1,1,0]))
    first=explored_map(visibility,pathing,area,cell_size=1)
    assert first['rows_north_to_south']==['.#','??']
    pathing.data=bytes([1,0,1,0])
    assert explored_map(visibility,pathing,area,cell_size=1)==first


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


def test_gather_can_return_to_distant_visible_minerals_but_not_hidden_resources():
    from s2clientprotocol import query_pb2 as query
    obs=sc.ResponseObservation()
    obs.observation.raw_data.units.add(tag=1,alliance=raw.Self,display_type=raw.Visible)
    for tag in range(10,18):
        u=obs.observation.raw_data.units.add(tag=tag,alliance=raw.Neutral,display_type=raw.Visible)
        u.pos.x=1
    for tag,display in ((99,raw.Visible),(100,raw.Hidden)):
        u=obs.observation.raw_data.units.add(tag=tag,alliance=raw.Neutral,display_type=display,mineral_contents=500)
        u.pos.x=28
    class Client:
        async def request(self,name,body):
            result=query.ResponseQuery(); result.abilities.add(unit_tag=1).abilities.add(ability_id=295)
            return result
    info=sc.ResponseGameInfo(); info.start_raw.playable_area.p1.x=30; info.start_raw.playable_area.p1.y=30
    view=asyncio.run(make_view(Client(),obs,sc.ResponseData(),info,'test'))
    assert [c['command']['target_tag'] for c in view['self'][0]['candidates']]==[99]


def test_snapshots_are_stale_locations_not_live_units_or_tag_targets():
    from s2clientprotocol import query_pb2 as query
    obs=sc.ResponseObservation()
    own=obs.observation.raw_data.units.add(tag=1,alliance=raw.Self,display_type=raw.Visible)
    own.pos.x=2; own.pos.y=2
    old=obs.observation.raw_data.units.add(tag=2,unit_type=100,alliance=raw.Enemy,display_type=raw.Snapshot,health=999)
    old.pos.x=18; old.pos.y=18
    obs.observation.raw_data.units.add(tag=3,unit_type=101,alliance=raw.Enemy,display_type=raw.Hidden)
    data=sc.ResponseData(); data.units.add(unit_id=100,name='KnownBuilding'); data.units.add(unit_id=101,name='HiddenSecret')
    info=sc.ResponseGameInfo(); info.start_raw.playable_area.p1.x=20; info.start_raw.playable_area.p1.y=20
    class Client:
        async def request(self,name,body):
            result=query.ResponseQuery(); abilities=result.abilities.add(unit_tag=1)
            abilities.abilities.add(ability_id=16); abilities.abilities.add(ability_id=23)
            return result
    view=asyncio.run(make_view(Client(),obs,data,info,'test'))
    assert view['last_known_entities']==[{'type':'KnownBuilding','alliance':'Enemy','position':[18.0,18.0],'status':'snapshot under fog; current presence and health unknown'}]
    assert view['visible_entities']==[]
    assert 'HiddenSecret' not in str(view)
    commands=[c['command'] for c in view['self'][0]['candidates'] if c['id'].startswith('last_known_')]
    assert len(commands)==2
    assert all(c['point']==[18,18] and 'target_tag' not in c for c in commands)


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
            assert name=='query'
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


def test_build_sites_require_visible_footprint_and_engine_approval():
    from s2clientprotocol import query_pb2 as query
    obs=sc.ResponseObservation()
    own=obs.observation.raw_data.units.add(tag=1,unit_type=45,alliance=raw.Self,health=45,health_max=45)
    own.pos.x=14; own.pos.y=14
    image=obs.observation.raw_data.map_state.visibility
    image.size.x=32; image.size.y=32; image.bits_per_pixel=8
    pixels=bytearray([2]*1024); pixels[14*32+8]=0; image.data=bytes(pixels)
    info=sc.ResponseGameInfo(); info.start_raw.playable_area.p1.x=32; info.start_raw.playable_area.p1.y=32
    data=sc.ResponseData(); data.abilities.add(ability_id=319,friendly_name='Build SupplyDepot',target=2,footprint_radius=1)
    class Client:
        async def request(self,name,body):
            result=query.ResponseQuery()
            if body.abilities:
                result.abilities.add(unit_tag=1).abilities.add(ability_id=319)
            else:
                assert not body.ignore_resource_requirements
                assert not any(p.target_pos.x==8 and p.target_pos.y==14 for p in body.placements)
                assert all(p.placing_unit_tag==1 for p in body.placements)
                for p in body.placements:
                    result.placements.add(result=1 if (p.target_pos.x,p.target_pos.y) in {(14,28),(20,14)} else 44)
            return result
    view=asyncio.run(make_view(Client(),obs,data,info,'build test'))
    assert {c['id'] for c in view['self'][0]['candidates']} == {'build_319_north_14','build_319_east'}


def test_concurrent_jev_calls_reserve_budget(monkeypatch):
    from types import SimpleNamespace
    import jev_sc2.jev as module
    started, release = asyncio.Event(), asyncio.Event()
    entered = []
    async def request(**kwargs):
        entered.append(True); started.set(); await release.wait()
        return SimpleNamespace(usage=SimpleNamespace(cost=0),
                               model_dump=lambda **kwargs: {'answers': {}})
    monkeypatch.setenv('OPENROUTER_API_KEY','test-key-not-a-credential')
    monkeypatch.setattr(module,'OpenRouter',lambda **kwargs: SimpleNamespace(
        alpha=SimpleNamespace(decisions=SimpleNamespace(create_async=request))))
    model=module.Jev(lambda *a,**k:None,'test',max_calls=1)
    async def concurrent():
        first=asyncio.create_task(model.ask({},{}))
        await started.wait()
        with pytest.raises(module.CallBudgetReached): await model.ask({},{})
        release.set(); await first
    asyncio.run(concurrent())
    assert len(entered)==model.calls==1
    assert model.inflight==0


def test_outcome_history_detects_replacement_hidden_by_stable_count():
    from player import recent_outcomes
    memory = {}
    def view(loop,tag,health=45):
        return {'loop':loop,'resources':{'minerals':loop},
                'self':[{'tag':tag,'type':'Marine','health':health}]}
    recent_outcomes(view(1,1),memory)
    recent_outcomes(view(20,1,20),memory)
    outcome=recent_outcomes(view(30,2),memory)
    assert outcome['own_units_appeared_by_type']=={'Marine':1}
    assert outcome['own_units_disappeared_by_type']=={'Marine':1}
    assert outcome['health_decreases_on_continuously_observed_units']=={'Marine':25}
    assert outcome['resource_changes']['minerals']==29
    outcome=recent_outcomes(view(1,5),memory)
    assert outcome['own_units_disappeared_by_type']=={}


def test_shared_investment_jev_can_save_or_choose_nonfirst_project():
    from player import choose_investment
    units=[{'tag':i,'position':[i,0],'candidates':[{'description':f'Train {name}',
            'project':{'type':name},'command':{'unit_tag':i,'ability_id':i}}]}
           for i,name in [(1,'Marine'),(2,'SCV')]]
    class Model:
        choice='save'
        def log(self,*args,**kwargs): pass
        async def ask(self,state,questions):
            return {'investment':{'choice':self.choice}}
    model=Model();view={'loop':1,'self':units}
    assert asyncio.run(choose_investment(view,{},model))==[]
    model.choice='project_1'
    assert asyncio.run(choose_investment(view,{},model))==[{'unit_tag':2,'ability_id':2}]


def test_purchase_only_building_does_not_trigger_empty_individual_control():
    import player
    class Model:
        def log(self,*args,**kwargs): pass
        async def ask(self,state,questions):
            if 'strategy' in questions: return {'strategy':{'choice':'strengthen'}}
            assert set(questions)=={'investment'}
            return {'investment':{'choice':'save'}}
    view={'loop':1,'self':[{'tag':1,'type':'Barracks','position':[0,0],
          'candidates':[{'id':'ability_560','description':'Train Marine',
                         'project':{'type':'Marine'},'command':{'unit_tag':1,'ability_id':560}}]}]}
    assert asyncio.run(player.decide(view,Model(),{}))==[]


def test_jev_can_choose_a_mixed_combat_selection_without_unit_name_rules():
    import player
    units=[]
    for tag,kind in [(1,'Alpha'),(2,'Beta')]:
        units.append({'tag':tag,'type':kind,'position':[tag,0], 'candidates':[
            {'id':'north','description':'Move north','command':{'unit_tag':tag,'ability_id':16,'point':[tag,6]}},
            {'id':'attack_move_north','description':'Attack-move north','command':{'unit_tag':tag,'ability_id':23,'point':[tag,6]}}]})
    class Model:
        def log(self,*args,**kwargs): pass
        async def ask(self,state,questions):
            if 'strategy' in questions:
                assert 'coordination' in questions
                return {'strategy':{'choice':'attack'},'coordination':{'choice':'mobile_combat'}}
            assert state['selection_facts']['MobileCombat']['count']==2
            assert state['type_selection_facts']['Alpha']['count']==1
            if 'purpose_MobileCombat' in questions:
                return {'purpose_MobileCombat':{'choice':'combat'}}
            return {'MobileCombat':{'choice':'group_attack_move_north'}}
    commands=asyncio.run(player.decide({'loop':1,'self':units},Model(),{}))
    assert [c['unit_tag'] for c in commands]==[1,2]
    assert all(c['ability_id']==23 for c in commands)


def test_jev_can_regroup_at_a_member_without_an_unoffered_self_move():
    import player
    units=[]
    for tag,other in [(1,2),(2,1)]:
        units.append({'tag':tag,'type':'Unit','position':[tag,0], 'candidates':[
            {'id':f'join_{other}','description':f'Join {other}',
             'command':{'unit_tag':tag,'ability_id':16,'point':[other,0]}},
            {'id':'hold_position','description':'Hold position',
             'command':{'unit_tag':tag,'ability_id':18}}]})
    class Model:
        def log(self,*args,**kwargs): pass
        async def ask(self,state,questions):
            if 'strategy' in questions: return {'strategy':{'choice':'assemble'}}
            if 'purpose_Unit' in questions: return {'purpose_Unit':{'choice':'positioning'}}
            assert 'group_join_1' in questions['Unit']['criteria']
            return {'Unit':{'choice':'group_join_1'}}
    commands=asyncio.run(player.decide({'loop':1,'self':units},Model(),{}))
    assert commands==[{'unit_tag':1,'ability_id':18},{'unit_tag':2,'ability_id':16,'point':[1,0]}]


def test_unaffordable_project_is_information_not_an_executable_command():
    from s2clientprotocol import query_pb2 as query
    flags=[]
    class Client:
        async def request(self,name,body):
            flags.append(body.ignore_resource_requirements)
            result=query.ResponseQuery()
            abilities=result.abilities.add(unit_tag=1)
            if body.ignore_resource_requirements:
                abilities.abilities.add(ability_id=321)
            return result
    obs=sc.ResponseObservation()
    obs.observation.raw_data.units.add(tag=1,unit_type=45,alliance=raw.Self,display_type=raw.Visible)
    data=sc.ResponseData()
    data.abilities.add(ability_id=321,friendly_name='Build Barracks',target=2)
    data.units.add(unit_id=21,name='Barracks',ability_id=321,mineral_cost=150)
    view=asyncio.run(make_view(Client(),obs,data,sc.ResponseGameInfo(),'test'))
    assert flags==[False,True]
    assert view['potential_projects'][0]['type']=='Barracks'
    assert view['potential_projects'][0]['minerals']==150
    assert view['self'][0]['candidates']==[]


def test_jev_can_choose_to_save_for_a_named_unaffordable_project():
    from player import choose_investment
    memory={}
    view={'loop':1,'self':[],'resources':{'minerals':50},'potential_projects':[
        {'type':'FutureBuilding','minerals':150,'vespene':0,'supply':0,'supply_provided':0}]}
    class Model:
        def log(self,*args,**kwargs): pass
        async def ask(self,state,questions):
            option=questions['investment']['criteria']['save_for_0']
            assert 'FutureBuilding' in option and "'minerals': 100" in option
            return {'investment':{'choice':'save_for_0'}}
    assert asyncio.run(choose_investment(view,{},Model(),memory))==[]
    assert memory['investment_intent']['target_project']=='FutureBuilding'


def test_investment_exploration_uses_only_jev_positive_probability_options():
    from player import choose_investment
    view={'loop':1,'self':[{'tag':1,'position':[0,0],'candidates':[
        {'description':'Train Unit','project':{'type':'Unit'},'command':{'unit_tag':1,'ability_id':1}}]}]}
    class Model:
        def log(self,*args,**kwargs): pass
        async def ask(self,state,questions):
            return {'investment':{'choice':'project_0','probabilities':{'save':1,'project_0':0,'invalid':100}}}
    memory={}
    assert asyncio.run(choose_investment(view,{},Model(),memory))==[]
    assert memory['investment_intent']['mode']=='save'


def test_reload_keeps_player_and_observation_adapter_atomic(tmp_path):
    def git(*args):
        return subprocess.check_output(['git','-C',str(tmp_path),*args],text=True)
    git('init','-q');git('config','user.name','Test');git('config','user.email','test@example.invalid')
    (tmp_path/'jev_sc2').mkdir()
    (tmp_path/'player.py').write_text('async def decide(*args): return 1\n')
    view=tmp_path/'jev_sc2/view.py';view.write_text('async def make_view(*args): return 2\n')
    git('add','.');git('commit','-qm','working pair')
    loader=PlayerLoader(tmp_path);loader.refresh();revision=loader.revision
    (tmp_path/'player.py').write_text('async def decide(*args): return 3\n')
    view.write_text('bad syntax!')
    git('add','.');git('commit','-qm','broken adapter')
    with pytest.raises(SyntaxError):loader.refresh()
    assert loader.revision==revision
    assert asyncio.run(loader.module.decide())==1
    assert asyncio.run(loader.view_module.make_view())==2
    view.write_text('async def make_view(*args): return 4\n')
    git('add','.');git('commit','-qm','repaired pair')
    loader.refresh()
    assert asyncio.run(loader.module.decide())==3
    assert asyncio.run(loader.view_module.make_view())==4


def test_named_savings_commitment_waits_then_requests_only_jev_chosen_project():
    from player import choose_investment
    project={'type':'ChosenProject','minerals':150,'vespene':0,'supply':0,'supply_provided':0}
    view={'loop':1,'self':[],'resources':{'minerals':50},'potential_projects':[project]}
    class Model:
        calls=0
        def log(self,*args,**kwargs): pass
        async def ask(self,state,questions):
            self.calls+=1
            return {'investment':{'choice':'save_for_0'}}
    model=Model();memory={}
    assert asyncio.run(choose_investment(view,{},model,memory))==[]
    assert asyncio.run(choose_investment({**view,'loop':2},{},model,memory))==[]
    command={'unit_tag':1,'ability_id':99}
    ready={**view,'loop':20,'self':[{'tag':1,'position':[0,0],'candidates':[
        {'description':'Build ChosenProject','project':project,'command':command}]}]}
    assert asyncio.run(choose_investment(ready,{},model,memory))==[command]
    assert model.calls==1
    assert memory['investment_intent']['mode']=='request_purchase'


def test_large_selection_is_not_truncated_and_shared_descriptions_stay_compact():
    import player
    units=[{'tag':i,'type':'Unit','position':[i,0],'candidates':[
        {'id':'join_999','description':f'Move to friendly unit tag 999, distance {i}.0',
         'command':{'unit_tag':i,'ability_id':16,'point':[0,0]}}]} for i in range(1,81)]
    class Model:
        def log(self,*args,**kwargs): pass
        async def ask(self,state,questions):
            if 'strategy' in questions: return {'strategy':{'choice':'assemble'}}
            if 'purpose_Unit' in questions: return {'purpose_Unit':{'choice':'positioning'}}
            assert len(questions['Unit']['criteria']['group_join_999'])<250
            return {'Unit':{'choice':'group_join_999'}}
    commands=asyncio.run(player.decide({'loop':1,'self':units},Model(),{}))
    assert {c['unit_tag'] for c in commands}==set(range(1,81))


def test_support_controls_use_owned_visible_compatible_targets_and_available_abilities():
    from s2clientprotocol import data_pb2 as data
    from jev_sc2.view import support_candidates
    catalog = {i:data.AbilityData(ability_id=i,friendly_name=label,target=target)
               for i,label,target in [(1,'Repair',3),(2,'Effect Heal',3),(3,'Load',3),(4,'UnloadAll',1)]}
    types = {1:data.UnitTypeData(unit_id=1,attributes=[data.Mechanical],cargo_size=1),
             2:data.UnitTypeData(unit_id=2,attributes=[data.Biological],cargo_size=1),
             3:data.UnitTypeData(unit_id=3,attributes=[data.Mechanical,data.Structure],cargo_size=0)}
    actor=raw.Unit(tag=1,alliance=raw.Self,display_type=raw.Visible,cargo_space_max=2)
    targets=[raw.Unit(tag=tag,unit_type=kind,alliance=raw.Self,display_type=display,
                      health=hp,health_max=100)
             for tag,kind,display,hp in [(2,1,raw.Visible,50),(3,2,raw.Visible,60),
                                        (4,3,raw.Visible,70),(5,1,raw.Hidden,20),
                                        (6,1,raw.Visible,100)]]
    def offered(legal):
        return support_candidates(actor,legal,catalog,types,[actor]+targets,{})
    commands=[c['command'] for c in offered({1,2,3,4})]
    assert [c['target_tag'] for c in commands if c['ability_id']==1]==[2,4]
    assert [c['target_tag'] for c in commands if c['ability_id']==2]==[3]
    assert [c['target_tag'] for c in commands if c['ability_id']==3]==[2,3,6]
    assert not any(c['ability_id']==4 for c in commands)
    assert offered(set())==[]
    actor.cargo_space_taken=2
    commands=[c['command'] for c in offered({3,4})]
    assert commands==[{'unit_tag':1,'ability_id':4}]
