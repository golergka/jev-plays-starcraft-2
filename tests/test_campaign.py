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
