import os
import pytest
from jev_sc2.mission_context import VisibleTimerReader


def bank(path, launch_stamp=2, sequence=1, value='12.5', count=1):
    path.write_text(f'''<Bank><Section name="Context">
    <Key name="launch_stamp"><Value int="{launch_stamp}"/></Key>
    <Key name="sequence"><Value int="{sequence}"/></Key>
    <Key name="count"><Value int="{count}"/></Key></Section>
    <Section name="Timer0"><Key name="window"><Value int="7"/></Key>
    <Key name="title"><Value text="Evacuation"/></Key>
    <Key name="elapsed"><Value flag="0"/></Key>
    <Key name="value"><Value fixed="{value}"/></Key></Section></Bank>''')
    os.utime(path, (100, 100))


def test_timer_freshness_and_generation(tmp_path):
    p=tmp_path/'timer'; reader=VisibleTimerReader(p,previous_launch_stamp=1,started_at=90)
    assert reader.poll(101) is None
    bank(p,launch_stamp=1); assert reader.poll(101) is None
    bank(p); assert reader.poll(106) is None
    result=reader.poll(102)
    assert result['timers']==[{'window':7,'title':'Evacuation','mode':'remaining','raw_timer_value':12.5}]
    assert VisibleTimerReader(p,previous_launch_stamp=1,started_at=101).poll(102) is None
    bank(p,sequence=2);reader.poll(102)
    bank(p,sequence=1)
    with pytest.raises(ValueError,match='rewound'):reader.poll(102)


@pytest.mark.parametrize('value,count', [('nan',1),('inf',1),('12',0)])
def test_timer_malformed_values_fail_loudly(tmp_path,value,count):
    p=tmp_path/'timer';bank(p,value=value,count=count)
    with pytest.raises(ValueError):VisibleTimerReader(p,previous_launch_stamp=1,started_at=90).poll(102)


def test_launch_change_during_attempt_is_loud(tmp_path):
    p=tmp_path/'timer';bank(p,launch_stamp=2)
    reader=VisibleTimerReader(p,previous_launch_stamp=1,started_at=90)
    reader.poll(102)
    bank(p,launch_stamp=3)
    with pytest.raises(ValueError,match='launch changed'):reader.poll(102)


def test_manifest_hash_and_previous_launch(tmp_path):
    import hashlib,json
    from jev_sc2.mission_context import timer_reader_for_map
    map_path=tmp_path/'mission.SC2Map';map_path.write_bytes(b'map')
    name='JevVisibleTimer'+'a'*32
    map_path.with_suffix('.bridge.json').write_text(json.dumps({'visible_timer_bank':name,'output_sha256':hashlib.sha256(b'map').hexdigest()}))
    bank(tmp_path/(name+'.SC2Bank'),launch_stamp=7)
    reader=timer_reader_for_map(map_path,new_launch=True,bank_directory=tmp_path)
    assert reader.previous_launch_stamp==7
    map_path.write_bytes(b'changed')
    with pytest.raises(ValueError,match='manifest'):
        timer_reader_for_map(map_path,new_launch=True,bank_directory=tmp_path)


def test_timer_context_survives_economic_projection():
    import player
    context={'timers':[{'title':'Observed timer','mode':'remaining','raw_timer_value':123}]}
    assert player.investment_state({'mission_context':context})['mission_context']==context


def add_objectives(path, *, state=1, count=1):
    text=path.read_text().replace('</Bank>',f'''<Section name="Objectives"><Key name="count"><Value int="{count}"/></Key></Section>
    <Section name="Objective0"><Key name="id"><Value int="1"/></Key>
    <Key name="name"><Value text="Visible task"/></Key>
    <Key name="description"><Value text="Visible detail"/></Key>
    <Key name="state"><Value int="{state}"/></Key>
    <Key name="primary"><Value flag="1"/></Key></Section></Bank>''')
    path.write_text(text);os.utime(path,(100,100))


def test_objectives_share_freshness_gate(tmp_path):
    p=tmp_path/'context';bank(p);add_objectives(p,state=3)
    reader=VisibleTimerReader(p,previous_launch_stamp=1,started_at=90,require_objectives=True)
    assert reader.poll(106) is None
    result=reader.poll(102)
    assert result['objectives']==[{'id':1,'name':'Visible task','description':'Visible detail','state':'failed','primary':True}]
    bank(p,launch_stamp=1);add_objectives(p)
    assert VisibleTimerReader(p,previous_launch_stamp=1,started_at=90,require_objectives=True).poll(102) is None


@pytest.mark.parametrize('state,count',[(0,1),(4,1),(1,0),(1,-1)])
def test_objective_count_and_state_fail_loudly(tmp_path,state,count):
    p=tmp_path/'context';bank(p);add_objectives(p,state=state,count=count)
    with pytest.raises(ValueError):
        VisibleTimerReader(p,previous_launch_stamp=1,started_at=90,require_objectives=True).poll(102)


def test_objective_enabled_build_cannot_silently_omit_export(tmp_path):
    p=tmp_path/'context';bank(p)
    with pytest.raises(ValueError,match='Incomplete visible objective'):
        VisibleTimerReader(p,previous_launch_stamp=1,started_at=90,require_objectives=True).poll(102)


def test_objective_startup_wait_is_bounded_and_latched():
    from jev_sc2.mission_context import ObjectiveInitializationGate
    gate=ObjectiveInitializationGate(100)
    assert not gate.check(None,100)
    assert not gate.check({'objectives':[]},110)
    assert gate.check({'objectives':[{'state':'active'}]},120)
    assert gate.check(None,150)  # This gate never hides later runtime deterioration.
    missing=ObjectiveInitializationGate(100)
    with pytest.raises(TimeoutError):missing.check({'objectives':[]},130)
    with pytest.raises(TimeoutError):missing.check({'objectives':[{}]},131)


def test_investment_retains_exact_game_loop():
    import player
    assert player.investment_state({'game_loop': 29923})['game_loop'] == 29923
    assert 'game_loop' not in player.investment_state({})
