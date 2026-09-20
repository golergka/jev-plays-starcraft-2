"""Live-reloaded experiment policy. All action choices come from Jev.

Contract: async decide(view: dict, jev, memory: dict) -> list[command dict].
The harness owns sockets, action validation, telemetry, and persistent memory.
Commit this file to activate it at the next decision boundary.
"""
import json
import os
import asyncio
from jev_sc2.concurrency import gather_owned
from openrouter.errors import PaymentRequiredResponseError, BadRequestResponseError
import math
import random
import re
from collections import Counter
from jev_sc2.cadence import measured_cadence


def recent_outcomes(view, memory, window=672):
    """Measured observation history; disappearing units are not assumed dead."""
    loop = view['loop']
    history = memory.setdefault('outcome_history', [])
    if history and loop < history[-1]['loop']:
        history.clear()
        memory.pop('cumulative_outcomes', None)
    current = {'loop':loop, 'resources':dict(view.get('resources', {})),
               'resource_counters':{k:v for k,v in view.get('player_score_telemetry',{}).items()
                   if k in ('collected_minerals','collected_vespene','spent_minerals','spent_vespene')},
               'units':{str(u['tag']):{'type':u['type'], 'health':u.get('health',0),
                                     'position':u.get('position'), 'build_progress':u.get('build_progress'),
                                     'orders':u.get('orders', [])}
                        for u in view['self']}}
    cumulative = memory.setdefault('cumulative_outcomes', {
        'since_loop': history[0]['loop'] if history else loop,
        'through_loop': history[0]['loop'] if history else loop,
        'appeared_by_type': {}, 'disappeared_by_type': {},
    })
    # Seed from retained history on hot reload, then count each transition once.
    # This deliberately does not reconstruct observations we no longer retain.
    for before, after in zip(history, history[1:] + [current]):
        if after['loop'] <= cumulative['through_loop']:
            continue
        a, b = before['units'], after['units']
        for field, tags, units in (
            ('appeared_by_type', b.keys()-a.keys(), b),
            ('disappeared_by_type', a.keys()-b.keys(), a),
        ):
            counts = Counter(cumulative[field])
            counts.update(units[tag]['type'] for tag in tags)
            cumulative[field] = dict(counts)
        cumulative['through_loop'] = after['loop']
    if not history or history[-1]['loop'] != loop:
        history.append(current)
    while len(history)>1 and history[1]['loop'] < loop-window:
        history.pop(0)
    appeared, disappeared, damage = Counter(), Counter(), Counter()
    completions = Counter()
    for before,after in zip(history,history[1:]):
        a,b = before['units'],after['units']
        appeared.update(b[t]['type'] for t in b.keys()-a.keys())
        disappeared.update(a[t]['type'] for t in a.keys()-b.keys())
        for t in a.keys() & b.keys():
            damage[b[t]['type']] += max(0,a[t]['health']-b[t]['health'])
            old_progress,new_progress = a[t].get('build_progress'),b[t].get('build_progress')
            if old_progress is not None and new_progress is not None and old_progress < 1 <= new_progress:
                completions[b[t]['type']] += 1
    movement = {}
    continuous = set.intersection(*(set(h['units']) for h in history))
    for tag in continuous:
        samples = [h['units'][tag] for h in history]
        if len(samples) < 2 or any(u.get('position') is None for u in samples):
            continue
        kind = samples[-1]['type']
        item = movement.setdefault(kind, {'units_observed_throughout_window':0,
            'mean_net_displacement':0, 'mean_sampled_distance_travelled':0})
        item['units_observed_throughout_window'] += 1
        item['mean_net_displacement'] += math.dist(samples[0]['position'],samples[-1]['position'])
        item['mean_sampled_distance_travelled'] += sum(math.dist(a['position'],b['position'])
            for a,b in zip(samples,samples[1:]))
    for item in movement.values():
        for key in ('mean_net_displacement','mean_sampled_distance_travelled'):
            item[key] = round(item[key]/item['units_observed_throughout_window'],1)
    point_order_progress = []
    for tag, unit in sorted(current['units'].items()):
        orders = unit.get('orders', [])
        if len(orders) != 1 or orders[0].get('target_point') is None:
            continue
        first = orders[0]
        comparable = []
        for entry in reversed(history):
            previous = entry['units'].get(tag)
            if previous is None or previous.get('position') is None:
                break
            previous_orders = previous.get('orders', [])
            if (len(previous_orders) != 1 or
                previous_orders[0].get('ability') != first.get('ability') or
                previous_orders[0].get('target_point') != first['target_point']):
                break
            comparable.append(entry)
        if len(comparable) < 2:
            continue
        comparable.reverse()
        samples = [entry['units'][tag] for entry in comparable]
        target = first['target_point']
        before = math.dist(samples[0]['position'], target)
        after = math.dist(samples[-1]['position'], target)
        point_order_progress.append({'tag':tag, 'type':samples[-1]['type'],
            'ability':first.get('ability'), 'target_point':target,
            'observed_loops':loop-comparable[0]['loop'],
            'initial_straight_line_distance':round(before,1),
            'current_straight_line_distance':round(after,1),
            'distance_reduction':round(before-after,1)})
    unfinished = []
    for tag,unit in current['units'].items():
        progress = unit.get('build_progress')
        if progress is None or progress >= 1:
            continue
        samples = []
        for entry in reversed(history):
            previous = entry['units'].get(tag)
            if previous is None or previous.get('build_progress') is None:
                break
            samples.append((entry['loop'],previous['build_progress']))
        oldest_loop,oldest_progress = samples[-1]
        unfinished.append({'tag':tag,'type':unit['type'],'progress':round(progress,3),
            'observed_loops':loop-oldest_loop,'progress_change':round(progress-oldest_progress,3)})
    current_presence = []
    for tag, unit in sorted(current['units'].items()):
        since = loop
        observations = 0
        for entry in reversed(history):
            if tag not in entry['units']:
                break
            since = entry['loop']
            observations += 1
        current_presence.append({'tag':tag, 'type':unit['type'],
            'continuously_observed_since_loop':since,
            'observed_span_loops':loop-since, 'observation_count':observations})
    old_counters = history[0].get('resource_counters', {})
    counter_changes = {k:v-old_counters[k] for k,v in current['resource_counters'].items()
                       if k in old_counters and v >= old_counters[k]}
    return {'observed_game_loops':loop-history[0]['loop'],
            'resource_counter_changes':counter_changes,
            'resource_counter_interpretation':'Own API collection/spending counter deltas over this observation window; missing or reset counters are omitted. These do not attribute spending to repairs or purchases, and may differ from net balances due to refunds or mission effects.',
            'cumulative_observed_unit_changes': {
                **cumulative,
                'interpretation': 'Counts of observed appearances and disappearances since since_loop, not kills or production totals. Loading, unloading, morphing and mission triggers can change presence. Earlier unretained history is unknown.',
            },
            'completed_from_observed_incomplete_by_type':dict(completions),
            'currently_incomplete_projects':unfinished,
            'construction_interpretation':'Only observed progress transitions count as completion. Newly appearing completed units are not attributed to construction. No progress over a short interval does not establish abandonment.',
            'unchanged_point_order_progress':point_order_progress,
            'point_order_interpretation':'Same sole point order across the latest consecutive comparable observations, not proof of uninterrupted execution. Positive distance reduction means closer to its destination. Straight-line distance is not route distance; necessary detours or combat can increase it. Missing entries mean insufficient comparable observations, not zero progress.',
            'current_unit_observation_spans':current_presence,
            'presence_interpretation':'Continuity in retained observations only, not unit age, birth time or survival prediction. An absent observation breaks the span; loading or visibility changes can cause absence. A replacement can have the same type and leave group size unchanged.',
            'movement_by_type':movement,
            'movement_interpretation':'Map units over the observed window, only units present at every sample. Sampled travel is a lower bound; net displacement can be zero after useful round trips. Neither measure alone indicates success or failure.',
            'own_units_appeared_by_type':dict(appeared),
            'own_units_disappeared_by_type':dict(disappeared),
            'health_decreases_on_continuously_observed_units':dict(damage),
            'resource_changes':{k:current['resources'].get(k,0)-history[0]['resources'].get(k,0)
                                for k in ('minerals','vespene','food_used','food_cap')},
            'interpretation':'Measured changes, not causal attribution. Disappearance can be death, transport loading, morphing or campaign triggers. Resource changes are net of income and spending. Consider whether your previous choices are producing mission progress.'}


