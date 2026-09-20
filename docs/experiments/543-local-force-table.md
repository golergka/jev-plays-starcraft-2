# Lab543: local force aggregation did not change sampled choices

The current observation already contains catalog damage/range/target classes,
unit health and shields, positions, group dispersion and nearby-enemy counts.
This probe aggregates selected units and visible enemies within12 of any member
by type, with summed observed health/shields and their existing catalog weapons.
It does not predict a winner or expose hidden information. All menus and their
recorded insertion order stay identical between arms.

First/middle/last threatened MobileCombat observations from trial540: loops621,
8489 and15070. Original and augmented choices match in all three pairs. Six
requests cost $0.006096384. No gameplay commands; no runtime deployment.

This small negative test does not prove the representation never helps. It does
rule out treating a missing aggregate force table as an established explanation
for these three decisions. Earlier lab447 tested weapon-present versus weaponless
subgroups; this test instead joins local enemy and friendly type/health facts.
