# Lab 485: live placement control and PointOrNone coverage

Lab484 was progress: it resolved the replay/live coordinate discrepancy. This diagnostic starts a separate non-real-time mission with no action requests, model calls, or campaign credit.

At loop zero, a normal SCV SupplyDepot query returned Success at its center and CantBuildLocationInvalid at two alternatives. Barracks ability421 returned CantLandLocationInvalid at its center and Success six units east and west. Omitted targets returned generic Error for both abilities. Thus generic omitted-target errors are not a reliable live legality filter.

Important limitation: 421 was NOT in this starting Barracks' available-ability list. Its placement query results establish geometry query behavior, not current ability availability, affordability, completed construction, or the cause of the previous failed add-on attempts.

The protobuf target enum explicitly includes PointOrNone (5). Our candidate generator handled None for this target type but only generated engine-checked point candidates for Point (2). Extend the same visible-footprint and engine-success checks to PointOrNone. Retain the untargeted candidate; Jev chooses whether/where to build. No site preference, automatic relocation, or mission-specific policy is added. The existing available-ability gate remains mandatory.

Validation: 227 tests pass, including both target modes rejecting unseen footprints and engine-rejected sites. Native screenshot at loop zero was black; it does not verify rendered gameplay. The follow-up run must start a fresh real-time game rather than restart this stepped diagnostic.
