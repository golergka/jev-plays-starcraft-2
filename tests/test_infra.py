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
            table=state['units']
            observed=[dict(zip(table['columns'],row)) for row in table['rows']]
            assert sum(u['type']=='Alpha' for u in observed)==1
            assert 'type_selection_facts' not in state
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


def test_jev_can_attack_move_to_member_without_attacking_the_anchor():
    import player
    units=[]
    for tag,other in [(1,2),(2,1)]:
        units.append({'tag':tag,'type':'Unit','position':[tag,0], 'candidates':[
            {'id':f'attack_move_join_{other}','description':f'Attack-move to {other}',
             'command':{'unit_tag':tag,'ability_id':23,'point':[other,0]}},
            {'id':'hold_position','description':'Hold position',
             'command':{'unit_tag':tag,'ability_id':18}}]})
    class Model:
        def log(self,*args,**kwargs): pass
        async def ask(self,state,questions):
            if 'strategy' in questions: return {'strategy':{'choice':'assemble'}}
            if 'purpose_Unit' in questions: return {'purpose_Unit':{'choice':'combat'}}
            assert 'group_attack_move_join_1' in questions['Unit']['criteria']
            return {'Unit':{'choice':'group_attack_move_join_1'}}
    commands=asyncio.run(player.decide({'loop':1,'self':units},Model(),{}))
    assert commands==[{'unit_tag':1,'ability_id':18},{'unit_tag':2,'ability_id':23,'point':[1,0]}]


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
                      health=hp,health_max=100,build_progress=1)
             for tag,kind,display,hp in [(2,1,raw.Visible,50),(3,2,raw.Visible,60),
                                        (4,3,raw.Visible,70),(5,1,raw.Hidden,20),
                                        (6,1,raw.Visible,100)]]
    def offered(legal):
        return support_candidates(actor,legal,catalog,types,[actor]+targets,{})
    commands=[c['command'] for c in offered({1,2,3,4})]
    for candidate in offered({1,2}):
        if candidate['command']['ability_id']==1:
            assert 'consume resources' in candidate['description']
            assert 'consume resources' in candidate['capability_description']
            assert 'cannot harvest at the same time' in candidate['description']
        else:
            assert 'consume resources' not in candidate['description']
    assert [c['target_tag'] for c in commands if c['ability_id']==1]==[2,4]
    assert [c['target_tag'] for c in commands if c['ability_id']==2]==[3]
    assert [c['target_tag'] for c in commands if c['ability_id']==3]==[2,3,6]
    assert not any(c['ability_id']==4 for c in commands)
    assert offered(set())==[]
    actor.cargo_space_taken=2
    commands=[c['command'] for c in offered({3,4})]
    assert commands==[{'unit_tag':1,'ability_id':4}]


def test_support_capability_is_visible_before_jev_selects_contribution():
    import player
    class Model:
        def log(self,*args,**kwargs): pass
        async def ask(self,state,questions):
            if 'strategy' in questions:
                return {'strategy':{'choice':'hold'}}
            if 'purpose_Carrier' in questions:
                assert 'load owned units' in questions['purpose_Carrier']['criteria']['other']
                assert state['selection_facts']['Carrier']['count']==1
                return {'purpose_Carrier':{'choice':'other'}}
            assert 'support_ability_3_2_only_1' in questions['Carrier']['criteria']
            return {'Carrier':{'choice':'support_ability_3_2_only_1'}}
    command={'unit_tag':1,'ability_id':3,'target_tag':2}
    view={'loop':1,'self':[{'tag':1,'type':'Carrier','position':[0,0],
        'cargo':{'used':0,'capacity':4,'passengers':[]},'candidates':[
            {'id':'ability_3_2','description':'Load target',
             'capability_description':'Load: load owned units into available cargo space','command':command}]}]}
    assert asyncio.run(player.decide(view,Model(),{}))==[command]


def test_jev_support_assignment_preserves_other_workers_and_excludes_duplicate_carriers():
    import player
    units=[{'tag':i,'position':[i,0],'orders':[{'ability':'Harvest'}]} for i in (1,2)]
    requests={'Support':[{'command':{'unit_tag':i,'ability_id':3,'target_tag':9},
                          'description':'Load passenger','exclusive_target':True} for i in (1,2)]}
    class Model:
        def log(self,*args,**kwargs): pass
        async def ask(self,state,questions):
            assert 'all' not in questions['Support']['criteria']
            assert 'Harvest' in questions['Support']['criteria']['unit_1']
            return {'Support':{'choice':'unit_2'}}
    chosen=asyncio.run(player.assign_support({'loop':1,'self':units},{},Model(),requests))
    assert chosen==[{'unit_tag':2,'ability_id':3,'target_tag':9}]


def test_engine_feedback_distinguishes_rejection_acceptance_and_stale_drop():
    from jev_sc2.__main__ import action_feedback
    from s2clientprotocol import error_pb2
    a=sc.Action(); a.action_raw.unit_command.ability_id=316; a.action_raw.unit_command.unit_tags.append(7)
    f=action_feedback([a],[error_pb2.NotEnoughMinerals],100,1,5,32)
    assert f['failures']==[{'ability_id':316,'unit_tags':[7],'result':'NotEnoughMinerals'}]
    assert f['accepted']==0 and not f['discarded_as_stale']
    assert action_feedback([a],[error_pb2.Success],100,1,5,32)['accepted']==1
    assert action_feedback([],[],100,1,40,32)['discarded_as_stale']


def test_income_observation_distinguishes_missing_from_zero():
    from s2clientprotocol import query_pb2 as query
    class Client:
        async def request(self,*args): return query.ResponseQuery()
    obs=sc.ResponseObservation()
    data=sc.ResponseData(); info=sc.ResponseGameInfo()
    view=asyncio.run(make_view(Client(),obs,data,info,'test'))
    assert view['resources']['estimated_minerals_per_minute'] is None
    obs.observation.score.score_details.collection_rate_minerals=0
    obs.observation.score.score_details.collection_rate_vespene=123
    view=asyncio.run(make_view(Client(),obs,data,info,'test'))
    assert view['resources']['estimated_minerals_per_minute']==0
    assert view['resources']['estimated_vespene_per_minute']==123


