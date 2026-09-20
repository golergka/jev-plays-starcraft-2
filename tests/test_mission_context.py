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
