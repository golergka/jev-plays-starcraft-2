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


def test_early_review_borrows_half_interval_and_repays_before_reborrowing():
    from jev_sc2.review_events import early_review_allowed, next_review_deadline
    event=[{'damaged_tags':[1],'new_nearby_enemy_tags':[],'disappeared_tags':[]}]
    assert not early_review_allowed(4,10,10,0,event)
    assert early_review_allowed(5,10,10,0,event)
    repayment=next_review_deadline(5,8,10,True)
    assert repayment==18  # Saved five seconds are added back, not forgotten.
    assert not early_review_allowed(14,18,8,repayment,event)
    assert not early_review_allowed(18,18,8,repayment,event)
    assert next_review_deadline(18,8,18,False)==26
    assert early_review_allowed(22,26,8,repayment,event)


def test_ordinary_schedule_and_non_triggering_events_remain_unchanged():
    from jev_sc2.review_events import early_review_allowed, next_review_deadline
    assert next_review_deadline(12,8,10,False)==20
    assert not early_review_allowed(8,10,10,0,[])
    assert not early_review_allowed(8,10,10,0,[{'damaged_tags':[], 'new_nearby_enemy_tags':[], 'disappeared_tags':[1]}])


def test_nearby_enemy_alone_does_not_spend_early_review_allowance():
    from jev_sc2.review_events import early_review_allowed
    arrivals=[{'damaged_tags':[], 'new_nearby_enemy_tags':[4], 'disappeared_tags':[]}]
    assert not early_review_allowed(8,10,10,0,arrivals)
    arrivals.append({'damaged_tags':[1], 'new_nearby_enemy_tags':[], 'disappeared_tags':[]})
    assert early_review_allowed(8,10,10,0,arrivals)