def test_compact_contribution_retains_measured_threats_and_existing_work():
    import player
    units=[{'tag':1,'type':'Worker','position':[0,0],'orders':[{'ability':'Harvest'}],'candidates':[]}]
    view={'self':units,'visible_entities':[{'type':'Threat','alliance':'Enemy','position':[3,4]},
                                          {'type':'Remote','alliance':'Enemy','position':[100,100]}]}
    facts=player.selection_facts(view,{'Worker':units},{})
    assert facts['Worker']['nearest_visible_enemy_distance']==5
    assert facts['Worker']['visible_enemies_within_12_of_any_member']=={'Threat':1}
    compact=player.investment_state({'selection_facts':facts,'units':units,**view})
    assert 'units' not in compact and 'self' not in compact
    assert compact['selection_facts']['Worker']['current_order_counts']=={'Harvest':1}


def test_feedback_names_and_counts_rejected_actions_without_prescribing_response():
    import player
    view={'self':[{'tag':1,'type':'Worker','candidates':[
        {'command':{'ability_id':316},'description':'Repair target',
         'capability_description':'Repair: restore damaged owned units'}]},
        {'tag':2,'type':'Worker','candidates':[]}]}
    memory={'action_feedback':[{'loop':5,'failures':[
        {'ability_id':316,'unit_tags':[1],'result':'NotEnoughMinerals'},
        {'ability_id':316,'unit_tags':[2],'result':'NotEnoughMinerals'}]}]}
    feedback=player.describe_action_feedback(view,memory)
    failure=feedback[0]['failures'][0]
    assert failure['action']=='Repair: restore damaged owned units'
    assert failure['rejected_commands']==2 and failure['unit_types']=={'Worker':2}
    assert len(feedback[0]['failures'])==1
    view['self'][0]['candidates']=[]
    assert player.describe_action_feedback(view,memory)[0]['failures'][0]['action']==failure['action']


def test_jev_contribution_commitment_retains_sample_and_rechecks_unavailable_choice():
    import player
    class Model:
        calls=0
        def log(self,*args,**kwargs): pass
        async def ask(self,state,questions):
            self.calls+=1
            assert '672 game loops' in questions['purpose_Test']['instructions']
            return {'purpose_Test':{'choice':'positioning','probabilities':{'income':1,'positioning':0,'unoffered':100}}}
    model=Model();memory={};state={};q={'purpose_Test':{'instructions':'Choose role','criteria':{'income':'Gather','positioning':'Move'}}}
    assert asyncio.run(player.choose_contributions({'loop':1},state,q,model,memory))['purpose_Test']['choice']=='income'
    assert asyncio.run(player.choose_contributions({'loop':100},state,q,model,memory))['purpose_Test']['choice']=='income'
    assert model.calls==1
    q['purpose_Test']['criteria'].pop('income')
    assert asyncio.run(player.choose_contributions({'loop':101},state,q,model,memory))['purpose_Test']['choice']=='positioning'
    assert model.calls==2


def test_unfinished_construction_has_context_action_not_repair_when_engine_offers_it():
    from s2clientprotocol import data_pb2 as data
    from jev_sc2.view import support_candidates
    actor=raw.Unit(tag=1,alliance=raw.Self,display_type=raw.Visible)
    target=raw.Unit(tag=2,unit_type=10,alliance=raw.Self,display_type=raw.Visible,
                    health=30,health_max=100,build_progress=.3)
    types={10:data.UnitTypeData(unit_id=10,attributes=[data.Structure,data.Mechanical])}
    abilities={1:data.AbilityData(ability_id=1,friendly_name='Smart',target=3),
               316:data.AbilityData(ability_id=316,friendly_name='Effect Repair SCV',target=3)}
    choices=support_candidates(actor,{1,316},abilities,types,[actor,target],{},builder=True)
    assert [c['command']['ability_id'] for c in choices]==[1]
    assert support_candidates(actor,{316},abilities,types,[actor,target],{},builder=True)==[]
    assert support_candidates(actor,{1},abilities,types,[actor,target],{},builder=False)==[]
    target.build_progress=1
    assert [c['command']['ability_id'] for c in support_candidates(actor,{1,316},abilities,types,[actor,target],{},builder=True)]==[316]


def test_attack_target_facts_expose_air_ground_without_asserting_legality():
    from s2clientprotocol import data_pb2 as data
    from jev_sc2.view import attack_target_facts
    attacker=raw.Unit(unit_type=1); target=raw.Unit(is_flying=False)
    product=data.UnitTypeData(unit_id=1);product.weapons.add(type=data.Weapon.Air)
    description=attack_target_facts(attacker,target,{1:product})
    assert description=='target is ground; catalog weapons target air'
    target.is_flying=True
    assert 'target is airborne' in attack_target_facts(attacker,target,{1:product})
    assert 'unspecified classes' in attack_target_facts(attacker,target,{})


@pytest.mark.parametrize('affordable',[False,True])
def test_gas_building_uses_visible_geyser_tag_and_resource_aware_availability(affordable):
    from s2clientprotocol import query_pb2 as query
    obs=sc.ResponseObservation()
    obs.observation.raw_data.units.add(tag=1,alliance=raw.Self,display_type=raw.Visible)
    for tag,display in [(2,raw.Visible),(3,raw.Hidden),(4,raw.Snapshot)]:
        obs.observation.raw_data.units.add(tag=tag,alliance=raw.Neutral,display_type=display,vespene_contents=2000)
    obs.observation.raw_data.units.add(tag=5,alliance=raw.Neutral,display_type=raw.Visible,mineral_contents=1000)
    data=sc.ResponseData()
    data.units.add(unit_id=100,name='GasPlant',ability_id=55,has_vespene=True,mineral_cost=75)
    data.abilities.add(ability_id=55,friendly_name='Build GasPlant',target=3)
    class Client:
        async def request(self,name,body):
            response=query.ResponseQuery()
            if affordable or body.ignore_resource_requirements:
                response.abilities.add(unit_tag=1).abilities.add(ability_id=55)
            return response
    view=asyncio.run(make_view(Client(),obs,data,sc.ResponseGameInfo(),'test'))
    assert view['potential_projects'][0]['allows_vespene_harvesting']
    commands=[c['command'] for c in view['self'][0]['candidates']]
    assert commands==([{'unit_tag':1,'ability_id':55,'target_tag':2}] if affordable else [])


