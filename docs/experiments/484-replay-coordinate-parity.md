# Lab 484: match live and replay coordinate systems

Previous turn classified as progress: replay loaded with original map data and produced new player-view evidence.

The live join sets raw_crop_to_playable_area=True. Lab483 replay omitted that option. Set the diagnostic to match the live interface and reran the same five checkpoints. Barracks 4349493269 now reports [81.5,10.5], exactly matching the live trace instead of [93.5,18.5]. This resolves the positional discrepancy without changing gameplay or claiming a simulation mismatch.

All five checkpoints still show no attached add-on and no orders. Both placement query variants still return generic Error. Coordinate correction therefore does not resolve the query issue. Replay queries are not sufficient evidence to filter live choices.

Source review: python-sc2's Unit.build forwards an optional target, default None, to the creation ability; this supports untargeted construction as a valid general API pattern but does not prove campaign add-on behavior or successful placement at this site. https://burnysc2.github.io/python-sc2/_modules/sc2/unit.html#Unit.build

Next useful check is live placement/available-ability validation, with a known ordinary build as a control, rather than further replay placement variants. Keep the execution issue distinct from Jev's inadequate army/resource decisions. No model calls, no gameplay orders, no campaign credit, no policy changes.
