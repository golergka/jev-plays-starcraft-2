"""Jev-selected advisory diagnosis; never filters or authorizes purchases."""
CRITERIA = {
            'income': 'Insufficient resource income limits progress.',
            'ground_combat': 'Insufficient capability to overcome ground enemies limits progress.',
            'air_combat': 'Insufficient capability to overcome flying enemies limits progress.',
            'survival': 'Inability to keep threatened owned units or structures alive limits progress.',
            'production': 'Insufficient production facilities or prerequisites limits progress.',
            'supply': 'Insufficient supply capacity limits progress.',
            'coordination': 'Positioning, movement or coordination of existing units limits progress.',
            'information': 'Insufficient information about the map or objective limits progress.',
            'interaction': 'An objective interaction or ability use limits progress.',
            'none': 'No single limiting capability can be identified from the observations.'}


def question():
    return {'type': 'choice', 'instructions': 'Identify the most important current bottleneck preventing progress toward the primary mission objective. Diagnose from the observations, not from a preferred action. A diagnosis does not authorize an action or require a purchase.', 'criteria': dict(CRITERIA)}


async def diagnose(state, jev, memory, loop, strategy):
    cached = memory.get('bottleneck_diagnosis')
    if not (cached and cached['loop'] <= loop < cached['review_at']
            and cached['strategy'] == strategy):
        q = question()
        answer = (await jev.ask(state, {'bottleneck': q})).get('bottleneck', {})
        choice = answer.get('choice')
        if choice not in CRITERIA:
            raise ValueError('Invalid bottleneck diagnosis: ' + str(choice))
        cached = {'loop': loop, 'review_at': loop + 672, 'strategy': strategy,
                  'choice': choice, 'description': CRITERIA[choice]}
        memory['bottleneck_diagnosis'] = cached
        jev.log('bottleneck_diagnosis', **cached)
    return {'answer': cached['description'], 'chosen_at_loop': cached['loop'],
            'review_at_loop': cached['review_at'],
            'meaning': 'Your diagnosis of the current bottleneck. Consider whether a purchase would address it. All purchases and saving remain available; this does not authorize or require any purchase.'}
