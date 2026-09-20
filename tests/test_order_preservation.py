import pytest
from s2clientprotocol import sc2api_pb2 as sc, raw_pb2 as raw
from jev_sc2.order_preservation import preserve_current_orders

@pytest.mark.parametrize('ability', [16,23,560])
@pytest.mark.parametrize('target', ['point','unit'])
def test_only_identical_movement_and_attack_are_preserved(ability,target):
    obs=sc.ResponseObservation();obs.observation.game_loop=100
    unit=obs.observation.raw_data.units.add(tag=1,alliance=raw.Self)
    order=unit.orders.add(ability_id=ability)
    action=sc.Action();cmd=action.action_raw.unit_command
    cmd.ability_id=ability;cmd.unit_tags.append(1)
    if target=='point':
        cmd.target_world_space_pos.x=12.5;cmd.target_world_space_pos.y=9
        order.target_world_space_pos.x=cmd.target_world_space_pos.x
        order.target_world_space_pos.y=cmd.target_world_space_pos.y
        order.target_world_space_pos.z=3
    else:cmd.target_unit_tag=order.target_unit_tag=2
    send,kept=preserve_current_orders([action],obs)
    assert bool(kept)==(ability in (16,23))
    assert bool(send)==(ability not in (16,23))
    if target=='point':cmd.target_world_space_pos.x+=1
    else:cmd.target_unit_tag+=1
    assert preserve_current_orders([action],obs)==([action],[])


def test_queue_and_no_target_are_not_silently_preserved():
    obs=sc.ResponseObservation();u=obs.observation.raw_data.units.add(tag=1,alliance=raw.Self)
    a=sc.Action();c=a.action_raw.unit_command;c.unit_tags.append(1);c.ability_id=16
    o=u.orders.add(ability_id=16)
    assert preserve_current_orders([a],obs)==([a],[])
    c.target_unit_tag=o.target_unit_tag=2
    c.queue_command=True
    assert preserve_current_orders([a],obs)==([a],[])
    c.queue_command=False;u.orders.add(ability_id=16,target_unit_tag=3)
    assert preserve_current_orders([a],obs)==([a],[])


def test_observed_engine_rounding_but_not_changed_destination():
    obs=sc.ResponseObservation();u=obs.observation.raw_data.units.add(tag=1,alliance=raw.Self)
    o=u.orders.add(ability_id=23);o.target_world_space_pos.x=153.333251953125;o.target_world_space_pos.y=48
    a=sc.Action();c=a.action_raw.unit_command;c.unit_tags.append(1);c.ability_id=23
    c.target_world_space_pos.x=153.3333282470703;c.target_world_space_pos.y=48
    assert preserve_current_orders([a],obs)[0]==[]
    c.target_world_space_pos.x+=0.001
    assert preserve_current_orders([a],obs)==([a],[])
