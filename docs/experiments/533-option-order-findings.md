# Labs 532–533: concrete menu order changes Jev choices

Using trial512's first/middle/last eligible MobileCombat requests, reverse only
criteria insertion order. State, choice identifiers, descriptions and instructions
remain identical. Alternate pair request order. Repeat the complete six-request
probe once to distinguish a repeatable response from an isolated draw.

| Loop | Original order | Reversed order |
| --- | --- | --- |
| 47 | Move west | Attack-move west |
| 6870 | Move to friendly unit 4374134785 | Continue existing orders |
| 14619 | Attack-move middle-east sector | Move middle-east sector |

Both probes produced this same table. Twelve requests cost $0.0094626 total,
using the existing shared rolling governor. No gameplay orders were issued.

This establishes order sensitivity on these three observations. It does not
establish which answer is better, a general positional bias, or a benefit from
shuffling/reversing menus. Two changed answers keep the same destination and
change execution mode; the middle sample changes the requested behavior more
substantially. Provider determinism/caching is not independently characterized.

Trial531 continues unchanged so that order preservation can be evaluated without
mixing this intervention into it. The native 4:24 view showed Zerg attacking the
Barracks and supply 6/27, with 1/4 relics and the primary objective incomplete.
Preserved orders therefore have not prevented substantial early attrition.

A subsequent general menu-order experiment should use a predetermined,
content-independent permutation, never choose a permutation to obtain a desired
tactic, and retain original identifiers in action mapping and logs. It should
not multiply online model requests through voting under the current budget.
