"""Compare full Choice with the complete production tournament, without game actions."""
import argparse
import asyncio
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dotenv import load_dotenv
from jev_sc2.jev import Jev
from player import ask_order_menus


def reconstruct(rows, selection):
    eligible = []
    for index, event in enumerate(rows):
        if event.get('event') != 'order_menu_tournament' or event.get('question') != selection:
            continue
        calls = [row for row in rows[:index] if row.get('event') == 'jev'
                 and set(row.get('questions', {})) == {selection}][-2:]
        if len(calls) != 2 or calls[0]['state'] != calls[1]['state']:
            continue
        left, right = [call['questions'][selection] for call in calls]
        if {k:v for k,v in left.items() if k != 'criteria'} != {
                k:v for k,v in right.items() if k != 'criteria'}:
            continue
        if set(left['criteria']) & set(right['criteria']):
            continue
        full = {**left, 'criteria': {**left['criteria'], **right['criteria']}}
        if len(full['criteria']) != event['options'] or len(json.dumps(full)) <= 16000:
            continue
        # Bound this experiment to exactly two leaves and one finalist call.
        items = list(full['criteria'].items())
        halves = [items[:len(items)//2], items[len(items)//2:]]
        if any(len(json.dumps({**full, 'criteria': dict(half)})) > 16000 for half in halves):
            continue
        eligible.append((event['time'], calls[0]['state'], full))
    return eligible


async def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--selection', default='Marine')
    parser.add_argument('--run', action='store_true', help='Issue at most 12 paid requests; default only validates inputs')
    args = parser.parse_args()
    rows = [json.loads(line) for line in args.source.read_text().splitlines()]
    eligible = reconstruct(rows, args.selection)
    if len(eligible) < 3:
        raise ValueError('Need three distinct, exactly reconstructable two-leaf tournaments')
    samples = [eligible[i] for i in (0, len(eligible)//2, len(eligible)-1)]
    print(json.dumps({'eligible': len(eligible), 'sample_option_counts': [len(q['criteria']) for _,_,q in samples], 'paid': args.run}))
    if not args.run:
        return
    load_dotenv(Path(__file__).resolve().parents[1]/'.env')
    model = Jev(lambda *a, **k: None, 'order-menu-cost-probe', max_calls=12)
    result = {'source': str(args.source), 'selection': args.selection, 'pairs': [],
              'method': 'First/middle/last reconstructed two-leaf menus. Both arms receive identical full state and criteria, in reconstructed order. Alternate arm order. Compare one full request against all three production tournament requests. Costs are measured, not estimated. No game commands; three samples do not establish live quality.'}
    try:
        for index, (stamp, state, question) in enumerate(samples):
            pair = {'source_time': stamp, 'options': len(question['criteria'])}
            result['pairs'].append(pair)
            arms = ['full', 'tournament'] if index % 2 == 0 else ['tournament', 'full']
            for arm in arms:
                before_cost, before_calls, started = model.cost, model.calls, time.monotonic()
                questions = {args.selection: question}
                answer = await (model.ask(state, questions) if arm == 'full'
                                else ask_order_menus(state, questions, model))
                pair[arm] = {'answer': answer[args.selection], 'cost_usd': model.cost-before_cost,
                             'calls': model.calls-before_calls, 'wall_seconds': time.monotonic()-started}
                result.update(calls=model.calls, cost_usd=model.cost)
                args.output.write_text(json.dumps(result, indent=2)+'\n')
    except BaseException as exc:
        result.update(error=type(exc).__name__, calls=model.calls, cost_usd=model.cost)
        args.output.write_text(json.dumps(result, indent=2)+'\n')
        raise
    print(json.dumps({'calls': model.calls, 'cost_usd': model.cost}))


if __name__ == '__main__':
    asyncio.run(main())
