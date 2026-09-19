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
    assert a['last_observed_resources']=={'minerals':123,'food_cap':9}
    assert a['decision_errors']==1
    assert 'secret_test_marker' not in json.dumps(output)


def test_history_is_bounded_newest_first_and_excludes_current_run(tmp_path):
    write_attempt(tmp_path,'01')
    write_attempt(tmp_path,'02',status='victory')
    current=write_attempt(tmp_path,'03')
    result=previous_attempts(tmp_path,'mission.SC2Map',exclude=current,limit=1)
    assert [a['result'] for a in result['attempts']]==['victory']
