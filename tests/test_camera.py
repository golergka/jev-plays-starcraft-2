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


def test_camera_reload_retains_previous_pair_if_camera_is_broken(tmp_path):
    import subprocess
    import pytest
    from jev_sc2.reload import PlayerLoader
    def git(*args):
        return subprocess.check_output(['git','-C',str(tmp_path),*args],text=True)
    git('init','-q'); git('config','user.name','Test'); git('config','user.email','test@example.invalid')
    (tmp_path/'player.py').write_text('async def decide(*args): return []\n')
    (tmp_path/'jev_sc2').mkdir()
    camera=tmp_path/'jev_sc2/camera.py'
    camera.write_text('def choose_shot(*args): return 1\n')
    git('add','.'); git('commit','-qm','valid')
    loader=PlayerLoader(tmp_path); loader.refresh(); previous=loader.revision
    camera.write_text('broken syntax!')
    git('add','.'); git('commit','-qm','invalid')
    with pytest.raises(SyntaxError): loader.refresh()
    assert loader.revision==previous
    assert loader.camera_module.choose_shot()==1


def test_camera_tracks_subject_during_hold_without_resetting_cut_timer():
    memory = {}
    view = {'self': [unit(1, 10)]}
    choose_shot(view, memory, now=0)
    view['self'][0]['position'] = [14, 10]
    shot = choose_shot(view, memory, now=2)
    assert shot['position'] == [14, 10]
    assert shot['reason'].startswith('tracking ')
    assert memory['cut_at'] == 0


def test_idle_army_beats_base_and_frames_subject_not_workers():
    workers = [dict(unit(i, 10), candidates=[{'id': 'gather_minerals'}]) for i in range(30)]
    shot = choose_shot({'self': workers + [unit(100, 18)]}, {}, now=0)
    assert shot['position'] == [18, 10]
    assert shot['reason'] == 'army overview'


def test_camera_cuts_to_shield_damage_and_rotates_quiet_scenes():
    memory = {}
    view = {'self': [unit(1, 10), dict(unit(2, 80), shield=100)]}
    choose_shot(view, memory, now=0)
    view['self'][1]['shield'] = 80
    assert choose_shot(view, memory, now=3)['position'][0] == 80
    assert choose_shot(view, memory, now=11)['position'][0] == 10
