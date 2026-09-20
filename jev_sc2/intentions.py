"""Jev-generated, advisory production intentions; never executes purchases."""
def target_questions(state):
    types=sorted({label[6:] for labels in state.get('observed_capabilities_by_type',{}).values()
                  for label in labels if label.startswith('Train ') and label[6:] in (set(state.get('unit_type_facts',{})) | set(state.get('historical_production_type_facts',{})))})
    questions={}
    for index,name in enumerate(types):
        current=state.get('selection_facts',{}).get(name,{}).get('count',0)
        questions[f'target_{index}']={'type':'choice',
            'instructions':f'Choose a production intent for {name} during the next 2016 game loops to help complete the primary mission objective. Currently observed count: {current}. This is a hypothetical goal, not an order. Shared resources and production capacity must be allocated separately across types.',
            'criteria':{
                'expand':f'Increase the number of owned {name} above the current count. Seek additional units of this type when resources and production allow.',
                'replace':f'Maintain the current number of {name}; replace observed losses but do not expand this type above the current count.',
                'stop':f'Do not produce more {name} during this horizon, including replacements. Existing units remain available.'}}

    return questions


async def production_intentions(state, jev, memory, loop, strategy):
    # Losing a producer must not erase previously observed producible types.
    # Historical catalog facts describe prior observations, not current legality.
    known = memory.setdefault('historical_production_type_facts', {})
    for labels in state.get('observed_capabilities_by_type', {}).values():
        for label in labels:
            name = label[6:] if label.startswith('Train ') else None
            if name in state.get('unit_type_facts', {}):
                known[name] = state['unit_type_facts'][name]
    state = {**state, 'historical_production_type_facts': dict(known),
             'historical_production_note': 'Previously observed catalog facts for trainable types; their producers or prerequisites may now be absent. These facts do not establish current production availability. Goals are hypothetical and purchases still use currently offered controls.'}
    questions = target_questions(state)
    if not questions:
        memory.pop('production_intentions', None)
        return None
    # Type changes invalidate cached intentions, but changes in counts do not.
    signature = tuple(q['instructions'].split(' during')[0] for q in questions.values())
    cached = memory.get('production_intentions')
    if not (cached and cached['loop'] <= loop < cached['review_at']
            and cached['strategy'] == strategy and cached['types'] == signature):
        answers = await jev.ask(state, questions)
        goals = []
        for key, question in questions.items():
            choice = answers.get(key, {}).get('choice')
            if choice not in question['criteria']:
                raise ValueError('Invalid production intention: '+str(choice))
            goals.append({'question':question['instructions'], 'chosen_intent':question['criteria'][choice]})
        cached = {'loop':loop, 'review_at':loop+2016, 'strategy':strategy,
                  'types':signature, 'goals':goals}
        memory['production_intentions'] = cached
        jev.log('production_intentions', **cached)
    return {'chosen_at_loop':cached['loop'], 'review_at_loop':cached['review_at'],
            'goals':cached['goals'], 'meaning':'Your previously chosen hypothetical production intentions. Counts in these goals refer to the observation at chosen_at_loop, not necessarily current counts. Goals may compete for shared resources. Select purchases independently; goals do not authorize purchases, eliminate alternatives or prohibit saving.'}
