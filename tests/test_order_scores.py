import asyncio
import pytest
from jev_sc2.order_scores import order_kind, rate_order_kinds


@pytest.mark.parametrize('key,kind', [
    ('group_attack_123','attack'), ('group_map_attack_move_north_west','attack_move'),
    ('group_last_known_attack_move_1','attack_move'), ('group_join_1','move'),
    ('group_north','move'), ('group_last_known_move_1','move'),
    ('group_hold_position','hold'), ('group_stop','stop'),
    ('continue','continue'), ('individual','individual'),
    ('support_123','other'), ('group_ability_123','other'),
])
def test_kinds(key, kind):
    assert order_kind(key) == kind


class Model:
    def __init__(self, bad=None):
        self.bad = bad
        self.events = []
    async def ask(self, state, questions):
        self.questions = questions
        result = {k: {'score': 3 if k.endswith('_move') else 1} for k in questions}
        if self.bad == 'missing':
            result.pop(next(iter(result)))
        elif self.bad is not None:
            result[next(iter(result))]['score'] = self.bad
        return result
    def log(self, event, **fields):
        self.events.append(fields)


def menus():
    return {'Marine': {'type':'choice','instructions':'Choose for Marine.', 'criteria': {
        'group_join_1':'Move to ally one', 'group_join_2':'Move to ally two',
        'group_hold_position':'Hold here', 'support_123':'Use an ability', 'continue':'Keep orders'}}}


def test_all_options_accounted_and_exact_targets_still_offered():
    model = Model()
    result = asyncio.run(rate_order_kinds({}, menus(), model, {}))
    assert set(result['Marine']['criteria']) == {'group_join_1','group_join_2'}
    assert sum(model.events[0]['option_counts'].values()) == 5
    assert set(model.questions) == {'0_move','0_hold','0_other','0_continue'}


@pytest.mark.parametrize('bad', ['missing', True, float('nan'), float('inf'), -1, 5, '3'])
def test_invalid_scores_are_loud(bad):
    with pytest.raises(ValueError):
        asyncio.run(rate_order_kinds({}, menus(), Model(bad), {}))
