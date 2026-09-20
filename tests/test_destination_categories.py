import asyncio
import copy
import pytest
from jev_sc2.destination_categories import category, select_categories

class Model:
    def __init__(self, choice): self.choice=choice; self.calls=0
    async def ask(self,state,questions):
        self.calls+=1
        return {k:{'choice':self.choice} for k in questions}
    def log(self,*a,**k):pass

def test_all_options_preserved_with_exact_terrain_descriptions():
    criteria={'group_east':'blocked terrain', 'group_attack_move_west':'walkable',
              'group_map_move_middle_east':'unknown', 'group_last_known_move_1':'stale',
              'group_move_2':'visible mineral', 'support_heal':'heal', 'continue':'keep'}
    q={'units':{'type':'choice','instructions':'choose','criteria':criteria}}
    original=copy.deepcopy(q); recovered={}
    for kind in {category(k) for k in criteria}:
        result=asyncio.run(select_categories({},q,Model(kind)))
        assert not recovered.keys() & result['units']['criteria'].keys()
        recovered.update(result['units']['criteria'])
    assert recovered==criteria and q==original

def test_single_category_skips_model_and_unknown_orders_survive():
    model=Model('invalid');q={'units':{'type':'choice','instructions':'choose','criteria':{'new_ability':'unknown','continue':'keep'}}}
    assert asyncio.run(select_categories({},q,model))==q
    assert model.calls==0

def test_invalid_category_raises():
    q={'units':{'type':'choice','instructions':'choose','criteria':{'group_east':'step','continue':'keep'}}}
    with pytest.raises(ValueError):asyncio.run(select_categories({},q,Model('invented')))
