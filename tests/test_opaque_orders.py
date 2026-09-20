import asyncio
from unittest.mock import AsyncMock
import pytest
import player


def test_opaque_roundtrip_preserves_actions_probabilities_and_other_questions(monkeypatch):
    questions={'army':{'criteria':{'move':'Go','attack':'Fight'}},'worker':{'criteria':{'continue':'Keep'}}}
    async def choose(state,encoded,jev):
        assert list(encoded['army']['criteria'].values())==['Go','Fight']
        assert encoded['worker']==questions['worker']
        return {'army':{'choice':'option_001','probabilities':{'option_000':.2,'option_001':.8}}}
    monkeypatch.setattr(player,'choose_concrete_orders',choose)
    class Model:
        def log(self,*a,**k):pass
    out=asyncio.run(player.choose_with_opaque_keys({},questions,Model(),{'army'}))
    assert out['army']['choice']=='attack'
    assert out['army']['probabilities']=={'move':.2,'attack':.8}
    assert list(questions['army']['criteria'])==['move','attack']


def test_unknown_alias_fails_loudly(monkeypatch):
    monkeypatch.setattr(player,'choose_concrete_orders',AsyncMock(return_value={'army':{'choice':'option_999'}}))
    with pytest.raises(ValueError,match='Unknown opaque'):
        asyncio.run(player.choose_with_opaque_keys({}, {'army':{'criteria':{'move':'Go'}}},None,{'army'}))