def test_failure_feedback_survives_harness_window_without_double_counting():
    import player
    failure = {'loop':100,'failures':[{'ability_id':1,'result':'InvalidTarget','unit_tags':[1]}]}
    memory = {'action_feedback':[failure]}
    view = {'loop':101,'self':[{'tag':1,'type':'Test','candidates':[]}]}
    assert len(player.describe_action_feedback(view,memory)) == 1
    assert len(player.describe_action_feedback(view,memory)) == 1
    memory['action_feedback'] = [{'loop':300,'failures':[]}]
    view['loop'] = 301
    feedback = player.describe_action_feedback(view,memory)
    assert [e['loop'] for e in feedback] == [100,300]
    assert feedback[0]['failures'][0]['rejected_commands'] == 1
    view['loop'] = 773
    memory['action_feedback'] = []
    assert player.describe_action_feedback(view,memory) == []
    view['loop'] = 101
    memory['action_feedback'] = [failure]
    player.describe_action_feedback(view,memory)
    view['loop'] = 1
    memory['action_feedback'] = []
    assert player.describe_action_feedback(view,memory) == []


def test_movement_outcomes_distinguish_round_trip_from_stationary_and_missing_units():
    from player import recent_outcomes
    memory = {}
    def view(loop,x,extra=False):
        units=[{'tag':1,'type':'Traveler','position':[x,0]},
               {'tag':2,'type':'Stationary','position':[0,0]}]
        if extra: units.append({'tag':3,'type':'Intermittent','position':[5,5]})
        return {'loop':loop,'self':units,'resources':{}}
    recent_outcomes(view(1,0,True),memory)
    recent_outcomes(view(10,3),memory)
    outcome=recent_outcomes(view(20,0,True),memory)['movement_by_type']
    assert outcome['Traveler']['mean_net_displacement']==0
    assert outcome['Traveler']['mean_sampled_distance_travelled']==6
    assert outcome['Stationary']['mean_sampled_distance_travelled']==0
    assert 'Intermittent' not in outcome
    assert recent_outcomes(view(1,0),memory)['movement_by_type']=={}


def test_job_grouping_separates_assignments_without_choosing_actions():
    from player import control_groups
    units=[{'tag':i,'type':'WorkerLike','candidates':[], 'orders':orders}
           for i,orders in enumerate([[],[{'ability':'Gather','target_tag':10}],
               [{'ability':'Gather','target_tag':11}], [{'ability':'Gather','target_tag':10}]],1)]
    original=__import__('copy').deepcopy(units)
    groups=control_groups(units,'by_current_order',{})
    assert sorted(sorted(u['tag'] for u in group) for group in groups.values())==[[1],[2,4],[3]]
    assert units==original
    assert len(control_groups(units,'by_type',{}))==1


def test_harvest_job_identity_survives_return_and_forgets_interrupted_assignment():
    from player import control_groups
    memory={}
    def unit(ability,target):
        return {'tag':1,'type':'AnyWorker','candidates':[],
                'orders':[{'ability':ability,'target_tag':target}]}
    gather=unit('Harvest Gather Any',10)
    control_groups([gather],'by_type',{},memory)
    a=control_groups([gather],'by_current_order',{},memory)
    b=control_groups([unit('Harvest Return Any',99)],'by_current_order',{},memory)
    assert list(a)==list(b)
    c=control_groups([unit('Harvest Gather Any',11)],'by_current_order',{},memory)
    assert list(a)!=list(c)
    control_groups([unit('Move Move',None)],'by_current_order',{},memory)
    unknown=control_groups([unit('Harvest Return Any',99)],'by_current_order',{},memory)
    assert 'resource unknown' in next(iter(unknown))
    assert 'target 99' not in next(iter(unknown))
    control_groups([gather],'by_type',{},memory)
    control_groups([],'by_type',{},memory)
    assert memory=={}


def test_large_jev_batch_splits_without_losing_choices_or_state():
    import asyncio
    from types import SimpleNamespace
    from jev_sc2.jev import Jev
    requests=[]
    async def create_async(**kw):
        requests.append(kw)
        answers={k:{'choice':'keep'} for k in kw['questions']}
        return SimpleNamespace(usage=SimpleNamespace(cost=0),
            model_dump=lambda **unused:{'answers':answers})
    model=Jev.__new__(Jev)
    model.client=SimpleNamespace(alpha=SimpleNamespace(decisions=SimpleNamespace(create_async=create_async)))
    model.log=lambda *a,**k:None
    model.session='test';model.model='typesafe/jev-1.13'
    model.max_calls=10;model.calls=0;model.inflight=0;model.cost=0
    state={'fact':'visible only'}
    questions={str(i):{'criteria':{'keep':'x'*25000}} for i in range(4)}
    answers=asyncio.run(model.ask(state,questions))
    assert set(answers)==set(questions)
    assert len(requests)==2 and model.calls==2 and model.inflight==0
    assert all(r['state'] is state for r in requests)
    assert {k:v for r in requests for k,v in r['questions'].items()}==questions


def test_order_context_deduplicates_capabilities_but_preserves_jobs_and_targets():
    from player import order_state
    source={'selection_facts':{'Worker / Harvest cycle':{'count':3,'current_order_counts':{'Gather':3},
        'available_projects':[{'type':'Building'}],'available_support_abilities':['Repair']}},
        'type_selection_facts':{'Worker':{'available_projects':[{'type':'Building'}]}},
        'units':[{'tag':1,'position':[2,3]}],'visible_entities':[{'tag':9}]}
    compact=order_state(source)
    assert compact['selection_facts']['Worker / Harvest cycle']=={'count':3,'current_order_counts':{'Gather':3}}
    assert compact['type_selection_facts']==source['type_selection_facts']
    assert [dict(zip(compact['visible_entities']['columns'],row)) for row in compact['visible_entities']['rows']]==source['visible_entities']
    assert [dict(zip(compact['units']['columns'], row)) for row in compact['units']['rows']]==source['units']
    assert 'available_projects' in source['selection_facts']['Worker / Harvest cycle']


def test_resource_category_keeps_every_target_and_jev_selects_both_stages():
    import asyncio
    from player import choose_concrete_orders
    class Model:
        calls=[]
        def log(self,*a,**k):pass
        async def ask(self,state,questions):
            self.calls.append(questions)
            return {'workers':{'choice':'gather_minerals' if len(self.calls)==1 else 'field_b'}}
    model=Model()
    question={'type':'choice','instructions':'Choose order','criteria':{
        'field_a':'Gather minerals at A','field_b':'Gather minerals at B',
        'gas_a':'Gather vespene gas at C','continue':'Keep orders'}}
    answer=asyncio.run(choose_concrete_orders({}, {'workers':question},model))
    assert answer['workers']['choice']=='field_b'
    assert set(model.calls[0]['workers']['criteria'])=={'gather_minerals','gather_vespene','continue'}
    assert set(model.calls[1]['workers']['criteria'])=={'field_a','field_b','continue'}
    assert 'gas_a' in question['criteria']


