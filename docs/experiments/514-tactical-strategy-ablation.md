# Lab 514: broad strategy hint does not explain three tactical choices

Reused the existing strategy-hint probe on three concrete MobileCombat requests
from trial 512 (loops 1532, 1846, 2592). Each paired request retained the full
recorded state and concrete question, removing only strategy_chosen_by_jev in
the treatment. Pair order alternated. Six calls cost $0.006662754.

Both arms chose group_map_attack_move_middle_east in all three pairs. This
small test provides no evidence that removing the strategic hint fixes these
orders. It does not prove the hint never matters, nor test changed strategy
wording or outcomes in a replay. No runtime change follows this negative result.
The probe now accepts an optional minimum loop and records sample loops so it
can distinguish these tactical samples from earlier contribution-role tests.
