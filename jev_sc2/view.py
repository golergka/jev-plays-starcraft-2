"""Player-visible facts, mechanical action candidates and legality checks."""
import math
from s2clientprotocol import raw_pb2 as raw, sc2api_pb2 as sc, query_pb2 as query


def bearing(dx, dy):
    """Translate geometry into words without choosing a tactical response."""
    if math.hypot(dx, dy) < 0.1:
        return 'same position'
    directions = ['east','northeast','north','northwest','west','southwest','south','southeast']
    return directions[round(math.atan2(dy, dx)/(math.pi/4)) % 8]


async def make_view(client, observation, data, info, objective):
    obs = observation.observation
    own = [u for u in obs.raw_data.units if u.alliance == raw.Self]
    # Do not pass snapshots, hidden units, or enemy orders to the policy.
    visible = [u for u in obs.raw_data.units if u.display_type == raw.Visible
               and u.alliance != raw.Self]
    abilities = await client.request('query', query.RequestQuery(
        abilities=[query.RequestQueryAvailableAbilities(unit_tag=u.tag) for u in own],
        ignore_resource_requirements=False))
    available = {a.unit_tag: {b.ability_id for b in a.abilities} for a in abilities.abilities}
    names = {u.unit_id: u.name for u in data.units}
    ability_names = {a.ability_id: a.friendly_name or a.button_name or a.link_name for a in data.abilities}
    remaps = {a.ability_id: a.remaps_to_ability_id for a in data.abilities}
    area = info.start_raw.playable_area
    view = {'loop': obs.game_loop, 'objective': objective, 'self': [],
            'resources': {'minerals': obs.player_common.minerals,
                          'vespene': obs.player_common.vespene,
                          'food_used': obs.player_common.food_used,
                          'food_cap': obs.player_common.food_cap}}
    for unit in own:
        legal = available.get(unit.tag, set())
        # Game versions may advertise concrete or generalized ability IDs.
        move = next((a for a in sorted(legal) if a in {16, 3794} or remaps.get(a) in {16, 3794}), None)
        attack = next((a for a in sorted(legal) if a in {23, 3674} or remaps.get(a) == 3674), None)
        def command(ability, **target):
            return {'unit_tag': unit.tag, 'ability_id': ability, **target}
        candidates = []
        surroundings = []
        for target in sorted(visible, key=lambda t: math.hypot(t.pos.x-unit.pos.x, t.pos.y-unit.pos.y))[:8]:
            distance = round(math.hypot(target.pos.x-unit.pos.x, target.pos.y-unit.pos.y), 1)
            label = names.get(target.unit_type, str(target.unit_type))
            surroundings.append({'tag':target.tag, 'type':label, 'distance':distance,
                                 'direction':bearing(target.pos.x-unit.pos.x,target.pos.y-unit.pos.y),
                                 'east_offset':round(target.pos.x-unit.pos.x,1),
                                 'north_offset':round(target.pos.y-unit.pos.y,1),
                                 'alliance':raw.Alliance.Name(target.alliance),
                                 'health':target.health, 'shield':target.shield})
            if target.alliance == raw.Enemy and attack is not None:
                candidates.append({'id':f'attack_{target.tag}',
                                   'description':f'Attack visible {label} tag {target.tag}, distance {distance}',
                                   'command':command(attack, target_tag=target.tag)})
            if target.alliance == raw.Neutral and move is not None:
                candidates.append({'id':f'move_{target.tag}',
                                   'description':f'Move to visible {label} tag {target.tag}, distance {distance}',
                                   'command':command(move, point=[target.pos.x,target.pos.y])})
        # Fixed compass displacements are action primitives, not tactical choices.
        if move is not None:
            for label, dx, dy in [('north',0,6),('south',0,-6),('east',6,0),('west',-6,0)]:
                x,y = unit.pos.x+dx, unit.pos.y+dy
                if area.p0.x <= x < area.p1.x and area.p0.y <= y < area.p1.y:
                    candidates.append({'id':label, 'description':f'Move six map units {label}',
                                       'command':command(move,point=[x,y])})
        view['self'].append({'tag':unit.tag, 'type':names.get(unit.unit_type,str(unit.unit_type)),
                             'health':unit.health, 'health_fraction':round(unit.health/max(unit.health_max,1),2),
                             'shield':unit.shield, 'weapon_cooldown':unit.weapon_cooldown,
                             'weapon_status':'ready' if unit.weapon_cooldown == 0 else 'cooling down',
                             'position':[unit.pos.x,unit.pos.y], 'surroundings':surroundings,
                             'orders':[{'ability':ability_names.get(o.ability_id,str(o.ability_id)),
                                        'target_tag':o.target_unit_tag if o.HasField('target_unit_tag') else None,
                                        'target_point':[o.target_world_space_pos.x,o.target_world_space_pos.y]
                                        if o.HasField('target_world_space_pos') else None} for o in unit.orders],
                             'candidates':candidates})
    return view


def validate_commands(commands, offered_view, fresh_observation):
    """Only exact offered commands for still-owned units and still-visible targets."""
    fresh = fresh_observation.observation
    owned = {u.tag for u in fresh.raw_data.units if u.alliance == raw.Self}
    visible = {u.tag for u in fresh.raw_data.units if u.display_type == raw.Visible}
    offered = [c['command'] for u in offered_view['self'] for c in u['candidates']]
    actions, seen = [], set()
    for cmd in commands:
        if cmd not in offered or cmd['unit_tag'] not in owned or cmd['unit_tag'] in seen:
            continue
        if 'target_tag' in cmd and cmd['target_tag'] not in visible:
            continue
        action = sc.Action()
        out = action.action_raw.unit_command
        out.ability_id = cmd['ability_id']
        out.unit_tags.append(cmd['unit_tag'])
        out.queue_command = False
        if 'target_tag' in cmd:
            out.target_unit_tag = cmd['target_tag']
        if 'point' in cmd:
            out.target_world_space_pos.x, out.target_world_space_pos.y = cmd['point']
        actions.append(action)
        seen.add(cmd['unit_tag'])
    return actions
