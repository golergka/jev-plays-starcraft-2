"""Measured controller timing facts, never a recommended review deadline."""
import statistics


def measured_cadence(history, current_loop):
    loops = [entry['loop'] for entry in history[-6:]]
    if len(loops) < 3 or any(type(loop) is not int or loop >= current_loop for loop in loops):
        return None
    gaps = [b-a for a,b in zip(loops, loops[1:])]
    if any(gap <= 0 for gap in gaps):
        return None
    median = statistics.median(gaps)
    return {
        'recent_completed_decision_gaps_game_loops': gaps,
        'median_gap_game_loops': median,
        'review_intervals_relative_to_observed_median': {
            str(n): round(n/median, 2) for n in (112,672,2016)},
        'meaning': 'Past measured controller cadence, not future timing or a recommended interval. Review deadlines are checked at decision boundaries; a deadline shorter than a decision gap can expire before the next opportunity to review. Concrete orders and investments still use fresh observations when decisions run.'}
