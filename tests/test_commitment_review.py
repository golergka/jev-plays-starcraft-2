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
