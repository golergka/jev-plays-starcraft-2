"""Concurrent work whose children must finish before its owner can shut down."""
import asyncio


async def gather_owned(*awaitables):
    tasks = [asyncio.ensure_future(work) for work in awaitables]
    try:
        return await asyncio.gather(*tasks)
    except BaseException:
        for task in tasks:
            if not task.done():
                task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        raise
