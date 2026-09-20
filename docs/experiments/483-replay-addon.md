# Lab 483: player-POV replay inspection

The initial replay launch failed with `LaunchError: Unable to open map.` Supplying the exact original map bytes in RequestStartReplay.map_data loaded it successfully. The diagnostic uses player 1, fog enabled, non-real-time stepping, and no action requests or model calls. It does not credit campaign progress.

At loops 21188, 21190, 21688, 21690, and 22479, Barracks 4349493269 was idle with add_on_tag zero. Both placement-query variants (omitted target and producer center) returned generic Error throughout. This does not establish placement-query support in replay or the correct add-on target semantics; do not deploy a legality filter based on these results. The replay reports position [93.5,18.5]; compare authoritative live evidence before asserting coordinate equivalence.

Native screenshot after stepping visibly showed the replay at 23:24/26:36: 2179 minerals, 340 gas, 12/27 supply, one of four relics, and enemy units inside the base near supply depots and the command center. The command center selected in this view had full health. This reinforces the observed combination of unspent resources and inadequate defense, without assigning a tactical intervention to the framework. It also verifies that the screen now displays the replay rather than the black view left by the failed launch.

Cost: zero Jev calls. No gameplay policy changed. Continue periodic native visual checks alongside telemetry; replay observations are diagnostic, not a new live attempt.
