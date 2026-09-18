"""Live-reloaded experiment policy. All action choices come from Jev.

Contract: async decide(view: dict, jev, memory: dict) -> list[command dict].
The harness owns sockets, action validation, telemetry, and persistent memory.
Commit this file to activate it at the next decision boundary.
"""
import json
import asyncio
from openrouter.errors import PaymentRequiredResponseError
import math
import random


async def decide(view, jev, memory):
    """Jev chooses shared or individual orders for each unit-type selection."""
    units = view['self'][:64]
    if not units:
        return []
    cohorts = {}
    for unit in units:
        cohorts.setdefault(unit['type'], []).append(unit)
    state = {k:view.get(k) for k in ('objective','resources','explored_map','visible_entities','last_known_entities')}
    state['units'] = [{k:u.get(k) for k in ('tag','type','position','health_fraction','orders','build_progress')}
                      for u in units]
    previous_counts = memory.get('previous_cohort_counts', {})
    state['selection_facts'] = {}
    for kind, selected in cohorts.items():
        candidate_ids = {c['id'] for u in selected for c in u['candidates']}
        state['selection_facts'][kind] = {
            'count':len(selected),
            'count_change_since_previous_decision':len(selected)-previous_counts.get(kind,len(selected)),
            'damaged_count':sum(u.get('health_fraction',1)<1 for u in selected),
            'lowest_health_percent':round(100*min(u.get('health_fraction',1) for u in selected)),
            'some_can_harvest_minerals':any(k.startswith('gather_') for k in candidate_ids),
            'some_can_construct_buildings':any(k.startswith('build_') for k in candidate_ids),
            'some_can_train_units':any(c['description'].startswith('Train ') for u in selected for c in u['candidates']),
        }
    memory['previous_cohort_counts'] = {k:len(v) for k,v in cohorts.items()}
    questions, tables = {}, {}
    for kind, selected in cohorts.items():
        tables[kind] = [{c['id']:c for c in u['candidates']} for u in selected]
        common = set.intersection(*(set(c) for c in tables[kind]))
        criteria = {'individual':'Choose separate orders for these units using further Jev decisions.',
                    'continue':'Keep the current orders of these units unchanged.'}
        for key in sorted(common):
            descriptions = list(dict.fromkeys(c[key]['description'] for c in tables[kind]))
            criteria['group_'+key] = f'Every one of the {len(selected)} {kind} units receives: ' + ' | '.join(descriptions)
        questions[kind] = {
            'type':'choice',
            'instructions':f'Choose the next order for the {len(selected)} {kind} units to advance the mission objective. '
                           'You may choose a shared order for this unit type or individual control. '
                           'Other unit types receive their own decisions in parallel. '
                           'Consider current orders, health, resources and known entities. '
                           'Use selection_facts for unit counts, recent changes, damage and economic capabilities. '
                           'Snapshot locations are stale, not live visible targets.',
            'criteria':criteria,
        }
    answers = await jev.ask(state,questions)
    commands = []
    for kind, selected in cohorts.items():
        choice = answers.get(kind,{}).get('choice')
        jev.log('group_choice',loop=view['loop'],cohort=kind,choice=choice,unit_count=len(selected))
        if choice == 'individual':
            submemory = memory.setdefault('cohorts',{}).setdefault(kind,{})
            commands.extend(await decide_individual({**view,'self':selected},jev,submemory))
        elif choice in questions[kind]['criteria'] and choice.startswith('group_'):
            commands.extend(c[choice[len('group_'):]]['command'] for c in tables[kind])
    return commands


async def decide_individual(view, jev, memory):
    # Candidate construction is mechanical; Jev selects each unit's action.
    # Start small: combat/movement experiments, no hand-coded build order.
    units = view['self'][:64]
    if not units:
        return []
    questions = {}
    state = {'objective': view['objective'], 'resources': view['resources']}
    state['explored_map'] = view.get('explored_map')
    state['visible_entities'] = view.get('visible_entities', [])
    state['last_known_entities'] = view.get('last_known_entities', [])
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
            'objective': view['objective'], 'squad_center': center,
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
        local = {k: v for k, v in unit.items() if k not in {'candidates', 'tag'}}
        history = memory.setdefault('history', {}).setdefault(tag, [])
        history[:] = [h for h in history if view['loop']-h['loop'] <= 112]
        if history:
            origin = history[0]['position']
            local['recent_progress'] = {
                'game_loops': view['loop']-history[0]['loop'],
                'displacement': round(math.dist(unit['position'], origin), 1),
                'last_choices': [h['choice'] for h in history[-4:]],
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