def test_research_controls_require_exact_offered_ability_and_unfinished_upgrade():
    from s2clientprotocol import data_pb2 as data
    from jev_sc2.view import research_candidates
    from player import is_purchase, investment_description
    unit=raw.Unit(tag=1)
    upgrade=data.UpgradeData(upgrade_id=5,name='TestUpgrade',ability_id=123,mineral_cost=100,vespene_cost=75,research_time=30)
    catalog={123:data.AbilityData(ability_id=123,target=1)}
    c=research_candidates(unit,{123},catalog,{123:upgrade},set())[0]
    assert is_purchase(c)
    assert c['command']=={'unit_tag':1,'ability_id':123}
    assert c['resource_cost']=={'minerals':100,'vespene':75,'supply':0}
    assert 'not an additional unit' in investment_description('Research TestUpgrade',c['project'],{})
    assert research_candidates(unit,set(),catalog,{123:upgrade},set())==[]
    assert research_candidates(unit,{123},catalog,{123:upgrade},{5})==[]
    catalog[123].target=2
    assert research_candidates(unit,{123},catalog,{123:upgrade},set())==[]


def test_outcomes_distinguish_started_completed_and_discontinuous_construction():
    from player import recent_outcomes
    memory={}
    def view(loop,progress):
        return {'loop':loop,'resources':{},'self':[] if progress is None else
            [{'tag':1,'type':'Project','build_progress':progress,'health':10}]}
    recent_outcomes(view(1,.2),memory)
    pending=recent_outcomes(view(20,.4),memory)
    assert pending['currently_incomplete_projects'][0]['progress_change']==.2
    assert pending['completed_from_observed_incomplete_by_type']=={}
    done=recent_outcomes(view(30,1),memory)
    assert done['completed_from_observed_incomplete_by_type']=={'Project':1}
    assert done['currently_incomplete_projects']==[]
    assert recent_outcomes(view(1,1),memory)['completed_from_observed_incomplete_by_type']=={}
    recent_outcomes(view(2,None),memory)
    pending=recent_outcomes(view(10,.3),memory)
    assert pending['currently_incomplete_projects'][0]['observed_loops']==0


def test_server_token_rejection_splits_exact_questions_and_releases_budget(monkeypatch):
    import asyncio
    from types import SimpleNamespace
    import jev_sc2.jev as module
    class Rejected(Exception): pass
    monkeypatch.setattr(module, 'BadRequestResponseError', Rejected)
    requests=[]
    async def create_async(**kw):
        requests.append(kw)
        if len(kw['questions']) > 1:
            raise Rejected('max_tokens_exceeded')
        return SimpleNamespace(usage=SimpleNamespace(cost=0),
            model_dump=lambda **unused:{'answers':{k:{'choice':'keep'} for k in kw['questions']}})
    model=module.Jev.__new__(module.Jev)
    model.client=SimpleNamespace(alpha=SimpleNamespace(decisions=SimpleNamespace(create_async=create_async)))
    model.log=lambda *a,**k:None
    model.session='test';model.model='typesafe/jev-1.13'
    model.max_calls=2;model.calls=0;model.inflight=0;model.cost=0
    state={'fact':'visible only'}
    questions={str(i):{'criteria':{'keep':'Continue'}} for i in range(2)}
    assert set(asyncio.run(model.ask(state,questions)))==set(questions)
    assert len(requests)==3 and model.calls==2 and model.inflight==0
    assert all(r['state'] is state for r in requests)
    assert {k:v for r in requests[1:] for k,v in r['questions'].items()}==questions
    model.max_calls=None
    async def always_reject(**kw): raise Rejected('max_tokens_exceeded')
    model.client.alpha.decisions.create_async=always_reject
    import pytest
    with pytest.raises(Rejected):
        asyncio.run(model.ask(state,{'single':questions['0']}))
    assert model.inflight==0


def test_order_context_rounds_spatial_text_without_mutating_execution_facts():
    from player import order_state
    source={'units':[{'tag':4399038467,'position':[53.71894073486328,21.01488494873047],
                      'health_fraction':0.123456,'orders':[{'target_tag':4399038467}]}],
            'visible_entities':[{'position':[1.123456,2.987654]}]}
    result=order_state(source)
    unit=dict(zip(result['units']['columns'],result['units']['rows'][0]))
    assert unit['position']==[53.72,21.01]
    assert dict(zip(result['visible_entities']['columns'],result['visible_entities']['rows'][0]))['position']==[1.12,2.99]
    assert unit['tag']==4399038467
    assert unit['health_fraction']==0.123456
    assert source['units'][0]['position'][0]==53.71894073486328


def test_concrete_orders_keep_only_queried_job_summaries_and_all_world_facts():
    import asyncio
    from player import choose_concrete_orders
    class Model:
        async def ask(self,state,questions):
            self.state=state
            return {'Worker / idle':{'choice':'continue'}}
        def log(self,*a,**k):pass
    model=Model()
    state={'selection_facts':{'Worker / idle':{'count':1},'Marine / idle':{'count':7}},
           'units':[{'tag':1},{'tag':2}], 'visible_entities':[{'tag':3}],
           'type_selection_facts':{'Marine':{'count':7}}, 'unit_type_facts':{'Marine':{'weapons':['test']}}}
    questions={'Worker / idle':{'criteria':{'continue':'Keep orders'},'type':'choice'}}
    asyncio.run(choose_concrete_orders(state,questions,model))
    assert model.state['selection_facts']=={'Worker / idle':{'count':1}}
    for key in ('units','visible_entities','unit_type_facts'):
        assert model.state[key]==state[key]
    assert 'type_selection_facts' not in model.state
    assert state['type_selection_facts']=={'Marine':{'count':7}}
    assert len(state['selection_facts'])==2


