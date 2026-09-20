from player import recent_outcomes


def sample(loop, position, target=(10, 0), ability='Move'):
    return {'loop':loop, 'resources':{}, 'self':[{'tag':1, 'type':'Marine',
        'position':position, 'orders':[{'ability':ability, 'target_point':list(target)}]}]}


def test_distance_reduction_distinguishes_travel_away_from_target():
    memory={}
    recent_outcomes(sample(1,[0,0]),memory)
    result=recent_outcomes(sample(100,[0,5]),memory)
    row=result['unchanged_point_order_progress'][0]
    assert row['distance_reduction']==-1.2
    assert row['observed_loops']==99
    assert result['movement_by_type']['Marine']['mean_net_displacement']==5


def test_changed_target_or_ability_and_old_history_are_not_comparable():
    for second in (sample(100,[1,0],target=(20,0)),sample(100,[1,0],ability='Attack')):
        memory={}
        recent_outcomes(sample(1,[0,0]),memory)
        assert recent_outcomes(second,memory)['unchanged_point_order_progress']==[]
    memory={}
    recent_outcomes(sample(1,[0,0]),memory)
    memory['outcome_history'][0]['units']['1'].pop('orders')
    assert recent_outcomes(sample(100,[1,0]),memory)['unchanged_point_order_progress']==[]


def test_recent_matching_suffix_survives_earlier_different_order():
    memory={}
    recent_outcomes(sample(1,[0,0],target=(20,0)),memory)
    recent_outcomes(sample(100,[1,0]),memory)
    row=recent_outcomes(sample(200,[3,0]),memory)['unchanged_point_order_progress'][0]
    assert row['observed_loops']==100
    assert row['distance_reduction']==2


def test_missing_middle_observation_breaks_continuity():
    memory={}
    recent_outcomes(sample(1,[0,0]),memory)
    recent_outcomes({'loop':100,'self':[],'resources':{}},memory)
    assert recent_outcomes(sample(200,[3,0]),memory)['unchanged_point_order_progress']==[]
