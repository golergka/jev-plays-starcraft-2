from player import recent_outcomes


def view(loop,tags):
    return {'loop':loop,'resources':{},'self':[{'tag':t,'type':'Marine','position':[0,0]} for t in tags]}


def test_equal_size_replacement_has_distinct_observation_span():
    memory={}
    recent_outcomes(view(1,[1,2]),memory)
    rows=recent_outcomes(view(100,[1,3]),memory)['current_unit_observation_spans']
    by_tag={r['tag']:r for r in rows}
    assert by_tag['1']['observed_span_loops']==99
    assert by_tag['3']['observed_span_loops']==0
    assert by_tag['3']['observation_count']==1


def test_reappearance_does_not_bridge_missing_observation():
    memory={}
    recent_outcomes(view(1,[1]),memory)
    recent_outcomes(view(100,[]),memory)
    row=recent_outcomes(view(200,[1]),memory)['current_unit_observation_spans'][0]
    assert row['continuously_observed_since_loop']==200
    assert row['observed_span_loops']==0
