"""Offline trace of Jev's strategic and selection decisions for armed units."""
import json
import sys
from pathlib import Path


def audit(run):
    rows = []
    for line in (run / 'events.jsonl').read_text().splitlines():
        event = json.loads(line)
        if event['event'] != 'jev':
            continue
        state = event.get('state', {})
        answers = event.get('response', {}).get('answers', {})
        if 'coordination' in answers:
            rows.append({'time': event['time'], 'loop': state.get('game_loop'),
                         'kind': 'strategy', 'answers': answers})
        for key, question in event.get('questions', {}).items():
            facts = state.get('selection_facts', {}).get(key, {})
            if not any(m['type'] == 'Marine' for m in facts.get('members', [])):
                continue
            answer = answers.get(key, {})
            choice = answer.get('choice')
            rows.append({'time': event['time'], 'loop': state.get('game_loop'),
                         'kind': 'selection', 'selection': key,
                         'strategy': state.get('strategy_chosen_by_jev'),
                         'choice': choice,
                         'description': question.get('criteria', {}).get(choice),
                         'facts': facts})
    return {'run': str(run), 'rows': rows,
            'limits': 'Recorded observations only. Marine is an audit filter, not a gameplay rule. Spatial separation is straight-line distance, not route length. No causal claim or game commands.'}


if __name__ == '__main__':
    result = audit(Path(sys.argv[1]))
    Path(sys.argv[2]).write_text(json.dumps(result, indent=2) + '\n')
    for row in result['rows']:
        if row['kind'] == 'strategy':
            print(row['loop'], 'strategy', {k: a.get('choice') for k, a in row['answers'].items()})
        else:
            f = row['facts']
            print(row['loop'], row['selection'], row['choice'], 'count', f.get('count'),
                  'spread', f.get('max_separation'), 'nearby', f.get('visible_enemies_within_12_of_any_member'))
