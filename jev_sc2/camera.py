"""Presentation-only camera director; never selects or changes unit orders."""
import math
import time


def choose_shot(view, memory, now=None):
    now = time.monotonic() if now is None else now
    units = view.get('self', [])
    if not units:
        return None
    enemies = [e for e in view.get('visible_entities', []) if e.get('alliance') == 'Enemy']
    previous = memory.get('units', {})
    shots = []
    for unit in units:
        pos = unit['position']
        old = previous.get(unit['tag'])
        vitality = unit.get('health', 0) + unit.get('shield', 0)
        damaged = old is not None and vitality < old.get('vitality', old['health'])
        moved = old is not None and math.dist(pos, old['position']) > .4
        contacts = [e for e in enemies if math.dist(pos, e['position']) <= 14]
        ids = {c['id'] for c in unit.get('candidates', [])}
        combat = any(i.startswith('attack') for i in ids)
        economic = any(i.startswith(('gather_', 'build_')) for i in ids)
        firing = unit.get('weapon_cooldown', 0) > 0
        # Mobile combat units remain interesting even between movement samples.
        score = 15 if combat and not economic else 1
        reason = 'army overview' if combat and not economic else 'base overview'
        moving_until = memory.setdefault('moving_until', {})
        if moved and not economic:
            moving_until[unit['tag']] = now + 4
        if moving_until.get(unit['tag'], -1) > now:
            score, reason = 35 if combat else 20, 'moving force'
        if contacts:
            score, reason = 60 + min(len(contacts), 10), 'visible engagement'
        if firing:
            score, reason = max(score, 85), 'weapons firing'
        if damaged:
            score, reason = 110, 'taking damage'
        nearby = [u for u in units if math.dist(pos, u['position']) <= 9]
        # Frame one local scene rather than averaging unrelated areas of the map.
        # Follow the subject, not a crowd of workers/buildings behind it.
        points = [pos] * 3 + [e['position'] for e in contacts]
        if contacts:
            points += [u['position'] for u in nearby]
        center = [sum(p[i] for p in points)/len(points) for i in (0, 1)]
        key = (round(pos[0]/12), round(pos[1]/12))
        recent = max((stamp for cell, stamp in memory.get('visited', {}).items()
                      if math.dist(cell, key) <= 1.5), default=-1000)
        score *= .65 if now-recent < 24 else 1
        shots.append({'position':center, 'reason':reason, 'score':score,
                      'key':key, 'urgent':damaged, 'tag':unit['tag']})
    memory['units'] = {u['tag']:{'position':u['position'][:], 'health':u.get('health', 0),
                              'vitality':u.get('health', 0)+u.get('shield', 0)} for u in units}
    memory['moving_until'] = {tag:deadline for tag,deadline in memory.get('moving_until', {}).items()
                              if tag in memory['units'] and deadline > now}
    best = max(shots, key=lambda s:s['score'])
    current = memory.get('shot')
    age = now-memory.get('cut_at', -1000)
    if current:
        close = math.dist(best['position'], current['position']) < 7
        # Tracking is separate from cutting: keep an army on screen during a shot.
        tracked = next((s for s in shots if s['tag'] == current.get('tag')), None)
        urgent_cut = best['urgent'] and not close and age >= 2.5
        if tracked and (age < 7 or (close and age < 12)) and not urgent_cut:
            if (now-memory.get('pan_at', -1000) >= 1 and
                    math.dist(tracked['position'], current['position']) >= 2):
                memory['shot'] = tracked
                memory['pan_at'] = now
                return {'position':tracked['position'], 'reason':'tracking ' + tracked['reason']}
            return None
        # Keep a readable shot; only a new damage event elsewhere can cut early.
        if age < 7 and not (best['urgent'] and not close and age >= 2.5):
            return None
        if close and age < 12:
            return None
    memory['shot'] = best
    memory['cut_at'] = now
    memory['pan_at'] = now
    memory.setdefault('visited', {})[best['key']] = now
    # Bound history for arbitrarily long campaigns.
    memory['visited'] = {k:v for k,v in memory['visited'].items() if now-v < 60}
    return {'position':best['position'], 'reason':best['reason']}
