"""Load committed player source atomically, without touching the game connection."""
import subprocess
import types


class PlayerLoader:
    def __init__(self, root):
        self.root = root
        self.revision = None
        self.attempted = None
        self.module = None
        self.view_module = None

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
        view_candidate = None
        view_path = 'jev_sc2/view.py'
        if self.git('ls-tree','--name-only',revision,'--',view_path):
            view_source = self.git('show',f'{revision}:{view_path}')
            view_candidate = types.ModuleType(f'jev_sc2.view_{revision}')
            view_candidate.__package__ = 'jev_sc2'
            exec(compile(view_source,f'{view_path}@{revision}','exec'),view_candidate.__dict__)
            if not callable(getattr(view_candidate,'make_view',None)):
                raise ValueError('view.py must export async make_view(...)')
        # Commit both components together, retaining both old components if
        # either new source fails. The socket and policy memory stay in place.
        self.module, self.view_module, self.revision = candidate, view_candidate, revision
        return revision
