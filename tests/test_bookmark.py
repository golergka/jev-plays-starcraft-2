import asyncio
from types import SimpleNamespace
from s2clientprotocol import sc2api_pb2 as sc, data_pb2 as data
from jev_sc2.bookmark import BookmarkRecovery


def observation(results=(), structure=True):
    o = sc.ResponseObservation()
    o.observation.game_loop = 12500
    o.observation.raw_data.units.add(tag=10, alliance=1, unit_type=7 if structure else 8,
                                     health=100, build_progress=1)
    for player, result in enumerate(results, 1):
        o.player_result.add(player_id=player, result=result)
    return o


class Client:
    status = sc.in_game
    def __init__(self):
        self.requests = []
        self.fail = False
    async def request(self, name, body):
        self.requests.append(name)
        if self.fail:
            raise RuntimeError('unavailable')
        if name == 'quick_load':
            self.status = sc.in_game
    async def observe(self):
        o = observation()
        o.observation.game_loop = 2
        return o


def recovery(enabled=True):
    client = Client()
    events = []
    catalog = SimpleNamespace(units=[SimpleNamespace(unit_id=7, attributes=[data.Structure])])
    b = BookmarkRecovery(client, catalog, lambda name, **fields: events.append((name,fields)), enabled)
    return b, client, events


def test_bookmark_is_opt_in():
    b,c,events = recovery(False)
    asyncio.run(b.maybe_save(observation()))
    assert c.requests == []


def test_save_is_throttled_and_recovery_is_bounded():
    async def scenario():
        b,c,events = recovery()
        await b.maybe_save(observation())
        await b.maybe_save(observation())
        assert c.requests == ['quick_save']
        c.status = sc.ended
        failed = observation([sc.Defeat,sc.Defeat])
        assert await b.recover(failed)
        assert events[-1][1]['loop'] == 2
        c.status = sc.ended
        assert not await b.recover(failed)
        await b.maybe_save(observation())
        assert c.requests == ['quick_save','quick_load']
    asyncio.run(scenario())


def test_victories_mixed_results_and_missing_buildings_never_restore():
    async def scenario():
        b,c,_ = recovery()
        await b.maybe_save(observation())
        c.status = sc.ended
        for o in [observation([sc.Victory,sc.Defeat]), observation([sc.Defeat]),
                  observation([sc.Defeat,sc.Defeat],structure=False)]:
            assert not await b.recover(o)
        assert c.requests == ['quick_save']
    asyncio.run(scenario())


def test_failed_load_consumes_retry_and_records_error():
    async def scenario():
        b,c,events = recovery()
        await b.maybe_save(observation())
        c.status = sc.ended
        c.fail = True
        assert not await b.recover(observation([sc.Defeat,sc.Defeat]))
        assert b.attempted
        assert events[-1][0] == 'api_bookmark_restore_failed'
    asyncio.run(scenario())
