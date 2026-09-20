"""Preserve matching active Move/Attack orders; never choose a tactic."""
import math
from s2clientprotocol import raw_pb2 as raw


def preserve_current_orders(actions, observation):
    own = {u.tag: u for u in observation.observation.raw_data.units if u.alliance == raw.Self}
    send, maintained = [], []
    for action in actions:
        cmd = action.action_raw.unit_command
        unit = own.get(cmd.unit_tags[0]) if len(cmd.unit_tags) == 1 else None
        match = False
        if (cmd.ability_id in (16, 23) and not cmd.queue_command
                and unit is not None and len(unit.orders) == 1):
            order = unit.orders[0]
            if order.ability_id == cmd.ability_id:
                if cmd.HasField('target_unit_tag') and order.HasField('target_unit_tag'):
                    match = cmd.target_unit_tag == order.target_unit_tag
                elif cmd.HasField('target_world_space_pos') and order.HasField('target_world_space_pos'):
                    # Observed engine rounding differs by ~7.6e-5 map units.
                    match = all(math.isclose(getattr(cmd.target_world_space_pos, axis),
                                             getattr(order.target_world_space_pos, axis),
                                             rel_tol=0, abs_tol=0.0001) for axis in ('x','y'))
        if match:
            record = {'unit_tag': unit.tag, 'ability_id': cmd.ability_id,
                      'observed_loop': observation.observation.game_loop,
                      'coordinate_tolerance': 0.0001}
            if cmd.HasField('target_unit_tag'):
                record['target_tag'] = cmd.target_unit_tag
            else:
                record['point'] = [cmd.target_world_space_pos.x, cmd.target_world_space_pos.y]
            maintained.append(record)
        else:
            send.append(action)
    return send, maintained
