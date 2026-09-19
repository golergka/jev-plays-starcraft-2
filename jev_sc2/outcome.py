"""Read a fresh, build-specific campaign ending marker; never use API objective results."""
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET


class OutcomeMonitor:
    def __init__(self, path, started_at, allow_credit=False):
        self.path = Path(path)
        self.started_at = started_at
        self.saw_active = False
        self.allow_credit = allow_credit

    @classmethod
    def for_map(cls, map_path, started_at, bank_directory=None):
        if not map_path:
            return None
        map_path = Path(map_path)
        manifest = map_path.with_suffix('.bridge.json')
        if not manifest.exists():
            return None
        metadata = json.loads(manifest.read_text())
        name = metadata.get('outcome_bank')
        if not name:
            return None
        if not re.fullmatch(r'JevOutcome[a-f0-9]{32}', name):
            raise ValueError('Invalid campaign outcome bank name')
        if hashlib.sha256(map_path.read_bytes()).hexdigest() != metadata['output_sha256']:
            raise ValueError('Campaign map does not match its outcome instrumentation manifest')
        directory = bank_directory or Path.home()/'Library/Application Support/Blizzard/StarCraft II/Banks'
        return cls(Path(directory)/(name+'.SC2Bank'), started_at,
                   allow_credit=metadata.get('campaign_credit') is True)

    def poll(self):
        try:
            if self.path.stat().st_mtime < self.started_at:
                return None
            root = ET.fromstring(self.path.read_bytes())
        except (FileNotFoundError, ET.ParseError):
            return None  # BankSave may be between its write and rename.
        value = root.find("./Section[@name='Outcome']/Key[@name='result']/Value")
        result = value.get('string') if value is not None else None
        if result == 'active':
            self.saw_active = True
            return None
        if not self.saw_active or result not in {'victory','defeat'}:
            return None
        stamp = root.find("./Section[@name='Outcome']/Key[@name='engine_time']/Value")
        return {'status':result, 'source':'campaign ending instrumentation',
                'credit_enabled':self.allow_credit,
                'bank':str(self.path), 'engine_time':stamp.get('int') if stamp is not None else None}
