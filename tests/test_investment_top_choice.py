import asyncio
import pytest
from player import choose_investment

@pytest.mark.parametrize('dependencies', [False, True])
@pytest.mark.parametrize('choice', ['project_0','save','invalid'])
def test_returned_purchase_choice_is_not_resampled(choice, dependencies):
    command={'unit_tag':1,'ability_id':560}
    view={'loop':5,'resources':{'minerals':100,'vespene':0,'supply_remaining':2},'self':[
        {'tag':1,'position':[0,0],'candidates':[{'description':'Train Marine','command':command,
        'project':{'type':'Marine','minerals':50,'vespene':0},'resource_cost':{'minerals':50,'vespene':0,'supply':1}}]}]}
    class Model:
        def log(self,*a,**k):pass
        async def ask(self,s,q):
            if 'investment' not in q:
                return {k: {'choice': 'complementary'} for k in q}
            assert ('your_purchase_dependency_assessments' in s) == dependencies
            return {'investment':{'choice':choice,'probabilities':{'save':1.0}}}
    memory={'investment_top_choice_enabled':True, 'purchase_dependencies_enabled':dependencies}
    call=choose_investment(view,{},Model(),memory)
    if choice=='invalid':
        with pytest.raises(ValueError):asyncio.run(call)
    else:
        assert asyncio.run(call)==([command] if choice=='project_0' else [])
    assert 'investment_rng' not in memory
