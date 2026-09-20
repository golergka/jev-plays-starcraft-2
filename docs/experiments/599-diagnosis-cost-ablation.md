# Lab 599: remove optional purchase diagnosis requests

Trial 596 is independently verified defeated. Its opening had the same 31 requests as trial 592 despite omitted worker questions. Inspecting player.decide shows investment and orders run concurrently, but an optional bottleneck diagnosis precedes investment selection. Three of trial592's first31 requests were diagnosis calls.

Next trial uses the same launch settings as596 except omitting --bottleneck-diagnosis. Jev still chooses strategy, roles, purchases, concrete execution and combat orders; no hand-coded replacement diagnosis is supplied. The budget and failure behavior stay unchanged. This removes an advisory model layer rather than changing any selected game action directly.

History consulted: lab467 introduced diagnosis and found two offline rebuild shifts; lab471 ended in defeat; lab504 removed diagnosis context in paired purchase probes and found repeated Bunker choices unchanged. There is no established mission benefit. This live ablation tests request cost and decision cadence, not a claim that the layer is universally useless.

Measure opening request count/cost and combat review gaps through loop1800, then independently verify outcome. A single retry is confounded by model/game variation and updated previous-attempt history; no causal victory claim from one run.
