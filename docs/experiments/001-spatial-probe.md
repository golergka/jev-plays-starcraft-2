# Synthetic probe: named directions versus signed offsets

This is an API/prompt experiment, **not gameplay**. Source:
`scripts/probe_jev.py`; exact returned choices and timings:
[001-spatial-probe.json](001-spatial-probe.json).

Four open-ground scenarios ask a critically wounded Marine to move directly away
from an adjacent melee enemy. Each is asked separately, then all four are batched.
Repeat with named enemy directions versus signed north/east offsets. Scenario IDs
are neutral (`case_a` etc.), so they do not reveal the direction.

| Representation | Separate calls | One four-question batch |
|---|---|---|
| Named direction | 4/4 correct; 332–540 ms each | 4/4 correct; 340 ms |
| Signed offsets | 3/4 correct; 328–582 ms each | 4/4 correct; 959 ms |

The separate negative-north case selected south, toward the attacker, with 0.69
probability. In the numeric batch it selected north by just 0.51 versus 0.49.
Named cases were decisive. Across ten calls median latency was 390.5 ms and total
reported cost was $0.000227136. This tiny unrandomized test is a diagnostic, not a
benchmark; latency differences need repetitions before drawing conclusions.

An earlier pilot accidentally included directions in scenario IDs; it is excluded
from this comparison. The corrected run supports testing semantic spatial labels
in the actual player, consistent with TypeSafe's documented numeric weaknesses.
Do not confuse confidence with demonstrated correctness or hand-code the tactical
answer: Python may label enemy bearing; Jev must still choose the action.
