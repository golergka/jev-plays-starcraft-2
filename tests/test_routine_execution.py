from player import continuing_income


def test_income_continuation_expires_and_reacts_to_changes():
    memory={}
    unit={'tag':1,'health_fraction':1.0,'orders':[{'ability':'Harvest Gather SCV'}]}
    view={'loop':100,'visible_entities':[]}
    def check(role='income',strategy='strengthen'):
        return continuing_income(view,[unit],role,strategy,'worker',memory)
    assert not check()  # First observation requires Jev review.
    view['loop']=150
    unit['orders'][0]['ability']='Harvest Return SCV'
    assert check()  # Return trips are part of the same engine task.
    view['loop']=473
    assert check()  # Measured paced decisions are about373loops apart.
    view['loop']=771
    assert check()
    view['loop']=772
    assert not check()  # No indefinite rolling extension.
    view['loop']=773
    unit['health_fraction']=.9
    assert not check()
    view['visible_entities']=[{'alliance':'Enemy'}]
    assert not check()
    view['visible_entities']=[]
    assert not check('other')
    assert not check()
    assert not check(strategy='protect')
    unit['orders']=[]
    assert not check(strategy='protect')  # Never assign idle workers automatically.


def test_no_membership_or_clock_rewind_reuse():
    memory={};view={'loop':100,'visible_entities':[]}
    units=[{'tag':1,'health_fraction':1,'orders':[{'ability':'Harvest Gather SCV'}]}]
    assert not continuing_income(view,units,'income','recover','workers',memory)
    units[0]['tag']=2
    assert not continuing_income(view,units,'income','recover','workers',memory)
    view['loop']=50
    assert not continuing_income(view,units,'income','recover','workers',memory)


def test_combat_controls_reach_jev_without_abstract_role_filter():
    import asyncio
    from player import decide
    commands={'north':{'unit_tag':1,'ability_id':16,'point':[0,5]},
              'attack_target':{'unit_tag':1,'ability_id':23,'target_tag':2}}
    unit={'tag':1,'type':'TestFighter','position':[0,0],'health_fraction':1,
          'candidates':[{'id':key,'description':'Attack visible enemy' if key.startswith('attack') else 'Move north','command':command}
                        for key,command in commands.items()]}
    class Model:
        seen=False
        def log(self,*args,**kwargs):pass
        async def ask(self,state,questions):
            assert 'purpose_TestFighter' not in questions
            if 'strategy' in questions:return {'strategy':{'choice':'protect'}}
            options=questions['TestFighter']['criteria']
            assert {'continue','group_north','group_attack_target'} <= options.keys()
            self.seen=True
            return {'TestFighter':{'choice':'group_attack_target'}}
    model=Model()
    assert asyncio.run(decide({'self':[unit],'loop':1},model,{}))==[commands['attack_target']]
    assert model.seen


def test_player_score_keeps_explicit_zero_and_missing_distinct():
    from s2clientprotocol import score_pb2
    from jev_sc2.view import player_score_summary
    score=score_pb2.ScoreDetails()
    assert player_score_summary(score)=={}
    score.killed_value_units=0
    score.total_damage_dealt.life=42
    score.lost_minerals.army=50
    assert player_score_summary(score)=={'killed_value_units':0,
        'total_damage_dealt':{'life':42},'lost_minerals':{'army':50}}


def test_entity_tables_preserve_visible_and_stale_facts_without_mutation():
    from player import order_state
    source={'visible_entities':[{'tag':1,'alliance':'Enemy','position':[1,2],'health':0},
                                {'tag':2,'alliance':'Neutral','position':[3,4],'health':100}],
            'last_known_entities':[{'tag':3,'position':[5,6],'last_seen_loop':12}]}
    result=order_state(source)
    for field in source:
        assert [dict(zip(result[field]['columns'],row)) for row in result[field]['rows']]==source[field]
        assert isinstance(source[field],list)
    heterogeneous={'visible_entities':[{'tag':1},{'tag':2,'health':None}]}
    assert order_state(heterogeneous)['visible_entities']==heterogeneous['visible_entities']


def test_type_tables_round_trip_and_reencoding_is_idempotent():
    from player import order_state
    facts={'Fighter':{'count':3,'capabilities':['attack']},'Worker':{'count':2,'capabilities':['harvest']}}
    result=order_state({'type_selection_facts':facts,'unit_type_facts':facts})
    for field in ('type_selection_facts','unit_type_facts'):
        table=result[field]
        assert {row[0]:dict(zip(table['columns'][1:],row[1:])) for row in table['rows']}==facts
    assert order_state(result)==result


