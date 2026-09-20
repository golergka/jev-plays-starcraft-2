"""Measure observable changes between model reviews; never schedule or act."""
import math


class ReviewEvents:
    def __init__(self):
        self.previous = None
        self.pending = []

    def observe(self, view, waiting):
        own = {u['tag']: float(u['health']) for u in view['self']}
        nearby = {e['tag'] for e in view.get('visible_entities', [])
                  if e.get('alliance') == 'Enemy' and any(
                      math.dist(e['position'], u['position']) <= 12 for u in view['self'])}
        current = (view['loop'], own, nearby)
        if self.previous is not None:
            loop, prior, threats = self.previous
            if view['loop'] < loop:
                self.pending.clear()
            elif waiting:
                changes = {'damaged_tags': sorted(t for t in own.keys() & prior.keys() if own[t] < prior[t]),
                           'disappeared_tags': sorted(prior.keys() - own.keys()),
                           'new_nearby_enemy_tags': sorted(nearby - threats)}
                if any(changes.values()):
                    self.pending.append({'loop': view['loop'], **changes})
                    # Bounded diagnostic history, not a hidden event queue.
                    self.pending = self.pending[-128:]
        self.previous = current

    def take(self, loop):
        events, self.pending = self.pending, []
        return {'review_loop': loop, 'events': events,
                'meaning': 'Observed changes during pacing since last review, at most latest 128 observations. Disappearance is not proven death. Nearby means within 12 center-distance units of any own unit, not a tactical threat score. No automatic orders or pacing bypass.'}


def early_review_allowed(now, deadline, interval, repaid_at, events):
    """Borrow at most half one pacing interval, never while prior debt remains."""
    return (now >= repaid_at and 0 < deadline-now <= interval/2 and
            any(e['damaged_tags'] or e['new_nearby_enemy_tags'] for e in events))


def next_review_deadline(start, interval, previous_deadline, borrowed):
    """An early decision adds its full measured interval after the old deadline."""
    return (max(start, previous_deadline) if borrowed else start) + interval
