"""Fresh, player-visible timer and optional objective context for the controller."""
import math
from pathlib import Path
import xml.etree.ElementTree as ET


class VisibleTimerReader:
    def __init__(self, path, *, previous_launch_stamp, started_at, max_age=5, require_objectives=False):
        if max_age <= 0:
            raise ValueError('Require a positive freshness interval')
        self.require_objectives = require_objectives
        self.path = Path(path)
        self.previous_launch_stamp = previous_launch_stamp
        self.launch_stamp = None
        self.started_at = started_at
        self.max_age = max_age
        self.sequence = 0

    def poll(self, now):
        try:
            modified = self.path.stat().st_mtime
            if modified < self.started_at or not 0 <= now-modified <= self.max_age:
                return None
            root = ET.fromstring(self.path.read_bytes())
        except (FileNotFoundError, ET.ParseError):
            return None  # Missing/in-progress saves are unavailable, never cached facts.
        sections = {}
        for section in root.findall('Section'):
            name = section.get('name')
            if name in sections:
                raise ValueError('Duplicate timer bank section')
            values = {}
            for key in section.findall('Key'):
                if key.get('name') in values or key.find('Value') is None:
                    raise ValueError('Malformed timer bank key')
                values[key.get('name')] = key.find('Value').attrib
            sections[name] = values
        context = sections.get('Context', {})
        def integer(values, key):
            return int(values[key]['int'])
        try:
            stamp = integer(context, 'launch_stamp')
            if stamp == self.previous_launch_stamp:
                return None
            if self.launch_stamp is not None and stamp != self.launch_stamp:
                raise ValueError('Timer launch changed during active attempt')
            sequence = integer(context, 'sequence')
            if sequence < self.sequence or sequence < 1:
                raise ValueError('Timer bank sequence rewound')
            count = integer(context, 'count')
            if count < 0 or count > 1024:
                raise ValueError('Invalid timer count')
            timer_sections = {k for k in sections if k.startswith('Timer')}
            if timer_sections != {f'Timer{i}' for i in range(count)}:
                raise ValueError('Timer count and sections disagree')
            timers = []
            for i in range(count):
                item = sections[f'Timer{i}']
                value = float(item['value']['fixed'])
                elapsed = item['elapsed']['flag']
                if not math.isfinite(value) or elapsed not in ('0', '1'):
                    raise ValueError('Invalid visible timer value or mode')
                timers.append({'window': integer(item, 'window'), 'title': item['title']['text'],
                               'mode': 'elapsed' if elapsed == '1' else 'remaining',
                               'raw_timer_value': value})
        except (KeyError, TypeError) as exc:
            raise ValueError('Incomplete visible timer bank') from exc
        objectives = None
        if self.require_objectives or 'Objectives' in sections:
            try:
                count = integer(sections['Objectives'], 'count')
                if not 0 <= count <= 1024:
                    raise ValueError('Invalid objective count')
                names = {k for k in sections if k.startswith('Objective') and k != 'Objectives'}
                if names != {f'Objective{i}' for i in range(count)}:
                    raise ValueError('Objective count and sections disagree')
                objectives = []
                seen = set()
                for i in range(count):
                    item = sections[f'Objective{i}']
                    identity = integer(item, 'id')
                    state = integer(item, 'state')
                    primary = item['primary']['flag']
                    if identity in seen or state not in (1, 2, 3) or primary not in ('0', '1'):
                        raise ValueError('Invalid visible objective identity, state or primary flag')
                    seen.add(identity)
                    objectives.append({'id': identity, 'name': item['name']['text'],
                        'description': item['description']['text'],
                        'state': {1:'active',2:'completed',3:'failed'}[state], 'primary': primary == '1'})
            except (KeyError, TypeError) as exc:
                raise ValueError('Incomplete visible objective bank') from exc
        self.launch_stamp = stamp
        self.sequence = sequence
        return {'source': 'player-visible native timer windows and objectives' if objectives is not None else 'player-visible native timer windows', 'timers': timers,
                **({'objectives': objectives} if objectives is not None else {}),
                'note': 'Native timer values; displayed formatting and rounding not yet validated.'}


def timer_reader_for_map(map_path, *, new_launch, bank_directory=None):
    """Resolve a hash-checked local build before launch or when attaching."""
    import hashlib
    import json
    import re
    import time
    path = Path(map_path)
    manifest = path.with_suffix('.bridge.json')
    if not manifest.exists():
        return None
    metadata = json.loads(manifest.read_text())
    name = metadata.get('visible_timer_bank')
    if not name:
        return None
    if not re.fullmatch(r'JevVisibleTimer[a-f0-9]{32}', name):
        raise ValueError('Invalid visible timer bank name')
    if hashlib.sha256(path.read_bytes()).hexdigest() != metadata['output_sha256']:
        raise ValueError('Timer map does not match instrumentation manifest')
    directory = bank_directory or Path.home()/'Library/Application Support/Blizzard/StarCraft II/Banks'
    bank = Path(directory)/(name+'.SC2Bank')
    previous = None
    if new_launch and bank.exists():
        marker = ET.parse(bank).find("./Section[@name='Context']/Key[@name='launch_stamp']/Value")
        if marker is None:
            raise ValueError('Existing timer bank has no launch stamp')
        previous = int(marker.attrib['int'])
    return VisibleTimerReader(bank,previous_launch_stamp=previous,
                              started_at=time.time() if new_launch else 0,
                              require_objectives=metadata.get('visible_objectives',False))
