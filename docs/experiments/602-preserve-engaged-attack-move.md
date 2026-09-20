# Lab 602: preserve a repeated attack-move while engaged

Lab601 observed Marines reporting an Attack Attack target followed by Attack Attack to the same point Jev repeatedly selected. The duplicate-order utility previously required exactly one order, so it resent these attack-moves.

Extend the existing opt-in --preserve-current-orders behavior only for exactly two orders: ability23 with a nonzero unit target followed by ability23 with a point. The new unqueued single-unit command must also be ability23 to the same point within the existing0.0001 coordinate tolerance. Preserve the engagement and pending destination; log preserved_engagement=true. Changed points, queued submissions, other abilities and longer queues pass through. Medic healing/Scan Move remains unchanged because this patch does not establish that equivalence.

This does not select an enemy, destination, or strategy. Jev still selects the repeated destination. It deliberately treats that repetition as maintaining the current engagement, even if the two observed orders were originally explicitly queued; it cannot prove engine provenance from observation alone. A future deliberate request to interrupt an engagement while retaining its destination would need an explicit force-reissue control.

Nine order-preservation tests pass, including the observed two-order shape and refusal cases. The helper is imported by the controller and is not in its live player reload set: current trial599 remains unchanged; evaluate this on the next controller launch. No improvement in mission outcome has yet been established.
