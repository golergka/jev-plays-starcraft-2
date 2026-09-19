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
