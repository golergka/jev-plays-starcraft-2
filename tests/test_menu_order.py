from jev_sc2.menu_order import permute_concrete_menus


def test_permutation_keeps_meaning_mapping_and_is_idempotent():
    criteria = {f'option_{i}': f'description {i}' for i in range(20)}
    questions = {'army': {'type': 'choice', 'instructions': 'Choose', 'criteria': criteria}}
    out = permute_concrete_menus(questions, {'army': {}}, '534')
    assert out == questions
    assert list(out['army']['criteria']) != list(criteria)
    again = permute_concrete_menus(out, {'army': {'changed': True}}, '534')
    assert list(again['army']['criteria']) == list(out['army']['criteria'])
    assert list(criteria) == [f'option_{i}' for i in range(20)]


def test_only_identified_concrete_choice_menus_are_changed():
    questions = {
        'investment': {'type': 'choice', 'criteria': {'a': 'A', 'b': 'B'}},
        'army': {'type': 'score', 'criteria': {'a': 'A', 'b': 'B'}},
    }
    assert permute_concrete_menus(questions, {'army': {}}, '534') == questions
    assert permute_concrete_menus(questions, {'investment': {}}, None) is questions