def describe_action_feedback(view, memory):
    """Join numeric engine rejections to observed control names, not advice."""
    # A new cache avoids carrying target-specific labels through a hot reload.
    labels = memory.setdefault('observed_control_labels',{})
    types = {u['tag']:u['type'] for u in view['self']}
    for unit in view['self']:
        for candidate in unit.get('candidates',[]):
            ability = candidate['command'].get('ability_id')
            if ability is not None:
                project = candidate.get('project',{})
                labels[ability] = (candidate.get('capability_description') or
                    (f'Purchase {project["type"]}' if project.get('type') else
                     f'Observed ability {ability}; target attribution unavailable'))
    history = []
    entries = {}
    delayed = [e for e in memory.get('engine_action_feedback',[])
               if e['loop'] <= view.get('loop',e['loop']) and
               ('surfaced_loop' not in e or 0 <= view.get('loop',e['loop'])-e['surfaced_loop'] <= 672)]
    for entry in delayed:
        entry.setdefault('surfaced_loop',view.get('loop',entry['loop']))
    for entry in memory.get('action_feedback',[]) + delayed:
        merged = entries.setdefault(entry['loop'], {**entry, 'failures':[], 'note':''})
        if 'surfaced_loop' in entry:
            merged['surfaced_loop'] = entry['surfaced_loop']
        merged['failures'].extend(entry.get('failures',[]))
        merged['note'] += entry.get('note','') + ' '
    for entry in entries.values():
        grouped = {}
        for failure in entry.get('failures',[]):
            key = (failure['ability_id'],failure['result'])
            item = grouped.setdefault(key,{'ability_id':key[0],
                'action':labels.get(key[0],f'Unknown observed ability {key[0]}'),
                'result':key[1],'rejected_commands':0,'unit_types':{}})
            item['rejected_commands'] += 1
            for tag in failure.get('unit_tags',[]):
                kind = types.get(tag,'no longer in current observation')
                item['unit_types'][kind] = item['unit_types'].get(kind,0)+1
        history.append({**entry,'failures':list(grouped.values())})
    # Keep rejection evidence beyond a contribution commitment, without replaying
    # the same harness entry every tick or treating old failures as current rules.
    loop = view.get('loop', max((e['loop'] for e in history), default=0))
    retained = memory.setdefault('retained_action_failures', {})
    if loop < memory.get('feedback_last_loop', loop):
        retained.clear()
    memory['feedback_last_loop'] = loop
    for entry in history:
        if entry['failures']:
            retained[entry['loop']] = entry
    retained = {k:v for k,v in retained.items() if 0 <= loop-v.get('surfaced_loop',k) <= 672}
    retained = dict(sorted(retained.items())[-32:])
    memory['retained_action_failures'] = retained
    combined = {**retained, **{e['loop']:e for e in history}}
    for entry in combined.values():
        for failure in entry['failures']:
            ability = failure['ability_id']
            failure['action'] = labels.get(ability,f'Unknown observed ability {ability}')
    return [combined[k] for k in sorted(combined)]


def compact_distance_labels(question):
    """Factor repeated distance semantics without dropping choices or values."""
    pattern = r'; straight-line distances across selection: ([0-9.]+) to ([0-9.]+); actual engine route and travel distance unknown'
    changed = False
    criteria = {}
    for key, description in question.get('criteria', {}).items():
        value, count = re.subn(pattern, r'; distance_range=[\1,\2]', description)
        changed = changed or bool(count)
        criteria[key] = value
    if not changed:
        return question
    return {**question, 'criteria': criteria, 'instructions': question.get('instructions', '') +
            '\nFor every option, distance_range=[minimum,maximum] gives straight-line distances across the selection. Actual engine route and travel distance are unknown.'}


async def ask_order_menus(state, questions, jev, *, full_first=True):
    """Try whole menus; use Jev-selected finalists only after a size rejection."""
    questions = {key:compact_distance_labels(q) for key,q in questions.items()}
    small, large = {}, {}
    for key, question in questions.items():
        criteria = question.get('criteria', {})
        destination = large if len(criteria) > 2 and len(json.dumps(question)) > 16000 else small
        destination[key] = question

    async def tournament(key, question):
        items = list(question['criteria'].items())
        middle = len(items)//2
        parts = [{**question, 'criteria': dict(items[:middle])},
                 {**question, 'criteria': dict(items[middle:])}]
        answers = await gather_owned(*(ask_order_menus(state, {key:part}, jev, full_first=False) for part in parts))
        winners = []
        for part, answer in zip(parts, answers):
            choice = answer.get(key, {}).get('choice')
            if choice not in part['criteria']:
                raise ValueError('Jev returned an invalid order-menu finalist')
            winners.append(choice)
        jev.log('order_menu_tournament', question=key, options=len(items), finalists=winners,
                interpretation='Final probabilities apply only to Jev-selected finalists, not the original full menu.')
        return await jev.ask(state, {key:{**question,
            'criteria':{choice:question['criteria'][choice] for choice in winners}}})

    async def large_menu(key, question):
        if full_first:
            try:
                return await jev.ask(state, {key:question})
            except BadRequestResponseError as exc:
                if 'max_tokens_exceeded' not in str(exc):
                    raise
                jev.log('order_menu_size_fallback', question=key,
                        options=len(question['criteria']))
        return await tournament(key, question)

    calls = ([jev.ask(state, small)] if small else [])
    calls.extend(large_menu(key, question) for key, question in large.items())
    answers = await gather_owned(*calls)
    return {key:value for answer in answers for key,value in answer.items()}


def sample_concrete_answer(answer, criteria, rng):
    weights = answer.get('probabilities', {})
    if not weights or any(k not in criteria or not isinstance(v, (int, float))
                          or not math.isfinite(v) or v < 0 for k, v in weights.items()):
        raise ValueError('Invalid concrete-order probability distribution')
    keys = sorted(weights)
    if sum(weights.values()) <= 0:
        raise ValueError('Empty concrete-order probability mass')
    return {**answer, 'choice': rng.choices(keys, weights=[weights[k] for k in keys], k=1)[0]}


async def choose_with_opaque_keys(state, questions, jev, selections):
    """Reversible presentation experiment; no action filtering or ranking."""
    if os.getenv('JEV_CONCRETE_MENU_SEED'):
        raise ValueError('Opaque-key experiment requires JEV_CONCRETE_MENU_SEED unset to preserve menu order')
    mappings = {name:{f'option_{i:03d}':key for i,key in enumerate(q['criteria'])}
                for name,q in questions.items() if name in selections}
    encoded = {name:({**q, 'criteria':{alias:q['criteria'][key]
                     for alias,key in mappings[name].items()}} if name in mappings else q)
               for name,q in questions.items()}
    answers = await choose_concrete_orders(state, encoded, jev)
    for name,mapping in mappings.items():
        if name not in answers:
            raise ValueError(f'Missing opaque answer for {name}')
        answer = answers[name]
        if answer.get('choice') not in mapping or any(k not in mapping for k in answer.get('probabilities',{})):
            raise ValueError(f'Unknown opaque action identifier for {name}')
        answers[name] = {**answer, 'choice':mapping[answer['choice']],
                        'probabilities':{mapping[k]:v for k,v in answer.get('probabilities',{}).items()}}
        jev.log('opaque_order_decode', selection=name, choice=answers[name]['choice'], mapping=mapping)
    return answers


async def choose_concrete_orders(state, questions, jev):
    """Jev chooses resource kind before location when both kinds are offered."""
    # Concrete questions name their selections exactly. Other selections retain
    # their raw unit observations and mechanics, but no repeated type aggregate.
    state = {**{k:v for k,v in state.items() if k != 'type_selection_facts'}, 'selection_facts': {
        name:facts for name,facts in state.get('selection_facts',{}).items()
        if name in questions}}
    first = dict(questions)
    resources = {}
    for key, question in questions.items():
        criteria = question['criteria']
        groups = {resource:{option:description for option,description in criteria.items()
                           if phrase in description}
                  for resource,phrase in [('minerals','Gather minerals'),('vespene','Gather vespene gas')]}
        if not all(groups.values()) or any(option != 'continue' and not any(option in g for g in groups.values()) for option in criteria):
            continue
        resources[key] = groups
        first[key] = {**question,'criteria':{
            'gather_minerals':'Gather minerals using one of the offered mineral-field targets; a later choice selects the field.',
            'gather_vespene':'Gather vespene gas using one of the offered gas targets; a later choice selects the target.',
            'continue':'Keep existing orders unchanged.'}}
    answers = await ask_order_menus(state, first, jev)
    targets = {}
    for key, groups in resources.items():
        choice = answers.get(key,{}).get('choice')
        resource = {'gather_minerals':'minerals','gather_vespene':'vespene'}.get(choice)
        jev.log('resource_category_choice',selection=key,choice=choice)
        if resource:
            targets[key] = {**questions[key],'criteria':{**groups[resource],
                'continue':'Keep existing orders unchanged.'}}
            answers[key] = {'choice':'continue'}
        elif choice != 'continue':
            answers[key] = {'choice':'continue'}
    if targets:
        answers.update(await ask_order_menus(state, targets, jev))
    return answers


def is_purchase(candidate):
    return candidate['description'].startswith(('Train ', 'Build ', 'Research '))


def investment_state(state):
    """Keep economic/force facts; raw terrain and repeated unit coordinates distract."""
    compact = {k:state[k] for k in ('objective','game_loop','mission_context','resources','completed_upgrades','selection_facts',
               'unit_type_facts','harvesting_assignments','recent_outcomes','recent_action_feedback','observed_capabilities_by_type','previous_investment_intent',
               'strategy_chosen_by_jev','production_commitment') if k in state}
    for source,target in [('visible_entities','visible_entities_by_alliance_and_type'),
                          ('last_known_entities','stale_entities_by_alliance_and_type')]:
        compact[target] = dict(Counter(e['alliance']+' '+e['type'] for e in (state.get(source) or [])))
    compact['selection_facts'] = state.get('type_selection_facts',state.get('selection_facts',{}))
    return compact


def presentation_coordinates(value, field=None):
    """Two-decimal spatial context; command tables retain engine precision."""
    if isinstance(value, dict):
        return {key:presentation_coordinates(item, key) for key,item in value.items()}
    if isinstance(value, list):
        if field in {'position', 'center', 'target_world_space_pos'}:
            return [round(item, 2) if isinstance(item, float) else item for item in value]
        return [presentation_coordinates(item) for item in value]
    return value