def test_busy_builder_requires_jev_interruption_choice_and_keep_wins_over_parallel_orders():
    import asyncio
    from player import decide
    build={'unit_tag':1,'ability_id':324,'point':[4,5]}
    unit={'tag':1,'type':'Worker','position':[0,0],'health_fraction':1,
          'orders':[{'ability':'Build ExistingStructure','target_point':[2,3]}],
          'candidates':[{'id':'build_new','description':'Build NewStructure',
                         'project':{'type':'NewStructure'},'command':build},
                        {'id':'north','description':'Move north',
                         'command':{'unit_tag':1,'ability_id':16,'point':[0,6]}}]}
    class Model:
        selection='keep_construction'
        producer_calls=0
        def log(self,*args,**kwargs):pass
        async def ask(self,state,questions):
            if 'strategy' in questions:return {'strategy':{'choice':'strengthen'}}
            if 'investment' in questions:return {'investment':{'choice':'project_0'}}
            if 'producer_site' in questions:
                self.producer_calls+=1
                assert 'Interrupt' in questions['producer_site']['criteria']['option_0']
                assert 'keep_construction' in questions['producer_site']['criteria']
                return {'producer_site':{'choice':self.selection}}
            key=next(iter(questions))
            return {key:{'choice':'positioning' if key.startswith('purpose_') else 'group_north'}}
    model=Model();view={'loop':1,'self':[unit]}
    assert asyncio.run(decide(view,model,{}))==[]
    assert model.producer_calls==1  # A sole busy builder cannot bypass Jev.
    model.selection='option_0'
    assert asyncio.run(decide(view,model,{}))==[build]  # Jev can explicitly interrupt.


def test_training_batch_is_jev_selected_bounded_and_reuses_investment_choice():
    import asyncio
    from player import choose_investment
    command={'unit_tag':1,'ability_id':560}
    unit={'tag':1,'position':[0,0],'orders':[],
          'candidates':[{'description':'Train FictionalUnit','project':{'type':'FictionalUnit'},'command':command}]}
    class Model:
        calls=0
        def log(self,*a,**k):pass
        async def ask(self,state,questions):
            self.calls+=1
            assert 'batch_0' in questions['investment']['criteria']
            return {'investment':{'choice':'batch_0' if self.calls==1 else 'save'}}
    model=Model();memory={};view={'loop':1,'self':[unit]};state={'strategy_chosen_by_jev':{'choice':'strengthen'}}
    for loop in (1,2,3):
        view['loop']=loop
        assert asyncio.run(choose_investment(view,state,model,memory))==[command]
    assert model.calls==1 and 'production_batch' not in memory
    view['loop']=4
    assert asyncio.run(choose_investment(view,state,model,memory))==[]
    assert model.calls==2


def test_training_batch_waits_for_legal_controls_and_expires_on_strategy_change():
    import asyncio
    from player import choose_investment
    memory={'production_batch':{'target_project':'FictionalUnit','remaining':2,'loop':1,'review_at':673,'strategy':'strengthen'}}
    view={'loop':2,'self':[],'resources':{},'potential_projects':[{'type':'FictionalUnit','minerals':50,'vespene':0,'supply':1}]}
    class Model:
        calls=0
        def log(self,*a,**k):pass
        async def ask(self,state,questions):
            self.calls+=1
            return {'investment':{'choice':'save'}}
    model=Model()
    assert asyncio.run(choose_investment(view,{'strategy_chosen_by_jev':{'choice':'strengthen'}},model,memory))==[]
    assert model.calls==0 and memory['production_batch']['remaining']==2
    assert asyncio.run(choose_investment(view,{'strategy_chosen_by_jev':{'choice':'protect'}},model,memory))==[]
    assert model.calls==1 and 'production_batch' not in memory


def test_training_batch_expiry_or_rewind_requires_fresh_jev_choice():
    import asyncio
    from player import choose_investment
    class Model:
        calls=0
        def log(self,*a,**k):pass
        async def ask(self,state,questions):
            self.calls+=1
            return {'investment':{'choice':'save'}}
    for loop in (0,673):
        model=Model()
        memory={'production_batch':{'target_project':'Unit','remaining':2,'loop':1,'review_at':673,'strategy':None}}
        view={'loop':loop,'self':[{'tag':1,'position':[0,0],
            'candidates':[{'description':'Train Unit','project':{'type':'Unit'},'command':{'unit_tag':1,'ability_id':560}}]}]}
        assert asyncio.run(choose_investment(view,{},model,memory))==[]
        assert model.calls==1 and 'production_batch' not in memory


def test_exclusive_job_suppresses_passenger_order_without_creating_actions():
    from player import coordinate_exclusive_jobs
    load={'unit_tag':1,'ability_id':777,'target_tag':2}
    move={'unit_tag':2,'ability_id':16,'point':[3,4]}
    other={'unit_tag':3,'ability_id':18}
    view={'loop':1,'self':[{'candidates':[{'exclusive_target':True,'command':load}]}]}
    class Log:
        def log(self,*args,**kwargs): pass
    assert coordinate_exclusive_jobs(view,[load,move,other],set(),Log())==[load,other]
    assert coordinate_exclusive_jobs(view,[move,other],set(),Log())==[move,other]
    assert coordinate_exclusive_jobs(view,[load,move],{2},Log())==[move]
    assert coordinate_exclusive_jobs(view,[load,move],set(),Log())==[load]


def test_competing_exclusive_jobs_do_not_arbitrarily_choose_a_carrier():
    from player import coordinate_exclusive_jobs
    jobs=[{'unit_tag':tag,'ability_id':777,'target_tag':2} for tag in (1,3)]
    move={'unit_tag':2,'ability_id':16,'point':[3,4]}
    view={'loop':1,'self':[{'candidates':[{'exclusive_target':True,'command':j} for j in jobs]}]}
    class Log:
        def log(self,*args,**kwargs): pass
    assert coordinate_exclusive_jobs(view,jobs+[move],set(),Log())==[move]
