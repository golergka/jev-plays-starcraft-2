import asyncio
import pytest
from jev_sc2.concurrency import gather_owned


def test_failure_cancels_and_joins_nested_siblings_before_owner_closes_log():
    async def run():
        started = asyncio.Event()
        events = []
        async def request():
            started.set()
            try:
                await asyncio.Event().wait()
            finally:
                await asyncio.sleep(0)
                events.append('request cleanup')
        async def denied():
            await started.wait()
            raise RuntimeError('budget denied')
        with pytest.raises(RuntimeError, match='budget denied'):
            await gather_owned(gather_owned(request()), denied())
        events.append('log closed')
        assert events == ['request cleanup', 'log closed']
        assert not [t for t in asyncio.all_tasks() if t is not asyncio.current_task() and not t.done()]
    asyncio.run(run())


def test_owned_gather_preserves_result_order():
    async def run():
        async def value(x):return x
        assert await gather_owned(value(1),value(2)) == [1,2]
    asyncio.run(run())
