"""Optional Jev-chosen destination/order families; no tactical selection in code."""
DESCRIPTIONS = {
    'regroup': 'Gather at a chosen friendly unit or structure, using Move or attack-move. Jev chooses the anchor and movement mode next; this does not guarantee a safe route.',
    'attack_move': 'Move to a selected location, engaging enemies encountered along the route.',
    'attack': 'Attack a currently visible enemy unit.',
    'move': 'Move to a selected location without attacking along the route.',
    'hold': 'Hold position instead of moving.',
    'stop': 'Stop current orders.',
    'continue': 'Keep existing orders unchanged.',
    'individual': 'Ask Jev to choose separate individual orders.',
    'support': 'Use an offered support ability with its specified executor.',
    'other': 'Use another offered order.',
}


def family(key):
    if key in ('continue', 'individual'): return key
    if key.startswith(('group_join_', 'group_attack_move_join_')): return 'regroup'
    if key.startswith('support_'): return 'support'
    if 'attack_move' in key: return 'attack_move'
    if key.startswith('group_attack_'): return 'attack'
    if key == 'group_hold_position': return 'hold'
    if key == 'group_stop': return 'stop'
    if key.startswith(('group_move_', 'group_map_move_', 'group_last_known_move_')) or key in ('group_north','group_south','group_east','group_west'): return 'move'
    return 'other'


async def select_families(state, questions, jev):
    groups = {}
    for key, question in questions.items():
        groups[key] = {}
        for option, description in question['criteria'].items():
            groups[key].setdefault(family(option), {})[option] = description
    queries = {key: {**questions[key],
        'instructions': questions[key]['instructions'] + ' First choose the kind of order; its exact target or destination will be chosen separately.',
        'criteria': {kind: DESCRIPTIONS[kind] for kind in kinds}}
        for key, kinds in groups.items() if len(kinds) > 1}
    answers = await jev.ask(state, queries) if queries else {}
    result = {}
    for key, kinds in groups.items():
        chosen = answers.get(key, {}).get('choice') if key in queries else next(iter(kinds))
        if chosen not in kinds:
            raise ValueError(f'Invalid Jev order family for {key}: {chosen!r}')
        result[key] = {**questions[key], 'criteria': kinds[chosen]}
        jev.log('order_family_choice', selection=key, family=chosen,
                original_options=len(questions[key]['criteria']), remaining_options=len(kinds[chosen]))
    return result
