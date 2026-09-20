"""Jev can release a stalled purchase reservation; never cancels engine orders."""
from jev_sc2.jobs import cancel

async def review_stalled(state, view, jev, memory):
    job = memory.get('production_batch', {})
    loop = view['loop']
    strategy = (state.get('strategy_chosen_by_jev') or {}).get('choice')
    if not (job.get('executor') and job.get('armed') and job.get('waiting')
            and job.get('remaining', 0) > 0 and job['loop'] <= loop < job['review_at']
            and job['strategy'] == strategy
            and loop - job['last_request_loop'] >= 224
            and loop >= job.get('reconsider_after', 0)):
        return
    facts = state.get('unit_type_facts', {}).get(job['target_project'], {})
    resources = view.get('resources', {})
    if facts.get('gas_cost') is None or resources.get('vespene') is None:
        return  # Do not manufacture unknown costs.
    summary = {
        'target_project': job['target_project'],
        'per_request_cost': {'minerals': facts.get('mineral_cost'), 'gas': facts['gas_cost']},
        'current_resources': {'minerals': resources.get('minerals'), 'gas': resources['vespene']},
        'gas_shortfall_for_one_request': max(0, facts['gas_cost'] - resources['vespene']),
        'observed_gas_income_per_minute': resources.get('estimated_vespene_per_minute'),
        'loops_since_last_request': loop-job['last_request_loop'],
        'loops_until_existing_deadline': job['review_at']-loop,
        'note': 'Arithmetic from already supplied observations and catalog. Income can change; this is not a forecast or recommendation.'}
    question = {'type': 'choice', 'instructions': 'Review your existing production commitment using current observations. Decide whether to keep its exclusive purchase reservation or release it so you can reconsider purchases. Releasing does not cancel already submitted training orders and does not select a replacement purchase.',
        'criteria': {'keep': 'Keep waiting for the remaining training requests until the existing deadline; no other new purchases may occur during this reservation.',
                     'release': 'Release the remaining unsubmitted training requests and their purchase reservation; reconsider all currently offered purchases at a separate decision.'}}
    answer = (await jev.ask({**state, 'existing_production_commitment': dict(job),
                            'remaining_request_resource_facts': summary},
                           {'commitment_review': question})).get('commitment_review', {})
    choice = answer.get('choice')
    if choice not in question['criteria']:
        raise ValueError('Invalid commitment review: '+str(choice))
    jev.log('stalled_commitment_review', loop=loop, choice=choice, resources=summary)
    if choice == 'release':
        cancel(memory, jev.log, loop, 'Jev released stalled reservation')
    else:
        job['reconsider_after'] = loop + 672
