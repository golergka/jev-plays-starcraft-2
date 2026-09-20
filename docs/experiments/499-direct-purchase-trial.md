# Lab499: direct returned purchase choice trial

Run runs/20260920T125822.620646Z, starting revision c188dcd. Same Smash mission restarted through the existing controller, native0:17 verified. Configuration matches493 plus --investment-top-choice. Stalled-commitment-review remains enabled; it did not trigger in493. New helper snapshot loader active from this launch. All235 tests passed before launch.

No extra choice calls or manually chosen unit priorities. The existing purchase question now follows Jev's returned choice, including Save or a batch, instead of sampling its distribution. Other policy stages unchanged. Shared rolling $0.10/300s limit unchanged;1800seconds/4000calls/max-age128.

Atloop482:16successfulcalls,$0.007682556,zero errors. Two investment_top_choice events (Marine purchases),zero investment_sample events: intended selection mode verified in the live logs. Outcome pending; early purchases do not establish improvement or victory.
