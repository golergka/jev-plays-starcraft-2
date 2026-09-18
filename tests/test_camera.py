from jev_sc2.camera import choose_shot


def unit(tag, x, health=100):
    return {'tag':tag,'position':[x,10], 'health':health,
            'candidates':[{'id':'attack_move_north'}]}


def test_camera_frames_visible_engagement_instead_of_large_distant_base():
    view={'self':[unit(i,10) for i in range(30)]+[unit(100,80)],
          'visible_entities':[{'alliance':'Enemy','position':[85,10]}]}
    shot=choose_shot(view,{},now=0)
    assert shot['position'][0]>75
    assert shot['reason']=='visible engagement'
    assert set(shot)=={'position','reason'}  # no unit commands


def test_camera_holds_shot_but_cuts_to_new_damage_elsewhere():
    memory={}; view={'self':[unit(1,10),unit(2,80)]}
    assert choose_shot(view,memory,now=0)['position'][0]==10
    view['self'][1]['health']=90
    assert choose_shot(view,memory,now=1) is None
    view['self'][1]['health']=80
    assert choose_shot(view,memory,now=3)['position'][0]==80
    assert choose_shot(view,memory,now=4) is None


def test_camera_follows_movement_and_ignores_snapshot_enemy_locations():
    memory={}; view={'self':[unit(1,10),unit(2,80)],
                    'last_known_entities':[{'alliance':'Enemy','position':[10,10]}]}
    choose_shot(view,memory,now=0)
    view['self'][1]['position']=[85,10]
    shot=choose_shot(view,memory,now=8)
    assert shot['reason']=='moving force'
    assert shot['position'][0]==85
