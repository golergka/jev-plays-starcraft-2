# Lab 619: expose observed vertical coordinates

Repeated movement to nearby entities motivated inspection of positional context. The adapter retained only x/y even though current raw unit positions include optional z. Add observed_world_z to owned and currently visible entity records, and retain it in the player's unit roster. Missing protobuf z remains null; hidden units stay excluded. Snapshot fields remain unchanged.

The shared combat context explicitly distinguishes API unit-position z from terrain connectivity or a route. Flying/model offsets can affect altitude. No hidden path query, destination filtering, route selection, or tactical rule is introduced.

93 infrastructure tests passed, including distinct own/visible z, hidden-unit exclusion and missing-z handling. Commit reloads adapter and player during trial618, so its later behavior includes this observation change. No claim yet that z explains repeated relic movement or improves decisions.
