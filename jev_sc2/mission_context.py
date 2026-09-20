"""Strict reader for experimental visible-timer banks; not wired to the player yet."""
import math
from pathlib import Path
import xml.etree.ElementTree as ET


class VisibleTimerReader:
    def __init__(self, path, *, previous_launch_stamp, started_at, max_age=5):
        if max_age <= 0:
            raise ValueError('Require a positive freshness interval')
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
        self.launch_stamp = stamp
        self.sequence = sequence
        return {'source': 'player-visible native timer windows', 'timers': timers,
                'note': 'Native timer values; displayed formatting and rounding not yet validated.'}
