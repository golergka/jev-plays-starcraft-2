import asyncio
import json

from jev_sc2.__main__ import result_for_player
from jev_sc2.campaign import run_sequence


def test_only_our_player_result_counts():
    results=[{'player':1,'result':'Defeat'},{'player':2,'result':'Victory'}]
    assert result_for_player(results,1)=='defeat'
    assert result_for_player(results,2)=='victory'
    assert result_for_player(results,None)=='incomplete'
    assert result_for_player([],1)=='incomplete'


def manifest(tmp_path):
    missions=[]
    for name,race in [('first','terran'),('second','zerg')]:
        (tmp_path/f'{name}.SC2Map').write_bytes(b'test map')
        missions.append({'id':name,'map':f'{name}.SC2Map','race':race,'objective':'Complete the mission'})
    path=tmp_path/'manifest.json'
    path.write_text(json.dumps({'missions':missions}))
    return path


def test_sequence_retries_defeat_advances_only_on_victory_and_preserves_budget(tmp_path):
    calls=[]
    results=iter(['defeat','victory','victory'])
    async def mission(args):
        calls.append(args)
        return {'status':next(results),'calls':10,'run':'test'}
    progress=asyncio.run(run_sequence(manifest(tmp_path),tmp_path/'progress.json',
                                    call_budget=40,mission_runner=mission))
    assert progress['completed']==['first','second']
    assert progress['status']=='sequence_complete'
    assert [x.race for x in calls]==['terran','terran','zerg']
    assert [x.max_calls for x in calls]==[40,30,20]
    assert calls[0].map==calls[1].map and calls[1].map!=calls[2].map


def test_unknown_outcome_does_not_restart_or_advance(tmp_path):
    calls=[]
    async def mission(args):
        calls.append(args)
        return {'status':'incomplete','calls':10,'reason':'clock stalled'}
    progress=asyncio.run(run_sequence(manifest(tmp_path),tmp_path/'progress.json',mission_runner=mission))
    assert progress['completed']==[]
    assert progress['status']=='needs_attention'
    assert len(calls)==1


def test_sequence_resume_does_not_replay_verified_completed_mission(tmp_path):
    path=manifest(tmp_path);state=tmp_path/'progress.json'
    async def win(args): return {'status':'victory','calls':10}
    first=asyncio.run(run_sequence(path,state,call_budget=10,mission_runner=win))
    assert first['completed']==['first']
    calls=[]
    async def second(args):
        calls.append(args.map)
        return {'status':'victory','calls':1}
    final=asyncio.run(run_sequence(path,state,call_budget=10,mission_runner=second))
    assert final['status']=='sequence_complete'
    assert calls==[str(tmp_path/'second.SC2Map')]


def test_extending_manifest_preserves_completed_prefix(tmp_path):
    path=manifest(tmp_path);state=tmp_path/'progress.json'
    async def win(args): return {'status':'victory','calls':1}
    asyncio.run(run_sequence(path,state,mission_runner=win))
    data=json.loads(path.read_text())
    (tmp_path/'third.SC2Map').write_bytes(b'test map')
    data['missions'].append({'id':'third','map':'third.SC2Map','race':'protoss','objective':'Complete mission'})
    path.write_text(json.dumps(data))
    calls=[]
    async def third(args):
        calls.append(args.map)
        return {'status':'victory','calls':1}
    result=asyncio.run(run_sequence(path,state,mission_runner=third))
    assert result['completed']==['first','second','third']
    assert calls==[str(tmp_path/'third.SC2Map')]


def test_resume_current_preserves_map_and_does_not_consume_new_attempt(tmp_path):
    path=manifest(tmp_path);state=tmp_path/'progress.json'
    async def initial(args):
        return {'status':'victory' if args.map.endswith('first.SC2Map') else 'incomplete','calls':1}
    asyncio.run(run_sequence(path,state,max_attempts=1,mission_runner=initial))
    calls=[]
    async def resume(args):
        calls.append(args)
        return {'status':'victory','calls':1}
    progress=asyncio.run(run_sequence(path,state,max_attempts=1,resume_current=True,mission_runner=resume))
    assert progress['status']=='sequence_complete'
    assert len(calls)==1 and calls[0].map is None
    assert calls[0].expected_map=='second.SC2Map'
    assert progress['attempts'][-1]['resumed'] is True


