from jev_sc2.review_events import ReviewEvents


def view(loop, health=45, enemies=(), present=True):
    return {'loop':loop,'self':[{'tag':1,'health':health,'position':[0,0]}] if present else [],
            'visible_entities':[{'tag':tag,'alliance':alliance,'position':[distance,0]} for tag,alliance,distance in enemies]}


def test_waiting_damage_and_visible_proximity_are_recorded_once():
    tracker=ReviewEvents()
    tracker.observe(view(1),False)
    changed=view(2,30,[(2,'Enemy',10),(3,'Neutral',1),(4,'Enemy',20)])
    tracker.observe(changed,True)
    tracker.observe({**changed,'loop':3},True)
    events=tracker.take(4)['events']
    assert events==[{'loop':2,'damaged_tags':[1],'disappeared_tags':[],'new_nearby_enemy_tags':[2]}]
    assert not tracker.pending


def test_disappearance_is_not_labeled_death_and_rewind_clears_pending():
    tracker=ReviewEvents();tracker.observe(view(10),False)
    tracker.observe(view(11,present=False),True)
    assert tracker.pending[0]['disappeared_tags']==[1]
    tracker.observe(view(0),True)
    assert not tracker.pending


def test_no_wait_does_not_add_events_and_history_is_bounded():
    tracker=ReviewEvents();tracker.observe(view(0,500),False)
    tracker.observe(view(1,499),False)
    assert not tracker.pending
    for n in range(2,150):tracker.observe(view(n,500-n),True)
    assert len(tracker.pending)==128