def test_split_requests_scope_job_summaries_without_removing_world_facts():
    import asyncio
    from types import SimpleNamespace
    from jev_sc2.jev import Jev
    requests=[]
    async def create_async(**kw):
        requests.append(kw)
        return SimpleNamespace(usage=SimpleNamespace(cost=0),model_dump=lambda **unused:
            {'answers':{k:{'choice':'keep'} for k in kw['questions']}})
    model=Jev.__new__(Jev)
    model.client=SimpleNamespace(alpha=SimpleNamespace(decisions=SimpleNamespace(create_async=create_async)))
    model.log=lambda *a,**k:None
    model.session='test';model.model='typesafe/jev-1.13'
    model.max_calls=10;model.calls=0;model.inflight=0;model.cost=0
    questions={str(i):{'criteria':{'keep':'x'*25000}} for i in range(4)}
    state={'selection_facts':{k:{'count':1} for k in questions},'units':[{'tag':1}],
           'visible_entities':[{'tag':9}]}
    assert set(asyncio.run(model.ask(state,questions)))==set(questions)
    assert len(requests)==2
    for request in requests:
        assert set(request['state']['selection_facts'])==set(request['questions'])
        assert request['state']['units']==state['units']
        assert request['state']['visible_entities']==state['visible_entities']
    assert len(state['selection_facts'])==4


def test_cumulative_outcomes_survive_window_without_recount_and_reset_on_rewind():
    from player import recent_outcomes
    memory={}
    def view(loop,tags):
        return {'loop':loop,'self':[{'tag':t,'type':'Marine','health':45} for t in tags]}
    recent_outcomes(view(1,[1,2]),memory,window=5)
    recent_outcomes(view(3,[2,3]),memory,window=5)
    recent_outcomes(view(3,[2,3]),memory,window=5)
    recent_outcomes(view(10,[2,3]),memory,window=5)
    result=recent_outcomes(view(20,[2,3]),memory,window=5)
    assert result['own_units_disappeared_by_type']=={}
    cumulative=result['cumulative_observed_unit_changes']
    assert cumulative['appeared_by_type']=={'Marine':1}
    assert cumulative['disappeared_by_type']=={'Marine':1}
    assert cumulative['since_loop']==1
    reset=recent_outcomes(view(1,[1]),memory)['cumulative_observed_unit_changes']
    assert reset['disappeared_by_type']=={}
    assert reset['through_loop']==1


def test_investment_sampling_retains_purchase_mass_and_logs_actual_distribution():
    from player import choose_investment
    view={'loop':1,'self':[{'tag':1,'position':[0,0],'candidates':[
        {'description':'Train Unit','project':{'type':'Unit'},'command':{'unit_tag':1,'ability_id':1}}]}]}
    class Rng:
        def choices(self,options,weights,k):
            assert options==['save','project_0']
            assert weights==pytest.approx([.75,.25])
            return ['project_0']
    class Model:
        events=[]
        def log(self,event,**values): self.events.append((event,values))
        async def ask(self,state,questions):
            return {'investment':{'choice':'save','probabilities':{'save':.75,'project_0':.25,'invalid':100}}}
    model=Model()
    commands=asyncio.run(choose_investment(view,{},model,{'investment_rng':Rng()}))
    assert commands==[{'unit_tag':1,'ability_id':1}]
    sample=next(v for e,v in model.events if e=='investment_sample')
    assert sample['sampling_probabilities']==pytest.approx({'save':.75,'project_0':.25})
    assert sample['probabilities']=={'save':.75,'project_0':.25}


def test_order_menu_tournament_exposes_every_option_and_uses_only_jev_finalists():
    from player import ask_order_menus
    questions={'squad':{'type':'choice','instructions':'Choose a legal order',
        'criteria':{str(i):str(i)+'x'*5000 for i in range(8)}}}
    class Model:
        requests=[]
        def log(self,*a,**kw):pass
        async def ask(self,state,qs):
            assert state=={'fact':'visible'}
            self.requests.append(qs)
            return {k:{'choice':max(q['criteria'],key=int)} for k,q in qs.items()}
    model=Model()
    answer=asyncio.run(ask_order_menus({'fact':'visible'},questions,model,full_first=False))
    assert answer['squad']['choice']=='7'
    assert {k for request in model.requests for k in request['squad']['criteria']}==set(map(str,range(8)))
    assert set(model.requests[-1]['squad']['criteria'])=={'3','7'}
    assert len(questions['squad']['criteria'])==8
    assert all(len(q['squad']['criteria'])<=2 for q in model.requests)


def test_large_order_menu_uses_one_full_request_and_only_size_errors_fallback(monkeypatch):
    import player
    class Rejected(Exception): pass
    monkeypatch.setattr(player,'BadRequestResponseError',Rejected)
    questions={'squad':{'type':'choice','instructions':'Choose',
        'criteria':{str(i):'x'*5000 for i in range(8)}}}
    class Model:
        def __init__(self,error=None): self.requests=[];self.error=error;self.events=[]
        def log(self,event,**kw): self.events.append(event)
        async def ask(self,state,qs):
            self.requests.append(qs)
            if self.error and len(self.requests)==1: raise Rejected(self.error)
            return {k:{'choice':max(q['criteria'],key=int)} for k,q in qs.items()}
    model=Model()
    assert asyncio.run(player.ask_order_menus({},questions,model))['squad']['choice']=='7'
    assert model.requests==[questions]
    model=Model('max_tokens_exceeded')
    assert asyncio.run(player.ask_order_menus({},questions,model))['squad']['choice']=='7'
    assert model.events.count('order_menu_size_fallback')==1
    assert set(model.requests[-1]['squad']['criteria'])=={'3','7'}
    assert len(model.requests)==8  # One rejected full menu, then seven bounded tree requests.
    model=Model('invalid_schema')
    with pytest.raises(Rejected,match='invalid_schema'):
        asyncio.run(player.ask_order_menus({},questions,model))
    assert len(model.requests)==1


def test_depot_state_controls_require_current_engine_offer_and_no_target():
    from jev_sc2.view import support_candidates
    from s2clientprotocol import data_pb2
    unit=raw.Unit(tag=7)
    catalog={a:data_pb2.AbilityData(ability_id=a,target=1) for a in (556,558)}
    assert support_candidates(unit,set(),catalog,{},[],{})==[]
    for ability in (556,558):
        offered=support_candidates(unit,{ability},catalog,{},[],{})
        assert len(offered)==1
        assert offered[0]['command']=={'unit_tag':7,'ability_id':ability}
    catalog[556].target=2
    assert support_candidates(unit,{556},catalog,{},[],{})==[]


def test_individual_worker_grouping_uses_observed_capabilities_and_preserves_other_groups():
    from player import control_groups
    units=[{'tag':i,'type':'Worker','candidates':[{'id':'gather_10'}],
            'orders':[{'ability':'Repair','target_tag':99}]} for i in (1,2)]
    units += [{'tag':i,'type':'Soldier','candidates':[]} for i in (3,4)]
    groups=control_groups(units,'individual_workers',{})
    assert [u['tag'] for u in groups['Worker / unit 1']]==[1]
    assert [u['tag'] for u in groups['Worker / unit 2']]==[2]
    assert [u['tag'] for u in groups['Soldier']]==[3,4]
    assert len(control_groups(units,'by_type',{}))==3
    assert len(control_groups(units,'by_current_order',{}))==3


