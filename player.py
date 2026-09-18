"""Live-reloaded experiment policy. All action choices come from Jev.

Contract: async decide(view: dict, jev, memory: dict) -> list[command dict].
The harness owns sockets, action validation, telemetry, and persistent memory.
Commit this file to activate it at the next decision boundary.
"""


async def decide(view, jev, memory):
    # Candidate construction is mechanical; Jev selects each unit's action.
    # Start small: combat/movement experiments, no hand-coded build order.
    units = view['self'][:12]
    if not units:
        return []
    questions = {}
    state = {'objective': view['objective'], 'units': [], 'resources': view['resources']}
    candidates = {}
    for unit in units:
        tag = str(unit['tag'])
        options = {'continue': None}
        actions = {'continue': None}
        for candidate in unit['candidates']:
            options[candidate['id']] = candidate['description']
            actions[candidate['id']] = candidate['command']
        candidates[tag] = actions
        state['units'].append({k: v for k, v in unit.items() if k != 'candidates'})
        questions[tag] = {
            'type': 'choice',
            'instructions': f'Choose the next action for unit tag {tag} to advance the objective. '
                            'Use this unit’s health, current orders and visible surroundings. '
                            'Continue means keep its existing order without sending a command.',
            'criteria': options,
        }
    answers = await jev.ask(state, questions)
    commands = []
    for tag, answer in answers.items():
        if tag not in candidates or answer.get('choice') not in candidates[tag]:
            continue
        action = candidates[tag][answer['choice']]
        if action is not None:
            commands.append(action)
    return commands
