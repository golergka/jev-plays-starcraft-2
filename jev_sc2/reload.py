"""Load committed player source atomically, without touching the game connection."""
import subprocess
import builtins
import types


class PlayerLoader:
    def __init__(self, root):
        self.root = root
        self.revision = None
        self.attempted = None
        self.module = None
        self.view_module = None
        self.camera_module = None

    def git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.root), *args], text=True).strip()

    def refresh(self):
        revision = self.git('rev-parse', 'HEAD')
        if revision == self.attempted:
            return None
        self.attempted = revision
        # Policy helpers use the same committed snapshot as player.py. A private
        # import table avoids changing modules used by an in-flight old player.
        helper_names = ('intentions', 'bottleneck', 'order_families',
                        'destination_categories', 'order_scores', 'commitment_review')
        helpers = {}
        helper_sources = {}
        for name in helper_names:
            path = f'jev_sc2/{name}.py'
            if self.git('ls-tree', '--name-only', revision, '--', path):
                fullname = f'jev_sc2.{name}'
                helpers[fullname] = types.ModuleType(fullname)
                helper_sources[fullname] = self.git('show', f'{revision}:{path}')
        def policy_import(name, globals=None, locals=None, fromlist=(), level=0):
            if level == 0 and fromlist and name in helpers:
                return helpers[name]
            return builtins.__import__(name, globals, locals, fromlist, level)
        policy_builtins = dict(vars(builtins), __import__=policy_import)
        for fullname, helper in helpers.items():
            helper.__package__ = 'jev_sc2'
            helper.__dict__['__builtins__'] = policy_builtins
            exec(compile(helper_sources[fullname], f'{fullname}@{revision}', 'exec'), helper.__dict__)
        source = self.git('show', f'{revision}:player.py')
        candidate = types.ModuleType(f'player_{revision}')
        candidate.__dict__['__builtins__'] = policy_builtins
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
        camera_candidate = None
        camera_path = 'jev_sc2/camera.py'
        if self.git('ls-tree','--name-only',revision,'--',camera_path):
            camera_source = self.git('show',f'{revision}:{camera_path}')
            camera_candidate = types.ModuleType(f'jev_sc2.camera_{revision}')
            exec(compile(camera_source,f'{camera_path}@{revision}','exec'),camera_candidate.__dict__)
            if not callable(getattr(camera_candidate,'choose_shot',None)):
                raise ValueError('camera.py must export choose_shot(view, memory)')
        # Commit all components together, retaining all old components if
        # either new source fails. The socket and policy memory stay in place.
        self.module, self.view_module, self.revision = candidate, view_candidate, revision
        self.camera_module = camera_candidate
        return revision