def test_investment_preserves_jev_relative_odds_and_family_mass():
    from player import investment_sampling_probabilities
    p = investment_sampling_probabilities({'save':.4,'save_for_0':.1,
                                         'project_0':.3,'batch_1':.2})
    assert sum(p.values()) == pytest.approx(1)
    assert p['save']+p['save_for_0'] == pytest.approx(.5)
    assert p['project_0']+p['batch_1'] == pytest.approx(.5)
    assert p['project_0']/p['batch_1'] == pytest.approx(1.5)
    assert p['save']/p['save_for_0'] == pytest.approx(4)
    assert investment_sampling_probabilities({'save':1e300}) == {'save':1}
    assert investment_sampling_probabilities({'project_0':1e-300}) == {'project_0':1}

    assert investment_sampling_probabilities({'save':1e300,'project_0':1e-300}) == {'save':1,'project_0':0}


def test_shared_attack_move_description_compacts_distances_without_changing_orders():
    import player
    units = [{'tag':tag, 'type':'Unit', 'position':[x,0], 'candidates':[
        {'id':'attack_move_join_99',
         'description':f'Attack-move to friendly Tower tag 99 observed position, engaging enemies encountered; distance {10-x:.1f}',
         'command':{'unit_tag':tag,'ability_id':23,'point':[10,0]}}]}
        for tag,x in [(1,0),(2,4)]]
    class Model:
        def log(self,*args,**kwargs): pass
        async def ask(self,state,questions):
            if 'strategy' in questions: return {'strategy':{'choice':'assemble'}}
            if 'purpose_Unit' in questions: return {'purpose_Unit':{'choice':'combat'}}
            description=questions['Unit']['criteria']['group_attack_move_join_99']
            assert description.count('Attack-move to friendly Tower')==1
            assert 'engaging enemies encountered' in description
            assert 'travel distances across selection: 6.0 to 10.0' in description
            return {'Unit':{'choice':'group_attack_move_join_99'}}
    commands=asyncio.run(player.decide({'loop':1,'self':units},Model(),{}))
    assert commands==[u['candidates'][0]['command'] for u in units]


def test_friendly_destination_facts_use_only_current_visible_local_enemies():
    from jev_sc2.view import friendly_destination_facts
    anchor=raw.Unit(tag=1,alliance=raw.Self,health=75,health_max=100)
    anchor.pos.x=10;anchor.pos.y=10
    entities=[]
    for tag,alliance,display,x in [(2,raw.Enemy,raw.Visible,22),
                                  (3,raw.Enemy,raw.Visible,23),
                                  (4,raw.Enemy,raw.Hidden,10),
                                  (5,raw.Enemy,raw.Snapshot,10),
                                  (6,raw.Ally,raw.Visible,10)]:
        e=raw.Unit(tag=tag,unit_type=999,alliance=alliance,display_type=display)
        e.pos.x=x;e.pos.y=10;entities.append(e)
    assert friendly_destination_facts(anchor,entities,{999:'ExampleEnemy'}) == (
        'anchor health 75/100; visible enemies within 12 of anchor: 1 ExampleEnemy')
    assert friendly_destination_facts(anchor,entities[1:],{}).endswith('none observed')


def test_purchase_description_exposes_observed_cargo_without_assigning_passengers():
    from player import investment_description
    state = {'type_selection_facts': {'Carrier': {
        'cargo_slots_used': 2, 'cargo_slots_available': 6,
        'passengers_by_type': {'Passenger': 2}}}}
    description = investment_description('Carrier', {}, state)
    assert '2 slots occupied, 6 available' in description
    assert "'Passenger': 2" in description
    assert 'loading is a separate decision' in description
    assert 'cargo:' not in investment_description('Unknown', {}, state)


@pytest.mark.parametrize('target', [1, 5])
def test_untargeted_build_requires_executable_ability_and_known_product(target):
    from s2clientprotocol import query_pb2 as query
    from player import is_purchase
    class Client:
        async def request(self, name, body):
            result = query.ResponseQuery()
            offered = result.abilities.add(unit_tag=1)
            for ability in (901, 902):
                offered.abilities.add(ability_id=ability)
            if body.ignore_resource_requirements:
                offered.abilities.add(ability_id=903)
            return result
    obs = sc.ResponseObservation()
    obs.observation.raw_data.units.add(tag=1, unit_type=21, alliance=raw.Self)
    data = sc.ResponseData()
    for ability, label in ((901, 'Build KnownAddon'), (902, 'Build UnknownAddon'), (903, 'Build UnaffordableAddon')):
        data.abilities.add(ability_id=ability, friendly_name=label, target=target)
    data.units.add(unit_id=9001, name='KnownAddon', ability_id=901, mineral_cost=50, vespene_cost=25)
    data.units.add(unit_id=9003, name='UnaffordableAddon', ability_id=903, mineral_cost=100)
    view = asyncio.run(make_view(Client(), obs, data, sc.ResponseGameInfo(), 'test'))
    candidates = view['self'][0]['candidates']
    assert len(candidates) == 1
    assert candidates[0]['command'] == {'unit_tag': 1, 'ability_id': 901}
    assert candidates[0]['resource_cost']['vespene'] == 25
    assert is_purchase(candidates[0])
    assert any(p['type'] == 'UnaffordableAddon' for p in view['potential_projects'])

    assert view['unrepresented_controls'] == {'21': {'902': {'name': 'Build UnknownAddon', 'target': target}}}


def test_return_resources_is_offered_only_to_engine_advertised_worker():
    from s2clientprotocol import query_pb2 as query
    class Client:
        async def request(self, name, body):
            result = query.ResponseQuery()
            result.abilities.add(unit_tag=1).abilities.add(ability_id=296)
            result.abilities.add(unit_tag=2)
            return result
    obs = sc.ResponseObservation()
    for tag in (1, 2):
        obs.observation.raw_data.units.add(tag=tag, unit_type=45, alliance=raw.Self)
    data = sc.ResponseData()
    data.abilities.add(ability_id=296, friendly_name='Harvest Return SCV', target=1)
    view = asyncio.run(make_view(Client(), obs, data, sc.ResponseGameInfo(), 'test'))
    assert view['self'][0]['candidates'][0]['command'] == {'unit_tag': 1, 'ability_id': 296}
    assert view['self'][0]['candidates'][0]['id'].startswith('gather_')
    assert view['self'][1]['candidates'] == []
    assert not view['unrepresented_controls']


