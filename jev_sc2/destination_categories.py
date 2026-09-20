"""Optional Jev-chosen destination/order families; no tactical selection in code."""
DESCRIPTIONS = {
    'sector': 'A map-sector destination. Distance and observed terrain vary; this is not necessarily an objective location or safe route.',
    'remembered': 'A last-known entity location under fog; current presence is unknown.',
    'local': 'A six-map-unit cardinal step from each unit position; terrain and nearby threats still matter.',
    'visible': 'A currently visible entity or its observed location; affiliation, distance and utility vary.',
    'other': 'Another originally offered order.',
}


def category(key):
    if key.startswith('group_map_'): return 'sector'
    if key.startswith('group_last_known_'): return 'remembered'
    if key in {'group_'+d for d in ('north','south','east','west')} | {'group_attack_move_'+d for d in ('north','south','east','west')}: return 'local'
    if key.startswith(('group_move_', 'group_attack_move_')): return 'visible'
    return 'other'


async def select_categories(state, questions, jev):
    groups = {}
    for key, question in questions.items():
        groups[key] = {}
        for option, description in question['criteria'].items():
            groups[key].setdefault(category(option), {})[option] = description
    queries = {key: {**questions[key],
        'instructions': questions[key]['instructions'] + ' First choose which kind of destination to use; the exact original destination will be selected next.',
        'criteria': {kind: DESCRIPTIONS[kind] for kind in kinds}}
        for key, kinds in groups.items() if len(kinds) > 1}
    answers = await jev.ask(state, queries) if queries else {}
    result = {}
    for key, kinds in groups.items():
        chosen = answers.get(key, {}).get('choice') if key in queries else next(iter(kinds))
        if chosen not in kinds:
            raise ValueError(f'Invalid Jev destination category for {key}: {chosen!r}')
        result[key] = {**questions[key], 'criteria': kinds[chosen]}
        jev.log('destination_category_choice', selection=key, category=chosen,
                original_options=len(questions[key]['criteria']), remaining_options=len(kinds[chosen]))
    return result
