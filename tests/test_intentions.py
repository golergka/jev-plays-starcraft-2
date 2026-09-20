import asyncio
import pytest
from jev_sc2.intentions import production_intentions

class Model:
    def __init__(self, choice='expand'): self.calls=0; self.choice=choice
    async def ask(self,state,questions):
        self.calls+=1
        return {k:{'choice':self.choice} for k in questions}
    def log(self,*args,**kwargs): pass

def test_intentions_cache_expiry_strategy_rewind_and_no_orders():
    async def run():
        state={'observed_capabilities_by_type':{'Barracks':['Train Marine']},'unit_type_facts':{'Marine':{}},'selection_facts':{'Marine':{'count':2}}}
        model=Model();memory={}
        a=await production_intentions(state,model,memory,100,'protect')
        assert '2' in a['goals'][0]['question']
        state['selection_facts']['Marine']['count']=0
        b=await production_intentions(state,model,memory,200,'protect')
        assert model.calls==1 and b['chosen_at_loop']==100
        assert 'commands' not in b
        await production_intentions(state,model,memory,2116,'protect')
        await production_intentions(state,model,memory,2117,'attack')
        await production_intentions(state,model,memory,0,'attack')
        assert model.calls==4
        assert await production_intentions({},model,memory,1,'attack') is None
        assert 'production_intentions' not in memory
    asyncio.run(run())

def test_invalid_goal_is_loud_and_not_cached():
    async def run():
        memory={}
        with pytest.raises(ValueError):
            await production_intentions({'observed_capabilities_by_type':{'X':['Train Marine']},'unit_type_facts':{'Marine':{}}},Model('invalid'),memory,0,'attack')
        assert 'production_intentions' not in memory
    asyncio.run(run())


def test_lost_producer_does_not_erase_known_military_goal():
    async def run():
        state={'observed_capabilities_by_type':{'Barracks':['Train Marine','Train Unknown']},
               'unit_type_facts':{'Marine':{'mineral_cost':50}},
               'selection_facts':{'Marine':{'count':2}}}
        model=Model(); memory={}
        await production_intentions(state,model,memory,100,'protect')
        state['unit_type_facts']={}
        state['selection_facts']={}
        result=await production_intentions(state,model,memory,2200,'protect')
        assert len(result['goals'])==1
        assert 'Marine' in result['goals'][0]['question']
        assert 'Currently observed count: 0.' in result['goals'][0]['question']
        assert 'historical_production_type_facts' not in state
        assert model.calls==2
    asyncio.run(run())
