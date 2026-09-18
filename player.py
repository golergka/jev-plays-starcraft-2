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
import re
from collections import Counter


def recent_outcomes(view, memory, window=672):
    """Measured observation history; disappearing units are not assumed dead."""
    loop = view['loop']
    history = memory.setdefault('outcome_history', [])
    if history and loop < history[-1]['loop']:
        history.clear()
    current = {'loop':loop, 'resources':dict(view.get('resources', {})),
               'units':{str(u['tag']):{'type':u['type'], 'health':u.get('health',0)}
                        for u in view['self']}}
    if not history or history[-1]['loop'] != loop:
        history.append(current)
    while len(history)>1 and history[1]['loop'] < loop-window:
        history.pop(0)
    appeared, disappeared, damage = Counter(), Counter(), Counter()
    for before,after in zip(history,history[1:]):
        a,b = before['units'],after['units']
        appeared.update(b[t]['type'] for t in b.keys()-a.keys())
        disappeared.update(a[t]['type'] for t in a.keys()-b.keys())
        for t in a.keys() & b.keys():
            damage[b[t]['type']] += max(0,a[t]['health']-b[t]['health'])
    return {'observed_game_loops':loop-history[0]['loop'],
            'own_units_appeared_by_type':dict(appeared),
            'own_units_disappeared_by_type':dict(disappeared),
            'health_decreases_on_continuously_observed_units':dict(damage),
            'resource_changes':{k:current['resources'].get(k,0)-history[0]['resources'].get(k,0)
                                for k in ('minerals','vespene','food_used','food_cap')},
            'interpretation':'Measured changes, not causal attribution. Disappearance can be death, transport loading, morphing or campaign triggers. Resource changes are net of income and spending. Consider whether your previous choices are producing mission progress.'}


def is_purchase(candidate):
    return candidate['description'].startswith(('Train ', 'Build '))


def investment_state(state):
    """Keep economic/force facts; raw terrain and repeated unit coordinates distract."""
    compact = {k:state[k] for k in ('objective','resources','selection_facts',
               'unit_type_facts','recent_outcomes','observed_capabilities_by_type','previous_investment_intent',
               'strategy_chosen_by_jev') if k in state}
    for source,target in [('visible_entities','visible_entities_by_alliance_and_type'),
                          ('last_known_entities','stale_entities_by_alliance_and_type')]:
        compact[target] = dict(Counter(e['alliance']+' '+e['type'] for e in (state.get(source) or [])))
    compact['selection_facts'] = state.get('type_selection_facts',state.get('selection_facts',{}))
    return compact


