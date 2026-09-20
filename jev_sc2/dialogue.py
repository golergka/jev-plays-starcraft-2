"""Read bounded runtime subtitle history; never read dialogue catalogs."""
from pathlib import Path
import xml.etree.ElementTree as ET


class DialogueReader:
    def __init__(self, path, *, started_at, previous_launch_stamp=None):
        self.path = Path(path)
        self.started_at = started_at
        self.previous_launch_stamp = previous_launch_stamp
        self.launch_stamp = None
        self.sequence = 0

    def poll(self):
        try:
            if self.path.stat().st_mtime < self.started_at:
                return None
            root = ET.fromstring(self.path.read_bytes())
        except (FileNotFoundError, ET.ParseError):
            return None
        sections = {}
        for section in root.findall('Section'):
            name = section.get('name')
            if name in sections:
                raise ValueError('Duplicate dialogue section')
            values = {}
            for key in section.findall('Key'):
                if key.get('name') in values or key.find('Value') is None:
                    raise ValueError('Malformed dialogue key')
                values[key.get('name')] = key.find('Value').attrib
            sections[name] = values
        try:
            context = sections['Context']
            stamp = int(context['launch_stamp']['int'])
            sequence = int(context['sequence']['int'])
            if stamp == self.previous_launch_stamp:
                return None
            if self.launch_stamp is not None and stamp != self.launch_stamp:
                raise ValueError('Dialogue launch changed during attempt')
            if sequence < self.sequence or sequence < 0:
                raise ValueError('Dialogue sequence rewound')
            messages = []
            for number in range(max(1, sequence-15), sequence+1):
                item = sections[f'Message{(number-1)%16}']
                if int(item['sequence']['int']) != number:
                    raise ValueError('Dialogue ring sequence mismatch')
                waited = item['captured_after_wait']['flag']
                if waited not in ('0', '1'):
                    raise ValueError('Invalid dialogue wait flag')
                messages.append({'sequence':number, 'text':item['text']['text'],
                                 'captured_at_engine_time':int(item['time']['int']),
                                 'captured_after_wait':waited == '1'})
        except (KeyError, TypeError) as exc:
            raise ValueError('Incomplete dialogue bank') from exc
        self.launch_stamp, self.sequence = stamp, sequence
        return {'source':'runtime transmissions addressed to controlled player',
                'messages':messages,
                'note':'Recent subtitle history, not necessarily still displayed. Blocking transmissions appear after the native call returns.'}


def dialogue_reader_for_map(map_path, *, new_launch, bank_directory=None):
    import hashlib
    import json
    import re
    import time
    path = Path(map_path)
    manifest = path.with_suffix('.bridge.json')
    if not manifest.exists():
        return None
    metadata = json.loads(manifest.read_text())
    name = metadata.get('visible_dialogue_bank')
    if not name:
        return None
    if not re.fullmatch(r'JevDialogue[a-f0-9]{32}', name):
        raise ValueError('Invalid dialogue bank name')
    if hashlib.sha256(path.read_bytes()).hexdigest() != metadata['output_sha256']:
        raise ValueError('Dialogue map does not match instrumentation manifest')
    directory = bank_directory or Path.home()/'Library/Application Support/Blizzard/StarCraft II/Banks'
    bank = Path(directory)/(name+'.SC2Bank')
    previous = None
    if new_launch and bank.exists():
        marker = ET.parse(bank).find("./Section[@name='Context']/Key[@name='launch_stamp']/Value")
        if marker is None:
            raise ValueError('Existing dialogue bank has no launch stamp')
        previous = int(marker.attrib['int'])
    return DialogueReader(bank, started_at=time.time() if new_launch else 0,
                          previous_launch_stamp=previous)
