"""Compare recorded investment choices with recent own-player score deltas."""
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dotenv import load_dotenv
from jev_sc2.jev import Jev


def numeric_delta(current, previous):
    result = {}
    for key, value in current.items():
        old = previous.get(key)
        if isinstance(value, dict) and isinstance(old, dict):
            result[key] = numeric_delta(value, old)
        elif isinstance(value, (int, float)) and isinstance(old, (int, float)):
            result[key] = value - old
    return result


async def main():
    source, output = map(Path, sys.argv[1:3])
    rows = [json.loads(line) for line in source.read_text().splitlines()]
    scores, samples = [], []
    for row in rows:
        if row['event'] == 'player_score':
            scores.append(row)
        if row['event'] != 'jev' or 'investment' not in row.get('questions', {}) or len(scores) < 2:
            continue
        before, after = scores[-2:]
        if after['loop'] <= before['loop']:
            continue
        outcome = {'from_loop': before['loop'], 'to_loop': after['loop'],
                   'own_player_score_changes': numeric_delta(after['values'], before['values']),
                   'meaning': 'Measured cumulative own-player score differences over the stated interval. These describe past outcomes, not causes, future predictions, target information, or a recommended action. Healing totals may include repairs; do not attribute them to a particular ability.'}
        samples.append((row, outcome))
    if len(samples) < 3:
        raise ValueError('Need three investment requests with earlier score intervals')
    result = {'source': str(source), 'method': 'First/middle/last eligible requests; same investment question and state, optionally append previous observed score interval. Alternate arm order, six calls maximum, no game commands.', 'pairs': []}
    load_dotenv(Path(__file__).resolve().parents[1] / '.env')
    model = Jev(lambda *a, **k: None, 'investment-outcomes-probe', max_calls=6)
    for index in (0, len(samples)//2, len(samples)-1):
        row, outcome = samples[index]
        pair = {'time': row['time'], 'outcome': outcome}
        result['pairs'].append(pair)
        arms = ['original', 'with_outcomes'] if len(result['pairs']) % 2 else ['with_outcomes', 'original']
        for arm in arms:
            state = row['state'] if arm == 'original' else {**row['state'], 'recent_measured_outcomes': outcome}
            pair[arm] = await model.ask(state, row['questions'])
            result.update(calls=model.calls, cost_usd=model.cost)
            output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({'calls': model.calls, 'cost_usd': model.cost, 'choices': [
        {arm: pair[arm]['investment']['choice'] for arm in ('original', 'with_outcomes')}
        for pair in result['pairs']]}))


if __name__ == '__main__':
    asyncio.run(main())