def order_state(state):
    """Avoid repeating type capabilities in every job selection's context."""
    compact = presentation_coordinates(state)
    # A columnar roster preserves every field while avoiding the same keys once
    # per unit. This matters when large economies exceed Jev's context window.
    for field, noun in (('units','unit'),('visible_entities','visible entity'),
                        ('last_known_entities','stale entity')):
        items = compact.get(field)
        if (isinstance(items,list) and items and all(isinstance(item,dict) for item in items)
                and all(item.keys()==items[0].keys() for item in items)):
            columns = list(items[0])
            compact[field] = {
                'encoding': f'Each row is one {noun}; values correspond to columns in order.',
                'columns':columns,
                'rows':[[item[key] for key in columns] for item in items],
            }
    for field in ('type_selection_facts','unit_type_facts'):
        mapping = compact.get(field)
        if isinstance(mapping,dict) and len(mapping)>1 and all(isinstance(v,dict) for v in mapping.values()):
            values=list(mapping.values())
            if all(value.keys()==values[0].keys() for value in values):
                columns=list(values[0])
                compact[field]={'encoding':'Each row begins with its type name, followed by values in column order.',
                    'columns':['type_name']+columns,
                    'rows':[[name]+[value[key] for key in columns] for name,value in mapping.items()]}
    repeated = {'available_projects', 'available_support_abilities', 'available_build_abilities'}
    compact['selection_facts'] = {name:{k:v for k,v in facts.items() if k not in repeated}
                                  for name,facts in compact.get('selection_facts',{}).items()}
    # Type-level facts retain the capability lists; concrete criteria name the
    # actual legal actions for each selection. Positions/orders remain intact.
    return compact


def control_state(state):
    compact = investment_state(state)
    compact['selection_facts'] = state.get('selection_facts',{})
    compact['type_selection_facts'] = state.get('type_selection_facts',{})
    return order_state(compact)


def investment_description(name, project, state):
    if project and project.get('kind') == 'upgrade':
        return (f"Research upgrade {name.removeprefix('Research ')}. Costs {project['minerals']} minerals and {project['vespene']} gas; "
                f"catalog research time {project['research_time']}. Produces an upgrade, not an additional unit. "
                'The API provides its name but no detailed effect description; do not assume unlisted effects.')
    facts = state.get('type_selection_facts',state.get('selection_facts',{})).get(name,{})
    capabilities = state.get('observed_capabilities_by_type',{}).get(name,[])
    effects = []
    if capabilities:
        effects.append('Adds another unit able to: '+', '.join(capabilities))
    else:
        effects.append('Its action capabilities have not yet been observed')
    if project and project.get('allows_vespene_harvesting'):
        effects.append('Enables workers to harvest gas from this site after construction')
    if project and project.get('catalog_tech_requirement_for'):
        effects.append('Satisfies a catalog technology prerequisite for '+
                       ', '.join(d['unit']+(' (requires attached addon)' if d['requires_attached'] else '')
                                 for d in project['catalog_tech_requirement_for'])+
                       '; other requirements and an appropriate producer may still be needed; this does not guarantee current trainability')
    if project and project.get('supply_provided',0):
        effects.append(f'Adds {project["supply_provided"]:g} supply capacity when complete')
    occupied = facts.get('cargo_slots_used', 0)
    available = facts.get('cargo_slots_available', 0)
    if occupied or available:
        effects.append(f'Existing owned {name} cargo: {occupied} slots occupied, {available} available; '
                       f'passengers by type: {facts.get("passengers_by_type", {})}. '
                       'This purchase does not issue loading commands; loading is a separate decision')
    type_facts = (state.get('unit_type_facts') or {}).get(name,{})
    weapons = type_facts.get('catalog_weapons',[])
    if weapons:
        effects.append('Has weapons: '+', '.join(f'{w["targets"]} targets at range {w["range"]}' for w in weapons))
    elif 'catalog_weapons' in type_facts:
        effects.append('No weapons listed in the unit catalog. Attack-order controls do not establish weapon damage; separate abilities or passengers may have other effects')
    return (f'Purchase one {name}. '+'. '.join(effects)+'. '
            f'Cost/effects: {project}. Already owned: {facts.get("count",0)}; '
            f'idle: {facts.get("idle_count",0)}; current orders: {facts.get("current_order_counts",{})}.')


def investment_sampling_probabilities(weights):
    """Normalize Jev's positive legal weights without changing relative odds."""
    largest = max(weights.values())
    scaled = {key:value/largest for key,value in weights.items()}
    total = sum(scaled.values())
    return {key:value/total for key,value in scaled.items()}


async def score_investment_options(state, criteria, jev, memory, loop):
    questions = {key:{'type':'score',
        'instructions':'Rate how useful this specific action is for completing the stated mission objective in the current observed situation. Account for costs, existing forces, current queues and known threats. Evaluate the action itself, including waiting when offered. Action: '+description,
        'criteria':['Actively undermines progress toward the objective.',
                    'Offers little useful progress in the current situation.',
                    'Offers some useful progress but limited immediate value.',
                    'Offers substantial useful progress in the current situation.',
                    'Offers exceptionally important progress toward the objective now.']}
        for key,description in criteria.items()}
    answers = await jev.ask(state, questions)
    scores = {key:answers.get(key,{}).get('score') for key in criteria}
    if any(isinstance(v,bool) or not isinstance(v,(int,float)) or
           not math.isfinite(v) or not 0 <= v <= 4 for v in scores.values()):
        raise ValueError('Incomplete or invalid Jev investment scores')
    best = max(scores.values())
    ties = [key for key,value in scores.items() if value == best]
    choice = memory.setdefault('investment_score_rng',random.Random(20260920)).choice(ties)
    jev.log('investment_scores',loop=loop,scores=scores,choice=choice,
            interpretation='Ranked descriptive ratings, not calibrated utility or win probabilities.')
    return choice


