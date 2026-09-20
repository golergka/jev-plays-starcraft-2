# Lab497: committed policy helpers participate in player reload

Inspection found PlayerLoader compiled committed player/view/camera files, while delayed imports of policy helpers used Python's ordinary module cache. Editing a previously imported helper would therefore not change the running policy on later commits.

Loader now compiles the six policy helpers (intentions,bottleneck,order_families,destination_categories,order_scores,commitment_review) from the same Git revision. A private import table in each player snapshot resolves their from-imports without mutating process-global modules. Existing in-flight/old player objects retain their old helper snapshots. Framework modules remain ordinary imports. New helper modules must be added to the explicit list.

Test verifies committed content overrides dirty helper files, new player sees new helper values, old player keeps old values, and invalid helper syntax preserves the last good player/revision. This loader is instantiated by the orchestrator; current493 keeps its already-loaded loader until the next launch. No change to this trial's policy behavior and no game restart for this infrastructure fix.
