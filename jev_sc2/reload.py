"""Load committed player source atomically, without touching the game connection."""
import subprocess
import types


class PlayerLoader:
    def __init__(self, root):
        self.root = root
        self.revision = None
        self.attempted = None
        self.module = None

    def git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.root), *args], text=True).strip()

    def refresh(self):
        revision = self.git('rev-parse', 'HEAD')
        if revision == self.attempted:
            return None
        self.attempted = revision
        source = self.git('show', f'{revision}:player.py')
        candidate = types.ModuleType(f'player_{revision}')
        exec(compile(source, f'player.py@{revision}', 'exec'), candidate.__dict__)
        if not callable(getattr(candidate, 'decide', None)):
            raise ValueError('player.py must export async decide(view, jev, memory)')
        self.module, self.revision = candidate, revision
        return revision

