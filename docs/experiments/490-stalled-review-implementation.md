# Lab490: optional Jev review of stalled production reservations

Implements lab489's resource-summary question behind --stalled-commitment-review (default off). Only armed, waiting executor jobs with remaining requests, matching strategy, and at least224loops since the last request qualify. Runs at an already scheduled investment review, not every observation. Keep caches672loops; release removes only the remaining reservation, leaving submitted engine orders untouched. Invalid answers raise. Missing gas cost/current balance skips the question instead of inventing facts. Shared Jev governor applies.

Purchase descriptions disclose the additional release opportunity when enabled. Subsequent purchase selection remains with Jev. No mission-specific rule, automatic release, gas assignment, or replacement production target. Current486 lacks the flag and remains unchanged across reload.

Validation:230 tests pass, including keep-cache/no-call when not stalled, explicit release preserving other memory, and invalid-answer failure preserving reservation. Offline evidence remains only three sequential pairs; improved campaign performance unproven. Next controlled run can enable the flag.
