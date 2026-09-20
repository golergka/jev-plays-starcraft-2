"""Build a local, experimental campaign copy with consistent objective reads/writes.

Does not change combat, objective conditions, rewards, or mission endings. The
result is not yet sufficient for automatic campaign completion verification.
Copyrighted assets and the provenance report stay beside ignored local maps.
"""
import argparse
import ctypes as c
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys
import tempfile
import uuid
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from jev_sc2.galaxy_bridge import TOKEN, VISIBLE_TIMER_CALLS, rewrite_objective_calls, append_after_unique_call, prepend_to_init_map

P, U, B = c.c_void_p, c.c_uint32, c.c_char_p


def bind(lib, name, args):
    function = getattr(lib, name)
    function.argtypes, function.restype = args, c.c_bool
    return function


class Assets:
    def __init__(self, storm, casc, storage, source):
        self.s, self.c = c.CDLL(str(storm)), c.CDLL(str(casc))
        for name, args in [
            ('SFileOpenArchive', [B,U,U,c.POINTER(P)]),
            ('SFileOpenFileEx', [P,B,U,c.POINTER(P)]),
            ('SFileReadFile', [P,P,U,c.POINTER(U),P]),
            ('SFileCloseFile', [P]), ('SFileCloseArchive', [P]),
            ('SFileAddFileEx', [P,B,B,U,U,U]),
        ]:
            bind(self.s, name, args)
        for name, args in [
            ('CascOpenStorage', [B,U,c.POINTER(P)]),
            ('CascOpenFile', [P,B,U,U,c.POINTER(P)]),
            ('CascReadFile', [P,P,U,c.POINTER(U)]),
            ('CascCloseFile', [P]), ('CascCloseStorage', [P]),
        ]:
            bind(self.c, name, args)
        for library, name in [(self.s, 'SFileGetFileSize'), (self.c, 'CascGetFileSize')]:
            function = bind(library, name, [P, c.POINTER(U)])
            function.restype = U
        self.archive, self.storage = P(), P()
        if not self.s.SFileOpenArchive(str(source).encode(), 0, 0, c.byref(self.archive)):
            raise RuntimeError('Cannot open source map')
        if not self.c.CascOpenStorage(str(storage).encode(), 0, c.byref(self.storage)):
            self.s.SFileCloseArchive(self.archive)
            raise RuntimeError('Cannot open installed game storage')

    def read(self, name, local=False):
        file = P()
        if local:
            opened = self.s.SFileOpenFileEx(self.archive, name.encode(), 0, c.byref(file))
        else:
            opened = self.c.CascOpenFile(self.storage, name.encode(), 0, 0, c.byref(file))
        if not opened:
            return None
        chunks = []
        try:
            high = U()
            expected = (self.s.SFileGetFileSize if local else self.c.CascGetFileSize)(file, c.byref(high))
            if high.value or expected > 64*1024*1024:
                raise ValueError(f'Unexpected script/document size: {name}')
            while True:
                buf, count = c.create_string_buffer(65536), U()
                if local:
                    ok = self.s.SFileReadFile(file, buf, len(buf), c.byref(count), None)
                else:
                    ok = self.c.CascReadFile(file, buf, len(buf), c.byref(count))
                chunks.append(buf.raw[:count.value])
                if not ok or count.value < len(buf):
                    break
            data = b''.join(chunks)
            if len(data) != expected:
                raise IOError(f'Truncated asset read: {name}: {len(data)} != {expected}')
            return data
        finally:
            (self.s.SFileCloseFile if local else self.c.CascCloseFile)(file)

    def close(self):
        self.s.SFileCloseArchive(self.archive)
        self.c.CascCloseStorage(self.storage)


def dependencies(document):
    if document is None:
        return []
    values = ET.fromstring(document).findall('./Dependencies/Value')
    result = []
    for value in values:
        match = re.search(r'(?:^|,)file:([^,]+)', value.text or '')
        if not match:
            raise ValueError(f'Dependency has no local path: {value.text}')
        result.append(match[1].replace('/', '\\').lower())
    return result


def includes(source):
    tokens = [t for t in TOKEN.finditer(source) if t.lastgroup not in {'space','comment'}]
    for index, token in enumerate(tokens):
        if token.lastgroup == 'identifier' and token.group() == 'include':
            following = tokens[index+1]
            if following.lastgroup != 'string':
                raise ValueError('Nonliteral include')
            name = json.loads(following.group()).replace('/', '\\').lower()
            if '..' in name.split('\\'):
                raise ValueError('Parent-relative includes need explicit resolution')
            yield name if name.endswith('.galaxy') else name + '.galaxy'


