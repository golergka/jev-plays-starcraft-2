import json
from jev_sc2.episodes import previous_attempts


def write_attempt(root, name, *, status='defeat', verified=True, map_name='mission.SC2Map', joined=True, first=3):
    directory=root/name;directory.mkdir()
    (directory/'result.json').write_text(json.dumps({'status':status,'local_map_path':map_name,
        'ui_verification':{'result':status} if verified else {}}))
    rows=([{'event':'joined_game'}] if joined else [])+[
        {'event':'tick','loop':first,'units':[{'type':'Unit'},{'type':'Unit'}]},
        {'event':'strategy_choice','choice':'recover'},
        {'event':'contribution_commitment','sampled_choice':'income'},
        {'event':'investment_choice','choice':'project_0','projects':['Unit']},
        {'event':'jev','state':{'resources':{'minerals':123,'food_cap':9},
                              'visible_entities':[{'secret_test_marker':'never copied'}]}},
        {'event':'investment_choice','choice':'save','projects':['Unit']},
        {'event':'investment_choice','choice':'save_for_0','projects':[]},
        {'event':'jev','state':{'resources':{'minerals':7,'food_cap':9}}},
        {'event':'decision_error'},
        {'event':'tick','loop':1000,'units':[{'type':'Unit'}]}]
    (directory/'events.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows))
    return directory


def test_history_filters_unverified_other_maps_and_partial_segments(tmp_path):
    write_attempt(tmp_path,'01')
    write_attempt(tmp_path,'02',verified=False)
    write_attempt(tmp_path,'03',map_name='different.SC2Map')
    write_attempt(tmp_path,'04',joined=False)
    write_attempt(tmp_path,'05',first=900)
    write_attempt(tmp_path,'06',status='incomplete')
    output=previous_attempts(tmp_path,'maps/mission.SC2Map')
    assert len(output['attempts'])==1
    a=output['attempts'][0]
    assert a['peak_observed_owned_counts']=={'Unit':2}
    assert a['purchase_proposal_counts']=={'Unit':1}
    assert a['contribution_choice_counts']=={'income':1}
    assert a['last_observed_resources']=={'minerals':7,'food_cap':9}
    assert a['peak_observed_minerals']==123
    assert a['investment_choice_counts']=={'purchase':1,'save':1,'save_for_project':1}
    assert a['decision_errors']==1
    assert 'secret_test_marker' not in json.dumps(output)


def test_history_is_bounded_newest_first_and_excludes_current_run(tmp_path):
    write_attempt(tmp_path,'01')
    write_attempt(tmp_path,'02',status='victory')
    current=write_attempt(tmp_path,'03')
    result=previous_attempts(tmp_path,'mission.SC2Map',exclude=current,limit=1)
    assert [a['result'] for a in result['attempts']]==['victory']


def test_history_distinguishes_background_attempts_from_accepted_commands(tmp_path):
    directory=write_attempt(tmp_path,'01')
    rows=[{'event':'production_job_armed','job':{'target_project':'Unit'}},
          {'event':'production_job_request'},
          {'event':'production_job_execution','results':[1]},
          {'event':'production_job_request'},
          {'event':'production_job_execution','results':[9]},
          {'event':'production_job_released'},
          {'event':'production_job_request'}]
    with (directory/'events.jsonl').open('a') as stream:
        for row in rows:stream.write(json.dumps(row)+'\n')
    attempt=previous_attempts(tmp_path,'mission.SC2Map')['attempts'][0]
    assert attempt['purchase_proposal_counts']=={'Unit':1}
    assert attempt['background_training_attempt_counts']=={'Unit':2}
    assert attempt['background_training_accepted_counts']=={'Unit':1}


def add_restart(directory, **overrides):
    path=directory/'events.jsonl'
    event={'event':'restarted_game','map':'mission.SC2Map','before_loop':12000,'after_loop':0,**overrides}
    path.write_text(json.dumps(event)+'\n'+path.read_text())


def test_verified_restart_is_a_fresh_episode(tmp_path):
    directory=write_attempt(tmp_path,'01',joined=False)
    add_restart(directory)
    assert len(previous_attempts(tmp_path,'mission.SC2Map')['attempts'])==1


def test_restart_still_requires_verified_result_and_early_observation(tmp_path):
    for name,kwargs in [('01',{'verified':False}),('02',{'first':900})]:
        directory=write_attempt(tmp_path,name,joined=False,**kwargs)
        add_restart(directory)
    assert not previous_attempts(tmp_path,'mission.SC2Map')['attempts']


def test_reject_wrong_map_nonrewind_and_invalid_restart_loops(tmp_path):
    for index,overrides in enumerate([
        {'map':'other.SC2Map'}, {'before_loop':0}, {'after_loop':1},
        {'before_loop':True}, {'after_loop':False}, {'before_loop':None},
    ]):
        directory=write_attempt(tmp_path,str(index),joined=False)
        add_restart(directory,**overrides)
    assert not previous_attempts(tmp_path,'mission.SC2Map')['attempts']


def test_reject_mixed_gameplay_before_restart(tmp_path):
    directory=write_attempt(tmp_path,'01')
    with (directory/'events.jsonl').open('a') as stream:
        stream.write(json.dumps({'event':'restarted_game','map':'mission.SC2Map','before_loop':12000,'after_loop':0})+'\n')
    assert not previous_attempts(tmp_path,'mission.SC2Map')['attempts']
