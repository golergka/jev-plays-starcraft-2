from jev_sc2.cadence import measured_cadence


def test_cadence_uses_only_completed_history_and_computes_ratios():
    result = measured_cadence([{'loop':100},{'loop':600},{'loop':1200}],1300)
    assert result['recent_completed_decision_gaps_game_loops'] == [500,600]
    assert result['median_gap_game_loops'] == 550
    assert result['review_intervals_relative_to_observed_median'] == {
        '112':0.2,'672':1.22,'2016':3.67}


def test_cadence_omits_insufficient_rewound_duplicate_or_future_history():
    for loops,current in [([1,2],3),([1,3,2],4),([1,1,2],3),([1,2,3],3),([1,2,3],2)]:
        assert measured_cadence([{'loop':n} for n in loops],current) is None


def test_cadence_bounds_history_to_six_samples():
    result = measured_cadence([{'loop':n} for n in [0,1000,1100,1200,1300,1400,1500,1600]],1700)
    assert result['recent_completed_decision_gaps_game_loops'] == [100]*5
