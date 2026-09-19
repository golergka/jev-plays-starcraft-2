import pytest
from jev_sc2.galaxy_bridge import rewrite_objective_calls


def test_rewrite_changes_only_calls_and_preserves_script_conditions():
    source = '''// ObjectiveSetState is mentioned in a comment
include "TriggerLibs/NativeLib"
void f () {
    if (ObjectiveGetState(id) == c_objectiveStateFailed) {
        ObjectiveSetState /* comment */ (id, c_objectiveStateCompleted);
        Log("ObjectiveSetState(id, \\\"keep\\\")");
    }
}
'''
    result, counts = rewrite_objective_calls(source)
    assert result == source.replace('ObjectiveGetState(id)', 'JevObjectiveGetState(id)').replace(
        'ObjectiveSetState /* comment */', 'JevObjectiveSetState /* comment */')
    assert counts == {'ObjectiveGetState': 1, 'ObjectiveSetState': 1}


def test_native_declarations_remain_bound_to_engine():
    source = 'native void ObjectiveSetState(int x, int state);\r\nObjectiveSetState(x, state);'
    result, counts = rewrite_objective_calls(source)
    assert result == source.replace('\r\nObjectiveSetState', '\r\nJevObjectiveSetState')
    assert counts == {'ObjectiveSetState': 1}


@pytest.mark.parametrize('source', [
    'void ObjectiveSetState(int a, int b) {}',
    'callback = ObjectiveSetState;',
])
def test_unrecognized_objective_usage_fails_closed(source):
    with pytest.raises(ValueError):
        rewrite_objective_calls(source)


def test_nonobjective_gameplay_and_strings_are_identical():
    source = 'UnitIssueOrder(u, order, false); /* objective */\nLog("ObjectiveGetState");\n'
    assert rewrite_objective_calls(source) == (source, {})
