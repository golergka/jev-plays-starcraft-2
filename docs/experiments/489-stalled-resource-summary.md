# Lab489: resource arithmetic changes stalled-commitment review

Read-only audit confirmed all three lab488 states already included Marauder mineral_cost100/gas_cost25, current gas0, measured gas income0, and waiting=True in production_commitment. The negative result was not caused by omitting these facts entirely.

Repeat the exact same three recorded states and question, adding one compact summary linking the existing target cost to current resources: per-request costs, current balances, gas shortfall25, observed gas income0, elapsed loops since request, loops until deadline. No projected income, automatic cancellation, replacement purchase, or tactical advice.

All three answers changed from keep to release (.61 probability each; low confidence .21/.22/.22). Three calls cost $0.001764336. This is a small offline comparison, not a mission-success result; the runs were sequential, and provider variability is not ruled out. It supports testing a bounded Jev reconsideration stage with explicit resource facts, rather than assuming raw catalog facts reliably connect to its commitment decision.

Live486 remains unchanged. At native10:13, two Barracks were visible near the Command Center with enemies in the base. Logs record accepted Barracks placements at7126 and8427; no add-on request yet. The main experiment's PointOrNone coverage remains unexercised.
