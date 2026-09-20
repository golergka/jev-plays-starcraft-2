"""Opt-in Jev ratings of order kinds; exact orders remain Jev choices."""
import math
import random

DESCRIPTIONS = {
    'attack': 'Attack a currently visible enemy unit.',
    'attack_move': 'Move to a selected location, engaging enemies encountered along the route.',
    'move': 'Move to a selected location without attacking along the route.',
    'hold': 'Hold position instead of moving.',
    'stop': 'Stop current orders.',
    'continue': 'Keep existing orders unchanged.',
    'individual': 'Ask Jev to choose separate individual orders.',
    'other': 'Use another offered ability or order; its exact choice follows separately.',
}
RATINGS = [
    'Actively undermines progress toward the objective.',
    'Offers little useful progress in the current situation.',
    'Offers some useful progress but limited immediate value.',
    'Offers substantial useful progress in the current situation.',
    'Offers exceptionally important progress toward the objective now.',
]


def order_kind(key):
    if key in ('continue', 'individual'):
        return key
    if not key.startswith('group_'):
        return 'other'
    action = key[6:]
    if 'attack_move' in action:
        return 'attack_move'
    if action.startswith('attack_'):
        return 'attack'
    if action == 'hold_position':
        return 'hold'
    if action == 'stop':
        return 'stop'
    if action in ('north', 'south', 'east', 'west') or action.startswith(
            ('join_', 'map_move_', 'last_known_move_')):
        return 'move'
    return 'other'


async def rate_order_kinds(state, questions, jev, memory):
    """Return narrowed menus, retaining every original option in a rated kind."""
    groups, ratings = {}, {}
    for index, (selection, question) in enumerate(questions.items()):
        grouped = {}
        for key, description in question['criteria'].items():
            grouped.setdefault(order_kind(key), {})[key] = description
        if not grouped:
            raise ValueError('Empty order menu')
        groups[selection] = grouped
        for kind in grouped:
            ratings[f'{index}_{kind}'] = {
                'type': 'score',
                'instructions': question['instructions'] +
                    ' Rate the usefulness of this kind of order now; its exact target or destination would be chosen separately. Order kind: ' + DESCRIPTIONS[kind],
                'criteria': RATINGS,
            }
    responses = await jev.ask(state, ratings)
    if set(responses) != set(ratings):
        raise ValueError('Incomplete Jev order-kind scores')
    narrowed = {}
    for index, (selection, grouped) in enumerate(groups.items()):
        scores = {kind: responses[f'{index}_{kind}'].get('score') for kind in grouped}
        if any(isinstance(v, bool) or not isinstance(v, (int, float)) or
               not math.isfinite(v) or not 0 <= v <= 4 for v in scores.values()):
            raise ValueError('Invalid Jev order-kind scores')
        best = max(scores.values())
        ties = [kind for kind, value in scores.items() if value == best]
        chosen = memory.setdefault('order_score_rng', random.Random(20260920)).choice(ties)
        jev.log('order_kind_scores', selection=selection, scores=scores, choice=chosen,
                option_counts={kind: len(options) for kind, options in grouped.items()},
                interpretation='Descriptive ratings, not calibrated utility; seeded random exact ties.')
        narrowed[selection] = {**questions[selection], 'criteria': grouped[chosen]}
    return narrowed