def build(args):
    report_path = args.destination.with_suffix('.bridge.json')
    if args.destination.exists() or report_path.exists():
        raise FileExistsError('Refusing to overwrite a map or provenance report')
    assets = Assets(args.storm, args.casc, args.storage, args.source)
    try:
        modules, seen = [], set()
        def add_module(module):
            if module in seen:
                return
            seen.add(module)
            document = assets.read(module + '\\documentinfo')
            for dependency in dependencies(document):
                add_module(dependency)
            modules.append(module)
        add_module('mods\\core.sc2mod')
        for module in dependencies(assets.read('DocumentInfo', local=True)):
            add_module(module)

        def resolve(name):
            for candidate in (name, 'base.sc2data\\' + name):
                data = assets.read(candidate, local=True)
                if data is not None:
                    return data, 'map:' + candidate
            candidates = []
            for module in modules:
                candidate = module + '\\base.sc2data\\' + name
                data = assets.read(candidate)
                if data is not None:
                    candidates.append((data, candidate))
            if not candidates:
                raise FileNotFoundError(f'Unresolved include {name}')
            # Until precedence has been verified, refuse differing overrides.
            if len({data for data, origin in candidates}) > 1:
                raise ValueError(f'Ambiguous dependency overrides: {[p for _,p in candidates]}')
            return candidates[-1]

        records, changed = {}, {}
        # SC2 normalizes punctuation out of bank filenames; use only alphanumerics.
        outcome_bank = 'JevOutcome' + uuid.uuid4().hex if args.record_outcomes else None
        timer_bank = 'JevVisibleTimer' + uuid.uuid4().hex if getattr(args, 'visible_timers', False) else None
        victory_hooks = []
        def visit(name):
            if name in records:
                return
            data, origin = resolve(name)
            source = data.decode('utf-8-sig')
            extra_calls = set(VISIBLE_TIMER_CALLS) if timer_bank else set()
            if outcome_bank: extra_calls.add('GameOver')
            rewritten, counts = rewrite_objective_calls(source, extra_calls=extra_calls)
            hooks = []
            if outcome_bank and origin.lower() == 'campaigns\\libertystory.sc2campaign\\base.sc2data\\triggerlibs\\campaignlib.galaxy':
                # Installed source audit: this unique call is in the genuine
                # mission-victory sequence, after the development-mode guard.
                rewritten = append_after_unique_call(rewritten, 'libCamp_gf_TS_SaveMissionCompletion',
                                                       'JevOutcomeRecord("victory");')
                victory_hooks.append(name)
                hooks.append('after campaign victory completion record')
            if outcome_bank and name == 'mapscript.galaxy':
                rewritten = prepend_to_init_map(rewritten, 'JevOutcomeInit();')
                hooks.append('initialize outcome bank')
            if timer_bank and name == 'mapscript.galaxy':
                rewritten = prepend_to_init_map(rewritten, 'JevVisibleTimerInit(1);')
                hooks.append('initialize visible timer export')
            records[name] = {'origin':origin, 'sha256':hashlib.sha256(data).hexdigest(),
                             'replacements':counts, 'outcome_hooks':hooks}
            for dependency in includes(source):
                visit(dependency)
            if counts or hooks:
                output = ('include "TriggerLibs/JevObjectiveBridge"\n' + rewritten).encode()
                changed[name] = output
                records[name]['output_sha256'] = hashlib.sha256(output).hexdigest()
        visit('mapscript.galaxy')
        if outcome_bank and len(victory_hooks) != 1:
            raise ValueError('Outcome recording requires the audited Wings of Liberty campaign library')
        if not changed:
            raise ValueError('No objective calls found; refusing a meaningless build')
        bridge = (Path(__file__).with_name('objective_state_bridge.galaxy')).read_bytes()
        if outcome_bank:
            bridge += b'\n' + Path(__file__).with_name('mission_outcome_bridge.galaxy').read_text().replace(
                'BANK_NAME', outcome_bank).encode()
        if timer_bank:
            bridge += b'\n' + Path(__file__).with_name('visible_timer_bridge.galaxy').read_text().replace(
                'TIMER_BANK_NAME', timer_bank).encode()
        changed['triggerlibs\\jevobjectivebridge.galaxy'] = b'include "TriggerLibs/natives"\n' + bridge
        shutil.copy2(args.source, args.destination)
        archive = P()
        if not assets.s.SFileOpenArchive(str(args.destination).encode(),0,0,c.byref(archive)):
            raise RuntimeError('Cannot open destination')
        try:
            with tempfile.TemporaryDirectory(prefix='jev-objective-bridge-') as temp:
                for index, (name, data) in enumerate(changed.items()):
                    path = Path(temp)/str(index)
                    path.write_bytes(data)
                    archive_name = 'MapScript.galaxy' if name == 'mapscript.galaxy' else name
                    if not assets.s.SFileAddFileEx(archive,str(path).encode(),archive_name.encode(),0x80000200,2,2):
                        raise RuntimeError(f'Cannot install {name}')
        finally:
            assets.s.SFileCloseArchive(archive)
        report = {'experimental':True, 'campaign_credit':False,
                  'source':str(args.source), 'source_sha256':hashlib.sha256(args.source.read_bytes()).hexdigest(),
                  'output_sha256':hashlib.sha256(args.destination.read_bytes()).hexdigest(),
                  'modules':modules, 'scripts':records, 'changed':list(changed),
                  'outcome_bank':outcome_bank, 'visible_timer_bank':timer_bank,
                  'bridge_sha256':hashlib.sha256(bridge).hexdigest()}
        report_path.write_text(json.dumps(report, indent=2)+'\n')
        print(json.dumps({'map':str(args.destination),'audited_scripts':len(records),
                          'changed':list(changed),'report':str(report_path)}))
    finally:
        assets.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('destination', type=Path)
    parser.add_argument('--storm', required=True, type=Path)
    parser.add_argument('--casc', required=True, type=Path)
    parser.add_argument('--storage', type=Path, default=Path('/Applications/StarCraft II'))
    parser.add_argument('--record-outcomes', action='store_true',
                        help='Experimental Wings of Liberty hooks: record real victory sequence/player defeat to a unique local bank')
    parser.add_argument('--visible-timers', action='store_true',
                        help='Experimental player-visible timer export; no player integration implied')
    build(parser.parse_args())