async def choose_investment(view, state, jev, memory=None):
    """Jev allocates the common budget, then selects the actual producer/site."""
    projects = {}
    for unit in view['self']:
        for candidate in unit['candidates']:
            if is_purchase(candidate):
                name = (candidate.get('project') or {}).get('type') or candidate['description'].split(';')[0]
                projects.setdefault(name, []).append((unit, candidate))
    potential = {p['type']:p for p in view.get('potential_projects',[])}
    if not projects and not potential:
        return []
    names = sorted(projects)
    criteria = {'save':'Make no new purchase at this review. Requests no new unit, structure or upgrade. Does not change existing orders or stop repairs; ongoing repairs may continue spending minerals.'}
    for i,name in enumerate(names):
        example = projects[name][0][1]
        criteria[f'project_{i}'] = investment_description(name,example.get('project'),state)
        if memory is not None and example['description'].startswith('Train '):
            criteria[f'batch_{i}'] = (f'Commit to up to three training requests for {name} over 2016 game loops, '
                'using currently executable controls and choosing the producer separately. No other new unit, structure or upgrade purchase is allowed while this batch is active, including while waiting for resources or an available training control. This exclusive purchase reservation ends when the batch finishes, expires, or your strategic priority changes. Repairs can still spend minerals while the batch is active. '
                'Each request costs the listed per-unit resources; rejected or stale requests still consume one attempt. '
                +investment_description(name,example.get('project'),state))
            if memory.get('stalled_commitment_review_enabled'):
                criteria[f'batch_{i}'] += ' You may also explicitly release a stalled reservation at a later model review, after at least 224 loops without a request; keeping it delays another such review by 672 loops.'
            if memory.get('production_executor_enabled'):
                criteria[f'batch_{i}'] += ' The producer selected for the first request stays fixed; after acceptance, remaining requests execute automatically between model reviews, at least 112 loops apart, only while affordable and available. No replacement producer is selected.'
    future_names = sorted(set(potential)-set(projects))
    for i,name in enumerate(future_names):
        project = potential[name]
        resources = view.get('resources',{})
        shortfall = {k:max(0,project[k]-resources.get(r,0)) for k,r in
                     [('minerals','minerals'),('vespene','vespene'),('supply','supply_remaining')]}
        criteria[f'save_for_{i}'] = (f'Commit to saving for {name} for up to 224 game loops, purchasing it if it becomes executable before that review. No other new purchase is allowed during this commitment. This does not reserve minerals against repair spending; ongoing repairs may delay affordability. '
            f'The engine offers its ability when resource requirements are ignored, but no executable purchase/site is currently offered. '
            f'Resource shortfall: {shortfall}. '+investment_description(name,project,state))
    carried = False
    choice = None
    strategy = (state.get('strategy_chosen_by_jev') or {}).get('choice')
    if memory is not None and memory.get('stalled_commitment_review_enabled'):
        from jev_sc2.commitment_review import review_stalled
        await review_stalled(state, view, jev, memory)
    batch = (memory or {}).get('production_batch')
    if batch:
        if batch.get('executor') and batch['loop'] <= view['loop'] < batch['review_at'] and batch['remaining'] > 0 and batch['strategy'] == strategy:
            return []  # Explicit job owns purchases; framework executes its fixed command.
        if (batch['loop'] <= view['loop'] < batch['review_at'] and batch['remaining']>0
                and batch['strategy']==strategy):
            target=batch['target_project']
            if target in projects:
                choice=f'project_{names.index(target)}'
                carried=True
            elif target in potential:
                jev.log('production_batch_wait',loop=view['loop'],target_project=target,remaining_attempts=batch['remaining'],review_at=batch['review_at'])
                return []
            else:
                jev.log('production_batch_released',current_loop=view['loop'],
                        reason='training control no longer offered',**batch)
                memory.pop('production_batch',None)
        else:
            reason = ('game loop rewound' if view['loop'] < batch['loop'] else
                      'review deadline reached' if view['loop'] >= batch['review_at'] else
                      'no requests remaining' if batch['remaining'] <= 0 else
                      'strategic priority changed')
            jev.log('production_batch_released',current_loop=view['loop'],reason=reason,**batch)
            memory.pop('production_batch',None)
    plan = (memory or {}).get('investment_intent',{})
    if (not carried and plan.get('mode')=='save_for_project' and
            plan.get('loop',0)<=view['loop']<plan.get('review_at',0)):
        target = plan['target_project']
        if target in projects:
            choice = f'project_{names.index(target)}'
            carried = True
            jev.log('investment_plan_ready',loop=view['loop'],target_project=target)
        elif target in potential:
            jev.log('investment_wait',loop=view['loop'],target_project=target,review_at=plan['review_at'])
            return []
    if not carried:
        purchase_state = investment_state(state)
        if memory is not None:
            purchase_state['production_commitment'] = memory.get('production_batch')
        if memory and memory.get('previous_attempts'):
            purchase_state['previous_attempts'] = memory['previous_attempts']
        if memory is not None and memory.get('production_intentions_enabled'):
            from jev_sc2.intentions import production_intentions
            goals = await production_intentions(purchase_state, jev, memory, view['loop'], strategy)
            if goals:
                purchase_state['jev_production_intentions'] = goals
        if memory is not None and memory.get('bottleneck_diagnosis_enabled'):
            from jev_sc2.bottleneck import diagnose
            purchase_state['jev_bottleneck_diagnosis'] = await diagnose(
                purchase_state, jev, memory, view['loop'], strategy)
        if (memory or {}).get('purchase_dependencies_enabled'):
            from jev_sc2.purchase_dependencies import assess
            purchase_state['your_purchase_dependency_assessments'] = await assess(
                purchase_state, criteria, jev, view['loop'])
        if memory is not None and memory.get('investment_scoring_enabled'):
            choice = await score_investment_options(purchase_state,
                criteria,jev,memory,view['loop'])
        else:
            answer = await jev.ask(purchase_state, {'investment': {
                'type':'choice',
                'instructions':'Allocate the shared resources across the entire force. Choose the next purchase, a bounded training batch, or save. '
                               'This decision selects the next new purchase. Other selections cannot start additional purchases in this review, but worker repairs can still consume shared minerals. '
                               'Existing queues continue. Compare the marginal benefit of each available project in the current situation.',
                'criteria':criteria,
            }})
            prediction = answer.get('investment',{})
            choice = prediction.get('choice')
            probabilities = prediction.get('probabilities',{})
            weights = {k:float(v) for k,v in probabilities.items()
                       if k in criteria and isinstance(v,(int,float)) and math.isfinite(v) and v>0}
            if (memory or {}).get('investment_top_choice_enabled'):
                if choice not in criteria:
                    raise ValueError('Invalid top investment choice: '+str(choice))
                jev.log('investment_top_choice',loop=view['loop'],choice=choice)
            elif memory is not None and weights:
                rng = memory.setdefault('investment_rng',random.Random(20260918))
                sampling_probabilities = investment_sampling_probabilities(weights)
                sampled = rng.choices(list(sampling_probabilities),
                                      weights=list(sampling_probabilities.values()),k=1)[0]
                jev.log('investment_sample',loop=view['loop'],top_choice=choice,
                        sampled_choice=sampled,probabilities=weights,
                        sampling_exponent=1, sampling_scope='jev_legal_distribution',
                        sampling_probabilities=sampling_probabilities,seed=20260918)
                choice = sampled
    if choice in criteria and choice.startswith('batch_'):
        index=int(choice.split('_')[1])
        memory['production_batch']={'target_project':names[index],'remaining':3,
            'loop':view['loop'],'review_at':view['loop']+2016,'strategy':strategy}
        jev.log('production_batch_chosen',**memory['production_batch'])
        choice=f'project_{index}'
    chosen_project = names[int(choice.split('_')[1])] if choice in criteria and choice.startswith('project_') else None
    def propose(command):
        batch=(memory or {}).get('production_batch')
        if batch and batch['target_project']==chosen_project:
            if memory.get('production_executor_enabled') and not batch.get('executor'):
                batch.update(executor=True, armed=False, command=dict(command), last_request_loop=view['loop'])
            batch['remaining']-=1
            jev.log('production_batch_request',loop=view['loop'],target_project=batch['target_project'],
                    remaining_attempts=batch['remaining'],command=command)
            if batch['remaining']==0:
                memory.pop('production_batch',None)
        return [command]
    jev.log('investment_choice',loop=view['loop'],choice=choice,projects=names,future_projects=future_names,
            source='carried_jev_commitment' if carried else ('jev_scores' if (memory or {}).get('investment_scoring_enabled') else 'jev_returned_choice' if (memory or {}).get('investment_top_choice_enabled') else 'jev_distribution'))
    if memory is not None:
        target = (future_names[int(choice.split('_')[-1])] if choice in criteria and choice.startswith('save_for_') else
                  names[int(choice.split('_')[-1])] if choice in criteria and choice.startswith('project_') else None)
        mode = 'save_for_project' if choice in criteria and choice.startswith('save_for_') else 'request_purchase' if target else 'save'
        memory['investment_intent'] = {'mode':mode,'target_project':target,'loop':view['loop'],
                                       'review_at':view['loop']+224 if mode=='save_for_project' else None}

    if choice in criteria and choice.startswith('save_for_'):
        return []
    if choice not in criteria or choice=='save':
        return []
    options = projects[names[int(choice.split('_')[1])]]
    constructing = {u['tag']:u['orders'][0] for u,c in options
                    if u.get('orders') and u['orders'][0].get('ability','').startswith('Build ')}
    if len(options)==1 and not constructing:
        return propose(options[0][1]['command'])
    criteria = {f'option_{i}':
                (f'Interrupt this worker’s existing construction {constructing[u["tag"]]} with a replacement order. '
                 if u['tag'] in constructing else '')+
                f'Unit {u["tag"]} at {u["position"]}, current orders {u.get("orders",[])}: {c["description"]}'
                for i,(u,c) in enumerate(options)}
    if constructing:
        criteria['keep_construction'] = ('Make no new purchase and keep these workers on their existing construction: '
                                        f'{constructing}. Their concurrent role orders will also be left unchanged this decision.')
    answer = await jev.ask({'objective':state.get('objective'), 'mission_context':state.get('mission_context'),
                            'selected_investment':names[int(choice.split('_')[1])],
                            'visible_entities':state.get('visible_entities',[])}, {'producer_site': {
        'type':'choice','instructions':'Execute your selected investment using one of these legal producer/site choices. Consider current work and location.',
        'criteria':criteria,
    }})
    choice=answer.get('producer_site',{}).get('choice')
    if choice=='keep_construction' and constructing:
        if memory is not None:
            memory['construction_retained']={'loop':view['loop'],'tags':list(constructing)}
        jev.log('construction_retained',loop=view['loop'],unit_tags=list(constructing))
        return []
    if choice in criteria:
        selected=options[int(choice.split('_')[1])]
        if selected[0]['tag'] in constructing:
            jev.log('construction_interruption_chosen',loop=view['loop'],unit_tag=selected[0]['tag'],
                    previous_order=constructing[selected[0]['tag']])
        return propose(selected[1]['command'])
    return []


async def arbitrate_spending(commands, view, state, jev):
    offered = {json.dumps(c['command'],sort_keys=True):c
               for u in view['self'] for c in u['candidates']}
    spending = {i:offered[json.dumps(cmd,sort_keys=True)] for i,cmd in enumerate(commands)
                if offered[json.dumps(cmd,sort_keys=True)].get('resource_cost')}
    totals = {k:sum(c['resource_cost'][k] for c in spending.values()) for k in ('minerals','vespene','supply')}
    resources = view.get('resources', {})
    available = {'minerals':resources.get('minerals',0),'vespene':resources.get('vespene',0),
                 'supply':resources.get('supply_remaining',0)}
    if all(totals[k] <= available[k] for k in totals):
        return commands
    criteria = {'defer':'Defer these proposed purchases and retain the resources for later.'}
    for i,c in spending.items():
        if all(c['resource_cost'][k] <= available[k] for k in available):
            criteria[f'buy_{i}'] = f'Execute only this purchase now: unit {commands[i]["unit_tag"]}: {c["description"]}; costs {c["resource_cost"]}'
    result = await jev.ask({**state,'proposed_total_cost':totals,'available_budget':available}, {'spending': {
        'type':'choice',
        'instructions':'The proposed purchases exceed the observed shared resource budget. '
                       'Choose one affordable purchase to execute now, or defer. '
                       'Other non-spending orders will still execute. Choose for overall mission progress.',
        'criteria':criteria,
    }})
    choice = result.get('spending',{}).get('choice')
    jev.log('spending_choice',loop=view['loop'],choice=choice,proposed_cost=totals,available=available)
    selected = int(choice[4:]) if choice in criteria and choice.startswith('buy_') else None
    return [cmd for i,cmd in enumerate(commands) if i not in spending or i==selected]


