# Lab 526: repeated current orders are an execution hypothesis

Reused lab363's accepted-command audit on trial512. It finds27 exact repeated
payloads among84 commands in unambiguous ticks:17 Train Marine,7 Attack and
3other ability295. Training repeats can represent legitimate new production;
they must not be deduplicated merely because payloads match.

A separate join with recorded unit orders finds14 successful attack-move
submissions whose unit already had Attack Attack to the same point at the
preceding model observation, across seven decision loops. This is stronger
than payload repetition, but still not proof of firing interruption: submission
uses a later observation, and no attack-cycle trace was measured.

A bounded execution experiment could preserve only an exactly matching sole
current Move/Attack order in the fresh observation. Changed targets, queues and
production must remain untouched, and maintained orders must be logged as such
rather than silently counted as discarded commands. Jev retains the action
choice. This audit alone establishes neither damage loss nor benefit from that
experiment. No runtime modification is included in this commit.
