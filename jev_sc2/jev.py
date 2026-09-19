"""Only Jev, via the documented OpenRouter Decisions SDK endpoint."""
import os
import json
import asyncio
import time
from openrouter import OpenRouter


class CallBudgetReached(Exception):
    pass


class Jev:
    def __init__(self, log, session, max_calls=None):
        key = os.environ.get('OPENROUTER_API_KEY')
        if not key:
            raise RuntimeError('Set OPENROUTER_API_KEY in .env')
        self.model = os.getenv('JEV_MODEL', 'typesafe/jev-1.13')
        if self.model not in {'typesafe/jev-1.13', '~typesafe/jev-latest'}:
            raise ValueError('This experiment permits Jev only')
        self.client = OpenRouter(api_key=key, x_open_router_title='Jev StarCraft Lab')
        self.log, self.session = log, session
        self.calls = 0
        self.inflight = 0
        self.max_calls = max_calls
        self.cost = 0.0

    async def ask(self, state, questions):
        # Conservative transport-size heuristic, not a token-count guarantee.
        # Preserve every question/criterion and the identical fair state.
        if len(questions) > 1 and len(json.dumps([state, questions])) > 80000:
            items = list(questions.items())
            middle = len(items)//2
            self.log('jev_request_split', questions=len(items),
                     request_chars=len(json.dumps([state, questions])))
            halves = await asyncio.gather(
                self.ask(state, dict(items[:middle])),
                self.ask(state, dict(items[middle:])))
            return {key:value for half in halves for key,value in half.items()}
        if self.max_calls is not None and self.calls + self.inflight >= self.max_calls:
            raise CallBudgetReached()
        self.inflight += 1
        try:
            started = time.monotonic()
            response = await self.client.alpha.decisions.create_async(
                model=self.model, state=state, questions=questions,
                session_id=self.session, timeout_ms=2000, retries=None,
                # SDK 1.1.158 otherwise appends /api/alpha to /api/v1 (404).
                server_url='https://openrouter.ai',
            )
            self.calls += 1
            self.cost += response.usage.cost or 0
            result = response.model_dump(mode='json')
            self.log('jev', latency_ms=round((time.monotonic()-started)*1000),
                     state=state, questions=questions, response=result)
            return result['answers']
        finally:
            self.inflight -= 1
