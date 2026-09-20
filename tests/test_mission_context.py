import os
import pytest
from jev_sc2.mission_context import VisibleTimerReader


def bank(path, generation=2, sequence=1, value='12.5', count=1):
    path.write_text(f'''<Bank><Section name="Context">
    <Key name="generation"><Value int="{generation}"/></Key>
    <Key name="sequence"><Value int="{sequence}"/></Key>
    <Key name="count"><Value int="{count}"/></Key></Section>
    <Section name="Timer0"><Key name="window"><Value int="7"/></Key>
    <Key name="title"><Value text="Evacuation"/></Key>
    <Key name="elapsed"><Value flag="0"/></Key>
    <Key name="value"><Value fixed="{value}"/></Key></Section></Bank>''')
    os.utime(path, (100, 100))


def test_timer_freshness_and_generation(tmp_path):
    p=tmp_path/'timer'; reader=VisibleTimerReader(p,expected_generation=2,started_at=90)
    assert reader.poll(101) is None
    bank(p,generation=1); assert reader.poll(101) is None
    bank(p); assert reader.poll(106) is None
    result=reader.poll(102)
    assert result['timers']==[{'window':7,'title':'Evacuation','mode':'remaining','raw_timer_value':12.5}]
    assert VisibleTimerReader(p,expected_generation=2,started_at=101).poll(102) is None
    bank(p,sequence=2);reader.poll(102)
    bank(p,sequence=1)
    with pytest.raises(ValueError,match='rewound'):reader.poll(102)


@pytest.mark.parametrize('value,count', [('nan',1),('inf',1),('12',0)])
def test_timer_malformed_values_fail_loudly(tmp_path,value,count):
    p=tmp_path/'timer';bank(p,value=value,count=count)
    with pytest.raises(ValueError):VisibleTimerReader(p,expected_generation=2,started_at=90).poll(102)
