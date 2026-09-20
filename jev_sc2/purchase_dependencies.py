"""Advisory Jev dependency assessment, without purchase filtering."""
CRITERIA={
 'self_contained':'After completion, the purchased entity can supply a relevant capability using its own abilities and existing resources; no additional unit purchase or passenger loading is needed. Ordinary orders may still be needed.',
 'complementary':'The relevant capability depends on additional unit production, passenger loading, or another complementary entity/action beyond ordinary use of this purchased entity.',
 'unclear':'The supplied facts do not establish the relevant dependency.'}

async def assess(state, criteria, jev, loop):
    options = {k: v for k, v in criteria.items() if k.startswith('project_')}
    if not options:
        return None
    questions = {k: {'type': 'choice', 'instructions':
        'Classify the dependency of this purchase for addressing the current mission situation and your stated bottleneck. This is a factual assessment, not a purchase recommendation. Purchase: ' + v,
        'criteria': dict(CRITERIA)} for k, v in options.items()}
    answers = await jev.ask(state, questions)
    for key in options:
        if answers.get(key, {}).get('choice') not in CRITERIA:
            raise ValueError('Invalid purchase dependency assessment: ' + key)
    jev.log('purchase_dependencies', loop=loop, answers=answers, options=options)
    return {'assessments': {k: {'purchase': v,
        'assessment': CRITERIA[answers[k]['choice']]} for k, v in options.items()},
        'meaning': 'Your dependency assessment; not a usefulness ranking. Complementary purchases may be valuable. All original options remain available.'}
