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
TOKEN = re.compile(
    r'(?P<string>"(?:\\.|[^"\\])*")|(?P<comment>//[^\r\n]*|/\*[\s\S]*?\*/)|'
    r'(?P<identifier>[A-Za-z_][A-Za-z_0-9]*)|(?P<space>\s+)|(?P<other>.)'
)


def rewrite_objective_calls(source):
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
        if token.lastgroup != 'identifier' or name not in OBJECTIVE_CALLS:
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
