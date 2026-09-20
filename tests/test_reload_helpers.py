import asyncio
import subprocess
import pytest
from jev_sc2.reload import PlayerLoader

def test_helpers_use_committed_snapshot_and_old_player_keeps_its_snapshot(tmp_path):
    def git(*args):return subprocess.check_output(['git','-C',str(tmp_path),*args],text=True)
    git('init','-q');git('config','user.name','Test');git('config','user.email','test@example.invalid')
    (tmp_path/'jev_sc2').mkdir()
    (tmp_path/'player.py').write_text('async def decide(*args):\n from jev_sc2.bottleneck import value\n return value\n')
    helper=tmp_path/'jev_sc2/bottleneck.py';helper.write_text('value = 1\n')
    def commit():git('add','.');git('commit','-qm','snapshot')
    commit();loader=PlayerLoader(tmp_path);loader.refresh();old=loader.module
    helper.write_text('value = 2\n');commit();helper.write_text('value = 999\n')
    loader.refresh()
    assert asyncio.run(loader.module.decide())==2
    assert asyncio.run(old.decide())==1
    good=loader.revision
    helper.write_text('broken syntax!');commit()
    with pytest.raises(SyntaxError):loader.refresh()
    assert loader.revision==good
    assert asyncio.run(loader.module.decide())==2
