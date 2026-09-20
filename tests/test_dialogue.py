import os
import xml.etree.ElementTree as ET
import pytest
from jev_sc2.dialogue import DialogueReader


def write_bank(path, stamp=10, sequence=21, wrong=False):
    root=ET.Element('Bank')
    def section(name, values):
        node=ET.SubElement(root,'Section',name=name)
        for key,value in values.items():
            ET.SubElement(ET.SubElement(node,'Key',name=key),'Value',**value)
    section('Context',{'launch_stamp':{'int':str(stamp)},'sequence':{'int':str(sequence)}})
    for n in range(max(1,sequence-15),sequence+1):
        section(f'Message{(n-1)%16}',{'sequence':{'int':str(n+1 if wrong else n)},
            'text':{'text':f'line {n}'},'time':{'int':'100'},'captured_after_wait':{'flag':'0'}})
    path.write_bytes(ET.tostring(root))


def test_ring_order_and_blocking_metadata(tmp_path):
    p=tmp_path/'bank';write_bank(p)
    d=DialogueReader(p,started_at=0).poll()
    assert [m['sequence'] for m in d['messages']]==list(range(6,22))
    assert d['messages'][-1]['text']=='line 21'


def test_previous_launch_and_old_file_are_not_exposed(tmp_path):
    p=tmp_path/'bank';write_bank(p)
    assert DialogueReader(p,started_at=0,previous_launch_stamp=10).poll() is None
    os.utime(p,(1,1))
    assert DialogueReader(p,started_at=2).poll() is None


def test_launch_change_rewind_and_corrupt_ring_fail(tmp_path):
    p=tmp_path/'bank';write_bank(p);reader=DialogueReader(p,started_at=0);reader.poll()
    for options in ({'stamp':11},{'sequence':20},{'wrong':True}):
        write_bank(p,**options)
        with pytest.raises(ValueError):reader.poll()


def test_missing_or_in_progress_bank_unavailable(tmp_path):
    p=tmp_path/'bank';reader=DialogueReader(p,started_at=0)
    assert reader.poll() is None
    p.write_text('<Bank>')
    assert reader.poll() is None


def test_factory_checks_map_hash_and_bank_path(tmp_path):
    import hashlib,json
    from jev_sc2.dialogue import dialogue_reader_for_map
    p=tmp_path/'map.SC2Map';p.write_bytes(b'map')
    metadata={'visible_dialogue_bank':'JevDialogue'+'a'*32,
              'output_sha256':hashlib.sha256(b'map').hexdigest()}
    side=p.with_suffix('.bridge.json');side.write_text(json.dumps(metadata))
    reader=dialogue_reader_for_map(p,new_launch=True,bank_directory=tmp_path)
    assert reader.path.parent==tmp_path
    p.write_bytes(b'changed')
    with pytest.raises(ValueError,match='manifest'):
        dialogue_reader_for_map(p,new_launch=True,bank_directory=tmp_path)
    metadata['visible_dialogue_bank']='../elsewhere';side.write_text(json.dumps(metadata))
    with pytest.raises(ValueError,match='bank name'):
        dialogue_reader_for_map(p,new_launch=True,bank_directory=tmp_path)