def selection_facts(view, cohorts, previous_counts):
    facts = {}
    for kind, selected in cohorts.items():
        tags = {u['tag'] for u in selected}
        economic_selected = [u for u in view['self'] if u['tag'] in tags]
        candidate_ids = {c['id'] for u in economic_selected for c in u['candidates']}
        facts[kind] = {
            'members':[{'tag':u['tag'],'type':u['type']} for u in selected],
            'count':len(selected),
            'center':[round(sum(u['position'][i] for u in selected)/len(selected),1) for i in (0,1)],
            'nearest_visible_enemy_distance':round(min((math.dist(u['position'],e['position'])
                for u in selected for e in view.get('visible_entities',[]) if e['alliance']=='Enemy'),default=math.inf),1)
                if any(e['alliance']=='Enemy' for e in view.get('visible_entities',[])) else None,
            'visible_enemies_within_12_of_any_member':dict(Counter(e['type'] for e in view.get('visible_entities',[])
                if e['alliance']=='Enemy' and any(math.dist(u['position'],e['position'])<=12 for u in selected))),
            'cargo_slots_used':sum((u.get('cargo') or {}).get('used',0) for u in selected),
            'cargo_slots_available':sum(max(0,(u.get('cargo') or {}).get('capacity',0)-(u.get('cargo') or {}).get('used',0)) for u in selected),
            'passengers_by_type':dict(Counter(p['type'] for u in selected for p in (u.get('cargo') or {}).get('passengers',[]))),
            'harvesters_assigned':sum((u.get('harvesters') or {}).get('assigned',0) for u in selected),
            'harvesters_ideal':sum((u.get('harvesters') or {}).get('ideal',0) for u in selected),
            'total_health':round(sum(u.get('health',0) for u in selected),1),
            'max_separation':round(max(math.dist(a['position'],b['position']) for a in selected for b in selected),1),
            'largest_distance_to_nearest_selection_member':round(max(min(math.dist(a['position'],b['position']) for b in selected if b['tag']!=a['tag']) for a in selected),1) if len(selected)>1 else None,
            'count_change_since_previous_decision':len(selected)-previous_counts.get(kind,len(selected)),
            'damaged_count':sum(u.get('health_fraction',1)<1 and u.get('build_progress',1)>=1 for u in selected),
            'incomplete_count':sum(u.get('build_progress',1)<1 for u in selected),
            'lowest_health_percent':round(100*min(u.get('health_fraction',1) for u in selected)),
            'current_order_counts':dict(Counter(o['ability'] for u in selected for o in u.get('orders',[]))),
            'idle_count':sum(not u.get('orders') for u in selected),
            'some_can_harvest_minerals':any(k.startswith('gather_') for k in candidate_ids),
            'some_can_construct_buildings':any(k.startswith('build_') for k in candidate_ids),
            'available_build_abilities':sorted({a for u in selected for a in u.get('available_build_abilities',[])}),
            'available_projects':list({c['project']['type']:c['project'] for u in economic_selected for c in u['candidates']
                                       if c.get('project')}.values()),
            'available_support_abilities':sorted({c['capability_description'] for u in selected for c in u['candidates'] if c.get('capability_description')}),
            'some_can_train_units':any(c['description'].startswith('Train ') for u in economic_selected for c in u['candidates']),
        }
    return facts



def harvesting_assignments(units, observed_targets):
    """Expose observed gather destinations across the return half of a cycle."""
    resources = {}
    for unit in units:
        for candidate in unit.get('candidates', []):
            description = candidate['description']
            for prefix, kind in (('Gather minerals', 'minerals'), ('Gather vespene gas', 'vespene')):
                if description.startswith(prefix):
                    resources[candidate['command']['target_tag']] = kind
    assignments = []
    for unit in units:
        orders = unit.get('orders') or []
        if not orders or not orders[0].get('ability', '').startswith(('Harvest Gather', 'Harvest Return')):
            continue
        returning = orders[0]['ability'].startswith('Harvest Return')
        target = observed_targets.get(unit['tag']) if returning else orders[0].get('target_tag')
        assignments.append({'worker_tag': unit['tag'], 'resource_target_tag': target,
                            'resource_kind': resources.get(target, 'unknown'),
                            'evidence': ('previously observed gather target; currently returning cargo' if target is not None
                                         else 'currently returning cargo; prior resource target unknown') if returning
                                        else 'current observed gather target'})
    return assignments


def control_groups(units, mode, learned, harvest_targets=None):
    groups = {}
    harvest_targets = {} if harvest_targets is None else harvest_targets
    present = {u["tag"] for u in units}
    for tag in list(harvest_targets):
        if tag not in present:
            harvest_targets.pop(tag)
    for unit in units:
        ids = {c['id'] for c in unit['candidates']}
        has_attack = any(k.startswith('attack') for k in ids)
        has_move = bool(ids & {'north','south','east','west'})
        economic = (any(k.startswith('gather_') for k in ids)
                    or unit.get('available_build_abilities')
                    or any(c.startswith(('Build ', 'Harvest')) for c in learned.get(unit['type'],[])))
        key = 'MobileCombat' if mode=='mobile_combat' and has_attack and has_move and not economic else unit['type']
        orders = unit.get('orders') or []
        order = orders[0] if orders else {}
        job = order.get('ability', 'idle')
        target = order.get('target_tag')
        # Remember only observed resource targets, never infer a resource from a
        # return-to-base target. Track this even while Jev uses another grouping.
        if job.startswith('Harvest Gather'):
            if target:
                harvest_targets[unit['tag']] = target
            else:
                harvest_targets.pop(unit['tag'], None)
            job = 'Harvest cycle'
        elif job.startswith('Harvest Return'):
            target = harvest_targets.get(unit['tag'])
            job = 'Harvest cycle' if target else f'Harvest return / resource unknown / unit {unit["tag"]}'
        else:
            harvest_targets.pop(unit['tag'], None)
        if mode == 'by_current_order':
            key = f'{unit["type"]} / {job}' + (f' / target {target}' if target else '')
        # Economic actors get independent role decisions in every grouping mode.
        # This changes granularity only; Jev still chooses each actor's task.
        if economic:
            key = f'{unit["type"]} / unit {unit["tag"]}'
        groups.setdefault(key, []).append(unit)
    return groups


async def choose_contributions(view, state, questions, jev, memory):
    """Sample Jev's distribution and retain its declared short commitment."""
    commitment_loops = memory.get('contribution_review_loops',672)
    if commitment_loops not in (112,672,2016):
        commitment_loops = 672
    plans = memory.setdefault('contribution_plans',{})
    pending, answers = {}, {}
    strategy = (state.get('strategy_chosen_by_jev') or {}).get('choice')
    for key,question in questions.items():
        plan = plans.get(key,{})
        if (plan.get('choice') in question['criteria'] and
            plan.get('strategy')==strategy and
            plan.get('loop',0)<=view['loop']<plan.get('review_at',0)):
            answers[key] = {'choice':plan['choice']}
        else:
            pending[key] = {**question,'instructions':question['instructions']+
                f' Commit to this contribution for up to {commitment_loops} game loops, '
                'unless its controls become unavailable or the strategic priority changes. '
                'Concrete orders are still selected separately during the commitment.'}
            name = key.removeprefix('purpose_')
            facts = state.get('selection_facts', {}).get(name)
            if facts is not None:
                pending[key]['instructions'] += (
                    '\nThe selection_facts record for this exact selection (' + name + ') is: '
                    + json.dumps(facts, separators=(',', ':')))
    predictions = await jev.ask(control_state(state),pending) if pending else {}
    rng = memory.setdefault('contribution_rng',random.Random(20260919))
    for key,question in pending.items():
        answer = predictions.get(key,{})
        weights = {k:float(v) for k,v in answer.get('probabilities',{}).items()
                   if k in question['criteria'] and isinstance(v,(int,float)) and math.isfinite(v) and v>0}
        top_mode = memory.get('contribution_top_choice', False)
        choice = (answer.get('choice') if top_mode else
                  rng.choices(list(weights),weights=list(weights.values()),k=1)[0] if weights else answer.get('choice'))
        if top_mode and choice not in question['criteria']:
            raise ValueError(f'Invalid Jev contribution choice for {key}: {choice!r}')
        if choice in question['criteria']:
            plans[key] = {'choice':choice,'loop':view['loop'],'review_at':view['loop']+commitment_loops,'strategy':strategy}
            answers[key] = {'choice':choice}
        jev.log('contribution_commitment',loop=view['loop'],question=key,
                top_choice=answer.get('choice'),sampled_choice=choice,selected_choice=choice,
                selection_mode='top_choice' if top_mode else 'sampled',
                probabilities=weights,review_at=view['loop']+commitment_loops)
    return answers


async def assign_support(view, state, jev, requests):
    """Jev selects executors; unselected units keep their current work."""
    questions, plans = {}, {}
    units = {u['tag']:u for u in view['self']}
    for kind, candidates in requests.items():
        options = {'continue':'Make no new support assignment; keep existing orders.'}
        plans[kind] = {'continue':[]}
        for candidate in candidates:
            command = candidate['command']
            unit = units[command['unit_tag']]
            key = f'unit_{unit["tag"]}'
            options[key] = (f'Only unit {unit["tag"]} at {unit["position"]} performs: {candidate["description"]}. '
                            f'Its current orders: {unit.get("orders",[])}. Other units keep their current work.')
            plans[kind][key] = [command]
        if len(candidates)>1 and not any(c.get('exclusive_target') for c in candidates):
            options['all'] = f'All {len(candidates)} eligible units perform this support action, replacing all their current orders. Concurrent repairs can consume shared resources.'
            plans[kind]['all'] = [c['command'] for c in candidates]
        questions[kind] = {'type':'choice',
            'instructions':f'Assign executors for the support action Jev selected for {kind}. Consider their existing jobs, resources and urgency. '
                           'One passenger can enter only one carrier, so loading offers single-carrier assignments. '
                           'Unselected units retain their current orders.',
            'criteria':options}
    compact = {k:state.get(k) for k in ('objective','mission_context','resources','strategy_chosen_by_jev','selection_facts','recent_action_feedback')}
    answers = await jev.ask(compact,questions) if questions else {}
    commands = []
    for kind in questions:
        choice = answers.get(kind,{}).get('choice')
        selected = plans[kind].get(choice,[])
        jev.log('support_assignment',loop=view['loop'],cohort=kind,choice=choice,
                eligible=len(requests[kind]),assigned=len(selected))
        commands.extend(selected)
    return commands


def continuing_income(view, selected, role, strategy, key, memory):
    """Keep an observed harvesting cycle; never choose a worker or resource."""
    reviews = memory.setdefault('income_execution_reviews', {})
    if role != 'income' or any(u.get('health_fraction') is None for u in selected):
        reviews.pop(key,None)
        return False
    previous = reviews.get(key)
    snapshot = {'loop':view['loop'], 'strategy':strategy,
                'health':{u['tag']:u['health_fraction'] for u in selected}}
    harvesting = bool(selected) and all(
        u.get('orders') and u['orders'][0].get('ability','').startswith(('Harvest Gather', 'Harvest Return'))
        for u in selected)
    # Scheduling trigger, not a claim that distant enemies are harmless.
    # Missing geometry forces review; never select a task or target here.
    threatened = any(
        not e.get('position') or any(not u.get('position') or
            math.dist(u['position'], e['position']) <= 12 for u in selected)
        for e in view.get('visible_entities', []) if e.get('alliance') == 'Enemy')
    if (role=='income' and harvesting and not threatened and previous
        and previous['strategy']==strategy
        and 0 <= view['loop']-previous['loop'] < 672
        and snapshot['health'].keys()==previous['health'].keys()
        and all(h >= previous['health'][tag] for tag,h in snapshot['health'].items())):
        return True
    # Only an actual review resets this deadline. Skips cannot extend it forever.
    reviews[key] = snapshot if role=='income' and harvesting and not threatened else None
    return False


