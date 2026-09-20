from player import compact_distance_labels


def test_distance_factoring_retains_options_numbers_and_other_details():
    q={'instructions':'Choose.','criteria':{'a':'Attack point; straight-line distances across selection: 1.2 to 3.4; actual engine route and travel distance unknown','b':'Keep existing order','c':'Move fog snapshot; straight-line distances across selection: 0.0 to 9.9; actual engine route and travel distance unknown'}}
    compact=compact_distance_labels(q)
    assert list(compact['criteria'])==list(q['criteria'])
    assert compact['criteria']['a']=='Attack point; distance_range=[1.2,3.4]'
    assert compact['criteria']['c']=='Move fog snapshot; distance_range=[0.0,9.9]'
    assert compact['criteria']['b']==q['criteria']['b']
    assert 'Actual engine route and travel distance are unknown' in compact['instructions']
    assert compact_distance_labels(compact)==compact
    assert 'straight-line' in q['criteria']['a']


def test_unrecognized_distance_format_is_unchanged():
    q={'criteria':{'a':'distance unknown'}}
    assert compact_distance_labels(q) is q
