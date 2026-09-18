"""Player-visible facts, mechanical action candidates and legality checks."""
import math
from s2clientprotocol import raw_pb2 as raw, sc2api_pb2 as sc, query_pb2 as query


def pixel(image, x, y):
    x, y = math.floor(x), math.floor(y)
    if not (0 <= x < image.size.x and 0 <= y < image.size.y):
        return None
    index = y*image.size.x+x
    if image.bits_per_pixel == 8 and index < len(image.data):
        return image.data[index]
    if image.bits_per_pixel == 1 and index//8 < len(image.data):
        return (image.data[index//8] >> (7-index%8)) & 1
    return None


def visible_terrain(visibility, pathing, x, y):
    # Full-map static data is never exposed at unexplored or fogged coordinates.
    if pixel(visibility, x, y) != 2:
        return 'unknown (not currently visible)'
    value = pixel(pathing, x, y)
    if value is None:
        return 'unknown (terrain unavailable)'
    return 'walkable static terrain' if value else 'blocked static terrain'


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
    catalog = {a.ability_id:a for a in data.abilities}
    products = {u.ability_id:u for u in data.units if u.ability_id}
    placements, placement_candidates = [], []
    area = info.start_raw.playable_area
    view = {'loop': obs.game_loop, 'objective': objective, 'self': [],
            'resources': {'minerals': obs.player_common.minerals,
                          'vespene': obs.player_common.vespene,
                          'food_used': obs.player_common.food_used,
                          'food_cap': obs.player_common.food_cap,
                          'supply_remaining': max(0,obs.player_common.food_cap-obs.player_common.food_used),
                          'supply_blocked': obs.player_common.food_used >= obs.player_common.food_cap}}
    for unit in own:
        legal = available.get(unit.tag, set())
        # Game versions may advertise concrete or generalized ability IDs.
        move = next((a for a in sorted(legal) if a in {16, 3794} or remaps.get(a) in {16, 3794}), None)
        attack = next((a for a in sorted(legal) if a in {23, 3674} or remaps.get(a) == 3674), None)
        def command(ability, **target):
            return {'unit_tag': unit.tag, 'ability_id': ability, **target}
        candidates = []
        for ability in sorted(legal):
            label = ability_names.get(ability, '')
            product = products.get(ability)
            details = '' if product is None else (
                f'; costs {product.mineral_cost} minerals and {product.vespene_cost} gas'
                f'; requires {product.food_required:g} supply; provides {product.food_provided:g} supply')
            if label.startswith('Train '):
                candidates.append({'id':f'ability_{ability}', 'description':label+details,
                                   'command':command(ability)})
            if label.startswith('Build ') and catalog[ability].target == 2:
                radius = catalog[ability].footprint_radius or 1.5
                offset = radius % 1
                for direction, dx, dy in [('north',0,6),('south',0,-6),('east',6,0),('west',-6,0)]:
                    x, y = math.floor(unit.pos.x)+dx+offset, math.floor(unit.pos.y)+dy+offset
                    cells = [(px,py) for px in range(math.floor(x-radius),math.ceil(x+radius))
                             for py in range(math.floor(y-radius),math.ceil(y+radius))]
                    if not all(area.p0.x <= px < area.p1.x and area.p0.y <= py < area.p1.y
                               and pixel(obs.raw_data.map_state.visibility,px,py)==2 for px,py in cells):
                        continue
                    placement = query.RequestQueryBuildingPlacement(ability_id=ability,placing_unit_tag=unit.tag)
                    placement.target_pos.x, placement.target_pos.y = x,y
                    placements.append(placement)
                    placement_candidates.append((candidates,{
                        'id':f'build_{ability}_{direction}',
                        'description':f'{label} at visible engine-checked site [{x},{y}]'+details,
                        'command':command(ability,point=[x,y]),
                    }))
        for label, ids, description in [
            ('stop', {4,3665}, 'Stop the current order; normal automatic targeting remains possible'),
            ('hold_position', {18,3793}, 'Hold position here instead of continuing the current movement order'),
        ]:
            ability = next((a for a in sorted(legal) if a in ids or remaps.get(a) in ids), None)
            if ability is not None:
                candidates.append({'id':label, 'description':description,
                                   'command':command(ability)})
        surroundings = []
        terrain = {}
        for target in sorted(visible, key=lambda t: math.hypot(t.pos.x-unit.pos.x, t.pos.y-unit.pos.y))[:8]:
            distance = round(math.hypot(target.pos.x-unit.pos.x, target.pos.y-unit.pos.y), 1)
            label = names.get(target.unit_type, str(target.unit_type))
            gather = next((a for a in sorted(legal) if a in {295,3666} or remaps.get(a)==3666), None)
            if gather is not None and target.mineral_contents > 0:
                candidates.append({'id':f'gather_{target.tag}',
                                   'description':f'Gather minerals from visible {label}, distance {distance}',
                                   'command':command(gather,target_tag=target.tag)})
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
            for teammate in own:
                if teammate.tag == unit.tag:
                    continue
                distance = math.hypot(teammate.pos.x-unit.pos.x, teammate.pos.y-unit.pos.y)
                candidates.append({'id': f'join_{teammate.tag}',
                                   'description': f'Move to friendly {names.get(teammate.unit_type, str(teammate.unit_type))} tag {teammate.tag}, distance {distance:.1f}',
                                   'command': command(move, point=[teammate.pos.x, teammate.pos.y])})
            for label, dx, dy in [('north',0,6),('south',0,-6),('east',6,0),('west',-6,0)]:
                x,y = unit.pos.x+dx, unit.pos.y+dy
                if area.p0.x <= x < area.p1.x and area.p0.y <= y < area.p1.y:
                    terrain[label] = visible_terrain(obs.raw_data.map_state.visibility,
                                                    info.start_raw.pathing_grid,x,y)
                    candidates.append({'id':label, 'description':f'Move six map units {label}; destination: {terrain[label]}',
                                       'command':command(move,point=[x,y])})
        view['self'].append({'tag':unit.tag, 'type':names.get(unit.unit_type,str(unit.unit_type)),
                             'build_progress':round(unit.build_progress,3),
                             'health':unit.health, 'health_fraction':round(unit.health/max(unit.health_max,1),2),
                             'shield':unit.shield, 'weapon_cooldown':unit.weapon_cooldown,
                             'weapon_status':'ready' if unit.weapon_cooldown == 0 else 'cooling down',
                             'position':[unit.pos.x,unit.pos.y], 'surroundings':surroundings,
                             'nearby_terrain':terrain,
                             'orders':[{'ability':ability_names.get(o.ability_id,str(o.ability_id)),
                                        'target_tag':o.target_unit_tag if o.HasField('target_unit_tag') else None,
                                        'target_point':[o.target_world_space_pos.x,o.target_world_space_pos.y]
                                        if o.HasField('target_world_space_pos') else None} for o in unit.orders],
                             'candidates':candidates})
    if placements:
        checked = await client.request('query',query.RequestQuery(
            placements=placements,ignore_resource_requirements=False))
        if len(checked.placements) != len(placement_candidates):
            raise RuntimeError('SC2 placement response length mismatch')
        for (candidates,candidate), result in zip(placement_candidates,checked.placements):
            if result.result == 1:
                candidates.append(candidate)
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
