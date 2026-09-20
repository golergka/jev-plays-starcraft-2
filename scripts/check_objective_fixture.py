"""Validate native diagnostic objective stages; never grant campaign credit."""
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

path=Path(sys.argv[1])
root=ET.fromstring(path.read_text())
sections={s.attrib['name']:{k.attrib['name']:k.find('Value').attrib for k in s.findall('Key')} for s in root.findall('Section')}
expected={
    'created':('Visible objective',1),
    'renamed':('Updated objective',1),
    'completed':('[Completed] Updated objective',2),
    'shown':('[Completed] Updated objective',2),
    'replacement':('Replacement',1),
    'registered_twice':('Replacement',1),
    'failed':('[Failed] Replacement',3),
    'returned_player':('[Failed] Replacement',3),
}
for stage,(name,state) in expected.items():
    actual=sections[stage]
    assert actual['count']['int']=='1',stage
    assert actual['section']['flag']=='1',stage
    assert actual['name']['text']==name,stage
    assert actual['state']['int']==str(state),stage
for stage in ('hidden','destroyed','other_player','destroy_all'):
    assert sections[stage]['count']['int']=='0',stage
    assert sections[stage]['section']['flag']=='0',stage
assert 'HIDDEN SECRET' not in path.read_text()
assert sections['Objectives']['count']['int']=='0'
result={'sections':sections,'validated_stages':12,
        'scope':'Native visibility/lifecycle fixture, not campaign success. Duplicate registration of the same ID tested; actual native allocation reuse not forced. Live reader/builder integration remains outstanding.'}
if len(sys.argv)>2:Path(sys.argv[2]).write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'validated_stages':12}))