async def decide(view, jev, memory):
    """Jev chooses shared or individual orders for each unit-type selection."""
    coverage = view.get('unrepresented_controls', {})
    if coverage != memory.get('last_unrepresented_controls'):
        jev.log('control_coverage', loop=view['loop'], unrepresented=coverage,
                meaning='Advertised abilities without offered candidates; may lack targets/sites or adapter support')
        memory['last_unrepresented_controls'] = coverage
    if view.get('player_score_telemetry'):
        jev.log('player_score',loop=view['loop'],values=view['player_score_telemetry'],
                note='API-reported cumulative player score; telemetry only, not policy context')
    units = [{**u,'candidates':[c for c in u['candidates'] if not is_purchase(c)]}
             for u in view['self']]
    if not units:
        return []
    cohorts = {}
    for unit in units:
        cohorts.setdefault(unit['type'], []).append(unit)
    state = {k:view.get(k) for k in ('objective','mission_context','resources','completed_upgrades','explored_map','visible_entities','last_known_entities','unit_type_facts')}
    state['game_loop'] = view['loop']
    state['recent_outcomes'] = recent_outcomes(view, memory)
    state['recent_action_feedback'] = describe_action_feedback(view,memory)
    state['previous_investment_intent'] = memory.get('investment_intent')
    state['production_commitment'] = memory.get('production_batch')
    learned = memory.setdefault('observed_capabilities_by_type', {})
    for unit in view['self']:
        capabilities = set(learned.get(unit['type'], []))
        # Remove older labels from retained hot-reload memory as well.
        capabilities.discard('Attack-move, engaging encountered enemies')
        capabilities.discard('Attack visible targets')
        for candidate in unit['candidates']:
            label = candidate['description']
            if label.startswith(('Train ', 'Build ')):
                capabilities.add(label.split(';')[0].split(' at visible')[0])
            if candidate['id'].startswith('gather_'):
                capabilities.add('Harvest resources')
            if label.startswith('Attack-move '):
                capabilities.add('Attack-move order control; damage depends on weapons or separate abilities')
            elif label.startswith('Attack visible '):
                capabilities.add('Attack-target order control; damage depends on weapons or separate abilities')
            elif label.startswith('Move '):
                capabilities.add('Move to locations or entities')
            if candidate.get('capability_description'):
                capabilities.add(candidate['capability_description'])
        learned[unit['type']] = sorted(capabilities)
    state['observed_capabilities_by_type'] = learned
    state['units'] = [{k:u.get(k) for k in ('tag','type','position','health','health_fraction','shield','weapon_cooldown','weapon_status','orders','build_progress','cargo','energy','harvesters')}
                      for u in units]
    state['type_selection_facts'] = selection_facts(view,cohorts,{})
    cohorts = control_groups(units,memory.get('coordination','by_type'),learned,memory.setdefault('harvest_targets',{}))
    state['harvesting_assignments'] = harvesting_assignments(units,memory['harvest_targets'])
    state['selection_facts'] = selection_facts(view,cohorts,memory.get('previous_cohort_counts',{}))
    strategy = memory.get('strategy')
    if (strategy is None or view['loop'] < strategy['loop']
            or view['loop'] >= strategy.get('review_at',strategy['loop']+112)):
        options = {
            'pursue_objective':'Commit effort to completing the active primary mission objectives described in mission_context. Further decisions choose the necessary movement, interactions, combat or preparation; this priority does not assume the objective is destruction of an enemy base.',
            'attack':'Commit forces to damaging or destroying the enemy base.',
            'strengthen':'Increase military strength through resource collection and production.',
            'protect':'Preserve owned units and structures from current threats.',
            'assemble':'Bring separated units together and accumulate a force before committing to an engagement.',
            'explore':'Acquire information about the map and enemy positions.',
            'recover':'Restore income and replace losses.',
            'continue_operations':'Let current tasks progress before changing commitment.',
        }
        cadence = measured_cadence(memory.get('action_feedback', []), view['loop'])
        decision = await jev.ask({**control_state(state),'previous_strategy':strategy,
            **({'measured_decision_cadence':cadence} if cadence else {}),
            **({'previous_attempts':memory['previous_attempts']} if memory.get('previous_attempts') else {})}, {'strategy': {
            'type':'choice',
            'instructions':'Choose the current strategic priority for completing the mission. '
                           'Consider resources, own force, known enemy force, and recent_outcomes. Reassess your previous strategy using these measured outcomes. '
                           'This priority will inform further Jev decisions; it does not execute a scripted plan.',
            'criteria':options,
        }, 'strategy_review': {
            'type':'choice',
            'instructions':'Choose when to review this high-level priority and selection grouping again. Tactical orders and investment decisions continue during this interval using fresh observations. Longer intervals reduce repeated model spending but delay revising the priority. The next review occurs at the first budget-permitted decision after the selected interval.',
            'criteria':{
                'soon':'Review after 112 game loops.',
                'medium':'Retain for 672 game loops.',
                'long':'Retain for 2016 game loops.',
            },
        }, 'contribution_review': {
            'type':'choice',
            'instructions':'Choose how long newly chosen unit contribution roles remain committed before reconsideration. Concrete orders still use fresh observations and Jev choices. Unavailable controls or a changed strategic priority end a role early. Longer commitments reduce reassignment and review cost but can prolong a poor allocation. This does not choose any unit task. Existing commitment deadlines remain unchanged.',
            'criteria':{
                'soon':'Retain newly chosen contribution roles for 112 game loops.',
                'medium':'Retain newly chosen contribution roles for 672 game loops.',
                'long':'Retain newly chosen contribution roles for 2016 game loops.',
            },
        }, 'coordination': {
            'type':'choice',
            'instructions':'Choose how to organize non-worker control selections. Observed harvesting/building units always receive independent contribution and order decisions. This chooses grouping only; further Jev decisions choose every order.',
            'criteria':{
                'by_type':'Keep different unit types in separate selections, allowing different shared orders.',
                'by_current_order':'Separate each unit type by its current first order and unit target, with idle units separate and observed gather/return cycles kept together by their known resource target. Choose distinct orders for those job selections to retain or change existing assignments independently.',
                'mobile_combat':'Combine units with movement and attack-order controls, excluding observed workers/builders, into one mixed selection. This may include weaponless support or transport units; control availability does not establish weapon damage. Give that selection shared orders or choose individual control. Other units keep type selections.',
            },
        }})
        contribution_horizon = {'soon':112,'medium':672,'long':2016}.get(
            decision.get('contribution_review',{}).get('choice'))
        if contribution_horizon is not None:
            memory['contribution_review_loops'] = contribution_horizon
            jev.log('contribution_review_choice',loop=view['loop'],duration_loops=contribution_horizon)
        selected = decision.get('strategy',{}).get('choice')
        if selected in options:
            horizon = {'soon':112,'medium':672,'long':2016}.get(
                decision.get('strategy_review',{}).get('choice'),112)
            strategy = {'loop':view['loop'],'choice':selected,'description':options[selected],
                        'review_at':view['loop']+horizon}
            memory['strategy'] = strategy
            jev.log('strategy_choice',**strategy)
        grouping = decision.get('coordination',{}).get('choice')
        if grouping in ('by_type','mobile_combat','by_current_order','individual_workers'):
            memory['coordination'] = grouping
            jev.log('coordination_choice',loop=view['loop'],choice=grouping)
            cohorts = control_groups(units,grouping,learned,memory.setdefault('harvest_targets',{}))
            state['selection_facts'] = selection_facts(view,cohorts,memory.get('previous_cohort_counts',{}))
    memory['previous_cohort_counts'] = {k:len(v) for k,v in cohorts.items()}
    state['strategy_chosen_by_jev'] = strategy
    questions, tables, plans, support_plans = {}, {}, {}, {}
    for kind, selected in cohorts.items():
        tables[kind] = [{c['id']:c for c in u['candidates']} for u in selected]
        common = set.intersection(*(set(c) for c in tables[kind]))
        criteria = {'individual':'Choose separate orders for these units using further Jev decisions.',
                    'continue':'Keep the current orders of these units unchanged.'}
        plans[kind] = {}
        support_plans[kind] = {}
        for key in sorted(common):
            if any(t[key].get('capability_description') for t in tables[kind]):
                continue
            descriptions = list(dict.fromkeys(re.sub(r'[,;] distance [0-9.]+','',c[key]['description']) for c in tables[kind]))
            description = ' | '.join(descriptions[:4])
            if len(descriptions)>4:
                description += f' (descriptions vary across {len(descriptions)} units; apply each offered version)'
            distances = [math.dist(u['position'],t[key]['command']['point'])
                         for u,t in zip(selected,tables[kind]) if 'point' in t[key]['command']]
            if distances:
                description += f'; straight-line distances across selection: {min(distances):.1f} to {max(distances):.1f}; actual engine route and travel distance unknown'
            # Shared executor scope is stated once in the question. Options that
            # affect only a subset continue to name that subset explicitly.
            criteria['group_'+key] = description
            plans[kind]['group_'+key] = [c[key]['command'] for c in tables[kind]]
        # Support need not redirect an entire cohort. Collect each offered
        # target once; a later Jev answer chooses its executor(s).
        for table in tables[kind]:
            for key,candidate in table.items():
                if candidate.get('capability_description'):
                    option = 'support_'+key
                    support_plans[kind].setdefault(option,[]).append(candidate)
                    criteria[option] = candidate['description']+'; choose executor(s) in a separate Jev decision'
        # Small support menus can name exact assignments in this same call,
        # avoiding a serial executor query. Larger menus retain the staged path
        # so all candidates remain available without an unbounded cross-product.
        if sum(len(cs) for cs in support_plans[kind].values()) <= 80:
            for option, candidates in list(support_plans[kind].items()):
                criteria.pop(option)
                for candidate in candidates:
                    command = candidate['command']
                    direct = f'{option}_only_{command["unit_tag"]}'
                    criteria[direct] = (f'Only unit {command["unit_tag"]}: {candidate["description"]}. '
                                        'All other units keep their current orders.')
                    plans[kind][direct] = [command]
                if len(candidates)>1 and not any(c.get('exclusive_target') for c in candidates):
                    direct = option+'_all'
                    criteria[direct] = (f'All {len(candidates)} eligible units: {candidates[0]["description"]}. '
                                        'Replaces all their current work; concurrent repairs share resources.')
                    plans[kind][direct] = [c['command'] for c in candidates]
            support_plans[kind] = {}
        # A member cannot join itself, so intersection alone hid in-selection
        # anchors. Expose the exact legal hold + join combination to Jev.
        for anchor,anchor_table in zip(selected,tables[kind]):
            for prefix,verb in (('join_','move'),('attack_move_join_','attack-move, engaging enemies encountered')):
                key = f'{prefix}{anchor["tag"]}'
                if key in common or 'hold_position' not in anchor_table:
                    continue
                followers = [(u,t) for u,t in zip(selected,tables[kind]) if u['tag']!=anchor['tag']]
                if not followers or not all(key in t for _,t in followers):
                    continue
                option = 'group_'+key
                criteria[option] = (f'Regroup this selection at {anchor["type"]} unit {anchor["tag"]} '
                                    f'position {anchor["position"]}: that unit holds position; '
                                    f'the other {len(followers)} units {verb} to its observed position.')
                plans[kind][option] = [anchor_table['hold_position']['command']]+[t[key]['command'] for _,t in followers]
        # A construction order need not apply to every member of a selection.
        # Offer actual legal individual builder/site pairs; Jev chooses the pair.
        for unit,table in zip(selected,tables[kind]):
            for key,candidate in table.items():
                if key.startswith('build_'):
                    option=f'unit_{unit["tag"]}_{key}'
                    criteria[option]=f'Only {kind} unit {unit["tag"]}: {candidate["description"]}'
                    plans[kind][option]=[candidate['command']]
        if not any(u['candidates'] for u in selected):
            continue  # No non-purchase action exists for Jev to choose here.
        questions[kind] = {
            'type':'choice',
            'instructions':f'Choose the next order for the {len(selected)} {kind} units to advance the mission objective. '
                           'You may choose a shared order for this selection or individual control. '
                           'Unless an option explicitly says otherwise, every unit in this selection receives the chosen shared order. '
                           'Other selections receive their own decisions in parallel. '
                           'Consider current orders, health, resources and known entities. '
                           'Count alone is not local fighting strength: max_separation and nearest-selection-member distances describe dispersion. '
                           'Use selection_facts for unit counts, recent changes, damage and economic capabilities. '
                           'Consider the strategic priority chosen by Jev alongside immediate threats. '
                           'Snapshot locations are stale, not live visible targets. '
                           'Ordinary Move changes location only: moving near a resource does not harvest it, moving near a building does not repair or enter it, and ordinary Move does not attack along the route.',
            'criteria':criteria,
        }
    # Separate semantic contribution from concrete command selection. Both are
    # Jev choices; categorization describes controls and never chooses a tactic.
    meanings = {
        'income':'Collect resource income to fund unit production and construction.',
        'production':'Produce more units.',
        'construction':'Construct one of the available_projects buildings, including any supply capacity listed there.',
        'combat':'Attack enemies or attack-move toward a location.',
        'positioning':'Move, regroup, scout, stop or hold position. Ordinary Move changes location only: moving near a resource does not harvest it, moving near a building does not repair or enter it, and ordinary Move does not attack along the route.',
        'other':'Use another available ability.',
        'individual':'Let separate Jev decisions choose orders for individual units.',
        'continue':'Keep the existing orders unchanged, whatever those orders currently are.',
    }
    def purpose(kind,key):
        if key in ('continue','individual'):
            return key
        if key.startswith('unit_'): return 'construction'
        if key.startswith('support_'): return 'other'
        action_id=key[len('group_'):]
        if action_id.startswith('gather_'): return 'income'
        if action_id.startswith('build_'): return 'construction'
        if 'attack' in action_id: return 'combat'
        if action_id.startswith('join_'): return 'positioning'
        if tables[kind][0][action_id]['description'].startswith('Train '): return 'production'
        if action_id.startswith('ability_'): return 'other'
        return 'positioning'
    direct_selections = {kind for kind,selected in cohorts.items()
        if all(any(c['id'].startswith('attack') for c in u['candidates'])
               and any(c['id'] in ('north','south','east','west') for c in u['candidates'])
               and not any(c['id'].startswith('gather_') for c in u['candidates'])
               and not u.get('available_build_abilities')
               and not any(c.startswith(('Build ', 'Harvest')) for c in learned.get(u['type'],[]))
               for u in selected)}
    purpose_questions = {f'purpose_{kind}': {
        'type':'choice',
        'instructions':f'Choose how the {len(cohorts[kind])} {kind} units should contribute to completing the mission now. '
                       'Different unit types can make different contributions to the same strategy. '
                       'Use their capabilities, current orders, resources and threats.',
        'criteria':{p:meanings[p]+((' Available: '+'; '.join(state['selection_facts'][kind]['available_support_abilities'])) if p=='other' else '')
                    for p in sorted({purpose(kind,k) for k in q['criteria']})},
    } for kind,q in questions.items() if kind not in direct_selections}
    async def choose_orders():
        roles = await choose_contributions(view,state,purpose_questions,jev,memory)
        answers, concrete_questions = {}, {}
        for kind,q in questions.items():
            if kind in direct_selections:
                concrete_questions[kind]=q
                jev.log('direct_order_menu',loop=view['loop'],cohort=kind,
                        reason='Movement/attack selection chooses among all offered orders without abstract role filtering')
                continue
            role=roles.get(f'purpose_{kind}',{}).get('choice')
            jev.log('purpose_choice',loop=view['loop'],cohort=kind,choice=role)
            if continuing_income(view,cohorts[kind],role,(strategy or {}).get('choice'),kind,memory):
                answers[kind]={'choice':'continue'}
                jev.log('routine_execution',loop=view['loop'],cohort=kind,
                        reason='Jev income role; observed harvest cycle continues', avoided_concrete_question=True)
            elif role in ('continue','individual'):
                answers[kind]={'choice':role}
            else:
                criteria={k:v for k,v in q['criteria'].items() if purpose(kind,k)==role}
                if criteria:
                    criteria['continue']='Keep current orders without reissuing them. If they already implement the chosen contribution, this maintains that work.'
                    concrete_questions[kind]={**q,'criteria':criteria,
                                              # 'Other' identifies an ability menu, not a need to act.
                                              'instructions':q['instructions'] + (
                                                  '' if role == 'other' else
                                                  ' Jev selected this contribution: '+meanings[role])}
        if concrete_questions:
            if memory.get('order_families_enabled'):
                from jev_sc2.order_families import select_families
                eligible = {k:q for k,q in concrete_questions.items() if k in direct_selections}
                concrete_questions.update(await select_families(order_state(state),eligible,jev))
            if memory.get('destination_categories_enabled'):
                from jev_sc2.destination_categories import select_categories
                eligible = {k:q for k,q in concrete_questions.items() if k in direct_selections}
                concrete_questions.update(await select_categories(order_state(state),eligible,jev))
            if memory.get('order_scoring_enabled'):
                from jev_sc2.order_scores import rate_order_kinds
                scored = {k:q for k,q in concrete_questions.items() if k in direct_selections}
                if scored:
                    concrete_questions.update(await rate_order_kinds(order_state(state),scored,jev,memory))
            if os.getenv('JEV_OPAQUE_COMBAT_KEYS') == '1':
                answers.update(await choose_with_opaque_keys(order_state(state),concrete_questions,jev,direct_selections))
            else:
                answers.update(await choose_concrete_orders(order_state(state),concrete_questions,jev))
            if memory.get('sample_combat_orders'):
                rng = memory.setdefault('combat_order_rng', random.Random(20260920))
                for kind in sorted(set(concrete_questions) & direct_selections):
                    original = answers[kind]
                    answers[kind] = sample_concrete_answer(
                        original, concrete_questions[kind]['criteria'], rng)
                    jev.log('combat_order_sample', loop=view['loop'], cohort=kind,
                            top_choice=original.get('choice'),
                            sampled_choice=answers[kind]['choice'],
                            probabilities=original.get('probabilities'), seed=20260920)
        commands, support_requests = [], {}
        for kind, selected in cohorts.items():
            choice = answers.get(kind,{}).get('choice')
            jev.log('group_choice',loop=view['loop'],cohort=kind,choice=choice,unit_count=len(selected))
            if choice == 'individual':
                submemory = memory.setdefault('cohorts',{}).setdefault(kind,{})
                commands.extend(await decide_individual({**view,'self':selected},jev,submemory))
            elif choice in support_plans[kind]:
                support_requests[kind] = support_plans[kind][choice]
            elif choice in plans[kind]:
                commands.extend(plans[kind][choice])
        commands.extend(await assign_support(view,state,jev,support_requests))
        return commands
    investment, commands = await gather_owned(choose_investment(view,state,jev,memory), choose_orders())
    # A selected purchase assigns its producer; preserve other Jev-selected orders.
    producer_tags = {c['unit_tag'] for c in investment}
    retained = memory.get('construction_retained',{})
    retained_tags = set(retained.get('tags',[])) if retained.get('loop')==view['loop'] else set()
    protected = producer_tags | retained_tags
    commands = [c for c in commands if c['unit_tag'] not in protected]+investment
    return coordinate_exclusive_jobs(view,commands,protected,jev)