def test_catalog_dependencies_use_available_units_and_explicit_tech_aliases():
    from jev_sc2.view import catalog_dependencies
    from player import investment_description
    data = sc.ResponseData()
    product = data.units.add(unit_id=100, name='Addon')
    product.tech_alias.append(101)
    data.units.add(unit_id=1, name='Direct', available=True, tech_requirement=100)
    data.units.add(unit_id=2, name='Aliased', available=True, tech_requirement=101, require_attached=True)
    data.units.add(unit_id=3, name='Unavailable', available=False, tech_requirement=100)
    data.units.add(unit_id=4, name='Unrelated', available=True, tech_requirement=102)
    deps = catalog_dependencies(product, data.units)
    assert deps == [{'unit':'Direct', 'requires_attached':False}, {'unit':'Aliased', 'requires_attached':True}]
    description = investment_description('Addon', {'catalog_tech_requirement_for':deps}, {})
    assert 'Aliased (requires attached addon)' in description
    assert 'does not guarantee current trainability' in description


def test_individual_history_survives_paced_reviews_but_expires_and_rewinds():
    import json
    import player

    class Model:
        facts = []

        def log(self, *args, **kwargs):
            pass

        async def ask(self, state, questions):
            if 'navigation' in questions:
                return {'navigation': {'choice': 'hold'}}
            self.facts.append(json.loads(questions['1']['instructions'].split('Unit facts: ', 1)[1]))
            return {'1': {'choice': 'continue'}}

    model, memory = Model(), {}
    unit = {'tag': 1, 'type': 'SCV', 'position': [1, 2],
            'health_fraction': 1, 'surroundings': [], 'candidates': []}
    for loop in (5, 305, 1000, 2):
        view = {'loop': loop, 'objective': 'Complete the mission',
                'resources': {}, 'self': [unit]}
        assert asyncio.run(player.decide_individual(view, model, memory)) == []
    assert 'recent_progress' not in model.facts[0]
    assert model.facts[1]['recent_progress']['game_loops'] == 300
    assert model.facts[1]['recent_progress']['last_choices'] == ['continue']
    assert 'recent_progress' not in model.facts[2]
    assert 'recent_progress' not in model.facts[3]


def test_jev_strategy_horizon_retains_priority_without_stopping_orders():
    import player

    class Model:
        strategy_calls = 0
        order_calls = 0

        def log(self, *args, **kwargs):
            pass

        async def ask(self, state, questions):
            if 'strategy' in questions:
                self.strategy_calls += 1
                return {'strategy': {'choice': 'protect'},
                        'strategy_review': {'choice': 'long'}}
            if 'purpose_Marine' in questions:
                return {'purpose_Marine': {'choice': 'positioning'}}
            self.order_calls += 1
            return {'Marine': {'choice': 'group_north'}}

    model, memory = Model(), {}
    command = {'unit_tag': 1, 'ability_id': 16, 'point': [1, 6]}
    unit = {'tag': 1, 'type': 'Marine', 'position': [1, 0],
            'candidates': [{'id': 'north', 'description': 'Move north', 'command': command}]}
    for loop, expected_reviews in ((1, 1), (500, 1), (2017, 2), (1, 3)):
        assert asyncio.run(player.decide({'self': [unit], 'loop': loop}, model, memory)) == [command]
        assert model.strategy_calls == expected_reviews
    assert model.order_calls == 4


def test_delayed_engine_failures_reach_player_without_invented_request_attribution():
    from jev_sc2.__main__ import observe_action_failures, action_feedback
    from s2clientprotocol import error_pb2
    import player
    memory = {}
    logged = []
    obs = sc.ResponseObservation()
    obs.observation.game_loop = 100
    obs.action_errors.add(unit_tag=7, ability_id=338, result=error_pb2.NotSupported)
    observe_action_failures(obs,memory,lambda event,**fields:logged.append((event,fields)))
    observe_action_failures(obs,memory,lambda event,**fields:logged.append((event,fields)))
    assert len(logged) == 1
    memory['action_feedback'] = [action_feedback([],[],100,0,0,128)]
    view = {'loop':110,'self':[{'tag':7,'type':'SCV','candidates':[]}]}
    feedback = player.describe_action_feedback(view,memory)
    assert len(feedback) == 1
    failure = feedback[0]['failures'][0]
    assert failure['result'] == 'NotSupported' and failure['ability_id'] == 338
    assert failure['unit_types'] == {'SCV':1}
    assert 'Unknown observed ability' in failure['action']
    assert 'not the original request loop' in feedback[0]['note']
    memory['action_feedback'] = []
    view['loop'] = 800
    assert player.describe_action_feedback(view,memory) == []
    view['loop'] = 5
    assert player.describe_action_feedback(view,memory) == []
    rewind = sc.ResponseObservation()
    rewind.observation.game_loop = 5
    observe_action_failures(rewind,memory,lambda *a,**k:None)
    assert memory['engine_action_feedback'] == []


def test_contribution_commitment_survives_paced_review_but_not_expiry_or_strategy_change():
    import player
    class Model:
        calls = 0
        def log(self,*a,**k): pass
        async def ask(self,state,questions):
            self.calls += 1
            return {'purpose_Test':{'choice':'income','probabilities':{'income':1}}}
    model = Model(); memory = {}
    q = {'purpose_Test':{'instructions':'Choose role','criteria':{'income':'Gather'}}}
    state = {'strategy_chosen_by_jev':{'choice':'protect'}}
    for loop in (1,488):
        asyncio.run(player.choose_contributions({'loop':loop},state,q,model,memory))
    assert model.calls == 1
    asyncio.run(player.choose_contributions({'loop':673},state,q,model,memory))
    assert model.calls == 2
    state['strategy_chosen_by_jev']['choice'] = 'recover'
    asyncio.run(player.choose_contributions({'loop':700},state,q,model,memory))
    assert model.calls == 3
    asyncio.run(player.choose_contributions({'loop':2},state,q,model,memory))
    assert model.calls == 4
    # A hot reload must not retroactively extend an earlier, shorter commitment.
    memory['contribution_plans']['purpose_Test'].update(loop=2,review_at=226)
    asyncio.run(player.choose_contributions({'loop':300},state,q,model,memory))
    assert model.calls == 5


