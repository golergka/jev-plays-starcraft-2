# Lab544: sample concrete combat choices from Jev's distribution

Trial540's19 MobileCombat answers had median top-two probability margin0.06.
The first seven observations include margins0.04,0.02,0.01 and an exact tie.
Returned probabilities are model outputs, not calibrated win probabilities.
Always selecting the returned top choice discards those alternatives.

Add optional --sample-combat-orders, disabled by default. Only existing direct
mobile combat selections use this path. Sample positive probability mass over
offered identifiers with fixed seed20260920; canonical key ordering makes draws
independent of dictionary insertion order. Keep RNG in persistent player memory
across commits. No reshaping, threshold, preferred tactic, additional request,
mission identifier or map coordinate enters sampling. Invalid distributions fail
loudly. Log original choice, sampled choice and full distribution.

Earlier contribution and investment sampling experiments concern different
questions. This changes concrete mobile orders only. Sampling may increase
incoherence or select low-quality alternatives; no benefit is established.
The next trial keeps trial540 flags and seed534, adding only this option.
No seed search or root tactical intervention is permitted in the comparison.
