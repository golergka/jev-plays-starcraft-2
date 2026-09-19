"""Execute only a previously accepted, explicitly bounded Jev production job."""

def cancel(memory, log, loop, reason):
    job = memory.pop('production_batch', None)
    if job:
        log('production_job_released', current_loop=loop, reason=reason, job=job)


def next_request(view, memory, log):
    job = memory.get('production_batch', {})
    if not job.get('executor') or not job.get('armed'):
        return []
    loop = view['loop']
    reason = ('loop rewound' if loop < job['loop'] else
              'deadline reached' if loop >= job['review_at'] else
              'strategy changed' if job['strategy'] != memory.get('strategy', {}).get('choice') else
              'completed request allowance' if job['remaining'] <= 0 else None)
    unit = next((u for u in view['self'] if u['tag'] == job['command']['unit_tag']), None)
    if reason or unit is None:
        cancel(memory, log, loop, reason or 'selected producer no longer observed')
        return []
    if loop - job['last_request_loop'] < 112:
        return []
    candidate = next((c for c in unit['candidates'] if c['command'] == job['command']
                      and c['description'].startswith('Train ')
                      and (c.get('project') or {}).get('type') == job['target_project']), None)
    resources = view.get('resources', {})
    costs = (candidate or {}).get('resource_cost')
    affordable = costs is not None and all(costs.get(k, 0) <= resources.get(v, 0)
        for k, v in [('minerals','minerals'), ('vespene','vespene'), ('supply','supply_remaining')])
    if not candidate or not affordable:
        if not job.get('waiting'):
            log('production_job_wait', loop=loop, reason='exact selected command unavailable or unaffordable', job=job.copy())
        job['waiting'] = True
        return []
    job['waiting'] = False
    job['remaining'] -= 1
    job['last_request_loop'] = loop
    log('production_job_request', loop=loop, remaining_attempts=job['remaining'], command=job['command'])
    return [dict(job['command'])]


def acknowledge_initial(memory, actions, results, loop, log):
    job = memory.get('production_batch', {})
    if not job.get('executor') or job.get('armed'):
        return
    command = job['command']
    accepted = any(result == 1 and list(action.action_raw.unit_command.unit_tags) == [command['unit_tag']]
                   and action.action_raw.unit_command.ability_id == command['ability_id']
                   for action, result in zip(actions, results))
    if accepted:
        job['armed'] = True
        log('production_job_armed', loop=loop, job=job.copy())
    else:
        cancel(memory, log, loop, 'initial request not accepted; no background execution')