def investment_description(name, project, state):
    facts = state.get('type_selection_facts',state.get('selection_facts',{})).get(name,{})
    capabilities = state.get('observed_capabilities_by_type',{}).get(name,[])
    effects = []
    if capabilities:
        effects.append('Adds another unit able to: '+', '.join(capabilities))
    else:
        effects.append('Its action capabilities have not yet been observed')
    if project and project.get('supply_provided',0):
        effects.append(f'Adds {project["supply_provided"]:g} supply capacity when complete')
    weapons = (state.get('unit_type_facts') or {}).get(name,{}).get('catalog_weapons',[])
    if weapons:
        effects.append('Has weapons: '+', '.join(f'{w["targets"]} targets at range {w["range"]}' for w in weapons))
    return (f'Purchase one {name}. '+'. '.join(effects)+'. '
            f'Cost/effects: {project}. Already owned: {facts.get("count",0)}; '
            f'idle: {facts.get("idle_count",0)}; current orders: {facts.get("current_order_counts",{})}.')


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
    criteria = {'save':'Make no new purchase now; preserve resources and let existing production/construction finish.'}
    for i,name in enumerate(names):
        example = projects[name][0][1]
        criteria[f'project_{i}'] = investment_description(name,example.get('project'),state)
    future_names = sorted(set(potential)-set(projects))
    for i,name in enumerate(future_names):
        project = potential[name]
        resources = view.get('resources',{})
        shortfall = {k:max(0,project[k]-resources.get(r,0)) for k,r in
                     [('minerals','minerals'),('vespene','vespene'),('supply','supply_remaining')]}
        criteria[f'save_for_{i}'] = (f'Commit to saving for {name} for up to 224 game loops (about ten seconds), purchasing it if it becomes executable before that review. No other purchase will spend that reserved budget during this commitment. '
            f'The engine offers its ability when resource requirements are ignored, but no executable purchase/site is currently offered. '
            f'Resource shortfall: {shortfall}. '+investment_description(name,project,state))
    carried = False
    choice = None
    plan = (memory or {}).get('investment_intent',{})
    if (plan.get('mode')=='save_for_project' and
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
        answer = await jev.ask(investment_state(state), {'investment': {
            'type':'choice',
            'instructions':'Allocate the shared resources across the entire force. Choose the single next investment, or save. '
                           'This decision controls all new training and construction; no other selection will spend resources this tick. '
                           'Existing queues continue. Compare the marginal benefit of each available project in the current situation.',
            'criteria':criteria,
        }})
        prediction = answer.get('investment',{})
        choice = prediction.get('choice')
        probabilities = prediction.get('probabilities',{})
        weights = {k:float(v) for k,v in probabilities.items()
                   if k in criteria and isinstance(v,(int,float)) and math.isfinite(v) and v>0}
        if memory is not None and weights:
            rng = memory.setdefault('investment_rng',random.Random(20260918))
            sampled = rng.choices(list(weights),weights=list(weights.values()),k=1)[0]
            jev.log('investment_sample',loop=view['loop'],top_choice=choice,
                    sampled_choice=sampled,probabilities=weights,seed=20260918)
            choice = sampled
    jev.log('investment_choice',loop=view['loop'],choice=choice,projects=names,future_projects=future_names,
            source='carried_jev_commitment' if carried else 'jev_distribution')
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
    if len(options)==1:
        return [options[0][1]['command']]
    criteria = {f'option_{i}':f'Unit {u["tag"]} at {u["position"]}, current orders {u.get("orders",[])}: {c["description"]}'
                for i,(u,c) in enumerate(options)}
    answer = await jev.ask({'objective':state.get('objective'),
                            'selected_investment':names[int(choice.split('_')[1])],
                            'visible_entities':state.get('visible_entities',[])}, {'producer_site': {
        'type':'choice','instructions':'Execute your selected investment using one of these legal producer/site choices. Consider current work and location.',
        'criteria':criteria,
    }})
    choice=answer.get('producer_site',{}).get('choice')
    if choice in criteria:
        return [options[int(choice.split('_')[1])][1]['command']]
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
            'count':len(selected),
            'total_health':round(sum(u.get('health',0) for u in selected),1),
            'max_separation':round(max(math.dist(a['position'],b['position']) for a in selected for b in selected),1),
            'largest_distance_to_nearest_selection_member':round(max(min(math.dist(a['position'],b['position']) for b in selected if b['tag']!=a['tag']) for a in selected),1) if len(selected)>1 else None,
            'count_change_since_previous_decision':len(selected)-previous_counts.get(kind,len(selected)),
            'damaged_count':sum(u.get('health_fraction',1)<1 for u in selected),
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


def control_groups(units, mode, learned):
    groups = {}
    for unit in units:
        ids = {c['id'] for c in unit['candidates']}
        has_attack = any(k.startswith('attack') for k in ids)
        has_move = bool(ids & {'north','south','east','west'})
        economic = (any(k.startswith('gather_') for k in ids)
                    or unit.get('available_build_abilities')
                    or any(c.startswith(('Build ', 'Harvest')) for c in learned.get(unit['type'],[])))
        key = 'MobileCombat' if mode=='mobile_combat' and has_attack and has_move and not economic else unit['type']
        groups.setdefault(key, []).append(unit)
    return groups


async def decide(view, jev, memory):
    """Jev chooses shared or individual orders for each unit-type selection."""
    units = [{**u,'candidates':[c for c in u['candidates'] if not is_purchase(c)]}
             for u in view['self']]
    if not units:
        return []
    cohorts = {}
    for unit in units:
        cohorts.setdefault(unit['type'], []).append(unit)
    state = {k:view.get(k) for k in ('objective','resources','explored_map','visible_entities','last_known_entities','unit_type_facts')}
    state['recent_outcomes'] = recent_outcomes(view, memory)
    state['previous_investment_intent'] = memory.get('investment_intent')
    learned = memory.setdefault('observed_capabilities_by_type', {})
    for unit in view['self']:
        capabilities = set(learned.get(unit['type'], []))
        for candidate in unit['candidates']:
            label = candidate['description']
            if label.startswith(('Train ', 'Build ')):
                capabilities.add(label.split(';')[0].split(' at visible')[0])
            if candidate['id'].startswith('gather_'):
                capabilities.add('Harvest resources')
        learned[unit['type']] = sorted(capabilities)
    state['observed_capabilities_by_type'] = learned
    state['units'] = [{k:u.get(k) for k in ('tag','type','position','health_fraction','orders','build_progress','cargo','energy')}
                      for u in units]
    state['type_selection_facts'] = selection_facts(view,cohorts,{})
    cohorts = control_groups(units,memory.get('coordination','by_type'),learned)
    state['selection_facts'] = selection_facts(view,cohorts,memory.get('previous_cohort_counts',{}))
    strategy = memory.get('strategy')
    if strategy is None or view['loop']-strategy['loop'] >= 112:
        options = {
            'attack':'Commit forces to damaging or destroying the enemy base.',
            'strengthen':'Increase military strength through resource collection and production.',
            'protect':'Preserve owned units and structures from current threats.',
            'assemble':'Bring separated units together and accumulate a force before committing to an engagement.',
            'explore':'Acquire information about the map and enemy positions.',
            'recover':'Restore income and replace losses.',
            'hold':'Let current tasks progress before changing commitment.',
        }
        decision = await jev.ask({**state,'previous_strategy':strategy}, {'strategy': {
            'type':'choice',
            'instructions':'Choose the current strategic priority for completing the mission. '
                           'Consider resources, own force, known enemy force, and recent_outcomes. Reassess your previous strategy using these measured outcomes. '
                           'This priority will inform further Jev decisions; it does not execute a scripted plan.',
            'criteria':options,
        }, 'coordination': {
            'type':'choice',
            'instructions':'Choose how to organize the next control selections. This chooses grouping only; further Jev decisions choose every order.',
            'criteria':{
                'by_type':'Keep different unit types in separate selections, allowing different shared orders.',
                'mobile_combat':'Combine units with movement and attack controls, excluding observed workers/builders, into a mixed combat selection. Give that force shared orders or choose individual control. Other units keep type selections.',
            },
        }})
        selected = decision.get('strategy',{}).get('choice')
        if selected in options:
            strategy = {'loop':view['loop'],'choice':selected,'description':options[selected]}
            memory['strategy'] = strategy
            jev.log('strategy_choice',**strategy)
        grouping = decision.get('coordination',{}).get('choice')
        if grouping in ('by_type','mobile_combat'):
            memory['coordination'] = grouping
            jev.log('coordination_choice',loop=view['loop'],choice=grouping)
            cohorts = control_groups(units,grouping,learned)
            state['selection_facts'] = selection_facts(view,cohorts,memory.get('previous_cohort_counts',{}))
    memory['previous_cohort_counts'] = {k:len(v) for k,v in cohorts.items()}
    state['strategy_chosen_by_jev'] = strategy
    questions, tables, plans = {}, {}, {}
    for kind, selected in cohorts.items():
        tables[kind] = [{c['id']:c for c in u['candidates']} for u in selected]
        common = set.intersection(*(set(c) for c in tables[kind]))
        criteria = {'individual':'Choose separate orders for these units using further Jev decisions.',
                    'continue':'Keep the current orders of these units unchanged.'}
        plans[kind] = {}
        for key in sorted(common):
            descriptions = list(dict.fromkeys(re.sub(r', distance [0-9.]+','',c[key]['description']) for c in tables[kind]))
            description = ' | '.join(descriptions[:4])
            if len(descriptions)>4:
                description += f' (descriptions vary across {len(descriptions)} units; apply each offered version)'
            distances = [math.dist(u['position'],t[key]['command']['point'])
                         for u,t in zip(selected,tables[kind]) if 'point' in t[key]['command']]
            if distances:
                description += f'; travel distances across selection: {min(distances):.1f} to {max(distances):.1f}'
            criteria['group_'+key] = f'Every one of the {len(selected)} {kind} units receives: ' + description
            plans[kind]['group_'+key] = [c[key]['command'] for c in tables[kind]]
        # A member cannot join itself, so intersection alone hid in-selection
        # anchors. Expose the exact legal hold + join combination to Jev.
        for anchor,anchor_table in zip(selected,tables[kind]):
            key = f'join_{anchor["tag"]}'
            if key in common or 'hold_position' not in anchor_table:
                continue
            followers = [(u,t) for u,t in zip(selected,tables[kind]) if u['tag']!=anchor['tag']]
            if not followers or not all(key in t for _,t in followers):
                continue
            option = 'group_'+key
            criteria[option] = (f'Regroup this selection at {anchor["type"]} unit {anchor["tag"]} '
                                f'position {anchor["position"]}: that unit holds position; '
                                f'the other {len(followers)} units move to its observed position.')
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
                           'Other selections receive their own decisions in parallel. '
                           'Consider current orders, health, resources and known entities. '
                           'Count alone is not local fighting strength: max_separation and nearest-selection-member distances describe dispersion. '
                           'Use selection_facts for unit counts, recent changes, damage and economic capabilities. '
                           'Consider the strategic priority chosen by Jev alongside immediate threats. '
                           'Snapshot locations are stale, not live visible targets.',
            'criteria':criteria,
        }
    # Separate semantic contribution from concrete command selection. Both are
    # Jev choices; categorization describes controls and never chooses a tactic.
    meanings = {
        'income':'Collect resource income to fund unit production and construction.',
        'production':'Produce more units.',
        'construction':'Construct one of the available_projects buildings, including any supply capacity listed there.',
        'combat':'Attack enemies or attack-move toward a location.',
        'positioning':'Move, regroup, scout, stop or hold position.',
        'other':'Use another available ability.',
        'individual':'Let separate Jev decisions choose orders for individual units.',
        'continue':'Keep the existing orders unchanged, whatever those orders currently are.',
    }
    def purpose(kind,key):
        if key in ('continue','individual'):
            return key
        if key.startswith('unit_'): return 'construction'
        action_id=key[len('group_'):]
        if action_id.startswith('gather_'): return 'income'
        if action_id.startswith('build_'): return 'construction'
        if 'attack' in action_id: return 'combat'
        if action_id.startswith('join_'): return 'positioning'
        if tables[kind][0][action_id]['description'].startswith('Train '): return 'production'
        if action_id.startswith('ability_'): return 'other'
        return 'positioning'
    purpose_questions = {f'purpose_{kind}': {
        'type':'choice',
        'instructions':f'Choose how the {len(cohorts[kind])} {kind} units should contribute to completing the mission now. '
                       'Different unit types can make different contributions to the same strategy. '
                       'Use their capabilities, current orders, resources and threats.',
        'criteria':{p:meanings[p]+((' Available: '+'; '.join(state['selection_facts'][kind]['available_support_abilities'])) if p=='other' else '')
                    for p in sorted({purpose(kind,k) for k in q['criteria']})},
    } for kind,q in questions.items()}
    async def choose_orders():
        roles = await jev.ask(state,purpose_questions) if purpose_questions else {}
        answers, concrete_questions = {}, {}
        for kind,q in questions.items():
            role=roles.get(f'purpose_{kind}',{}).get('choice')
            jev.log('purpose_choice',loop=view['loop'],cohort=kind,choice=role)
            if role in ('continue','individual'):
                answers[kind]={'choice':role}
            else:
                criteria={k:v for k,v in q['criteria'].items() if purpose(kind,k)==role}
                if criteria:
                    criteria['continue']='Keep current orders without reissuing them. If they already implement the chosen contribution, this maintains that work.'
                    concrete_questions[kind]={**q,'criteria':criteria,
                                              'instructions':q['instructions']+' Jev selected this contribution: '+meanings[role]}
        if concrete_questions:
            answers.update(await jev.ask(state,concrete_questions))
        commands = []
        for kind, selected in cohorts.items():
            choice = answers.get(kind,{}).get('choice')
            jev.log('group_choice',loop=view['loop'],cohort=kind,choice=choice,unit_count=len(selected))
            if choice == 'individual':
                submemory = memory.setdefault('cohorts',{}).setdefault(kind,{})
                commands.extend(await decide_individual({**view,'self':selected},jev,submemory))
            elif choice in plans[kind]:
                commands.extend(plans[kind][choice])
        return commands
    investment, commands = await asyncio.gather(choose_investment(view,state,jev,memory), choose_orders())
    # A selected purchase assigns its producer; preserve other Jev-selected orders.
    producer_tags = {c['unit_tag'] for c in investment}
    return [c for c in commands if c['unit_tag'] not in producer_tags]+investment


async def decide_individual(view, jev, memory):
    # Candidate construction is mechanical; Jev selects each unit's action.
    # Start small: combat/movement experiments, no hand-coded build order.
    units = view['self']
    if not units:
        return []
    questions = {}
    state = {'objective': view['objective'], 'resources': view['resources']}
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
