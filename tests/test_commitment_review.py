import asyncio
import pytest
from jev_sc2.commitment_review import review_stalled

def fixture(choice):
    state={'strategy_chosen_by_jev':{'choice':'grow'},'unit_type_facts':{'Unit':{'mineral_cost':100,'gas_cost':25}}}
    view={'loop':500,'resources':{'minerals':200,'vespene':0,'estimated_vespene_per_minute':0}}
    job={'executor':True,'armed':True,'waiting':True,'remaining':1,'loop':0,'review_at':2000,'strategy':'grow','last_request_loop':100,'target_project':'Unit'}
    memory={'production_batch':job}
    class Model:
        calls=0
        def log(self,*a,**k):pass
        async def ask(self,s,q):
            self.calls+=1
            assert s['remaining_request_resource_facts']['gas_shortfall_for_one_request']==25
            return {'commitment_review':{'choice':choice}}
    return state,view,Model(),memory

def test_release_requires_jev_and_removes_only_reservation():
    s,v,m,mem=fixture('release');mem['other']='preserved'
    asyncio.run(review_stalled(s,v,m,mem))
    assert mem=={'other':'preserved'} and m.calls==1

def test_keep_caches_and_nonstalled_skips():
    s,v,m,mem=fixture('keep')
    asyncio.run(review_stalled(s,v,m,mem));asyncio.run(review_stalled(s,v,m,mem))
    assert m.calls==1
    v['loop']=1200;mem['production_batch']['waiting']=False
    asyncio.run(review_stalled(s,v,m,mem));assert m.calls==1

def test_invalid_answer_is_loud_and_keeps_reservation():
    s,v,m,mem=fixture('invalid')
    with pytest.raises(ValueError):asyncio.run(review_stalled(s,v,m,mem))
    assert mem['production_batch']['remaining']==1

def test_release_refreshes_next_purchase_context():
    from player import choose_investment
    s,v,m,mem=fixture('release')
    mem['stalled_commitment_review_enabled']=True
    s['production_commitment']=dict(mem['production_batch'])
    v['self']=[{'tag':1,'position':[0,0],'candidates':[{
        'description':'Train Unit','command':{'unit_tag':1,'ability_id':560},
        'project':{'type':'Unit','minerals':100,'vespene':0},
        'resource_cost':{'minerals':100,'vespene':0,'supply':0}}]}]
    class Model:
        calls=[]
        def log(self,*a,**k):pass
        async def ask(self,state,questions):
            self.calls.append(next(iter(questions)))
            if 'commitment_review' in questions:
                return {'commitment_review':{'choice':'release'}}
            assert state['production_commitment'] is None
            return {'investment':{'choice':'save'}}
    model=Model()
    assert asyncio.run(choose_investment(v,s,model,mem))==[]
    assert model.calls==['commitment_review','investment']
    assert s['production_commitment']['remaining']==1
