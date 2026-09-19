from copy import deepcopy
from s2clientprotocol import sc2api_pb2 as sc
from jev_sc2.jobs import next_request, acknowledge_initial


def fixture():
    command={'unit_tag':1,'ability_id':560}
    job={'executor':True,'armed':True,'command':command,'target_project':'Marine',
         'remaining':2,'loop':5,'review_at':2021,'last_request_loop':5,'strategy':'protect'}
    view={'loop':117,'resources':{'minerals':50,'vespene':0,'supply_remaining':1},
          'self':[{'tag':1,'candidates':[{'command':command,'description':'Train Marine',
                    'project':{'type':'Marine'},'resource_cost':{'minerals':50,'vespene':0,'supply':1}}]}]}
    return view, {'production_batch':job,'strategy':{'choice':'protect'}}


def test_fixed_job_is_bounded_spaced_and_ends_without_new_choices():
    view,memory=fixture(); log=lambda *a,**k:None
    assert next_request(view,memory,log)==[{'unit_tag':1,'ability_id':560}]
    assert next_request(view,memory,log)==[]
    view['loop']=229
    assert len(next_request(view,memory,log))==1
    view['loop']=230
    assert next_request(view,memory,log)==[]
    assert 'production_batch' not in memory


def test_job_waits_for_affordability_and_never_changes_producer():
    view,memory=fixture();events=[];log=lambda e,**k:events.append(e)
    view['resources']['minerals']=49
    assert next_request(view,memory,log)==[]
    assert memory['production_batch']['remaining']==2
    assert events==['production_job_wait']
    view['resources']['minerals']=50
    view['self'][0]['tag']=2
    view['self'][0]['candidates'][0]['command']={'unit_tag':2,'ability_id':560}
    assert next_request(view,memory,log)==[]
    assert 'production_batch' not in memory


def test_invalidated_or_legacy_jobs_never_execute():
    for change in ('rewind','deadline','strategy','unarmed','legacy','unavailable'):
        view,memory=fixture();job=memory['production_batch']
        if change=='rewind':view['loop']=0
        if change=='deadline':view['loop']=2021
        if change=='strategy':memory['strategy']['choice']='other'
        if change=='unarmed':job['armed']=False
        if change=='legacy':job.pop('executor')
        if change=='unavailable':view['self'][0]['candidates']=[]
        assert next_request(view,memory,lambda *a,**k:None)==[]


def test_initial_job_requires_accepted_matching_action():
    for accepted in (False,True):
        view,memory=fixture();memory['production_batch']['armed']=False
        action=sc.Action();action.action_raw.unit_command.unit_tags.append(1)
        action.action_raw.unit_command.ability_id=560
        acknowledge_initial(memory,[action],[1 if accepted else 9],5,lambda *a,**k:None)
        assert bool(memory.get('production_batch',{}).get('armed'))==accepted


def test_executor_job_requires_explicit_jev_batch_and_announces_fixed_producer():
    import asyncio
    from player import choose_investment
    view,memory=fixture();memory.pop('production_batch');memory['production_executor_enabled']=True
    view['self'][0]['position']=[0,0]
    class Model:
        def log(self,*a,**k):pass
        async def ask(self,state,questions):
            assert 'producer selected for the first request stays fixed' in questions['investment']['criteria']['batch_0']
            return {'investment':{'choice':'batch_0'}}
    commands=asyncio.run(choose_investment(view,{'strategy_chosen_by_jev':{'choice':'protect'}},Model(),memory))
    assert commands==[{'unit_tag':1,'ability_id':560}]
    job=memory['production_batch']
    assert job['executor'] and not job['armed'] and job['remaining']==2
    assert next_request(view,memory,lambda *a,**k:None)==[]
