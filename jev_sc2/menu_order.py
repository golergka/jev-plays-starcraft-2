"""Reproducible presentation order, independent of game state and choice meaning."""
import hashlib


def permute_concrete_menus(questions, selection_facts, seed):
    if seed is None:
        return questions
    result = {}
    for name, question in questions.items():
        criteria = question.get('criteria')
        if name not in selection_facts or question.get('type') != 'choice' or not criteria:
            result[name] = question
            continue
        def rank(key):
            payload = '\0'.join((str(seed), name, key)).encode()
            return hashlib.sha256(payload).digest(), key
        result[name] = {**question, 'criteria': {
            key: criteria[key] for key in sorted(criteria, key=rank)}}
    return result
