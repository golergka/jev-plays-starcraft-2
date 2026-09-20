"""Paired recorded-state test of measured cadence for Jev review choices."""
import asyncio
import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dotenv import load_dotenv
from jev_sc2.jev import Jev


async def main():
    source, output = map(Path, sys.argv[1:3])
    rows = [json.loads(line) for line in source.read_text().splitlines()]
    samples = []
    for i, row in enumerate(rows):
        if row['event'] != 'jev' or 'strategy_review' not in row.get('questions', {}):
            continue
        past = [e for e in rows[:i] if e['event'] == 'tick'][-6:]
        if len(past) < 3:
            continue
        gaps = [b['loop']-a['loop'] for a,b in zip(past,past[1:])]
        if any(g <= 0 for g in gaps):
            continue
        median = statistics.median(gaps)
        cadence = {
            'recent_completed_decision_gaps_game_loops': gaps,
            'median_gap_game_loops': median,
            'review_intervals_relative_to_observed_median': {
                str(n): round(n/median, 2) for n in (112,672,2016)},
            'meaning': 'Past measured controller cadence, not future timing or a recommended interval. Review deadlines are checked at decision boundaries; a deadline shorter than a decision gap can expire before the next opportunity to review. Concrete orders and investments still use fresh observations when decisions run.'}
        samples.append((row,cadence))
    if len(samples) < 3:
        raise ValueError('Need three strategic requests with earlier completed-decision history')
    load_dotenv(Path(__file__).resolve().parents[1]/'.env')
    model = Jev(lambda *a, **k: None, 'strategy-cadence-probe', max_calls=6)
    result = {'source':str(source), 'method':'First/middle/last eligible strategic requests. Identical complete strategic question batch; add only trailing observed cadence and computed interval ratios. Alternate arm order; six calls maximum, no game commands.', 'pairs':[]}
    for index in (0,len(samples)//2,len(samples)-1):
        row,cadence = samples[index]
        pair = {'time':row['time'], 'cadence':cadence}
        result['pairs'].append(pair)
        arms = ['original','with_cadence'] if len(result['pairs']) % 2 else ['with_cadence','original']
        for arm in arms:
            state = row['state'] if arm == 'original' else {**row['state'],'measured_decision_cadence':cadence}
            pair[arm] = await model.ask(state,row['questions'])
            result.update(calls=model.calls,cost_usd=model.cost)
            output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'calls':model.calls,'cost_usd':model.cost,'choices':[{a:{k:v['choice'] for k,v in p[a].items()} for a in ('original','with_cadence')} for p in result['pairs']]}))


if __name__ == '__main__':
    asyncio.run(main())
