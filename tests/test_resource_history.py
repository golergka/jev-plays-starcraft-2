from player import recent_outcomes


def view(loop, counters):
    return {'loop':loop,'self':[],'resources':{},'player_score_telemetry':counters}


def test_own_collection_and_spending_are_separate_from_net_balance():
    memory={}
    recent_outcomes(view(1,{'collected_minerals':100,'spent_minerals':90,'killed_value_units':500}),memory)
    result=recent_outcomes(view(100,{'collected_minerals':200,'spent_minerals':190,'killed_value_units':900}),memory)
    assert result['resource_counter_changes']=={'collected_minerals':100,'spent_minerals':100}


def test_missing_reset_and_old_reload_history_do_not_invent_zero():
    memory={}
    recent_outcomes(view(1,{'spent_minerals':90}),memory)
    assert recent_outcomes(view(20,{'spent_minerals':5,'collected_minerals':10}),memory)['resource_counter_changes']=={}
    memory['outcome_history'][0].pop('resource_counters')
    assert recent_outcomes(view(30,{'spent_minerals':100}),memory)['resource_counter_changes']=={}
