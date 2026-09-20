# Labs 524–525: offering proximity grouping

Added one hypothetical coordination option: mobile non-worker selections split
into connected components with links at most12 map units; Jev would choose
orders independently for each component. Existing modes retained; no tactical
destination or preferred action prescribed. No runtime grouping was implemented.

Lab524 used first/middle/last strategic states. It changed the last choice from
mobile_combat to by_proximity, but that state had no MobileCombat selection.
The middle state had only one member. This sampling does not demonstrate useful
selection of spatial groups. Six calls cost $0.003062724.

Lab525 corrects the sample: first/middle/last strategy states whose recorded
MobileCombat max_separation exceeds12 (loops820,3053,10526). Both baseline and
treatment choose mobile_combat in all three pairs. Six calls cost $0.003409224.
The treatment is a hypothetical mode description, not observed execution or
proof grouping cannot help. No implementation/deployment follows this result.

The state audit also confirmed actual enemy proximity, damage, count decreases,
and dispersion are already supplied. At2592 it reports four members,291health,
41.1max separation and nearby Hydralisks/Mutalisk among other visible enemies.
The repeated advance cannot be attributed simply to all these facts being absent.
