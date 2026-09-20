# Lab534: optional reproducible concrete-menu permutation

Labs532–533 found reproducible order sensitivity. Add an opt-in presentation
experiment through JEV_CONCRETE_MENU_SEED. It applies only to choice questions
identified by selection_facts, not investment, strategic, or scoring questions.
SHA-256 of seed, question identifier and criterion identifier defines ordering.
The ordering never examines descriptions, health, destinations or model answers.
Every identifier, description, instruction and action mapping stays unchanged.
Repeated application (including transport splits) is idempotent. Original
questions are not mutated. Actual request menus remain in normal Jev logs.

For the next trial, preselect seed 534 (this lab number) before observing its
answers. Do not search seeds for preferred tactics. This adds no model requests.
No gameplay benefit is established; an arbitrary permutation could worsen play.

The default is disabled. Trial531 started without the environment variable and
retains its existing SDK object, so committing this does not change that trial.
At native 7:09 the Barracks near the Command Center was burning under Zerg
attack, 6/11 supply and 1/4 relics. Two preservation events retained three orders
through loop7213. Preservation has not prevented the observed base pressure.

Validation: 94 tests passed across test_menu_order.py and test_infra.py. Tests
check mapping preservation, stable reapplication despite state changes,
nonmutation, opt-out, and exclusion of nonconcrete/scoring questions.
