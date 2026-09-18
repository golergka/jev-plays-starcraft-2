"""Live-reloaded experiment policy. All action choices come from Jev.

Contract: async decide(view: dict, jev, memory: dict) -> list[command dict].
The harness owns sockets, action validation, telemetry, and persistent memory.
Commit this file to activate it at the next decision boundary.
"""
import json
import math
import random


async def decide(view, jev, memory):
    # Candidate construction is mechanical; Jev selects each unit's action.
    # Start small: combat/movement experiments, no hand-coded build order.
    units = view['self'][:64]
    if not units:
        return []
    questions = {}
    state = {'objective': view['objective'], 'resources': view['resources']}
    squad = [{**{k:u[k] for k in ('tag','type','position','health_fraction')},
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
            'squad': squad, 'max_squad_separation': separation,
            'visible_entities': list(surroundings.values()),
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
    candidates = {}
    for unit in units:
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
    answers = await jev.ask(state, questions)
    commands = []
    for tag, answer in answers.items():
        if tag not in candidates or answer.get('choice') not in candidates[tag]:
            continue
        action = candidates[tag][answer['choice']]
        memory['history'][tag][-1]['choice'] = answer['choice']
        if action is not None:
            commands.append(action)
    return commands
