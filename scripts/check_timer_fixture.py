"""Validate recorded diagnostic stages, not campaign success or screen rounding."""
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

root = ET.parse(sys.argv[1]).getroot()
stages = {}
for name in ('created','paused','still_paused','replaced','hidden','shown','destroyed'):
    section = root.find(f"Section[@name='{name}']")
    if section is None:
        raise ValueError(f'Fixture incomplete: missing {name}')
    stages[name] = {k.attrib['name']: dict(k.find('Value').attrib) for k in section.findall('Key')}
for name in ('created','paused','still_paused','replaced','shown'):
    assert stages[name]['count']['int']=='1', (name, stages[name])
    assert stages[name]['timer_section']['flag']=='1'
for name in ('hidden','destroyed'):
    assert stages[name]['count']['int']=='0', (name, stages[name])
    assert stages[name]['timer_section']['flag']=='0'
for name in ('created','paused','still_paused'):
    assert stages[name]['title']['text']=='VISIBLE FIXTURE 60'
    assert stages[name]['elapsed']['flag']=='0'
assert stages['paused']['value']==stages['still_paused']['value']
assert 0 < float(stages['paused']['value']['fixed']) < float(stages['created']['value']['fixed']) <= 60
for name in ('replaced','shown'):
    assert stages[name]['title']['text']=='REPLACED ELAPSED'
    assert stages[name]['elapsed']['flag']=='1'
assert float(stages['shown']['value']['fixed']) > float(stages['replaced']['value']['fixed'])
assert 'HIDDEN FIXTURE' not in ET.tostring(root,encoding='unicode')
result={'passed':True,'scope':'Native fixture stage exports: visibility, pause, replacement, elapsed mode, destruction. Does not validate display rounding or launch freshness.','stages':stages}
if len(sys.argv)>2:Path(sys.argv[2]).write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
