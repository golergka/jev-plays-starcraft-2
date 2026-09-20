"""Conservative source rewriting for the campaign objective compatibility layer.

Only call names change. Comments, strings, native declarations and all mission
conditions remain byte-for-byte unchanged. Callers must separately resolve the
entire include closure and supply the adapter before using a transformed map.
"""
import re
from collections import Counter

OBJECTIVE_CALLS = frozenset({
    'ObjectiveCreate', 'ObjectiveCreateForPlayers', 'ObjectiveGetState',
    'ObjectiveSetState', 'ObjectiveGetName', 'ObjectiveSetName',
    'ObjectiveDestroy', 'ObjectiveDestroyAll',
})
VISIBLE_TIMER_CALLS = frozenset({
    'TimerWindowCreate', 'TimerWindowDestroy', 'TimerWindowSetTimer',
    'TimerWindowSetTitle', 'TimerWindowSetStyle',
})
TOKEN = re.compile(
    r'(?P<string>"(?:\\.|[^"\\])*")|(?P<comment>//[^\r\n]*|/\*[\s\S]*?\*/)|'
    r'(?P<identifier>[A-Za-z_][A-Za-z_0-9]*)|(?P<space>\s+)|(?P<other>.)'
)


def rewrite_objective_calls(source, extra_calls=()):
    """Return rewritten source and per-native replacement counts.

    Reject objective declarations outside the native library rather than silently
    renaming a function definition or overriding an unknown mission abstraction.
    """
    tokens = list(TOKEN.finditer(source))
    significant = [i for i, token in enumerate(tokens)
                   if token.lastgroup not in {'space', 'comment'}]
    replacements = {}
    counts = Counter()
    for position, index in enumerate(significant):
        token = tokens[index]
        name = token.group()
        if token.lastgroup != 'identifier' or name not in OBJECTIVE_CALLS | frozenset(extra_calls):
            continue
        if position + 1 >= len(significant) or tokens[significant[position+1]].group() != '(':
            raise ValueError(f'Unsupported reference to {name}; expected a direct call')
        previous = tokens[significant[position-1]].group() if position else None
        before_previous = tokens[significant[position-2]].group() if position > 1 else None
        if previous in {'int', 'void', 'text'}:
            if before_previous == 'native':
                continue
            raise ValueError(f'Unexpected objective declaration: {name}')
        replacements[index] = 'Jev' + name
        counts[name] += 1
    return ''.join(replacements.get(i, token.group()) for i, token in enumerate(tokens)), dict(counts)


def append_after_unique_call(source, name, statement):
    """Instrument one audited zero-argument call; reject missing/changed sites."""
    tokens = [t for t in TOKEN.finditer(source) if t.lastgroup not in {'space', 'comment'}]
    sites = []
    for i, token in enumerate(tokens):
        if token.lastgroup != 'identifier' or token.group() != name:
            continue
        if i and tokens[i-1].group() in {'void','int','bool','text'}:
            continue
        if [t.group() for t in tokens[i+1:i+4]] != ['(',')',';']:
            raise ValueError(f'Unsupported instrumentation site for {name}')
        sites.append(tokens[i+3].end())
    if len(sites) != 1:
        raise ValueError(f'Expected one audited {name} call, found {len(sites)}')
    end = sites[0]
    return source[:end] + '\n    ' + statement + source[end:]


def prepend_to_init_map(source, statement):
    tokens = [t for t in TOKEN.finditer(source) if t.lastgroup not in {'space','comment'}]
    sites = []
    for i, token in enumerate(tokens):
        if token.group() == 'InitMap' and [t.group() for t in tokens[max(0,i-1):i+4]] == ['void','InitMap','(',')','{']:
            sites.append(tokens[i+3].end())
    if len(sites) != 1:
        raise ValueError('Expected exactly one InitMap definition')
    end = sites[0]
    return source[:end] + '\n    ' + statement + source[end:]
