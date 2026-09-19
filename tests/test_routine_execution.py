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