def test_resume_map_identity_rejects_other_or_unknown_map():
    import pytest
    from types import SimpleNamespace
    from jev_sc2.__main__ import check_map_identity
    check_map_identity(SimpleNamespace(local_map_path='Maps/second.SC2Map'),'second.SC2Map')
    for actual in ('Maps/first.SC2Map',''):
        with pytest.raises(RuntimeError,match='map mismatch'):
            check_map_identity(SimpleNamespace(local_map_path=actual),'second.SC2Map')


def test_opt_in_stall_recovery_is_bounded_and_preserves_completed_missions(tmp_path):
    path=manifest(tmp_path);calls=[]
    async def mission(args):
        calls.append(args)
        if args.map.endswith('first.SC2Map'): return {'status':'victory','calls':1}
        return {'status':'incomplete','calls':2,'reason':'Game clock stalled for ten seconds; inspect pause/tutorial UI'}
    result=asyncio.run(run_sequence(path,tmp_path/'progress.json',call_budget=20,
        max_attempts=2,retry_stalls=True,mission_runner=mission))
    assert result['completed']==['first'] and result['status']=='needs_attention'
    assert len(calls)==3 and calls[1].map==calls[2].map
    assert [c.max_calls for c in calls]==[20,19,17]
    assert all(a['status']=='incomplete' and a['recovery']=='restart_same_mission_after_clock_stall' for a in result['attempts'][1:])


def test_stall_recovery_does_not_restart_budget_or_unknown_failures(tmp_path):
    calls=[]
    async def mission(args):
        calls.append(args)
        return {'status':'incomplete','calls':1,'reason':'Jev call budget reached'}
    result=asyncio.run(run_sequence(manifest(tmp_path),tmp_path/'progress.json',
        retry_stalls=True,mission_runner=mission))
    assert len(calls)==1 and result['completed']==[]


def test_campaign_passes_configured_decision_age_to_runner(tmp_path):
    seen=[]
    async def mission(args):
        seen.append(args.max_age_loops)
        return {'status':'incomplete','calls':0,'run':'test'}
    asyncio.run(run_sequence(manifest(tmp_path),tmp_path/'age.json',
        max_age_loops=64,mission_runner=mission))
    assert seen==[64]


def test_replay_failure_does_not_erase_terminal_run_result(tmp_path, monkeypatch):
    from types import SimpleNamespace
    import jev_sc2.__main__ as runner
    from s2clientprotocol import sc2api_pb2 as sc
    class Client:
        status = sc.ended
        async def request(self, name, body):
            if name == 'ping':return SimpleNamespace(game_version='test')
            if name == 'save_replay':raise RuntimeError('Not currently recording a replay')
            raise AssertionError(name)
        async def observe(self):
            o=sc.ResponseObservation()
            o.observation.player_common.player_id=1
            o.player_result.add(player_id=1,result=sc.Defeat)
            return o
        async def close(self):pass
    client=Client();client.ws=client
    async def connect(*args,**kwargs):return client
    monkeypatch.setattr(runner,'ROOT',tmp_path)
    monkeypatch.setattr(runner.SC2,'connect',connect)
    monkeypatch.setattr(runner,'PlayerLoader',lambda root:SimpleNamespace(refresh=lambda:None,revision='test'))
    monkeypatch.setattr(runner,'Jev',lambda *args,**kwargs:SimpleNamespace(calls=0,cost=0))
    args=SimpleNamespace(doctor=False,attach=True,map=None,port=5001,objective='test',
                         seconds=30,max_calls=10,max_age_loops=32)
    result=asyncio.run(runner.run(args))
    assert result['status']=='defeat'
    assert result['replay'] is None
    assert 'Not currently recording' in result['replay_error']
    assert json.loads(next((tmp_path/'runs').glob('*/result.json')).read_text())==result


def test_unanimous_campaign_objective_results_do_not_verify_completion():
    for result in ['Victory','Defeat']:
        assert result_for_player([{'player':1,'result':result},
                                  {'player':2,'result':result}],1)=='incomplete'


def test_checkpoint_under_verification_review_cannot_advance(tmp_path):
    import pytest
    path=manifest(tmp_path);state=tmp_path/'progress.json'
    state.write_text(json.dumps({'completed':[],'attempts':[],
                                'verification_review_required':['first']}))
    async def should_not_run(args):raise AssertionError('must not launch a map')
    with pytest.raises(ValueError,match='independent verification'):
        asyncio.run(run_sequence(path,state,mission_runner=should_not_run))