def coordinate_exclusive_jobs(view, commands, protected, jev):
    """Honor selected multi-unit jobs for this cycle, without choosing new jobs."""
    offered = [c['command'] for unit in view['self'] for c in unit['candidates']
               if c.get('exclusive_target')]
    jobs = [c for c in commands if c in offered]
    participants = Counter(tag for c in jobs for tag in (c['unit_tag'],c['target_tag']))
    rejected = [c for c in jobs if c['target_tag'] in protected or
                any(participants[tag]>1 for tag in (c['unit_tag'],c['target_tag']))]
    accepted = [c for c in jobs if c not in rejected]
    reserved = {c['target_tag'] for c in accepted}
    discarded = [c for c in commands if c in rejected or c['unit_tag'] in reserved]
    if jobs:
        jev.log('exclusive_job_coordination',loop=view['loop'],accepted_jobs=accepted,
                rejected_jobs=rejected,discarded_commands=discarded,
                reason='Selected joint job reserves its passenger for this cycle; competing joint jobs or protected work are not overridden')
    return [c for c in commands if c not in discarded]


async def decide_individual(view, jev, memory):
    # Candidate construction is mechanical; Jev selects each unit's action.
    # Start small: combat/movement experiments, no hand-coded build order.
    units = view['self']
    if not units:
        return []
    questions = {}
    state = {'objective': view['objective'], 'mission_context':view.get('mission_context'), 'resources': view['resources']}
    state['explored_map'] = view.get('explored_map')
    state['visible_entities'] = view.get('visible_entities', [])
    state['last_known_entities'] = view.get('last_known_entities', [])
    state['unit_type_facts'] = view.get('unit_type_facts', {})
    squad = [{**{k:u[k] for k in ('tag','type','position','health_fraction')},
              'build_progress':u.get('build_progress',1),
              'nearby_terrain':u.get('nearby_terrain', {})} for u in units]
    separation = round(max(math.dist(a['position'], b['position']) for a in units for b in units), 1)
    state['squad'] = squad
    state['max_squad_separation'] = separation
    # Jev chooses the squad intent as well as the individual commands. This
    # cadence is an inference budget, not a scripted route or unstuck action.
    navigation = memory.get('navigation', {})
    if not navigation or view['loop'] - navigation['loop'] >= 112:
        center = [round(sum(u['position'][i] for u in units)/len(units), 1) for i in (0, 1)]
        # Spatial memory is measured from our own positions, not hidden map data.
        visits = memory.setdefault('visited_cells', {})
        cell = (math.floor(center[0]/10), math.floor(center[1]/10))
        visits[cell] = visits.get(cell, 0) + 1
        surroundings = {str(e['tag']): {
            'type': e['type'], 'alliance': e['alliance'],
            'position': [round(u['position'][0]+e['east_offset'], 1),
                         round(u['position'][1]+e['north_offset'], 1)],
        } for u in units for e in u['surroundings']}
        outcomes = memory.setdefault('navigation_outcomes', [])
        if navigation:
            outcomes.append({'intent': navigation['intent'],
                             'elapsed_loops': view['loop']-navigation['loop'],
                             'displacement': round(math.dist(center, navigation['center']), 1)})
            del outcomes[:-8]
        navigation_options = {
            'north': 'Explore north (increasing map y)',
            'south': 'Explore south (decreasing map y)',
            'east': 'Explore east (increasing map x)',
            'west': 'Explore west (decreasing map x)',
            'engage': 'Fight the visible enemies',
            'neutral': 'Approach a visible neutral entity',
            'hold': 'Hold position',
            **{f'regroup_{u["tag"]}': f'Gather the squad around friendly {u["type"]} tag {u["tag"]} at {u["position"]}' for u in units},
        }
        intent = await jev.ask({
            'objective': view['objective'], 'mission_context':view.get('mission_context'), 'squad_center': center,
            'explored_map': view.get('explored_map'),
            'last_known_entities': view.get('last_known_entities', []),
            'squad': squad, 'max_squad_separation': separation,
            'visible_entities': view.get('visible_entities',list(surroundings.values())),
            'previous_navigation': navigation,
            'recent_intent_outcomes': outcomes,
            'visited_areas': [{'center': [x*10+5, y*10+5], 'visits': count}
                              for (x,y), count in visits.items()],
        }, {'navigation': {
            'type': 'choice',
            'instructions': 'Choose the squad intent that best advances the mission objective. '
                            'The objective location may be unknown. Consider exploration and '
                            'whether the previous intent produced useful progress. '
                            'Use visited areas to recognize repeated routes. Neutral '
                            'entities are not enemies. Individual units will choose how to execute this intent.',
            'criteria': navigation_options,
        }})
        choice = intent.get('navigation', {}).get('choice')
        # Explore using Jev's probabilities, with no human-authored route weights.
        probabilities = intent.get('navigation', {}).get('probabilities', {})
        allowed = set(navigation_options)
        weights = {k:float(v) for k,v in probabilities.items()
                   if k in allowed and isinstance(v,(int,float)) and math.isfinite(v) and v > 0}
        if weights:
            rng = memory.setdefault('navigation_rng', random.Random(20260918))
            top_choice = choice
            choice = rng.choices(list(weights), weights=list(weights.values()), k=1)[0]
            jev.log('navigation_sample', loop=view['loop'], top_choice=top_choice,
                    sampled_choice=choice, probabilities=weights, seed=20260918)
        if choice in allowed:
            navigation = {'loop': view['loop'], 'center': center, 'intent': choice}
            memory['navigation'] = navigation
    state['squad_intent_chosen_by_jev'] = navigation.get('intent')
    # Round-robin inference scheduling only: no unit action is chosen here.
    ordered = sorted(units,key=lambda u:u['tag'])
    cursor = memory.get('decision_cursor', -1)
    batch = ([u for u in ordered if u['tag'] > cursor]
             + [u for u in ordered if u['tag'] <= cursor])[:12]
    memory['decision_cursor'] = batch[-1]['tag']
    jev.log('decision_batch',loop=view['loop'],unit_tags=[u['tag'] for u in batch])
    candidates = {}
    for unit in batch:
        tag = str(unit['tag'])
        options = {'continue': None}
        actions = {'continue': None}
        for candidate in unit['candidates']:
            description = candidate['description']
            destination = candidate['command'].get('point')
            enemies = [e for e in unit['surroundings'] if e['alliance'] == 'Enemy']
            if destination is not None and enemies:
                dx = destination[0] - unit['position'][0]
                dy = destination[1] - unit['position'][1]
                before = min(e['distance'] for e in enemies)
                after = min(math.hypot(e['east_offset']-dx, e['north_offset']-dy) for e in enemies)
                change = 'farther from' if after > before else 'closer to'
                description += f'; destination is {change} the nearest visible enemy ({before:.1f} to {after:.1f} map units), assuming enemies stay still'
            options[candidate['id']] = description
            actions[candidate['id']] = candidate['command']
        candidates[tag] = actions
        local = {k: v for k, v in unit.items() if k != 'candidates'}
        history = memory.setdefault('history', {}).setdefault(tag, [])
        # Budget pacing can put consecutive reviews beyond the former 112-loop
        # horizon. Keep bounded factual history over the outcome window instead.
        history[:] = [h for h in history if 0 <= view['loop']-h['loop'] <= 672][-8:]
        if history:
            origin = history[0]['position']
            local['recent_progress'] = {
                'game_loops': view['loop']-history[0]['loop'],
                'displacement': round(math.dist(unit['position'], origin), 1),
                'last_choices': [h['choice'] for h in history[-4:]],
                'interpretation': 'Previous selections, not proof of execution or success. Displacement is net movement; useful round trips may return to the same position.',
            }
        history.append({'loop': view['loop'], 'position': unit['position'], 'choice': 'pending'})
        questions[tag] = {
            'type': 'choice',
            'instructions': 'Choose the next action for this unit to advance the objective. '
                            'Consider the squad intent chosen by Jev, this unit’s role, and immediate threats. '
                            'Workers and production buildings can choose economic actions instead of squad movement. '
                            'For regroup_TAG, the meeting unit is TAG: approach that friendly unit. '
                            'If you are the meeting unit, consider staying to let teammates arrive. '
                            'Use this unit’s health, current orders and visible surroundings. '
                            'Continue means keep its existing order without sending a command. '
                            'Consider whether recent choices are making progress toward the objective. '
                            'Unit facts: ' + json.dumps(local, separators=(',', ':')),
            'criteria': options,
        }
    items = list(questions.items())
    results = await asyncio.gather(*(jev.ask(state,dict(items[i:i+6]))
                                    for i in range(0,len(items),6)), return_exceptions=True)
    answers = {}
    failures = []
    for result in results:
        if isinstance(result, BaseException):
            failures.append(result)
            jev.log('decision_batch_error',error=type(result).__name__)
        else:
            answers.update(result)
    billing = next((e for e in failures if isinstance(e, PaymentRequiredResponseError)), None)
    if billing is not None:
        raise billing
    if not answers and failures:
        raise failures[0]
    commands = []
    for tag, answer in answers.items():
        if tag not in candidates or answer.get('choice') not in candidates[tag]:
            continue
        action = candidates[tag][answer['choice']]
        memory['history'][tag][-1]['choice'] = answer['choice']
        if action is not None:
            commands.append(action)
    return commands
