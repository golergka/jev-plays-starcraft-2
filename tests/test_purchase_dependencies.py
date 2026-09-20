import asyncio
import pytest
from jev_sc2.purchase_dependencies import assess


def test_assessment_preserves_options_and_surfaces_invalid_answer():
    criteria = {'project_0': 'Purchase A', 'project_1': 'Purchase B', 'save': 'Save'}
    class Model:
        invalid = False
        calls = 0
        def log(self, *a, **k): pass
        async def ask(self, state, questions):
            self.calls += 1
            assert set(questions) == {'project_0', 'project_1'}
            return {key: {'choice': 'invalid' if self.invalid else 'complementary'}
                    for key in questions}
    model = Model()
    result = asyncio.run(assess({}, criteria, model, 10))
    assert set(result['assessments']) == {'project_0', 'project_1'}
    assert criteria == {'project_0': 'Purchase A', 'project_1': 'Purchase B', 'save': 'Save'}
    model.invalid = True
    with pytest.raises(ValueError):
        asyncio.run(assess({}, criteria, model, 11))
    assert asyncio.run(assess({}, {'save': 'Save'}, model, 12)) is None
    assert model.calls == 2
