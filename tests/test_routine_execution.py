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
    view['loop']=212
    assert not check()  # No indefinite rolling extension.
    view['loop']=213
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
