# Addon placement review

Sources checked:
- https://github.com/Blizzard/s2client-proto/blob/master/s2clientprotocol/query.proto
- https://github.com/Blizzard/s2client-proto/blob/master/docs/protocol.md#action-errors

The protocol defines a building-placement query with ability ID, optional target
position and optional placing-unit tag. It does not specify addon-specific
coordinates or guarantee that omitting the position tests an engine-defined
addon site. Initial action validation and later execution failures are reported
separately, through ResponseAction and ResponseObservation.

Local implementation: `jev_sc2/view.py` offers catalog Build abilities with target
1 or5 as untargeted actions, labelled engine-defined location. Only target2
point builds pass through placement queries. Therefore the recorded addon
requests were offered without independent placement preflight. This is not proof
that their sites were invalid or their command format wrong.

`observe_action_failures` is called on ordinary, background-job and post-decision
observations. The recorded run has no corresponding delayed failure. Sparse
model-state logs cannot substitute for an engine reproduction. Lab481 also has
a later Marine request at24403; earlier observations already showed no ongoing
addon order, so it does not establish that request interrupted construction.

Next diagnostic: on an observed owned producer, compare advertised ability,
placement-query behavior and subsequent orders/addon observations. Keep the
query result diagnostic until its addon semantics are empirically established;
do not silently remove actions using an assumed coordinate convention. No new
live game, model calls, tactical commands or policy changes in this review.
