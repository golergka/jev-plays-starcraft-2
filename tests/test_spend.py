import json
import pytest
from jev_sc2.spend import RollingSpend, SpendThrottled


def test_shared_rolling_window_reserves_before_requests_and_survives_restart(tmp_path):
    now=[1000.0]
    a=RollingSpend(tmp_path/'spend.db',limit=.02,reserve=.01,clock=lambda:now[0])
    b=RollingSpend(tmp_path/'spend.db',limit=.02,reserve=.01,clock=lambda:now[0])
    first=a.acquire();second=b.acquire()
    with pytest.raises(SpendThrottled) as error:a.acquire()
    assert error.value.retry_after==300
    a.settle(first,.002)
    with pytest.raises(SpendThrottled):b.acquire()
    b.settle(second,.002)
    a.acquire()  # Actual costs release unused reservations.
    now[0]=1301
    b.acquire()  # Sliding expiry, no fixed time buckets.


def test_unknown_bill_keeps_reservation_and_actual_overshoot_throttles(tmp_path):
    budget=RollingSpend(tmp_path/'spend.db',limit=.01,reserve=.01,clock=lambda:1000)
    token=budget.acquire();budget.settle(token,None)
    with pytest.raises(SpendThrottled):budget.acquire()
    budget.settle(token,.03)
    with pytest.raises(SpendThrottled) as error:budget.acquire()
    assert error.value.spent==.03


def test_ramp_persists_and_hot_configuration_is_read(tmp_path):
    now=[1000.0];config=tmp_path/'budget.json'
    config.write_text(json.dumps({'start_usd_per_5_min':.42,'target_usd_per_5_min':.1,'ramp_seconds':10800,'started_at':1000}))
    def create():return RollingSpend(tmp_path/'spend.db',clock=lambda:now[0],config_path=config)
    assert create().limit==pytest.approx(.42)
    now[0]+=5400
    assert create().limit==pytest.approx(.26)
    now[0]+=5400
    assert create().limit==pytest.approx(.1)
    now[0]+=5000
    assert create().limit==pytest.approx(.1)


def test_seed_recent_logged_cost_once(tmp_path):
    directory=tmp_path/'run';directory.mkdir()
    (directory/'events.jsonl').write_text(json.dumps({'event':'jev','time':999,'response':{'usage':{'cost':.02}}})+'\n')
    b=RollingSpend(tmp_path/'spend.db',limit=.02,clock=lambda:1000)
    b.seed(tmp_path);b.seed(tmp_path)
    with pytest.raises(SpendThrottled) as error:b.acquire()
    assert error.value.spent==.02


def test_concurrent_process_style_reservations_cannot_all_admit(tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    path=tmp_path/'spend.db'
    RollingSpend(path,limit=.02,reserve=.01,clock=lambda:1000)
    def attempt(_):
        try:
            RollingSpend(path,limit=.02,reserve=.01,clock=lambda:1000).acquire()
            return True
        except SpendThrottled:
            return False
    with ThreadPoolExecutor(max_workers=8) as pool:
        assert sum(pool.map(attempt,range(8)))==2


def test_wrapper_throttles_before_sdk_and_settles_actual_cost(tmp_path):
    import asyncio
    from types import SimpleNamespace
    from jev_sc2.jev import Jev
    requests=[]
    async def request(**kwargs):
        requests.append(kwargs)
        return SimpleNamespace(usage=SimpleNamespace(cost=.002),
            model_dump=lambda **kw:{'answers':{'q':{'choice':'keep'}}})
    model=Jev.__new__(Jev)
    model.client=SimpleNamespace(alpha=SimpleNamespace(decisions=SimpleNamespace(create_async=request)))
    model.model='typesafe/jev-1.13';model.session='test';model.log=lambda *a,**kw:None
    model.calls=0;model.inflight=0;model.max_calls=None;model.cost=0
    model.spend=RollingSpend(tmp_path/'spend.db',limit=.01,reserve=.01,clock=lambda:1000)
    assert asyncio.run(model.ask({}, {'q':{'criteria':{'keep':'Continue'}}}))['q']['choice']=='keep'
    assert model.cost==.002
    with pytest.raises(SpendThrottled):
        asyncio.run(model.ask({}, {'q':{'criteria':{'keep':'Continue'}}}))
    assert len(requests)==1 and model.calls==1 and model.inflight==0


def test_cli_budget_failure_is_loud_and_nonzero(monkeypatch, capsys):
    from jev_sc2 import __main__ as harness
    attempts=[]
    async def denied(args):
        attempts.append(args)
        raise SpendThrottled(12,.1,.1)
    monkeypatch.setattr(harness,'run',denied)
    monkeypatch.setattr('sys.argv',['jev_sc2','--attach'])
    with pytest.raises(SystemExit) as error:
        harness.main()
    assert error.value.code==2
    assert len(attempts)==1
    assert 'Controller stopped; no automatic retry' in capsys.readouterr().err
