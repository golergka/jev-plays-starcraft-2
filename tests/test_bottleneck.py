import asyncio
import copy
import pytest
from jev_sc2.bottleneck import diagnose, question

class Model:
    def __init__(self, choice='income'):
        self.choice = choice
        self.calls = 0
    async def ask(self, state, questions):
        self.calls += 1
        assert 'none' in questions['bottleneck']['criteria']
        return {'bottleneck': {'choice': self.choice}}
    def log(self, *args, **kwargs):
        pass

def test_cache_expiry_strategy_and_rewind():
    async def run():
        model = Model(); memory = {}; state = {'resources': {'minerals': 100}}
        original = copy.deepcopy(state)
        first = await diagnose(state, model, memory, 10, 'explore')
        assert first['answer'] == question()['criteria']['income']
        await diagnose(state, model, memory, 681, 'explore')
        assert model.calls == 1
        await diagnose(state, model, memory, 682, 'explore')
        await diagnose(state, model, memory, 683, 'protect')
        await diagnose(state, model, memory, 0, 'protect')
        assert model.calls == 4
        assert state == original
        assert 'commands' not in first
    asyncio.run(run())

def test_invalid_diagnosis_fails_loudly_without_cache():
    async def run():
        memory = {}
        with pytest.raises(ValueError, match='Invalid bottleneck'):
            await diagnose({}, Model('unlisted'), memory, 0, None)
        assert not memory
    asyncio.run(run())

def test_uncertainty_is_valid_and_criteria_are_not_mutable_globally():
    async def run():
        result = await diagnose({}, Model('none'), {}, 0, None)
        assert result['answer'] == question()['criteria']['none']
        q = question(); q['criteria'].clear()
        assert len(question()['criteria']) == 10
    asyncio.run(run())
