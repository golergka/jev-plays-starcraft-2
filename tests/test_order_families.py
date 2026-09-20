import asyncio
import unittest
from jev_sc2.order_families import family, select_families

class FakeJev:
    def __init__(self, choice): self.choice = choice; self.calls = []
    async def ask(self, state, questions):
        self.calls.append(questions)
        return {k:{'choice':self.choice} for k in questions}
    def log(self, *args, **kwargs): pass

class OrderFamiliesTests(unittest.TestCase):
    def test_targets_share_regroup_family(self):
        for key in ('group_join_1', 'group_attack_move_join_2'):
            self.assertEqual(family(key), 'regroup')
        self.assertEqual(family('group_ability_999'), 'other')

    def test_partition_preserves_exact_options_and_descriptions(self):
        criteria={'group_join_1':'move to friend','group_attack_move_join_2':'fight toward friend',
                  'group_attack_3':'attack enemy','continue':'unchanged','group_ability_999':'unknown ability'}
        q={'units':{'type':'choice','instructions':'choose','criteria':criteria}}
        recovered={}
        for kind in {family(k) for k in criteria}:
            jev=FakeJev(kind)
            result=asyncio.run(select_families({},q,jev))
            recovered.update(result['units']['criteria'])
            self.assertEqual(len(jev.calls),1)
        self.assertEqual(recovered,criteria)
        self.assertEqual(q['units']['criteria'],criteria)

    def test_invalid_answer_is_loud(self):
        q={'units':{'type':'choice','instructions':'choose','criteria':{'continue':'keep','group_join_1':'join'}}}
        with self.assertRaises(ValueError):
            asyncio.run(select_families({},q,FakeJev('invented')))

    def test_single_family_avoids_extra_call(self):
        jev=FakeJev('invalid')
        q={'units':{'type':'choice','instructions':'choose','criteria':{'continue':'keep'}}}
        self.assertEqual(asyncio.run(select_families({},q,jev)),q)
        self.assertEqual(jev.calls,[])
