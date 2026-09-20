# Lab 595: localize the harvesting review trigger

Audit found continuing_income disabled its shortcut whenever any enemy was visible
anywhere. Static distant enemies therefore forced repeated concrete worker order
questions despite a Jev-selected income role and an ongoing harvest cycle.

The shortcut now requests review for an enemy within12 map units of any selected
worker, or unknown geometry. This reuses the existing local-neighborhood scale in
selection facts. It is a scheduling heuristic, not a guarantee of safety or an
instruction to ignore distant opponents. No new task, target or order is chosen.
Existing672-loop expiry, strategy/membership changes, health decrease and loss of
harvesting still force reviews; abstract Jev role reviews continue independently.
Long-range threats can fall outside the radius; damage still invalidates reuse.

14 routine-execution tests passed including distant/nearby/unknown enemy geometry.
No paid calls and no live trial yet; actual savings and gameplay effects unproven.
