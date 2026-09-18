import asyncio
import subprocess
import pytest
from s2clientprotocol import raw_pb2 as raw, sc2api_pb2 as sc
from jev_sc2.reload import PlayerLoader
from jev_sc2.sc2 import SC2, find_executable
from jev_sc2.view import validate_commands


def test_reload_uses_commit_and_retains_good_policy(tmp_path):
    def git(*args):
        return subprocess.check_output(['git','-C',str(tmp_path),*args],text=True)
    git('init','-q')
    git('config','user.name','Test')
    git('config','user.email','test@example.invalid')
    source=tmp_path/'player.py'
    source.write_text('async def decide(*args): return [1]\n')
    git('add','player.py'); git('commit','-qm','first')
    loader=PlayerLoader(tmp_path); loader.refresh()
    first=loader.revision
    source.write_text('async def decide(*args): return [2]\n')
    assert loader.refresh() is None
    assert asyncio.run(loader.module.decide()) == [1]
    git('add','player.py'); git('commit','-qm','second')
    assert loader.refresh() != first
    assert asyncio.run(loader.module.decide()) == [2]
    source.write_text('broken syntax!')
    git('add','player.py'); git('commit','-qm','broken')
    with pytest.raises(SyntaxError): loader.refresh()
    assert asyncio.run(loader.module.decide()) == [2]
    assert loader.refresh() is None


def test_rejects_hidden_targets_unowned_units_and_unoffered_commands():
    observation=sc.ResponseObservation()
    units=observation.observation.raw_data.units
    units.add(tag=1,alliance=raw.Self,display_type=raw.Visible)
    units.add(tag=2,alliance=raw.Enemy,display_type=raw.Hidden)
    cmd={'unit_tag':1,'ability_id':23,'target_tag':2}
    view={'self':[{'candidates':[{'command':cmd}]}]}
    assert validate_commands([cmd],view,observation)==[]
    units[1].display_type=raw.Visible
    assert len(validate_commands([cmd,cmd],view,observation))==1
    assert validate_commands([{**cmd,'ability_id':999}],view,observation)==[]
    units[0].alliance=raw.Enemy
    assert validate_commands([cmd],view,observation)==[]


def test_debug_is_unavailable():
    with pytest.raises(ValueError,match='Forbidden'):
        asyncio.run(SC2(None).request('debug',None))


def test_latest_build_numerically(tmp_path):
    for version in [9,100]:
        p=tmp_path/f'Versions/Base{version}/SC2.app/Contents/MacOS/SC2'
        p.parent.mkdir(parents=True); p.touch()
    assert 'Base100' in str(find_executable(tmp_path))