def test_feedback_does_not_attribute_failure_to_last_candidate_target():
    import player
    memory={'observed_ability_labels':{324:'Build Bunker at [99,99]'},
            'engine_action_feedback':[{'loop':10,'failures':[
                {'ability_id':324,'unit_tags':[1],'result':'BuildTechRequirementsNotMet'}]}]}
    view={'loop':10,'self':[{'tag':1,'type':'SCV','candidates':[
        {'command':{'ability_id':324,'point':[2,3]},'description':'Build Bunker at [2,3]',
         'project':{'type':'Bunker'}}]}]}
    failure=player.describe_action_feedback(view,memory)[0]['failures'][0]
    assert failure['action']=='Purchase Bunker'
    view['self'][0]['candidates']=[]
    memory['engine_action_feedback']=[]
    view['loop']=20
    assert player.describe_action_feedback(view,memory)[0]['failures'][0]['action']=='Purchase Bunker'
    # Retained pre-reload failures must not retain an invented location either.
    memory['retained_action_failures'][10]['failures'][0]['action']='Build Bunker at [99,99]'
    assert player.describe_action_feedback(view,memory)[0]['failures'][0]['action']=='Purchase Bunker'


def test_restart_keeps_client_and_checks_identity_clock_and_hard_reset():
    from jev_sc2.__main__ import restart_attached_game
    class Client:
        status=sc.in_game
        def __init__(self,name='mission.SC2Map',hard=False,after=0):
            self.name=name;self.hard=hard;self.after=after;self.requests=[];self.observations=0
        async def request(self,name,body):
            self.requests.append(name)
            if name=='game_info':return sc.ResponseGameInfo(local_map_path=self.name)
            assert name=='restart_game'
            return sc.ResponseRestartGame(need_hard_reset=self.hard)
        async def observe(self):
            self.observations+=1
            result=sc.ResponseObservation()
            result.observation.game_loop=100 if self.observations==1 else self.after
            return result
    c=Client();events=[]
    assert asyncio.run(restart_attached_game(c,'mission.SC2Map',lambda e,**f:events.append((e,f))))>0
    assert c.requests==['game_info','restart_game'] and c.observations==2
    assert events[0][1]['after_loop']==0
    c=Client(name='wrong.SC2Map')
    with pytest.raises(RuntimeError,match='mismatch'):
        asyncio.run(restart_attached_game(c,'mission.SC2Map',lambda *a,**k:None))
    assert c.requests==['game_info'] and c.observations==0
    c=Client(hard=True)
    with pytest.raises(RuntimeError,match='hard reset'):
        asyncio.run(restart_attached_game(c,'mission.SC2Map',lambda *a,**k:None))
    assert c.observations==1
    with pytest.raises(RuntimeError,match='clock'):
        asyncio.run(restart_attached_game(Client(after=101),'mission.SC2Map',lambda *a,**k:None))


@pytest.mark.parametrize('attach,map_path,expected',[(False,None,'m.SC2Map'),(True,'m.SC2Map','m.SC2Map'),(True,None,None)])
def test_restart_rejects_ambiguous_setup_before_connecting(attach,map_path,expected):
    from types import SimpleNamespace
    from jev_sc2.__main__ import run
    with pytest.raises(ValueError,match='requires --attach'):
        asyncio.run(run(SimpleNamespace(restart=True,attach=attach,map=map_path,expected_map=expected)))


def test_unseen_engine_failure_survives_long_budget_pacing_gap():
    from jev_sc2.__main__ import observe_action_failures
    from s2clientprotocol import error_pb2
    import player
    memory = {}
    obs = sc.ResponseObservation()
    obs.observation.game_loop = 100
    obs.action_errors.add(unit_tag=7, ability_id=558, result=error_pb2.CantBuildLocationInvalid)
    observe_action_failures(obs,memory,lambda *a,**k:None)
    fresh = sc.ResponseObservation()
    fresh.observation.game_loop = 1100
    observe_action_failures(fresh,memory,lambda *a,**k:None)
    view = {'loop':1100,'self':[]}
    feedback = player.describe_action_feedback(view,memory)
    assert feedback[0]['loop'] == 100
    assert feedback[0]['surfaced_loop'] == 1100
    assert feedback[0]['failures'][0]['result'] == 'CantBuildLocationInvalid'
    view['loop'] = 1773
    assert player.describe_action_feedback(view,memory) == []
    fresh.observation.game_loop = 1773
    observe_action_failures(fresh,memory,lambda *a,**k:None)
    assert memory['engine_action_feedback'] == []


def test_jev_selected_role_duration_applies_only_to_new_commitments():
    import player
    class Model:
        calls = 0
        def log(self,*a,**k): pass
        async def ask(self,state,questions):
            self.calls += 1
            return {'purpose_Test':{'choice':'income','probabilities':{'income':1}}}
    model=Model(); memory={'contribution_review_loops':2016}
    q={'purpose_Test':{'instructions':'Choose role','criteria':{'income':'Gather'}}}
    state={'strategy_chosen_by_jev':{'choice':'protect'}}
    asyncio.run(player.choose_contributions({'loop':1},state,q,model,memory))
    assert memory['contribution_plans']['purpose_Test']['review_at']==2017
    memory['contribution_review_loops']=112
    asyncio.run(player.choose_contributions({'loop':1000},state,q,model,memory))
    assert model.calls==1
    asyncio.run(player.choose_contributions({'loop':2017},state,q,model,memory))
    assert model.calls==2
    assert memory['contribution_plans']['purpose_Test']['review_at']==2129


def test_scored_investments_keep_every_option_and_choose_jev_rating():
    import player
    class Model:
        def log(self,*a,**k): pass
        async def ask(self,state,questions):
            assert set(questions)=={'save','project_0','batch_0'}
            assert all(q['type']=='score' for q in questions.values())
            return {k:{'score':v} for k,v in {'save':1.5,'project_0':2.1,'batch_0':2.8}.items()}
    choice=asyncio.run(player.score_investment_options({},
        {'save':'Wait','project_0':'Purchase fictional unit','batch_0':'Train three'},Model(),{},5))
    assert choice=='batch_0'


@pytest.mark.parametrize('bad',[None,float('nan'),float('inf'),-1,5,True])
def test_scored_investment_rejects_invalid_ratings(bad):
    import player
    class Model:
        def log(self,*a,**k): pass
        async def ask(self,state,questions):return {'save':{'score':bad}}
    with pytest.raises(ValueError,match='investment scores'):
        asyncio.run(player.score_investment_options({}, {'save':'Wait'},Model(),{},1))
