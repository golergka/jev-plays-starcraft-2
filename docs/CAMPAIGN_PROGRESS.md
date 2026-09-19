# Three-campaign objective

Scope confirmed by the user: Wings of Liberty, Heart of the Swarm, and Legacy of
the Void. No campaign has been completed. Two mission victories are verified.

The user subsequently authorized individual campaign missions played in sequence
with progression recorded here. Native campaign controls and account achievement
credit are not required. The standalone-map route is therefore the active route.
Only verified victories advance this journal; merely loading a later map does not.

| Campaign | Mission | Verified result |
| --- | --- | --- |
| Wings of Liberty | Liberation Day (`traynor01`) | **Victory**, API player 1, loop 3512; lab 048 |
| Wings of Liberty | The Outlaws (`traynor02`) | **Victory**, API player 1; lab 079 |
| Heart of the Swarm | Campaign | Not started; normal UI offers purchase |
| Legacy of the Void | Campaign | Not started; normal UI says Purchase To Play |

## Native-client inspection — 2026-09-18

Saved the preceding standalone second-mission replay under the ignored
`runs/campaign-transition/` directory, then used `leave_game`. API status became
`launched`, but the client displayed a black screen rather than campaign menus.
After `quit`, temporarily removed `-listen` and `-port` from Battle.net's
additional arguments, leaving `-displayMode 0`, and launched with Play.
Authentication succeeded and the normal campaign interface appeared.

- Wings of Liberty offers **New Campaign**.
- Heart of the Swarm opens a digital-download purchase screen. Its displayed
  `RUB 0` prices are not verified checkout prices or evidence of ownership.
- Legacy of the Void's main story explicitly says **Purchase To Play**; the
  epilogue is locked. Its prologue is listed separately.

The official [protocol lifecycle](https://github.com/Blizzard/s2client-proto/blob/master/docs/protocol.md)
and [request definitions](https://github.com/Blizzard/s2client-proto/blob/master/s2clientprotocol/sc2api.proto)
document standalone create/join and observation/action requests, but provide no
native campaign-menu navigation or persistent campaign save-loading request.
This does not prove all integration routes impossible; an API attachment to a
normal campaign remains unverified. Do not label independent extracted-map runs
as completion of the native campaigns or fabricate campaign-bank progress.

Restored `-listen 127.0.0.1 -port 5001 -displayMode 0` through Battle.net to continue
Jev-only standalone experiments while that integration gap remains open.

## Lab 043: missing player command

The action vocabulary offered targeted attack and point movement, but omitted
point-targeted attack-move. Added four compass attack-move candidates using the
same queried attack ability, bounds and player-visible terrain descriptions.
Jev still selects every action. No direction, route, combat priority or build
order is selected by the harness. Next trial returns to the opening mission to
measure command uptake, health and progress. This is not a victory claim.

Result: 220 calls cost $0.053164. Jev selected attack-move actions; all six ground
units remained at full health (425 total). Navigation still circled the starting
area. No victory or combat progress was verified. Summary:
`docs/experiments/026-attack-move.json`.

## Lab 044: expose the mission marker the player can already see

The normal rendered minimap displays a mission objective marker near its northern
edge, about two-thirds of the way from west to east, despite unexplored terrain.
The raw observations did not convey this UI fact. Transcribed that approximate
location into the objective text, with API map bounds x=0..102, y=0..118 and the
coordinate convention. Exact world coordinates and a route are explicitly
unknown. This is an observation from the player's screen, not hidden map-script
knowledge or an instruction to take a particular action. All choices remain Jev's.
Resume the existing map for 300 calls to see whether this information changes
navigation. This run resets policy memory but preserves live units and game state.

Result: the marker trial advanced into town, triggering the propaganda scene and
the Adjutant's warning that a large Dominion force is gathering in the town center.
300 calls cost $0.096452. This is qualitative progress, not a controlled causal
comparison and not a victory. The marker was manually transcribed, so observation
ingestion is not fully autonomous yet. Gameplay orders themselves came from Jev.

The user reiterated that exploring Jev matters more than mechanically completing
the campaign. Direct tactical orders from the supervising assistant would only be
an intermediate debugging technique; the final player must make its own choices.

## Lab 045: longer action reach

Offer move and attack-move to the centers of a uniform 3x3 partition of the playable
map. Every point is an ordinary player-clickable coordinate; its terrain is only
described when currently visible. There is no objective-specific target, path
planner, priority weight, or automatic action. Jev chooses whether to use these
alongside short movement, attack, regroup, hold and continue. Resume the marker
trial's game state to test uptake. Candidate construction requires a harness
restart; committed player policy still reloads during a running game.

Before running this trial, the user pointed out the API's map information. Added
a coarse text map directly from `StartRaw.pathing_grid` and the player's dynamic
visibility. Revealed terrain (visibility 1=fogged or 2=visible) is represented;
unexplored/full-hidden terrain stays unknown. The overview distinguishes blocked,
walkable, mixed and partially explored cells, with explicit coordinate orientation.
No route or action is computed. Both squad and unit Jev requests receive it.
Consequently lab 045 tests the combined broader observation/action interface,
not an isolated long-range-action ablation. A regression test changes hidden
terrain bytes and confirms that the Jev-facing map stays identical.

Source fields: Blizzard's [raw protocol](https://github.com/Blizzard/s2client-proto/blob/master/s2clientprotocol/raw.proto)
and [spatial layers](https://github.com/Blizzard/s2client-proto/blob/master/s2clientprotocol/spatial.proto).
The minimap `alerts` field documents unit-attacked alerts, not campaign objective
markers. Those markers are not exposed as a named raw field in these definitions.

Result: 300 calls, $0.132396, median request latency 422 ms. No long-range map
candidate was selected. The squad acquired reinforcements (ten owned units at the
end), clustered tightly, and stalled around town. No victory. This is evidence
that adding a terrain grid and more actions alone did not produce useful long
movement choices in this trial. Summary: `028-map-overview.json`.

## Lab 046: restore legitimate snapshot information

A direct API inspection with the harness stopped found `LogisticsHeadquarters`
at (72.5,108.5), alliance Enemy, display type Snapshot. There were no currently
visible enemy units in that inspection. Blizzard defines Snapshot as the dimmed
unit representation retained under fog. The earlier filter discarded this
player-known information, explaining why the objective location was missing.

Expose all snapshots as stale type/location/alliance facts, with no health,
orders or live-presence claim. Offer point-targeted move/attack-move to every
snapshot location equally. Also expose all currently visible entities globally
and all visible enemy attack targets, rather than dropping distant ones through
the nearest-eight local-context limit. Hidden units remain excluded, and the
validator still forbids tag-targeting anything not currently visible.

Remove the manually transcribed marker from the objective. Resume with only
"Destroy the Logistics Headquarters. Raynor must survive." All spatial inputs now
come directly from the player API. No route or target is selected by the harness.
13 tests pass, including stale-snapshot and hidden-terrain boundaries.

Result: 300 calls, $0.166383, median request 456.5 ms. Jev chose snapshot-location
orders and moved out of the stalled area, but the force split, lost a Marine and
ended south of its starting position. Nine units remain, 428 total health, final
separation 12.1 map units (over 40 at an intermediate measurement). No victory.
The input omission is fixed, but that alone does not establish competent navigation.

## Lab 047: Jev chooses coordination granularity

Add one Jev decision selecting either a shared order or individual control. Shared
choices are the intersection of the actual offered action IDs for all owned units;
the chosen command maps back to each unit's exact offered action and is validated
normally. Jev may instead select `individual` to invoke the existing individual
policy, or `continue` to retain all current orders. No option receives a manual
weight, no action is forced and no game-specific route is added. This tests whether
one shared model decision reduces contradictory orders and fragmentation. Log
`group_choice` events and the last eight choices/centers for measured feedback.

First segment: 29 calls ($0.006262), repeatedly selecting a shared attack-move to
the Headquarters snapshot. Reached the next town cinematic; temporarily zero
owned units made the harness stop after ten seconds. UI inspection confirmed a
cinematic, not a loss, and it was skipped through the normal UI.

Resumed segment: the force reached the Headquarters and Jev switched to shared
direct attacks on it. The final observed Headquarters health was 218, followed
by the visible **DEFEAT / Raynor has died** screen. This is a confirmed defeat,
not a win inferred from empty observations. The API did not provide a result.
Jev did not protect Raynor adequately while focusing the objective. The starting
force had already lost health and a Marine during earlier trials, so the next
test restarts the mission with the same shared-order policy and a fresh force.
Summaries: `030-shared-orders-cinematic.json`, `031-shared-orders-defeat.json`.

## Lab 048: fresh force, unchanged policy

The fresh opening reached town at about 55 seconds on the visible game clock,
with all six starting units alive. The second cinematic again temporarily hid
the force; the harness stopped after 190 calls, costing $0.044435. No outcome
was claimed. Saved the summary and resumed the same game after skipping the
cinematic. The policy is unchanged. The harness now waits up to ninety seconds
without inference when owned units disappear, avoiding repeated false stops for
campaign cutscenes. A stalled clock or actual API result remains independently
handled. No empty observation is classified as victory or defeat.

**Verified victory:** reconnecting found the game already ended. A fresh API
observation reported player 1 Victory at loop 3512. The last Jev-issued shared
attack-move continued through the cinematic while the harness was disconnected;
there were no assistant tactical inputs or substitute decisions. The rendered
client showed the Headquarters destruction ending scene with Raynor alive.
Saved `runs/lab048-victory/LiberationDay.SC2Replay` (20,515 bytes) and result JSON.
The ended-game attach path now logs the actual result and saves the replay instead
of raising an error. `033-liberation-day-victory.json` records the API result.

This fresh attempt made 190 Jev calls costing $0.044435 before the cinematic
interruption. It suggests the simpler shared-order interface is useful here;
it does not establish robust hero protection, and the preceding injured-force
attempt failed. The first mission is now complete in our standalone progression.

## Lab 050–051: mixed economy and combat selections

Loaded The Outlaws after the verified victory. With buildings and mobile units
together, the whole-force action intersection mostly forces individual control.
Jev mined, trained Marines/SCVs and completed multiple Supply Depots. The army
advanced while production continued; no victory yet. Saved a pre-change summary
as `034-outlaws-before-cohorts.json` (a partial run, not an independent episode).

Lab 051 splits selections mechanically by unit type, like selecting matching
units in the game. Each type gets a Jev choice between a shared action, individual
control, and continuing orders. All type questions share one SDK request; per-unit
decisions happen only when Jev selects them. No unit type is told to attack, mine
or build by code. The intersection still restricts shared actions to commands
offered to every member of that selection. This lets Marines coordinate without
requiring Command Centers to execute the same order. The preceding harness reached
its 400-call budget before this commit ($0.341052), so no live reload occurred in
that run. Resumed the same running game with the new policy and fresh policy memory;
the final preceding summary is `035-outlaws-individual.json`. This is a sequential
continuation, not an independent comparison or a verified hot-reload event.

The type-based model sent both Marines and SCVs toward the enemy base. At an
intermediate observation only two Marines remained, while eleven SCVs were far
from the mineral line. This is not labeled defeat: buildings remained and the
game was live. The policy appears to prioritize the attack without adequately
preserving its force or economy. Summary `036-cohorts-before-count-facts.json`
is an intermediate snapshot, not a final result.

## Lab 052: arithmetic and capability facts

Following TypeSafe's documented advice to do counting/arithmetic in code, expose
per-selection counts, count changes, damaged-unit counts, lowest health percent,
and whether offered actions include harvesting, construction or training.
These are measured facts, not a priority score or scripted response. Jev still
decides whether to keep attacking, retreat, harvest, build, train or delegate to
individual control. A missing unit is not automatically called dead because
campaign cinematics can alter observation ownership. The report now separates
health/count/position by unit type so building health cannot hide army losses.

The live reload is confirmed at revision `d83b309`. The combined continuation
ended at its 300-second limit after 427 calls, costing $0.324737. Adding count
facts did not restore a functioning force: the final report has no Marines and
five observed SCVs. No API defeat or victory was returned; this attempt is stopped
and retried, not falsely recorded as a completed mission. Summary:
`037-worker-attack-failure.json`.

## Lab 053: Jev chooses strategic priority with catalog weapon facts

Retry The Outlaws from its initial state. Add catalog weapon ranges, damage per
cycle and computed damage/time (before armor/bonuses) for observed or remembered
unit types. Catalog data was read at game join; it is not a hidden enemy upgrade
oracle. An empty weapon list does not establish safety, especially for garrisons.
Also expose supply still under construction to avoid requiring Jev to count it.

Every 112 loops, Jev chooses attack, strengthen, protect, explore, recover or hold
from current observations. This becomes explicit semantic context for Jev's
per-type decisions. Code does not execute any plan from that label, impose a
build order, reserve particular workers, or force a tactical response. This is a
combined context/decision-structure experiment, not an isolated ablation. It tests
whether a separate strategic judgment avoids interpreting every unit's task as
"attack the objective immediately," while retaining Jev-only action selection.

Result: stopped after 256 calls ($0.126299) with only the three starting buildings
observed; all mobile units had disappeared. Jev chose explore once, attack sixteen
times and strengthen twelve times, with the strengthening shift too late to keep
the mobile force. No victory or API defeat was returned. Saved an interrupted-run
replay separately under `runs/lab053-stopped/`. This does not isolate model limits:
another action-space omission was found during inspection.

## Lab 054: complete visible resource targeting

Gather candidates were still restricted to the nearest eight non-owned entities,
even after enemy attack targets were made global. A worker far from home therefore
could not issue a direct return-to-mining order for a distant visible mineral field.
Offer every currently visible mineral field and owned gas resource to units whose
queried abilities allow harvesting. Hidden resources remain excluded. Descriptions
state that gathering supplies income for unit production and construction; this is
a game-rule fact, not an order to harvest. Jev may still choose combat or other
actions. A test surrounds a worker with eight nearby neutral distractions and
checks that a distant visible mineral remains targetable while a hidden one does
not. Retry from initial state; no resources or units are injected into the game.

Result: early worker mining did not persist. Jev later committed the workers to
combat again and lost all mobile units. Stopped after 405 calls ($0.204721); only
the three starting buildings remained observed, with no API result. Saved the
replay under `runs/lab054-stopped/`. Completing the gather action space was a real
interface correction, but it did not by itself correct the decision pattern.

## Lab 055: contribution first, concrete action second

Test a closed-choice hierarchy per unit type. Jev first chooses income, production,
construction, combat, positioning, continuing orders or individual control, limited
to categories actually represented by available actions. Then Jev chooses a concrete
offered command within its own selected category. Categories describe controls;
the code never assigns an economic role to SCVs or a combat role to Marines.
The first question explicitly allows different unit types to contribute differently
to one overall strategy. This tests semantic decision framing and reduces the
number of concrete alternatives in the second choice, at the cost of another
inference stage. Both decisions and their latency are logged. Same fresh map and
objective, with no manual target or route input.

Result: 499 calls, $0.194834. SCVs chose income on all 223 contribution decisions.
The economy survived with eighteen workers; Marines were produced and lost, and
the army was gone at the run boundary. There was no victory. Resource orders
continued while the harness was stopped, and minerals accumulated before the
next continuation; that continuation is not a matched initial-state comparison.

Thirteen submitted ticks proposed two 50-mineral training orders against an
observed balance below 100 (for example 55 minerals). Response codes were Success;
no NotEnoughMinerals event was logged. This demonstrates proposed budget conflicts,
not which production orders the engine ultimately fulfilled. Do not attribute
all army losses or production imbalance to this mechanism without more evidence.

## Lab 056: Jev resolves spending conflicts and chooses individual builders

Annotate production/construction candidates with their catalog mineral, gas and
supply costs. If proposed costs exceed the observed shared budget, ask Jev which
single affordable purchase to make or whether to defer; other already-chosen,
non-spending orders remain. No purchase is selected by Python command ordering.
This simple resolver models the current one-unit Terran production options; it
does not establish correct costs for untested multi-unit morph abilities.

Also offer individual worker/site construction choices alongside shared orders.
Previously a build option could vanish from the group intersection when only some
workers had a legal site, leaving only an indirect generic individual-control
option. Jev now explicitly chooses both builder and site from engine-approved
candidates. Tests verify non-first purchase selection by Jev and construction
availability when only one worker can build. Seventeen tests pass.

Continuation result: visible **DEFEAT / All of your structures have been destroyed**.
Jev kept choosing income for SCVs during the raid, even after choosing protect as
the strategic priority once. This is a real defensive decision failure. The API
did not return a result; the game clock stalled. The continuation began with a
large mineral bank accumulated by persistent mining orders while the harness was
stopped, so it is not a controlled fresh-policy comparison. 88 calls cost $0.034277.

## Lab 057: widen the legal building-site search

The building menu also suffered from testing only four locations six units from
each worker. The crowded mineral-line continuation offered no construction sites.
Query the same four compass directions at distances 6, 10 and 14, retaining at
most four engine-approved sites per ability/worker. Every footprint must still be
currently visible and within the playable area. No site is selected automatically.
Expose queried Build ability names separately from generated sites, so an empty
site list is not represented as proof that the unit lacks construction abilities.
The placement test now requires an accepted farther site while rejecting closer
sites and an unseen footprint. Retry The Outlaws from a fresh initial state with
the spending and individual-builder changes present from the beginning.

## Lab 058: maintain a task without resubmitting it

The contribution hierarchy accidentally made a concrete new order mandatory after
choosing income. Live observations show workers already in `Harvest Gather SCV`
and `Harvest Return SCV` orders while new gather commands keep being proposed.
Repeated orders may disrupt that work; the exact throughput effect is not yet
isolated. Add a `continue` alternative inside every concrete contribution choice,
explicitly meaning retain current orders when they already perform that work.
Give Jev current-order counts and idle counts instead of requiring it to count a
long unit list. It still chooses whether to continue or issue a different order;
there is no automatic worker policy or suppression of model-selected commands.
Commit this player-only change during the existing lab 057 run and inspect the
actual reload event before claiming a live transition.

Confirmed live reload to `10d75e9`. The combined run ended at 500 calls ($0.191827),
with workers and base alive but supply blocked. Minerals accumulated after the
leaf-level continue change (685 in one inspected state). This is sequential
evidence, not an isolated throughput benchmark. No victory.

## Lab 059: project effects must reach the contribution decision

Consulted the journal: labs 036–038 already showed that available building names
alone did not solve supply block, while explicit supply effects elicited a completed
Depot. The new hierarchy exposed those effects only in concrete action descriptions,
after the contribution choice had already been made. Put distinct available
projects and their mineral/gas/supply costs and supply provided into per-selection
facts as well. Include supply provided/required in unit-type facts. This restores
known useful observation content at the decision stage that needs it; no code
chooses a Depot or assigns a builder. Resume the same supply-blocked game, rather
than resetting its functioning economy.


## Lab 060: temporal outcomes instead of one-tick count changes

Lab 059 produced two additional completed Depots (three total), resolving the
previous supply block. During the running trial Jev accumulated over 3,000
minerals, grew beyond 30 SCVs, and sent successive small Marine forces out.
One-tick count differences often read zero even while replacement units kept
arriving and disappearing. Add a rolling 672-loop observation history with
per-type arrivals, disappearances, measured health decreases and net resource
changes. Explicitly label disappearance as ambiguous (death, transport, morph or
campaign script), and resources as net income minus spending. Jev receives these
facts at every decision layer and is asked to reassess its previous strategic
priority; no strategy, production cap, timing or combat response is scripted.
A test verifies that replacing a Marine is visible despite unchanged total count.


## Lab 061: one shared investment choice across the economy

Lab 060 reloaded live at revision 0320c12. Its history records Marine arrivals and
disappearances, and strategic choices vary more, but the continuing run still
has only two Marines and forty SCVs after 661 calls across labs 059–060. Four
Depots are complete. This is not a win or proof that history improved play.

Test a shared Jev investment decision across every currently available training
and construction project, with an explicit save-resources alternative. Jev then
chooses the actual producer/site if there is more than one. Unit-type selections
retain movement, combat and gathering decisions but cannot make independent
purchases. A selected producer receives the selected investment order; other
Jev orders remain intact. No purchase priority or worker/army ratio is in code.
The project choice runs concurrently with contribution choices to contain latency.

Also fix missing SCV cost metadata: when the catalog's product ability mapping
is absent, match the exact advertised Train/Build name to the unit catalog.
This is presentation/lookup, not a guessed cost. The view change requires a
harness restart; player changes reload on commit. Nineteen tests pass, including
Jev choosing save or the non-first project and a single eligible builder.


## Lab 062: remove an execution veto and fix branch concurrency

The initial lab 061 window recorded 24 stale ticks out of 31. Although the first
contribution query ran beside investment selection, concrete order selection still
waited for the entire investment branch. Run both complete decision branches
concurrently. The builder/site request now gets its selected project, objective,
visible entities, and explicit candidate facts rather than repeating the whole
state. Project selection still sees the full observations and measured outcomes.

All 21 observed builder/site choices selected defer among roughly 137 concrete
pairs. This duplicated the save alternative after Jev had already decided to buy,
and split execution probability across many similar choices. Remove the redundant
veto from the execution allocation stage; Jev still chooses save versus each
purchase at the shared investment step, and chooses the exact legal pair. No code
picks a location or builder. Test in the existing game via committed player reload.


## Lab 063: omit empty action selections

After lab 062, Jev selected Marines through the shared purchase step, but 30 of
33 inspected ticks still exceeded the 32-loop freshness limit. Command Centers
chose individual control 25 times despite having no non-purchase candidates;
the fallback then wasted navigation/action inference on an empty action surface.
Exclude selections with no candidate actions from contribution questions. Their
purchase opportunities remain in the global investment decision and their state
remains visible. This does not suppress any available action or select a tactic.
A regression test ensures a purchase-only building gets no empty control query.


## Lab 064: explain purchased capabilities from observed controls

The first 13 ticks of lab 063 had four stale decisions, versus 30/33 in the prior
inspected window. This is a sequential sample, not a latency benchmark. Jev chose
Marine purchases or saving resources and stopped adding workers in that window.
A single Barracks still limits production despite the large accumulated bank.

Purchase descriptions have costs and supply effects but omit what a building can
do. Learn Train/Build/Harvest capabilities from actually offered own-unit controls
and retain them in policy memory. Present those observations directly beside each
investment, along with existing counts and current orders. This makes, for example,
an owned production building's observed training capability explicit without
hardcoding which building to buy or giving Jev a build order. Unseen unit types
remain capability-unknown. This knowledge resets with a harness restart.


## Lab 065: fresh Outlaws evaluation of shared investment

The lab 063–064 continuation ended normally at 299 successful calls ($0.161267)
without a result. It inherited forty-plus SCVs, six Depots and two Command Centers
from earlier policies. This is a poor starting point for evaluating whether the
shared investment policy avoids worker overproduction. Start The Outlaws fresh
with the latest policy and a 500-call/300-second budget. No new tactical rules or
model changes accompany the reset. Previous runs and replays remain preserved.


## Lab 066: make dispersion explicit and offer assembling as a priority

In the fresh lab 065 opening, five Marines counted as one selection while one was
near the home base and four were fighting far away. Later only two were near a
pair of Hellions. The history eventually showed seven Marine disappearances;
Jev chose strengthen but replacement Marines kept traveling separately. These
observations expose a missing aggregate: counts are not local force strength.

Add measured per-selection health, maximum separation, and the largest distance
to a nearest same-type neighbor. Add assembling to the strategic options Jev may
choose, with no automatic orders attached. Existing regroup/movement choices
remain available. This tests whether concrete dispersion facts and an explicit
strategic alternative change Jev's selections, rather than programming a minimum
army size or rendezvous route. The current fresh trial continues through reload.


Lab 065–066 ended at 499 successful calls ($0.203943) with sixteen SCVs, five
Marines, three Depots and the base intact. No result. Jev selected assembling
three times and repeatedly chose the Barracks as a regroup target, but the final
Marine maximum separation was 56.7 map units. A different label and occasional
regrouping do not establish sustained cohesion. Extend the same game with the
unchanged policy for up to 1,000 calls / 600 seconds to evaluate persistence.


## Lab 067: generic sequencing and verified own-player outcomes

Clarified experiment rule: frequent live patches are welcome, but must improve
general principles and transfer to unseen missions; they must not steer a
particular attempt through hardcoded tactics. Keep Jev responsible for purchases,
combat, destinations and timing. No requirement to freeze the policy was intended.

Add a generic manifest-driven sequence runner and machine-readable attempt results.
It advances only on the controlled player's Victory, retries explicit Defeat,
shares a call budget across attempts, and records incomplete/ambiguous outcomes
without advancement. Resume skips the completed prefix. It does not count an
ally's victory or a stalled clock as our success. Join race is configurable for
future campaign scenarios. Four orchestration tests bring the suite to 24 passes.

The initial two-mission manifest is an integration fixture, not a replacement for
the all-three-campaign goal. Live multi-mission progression remains unverified;
this change does not imply that the full campaign, UI recovery, or later-race
ability coverage works. The existing Outlaws trial continues unchanged while
this harness work is prepared for the next process start.


## Lab 068: isolate context filtering before changing live investment

The unchanged continuation repeatedly saved resources while its bank rose from
about 1,000 to over 4,600 minerals. Tested four recorded investment states offline,
with the exact same questions/options under two conditions. Full state included
21–24k characters of map geometry, unit positions, and other observations. A compact
state retained economic resources, selection aggregates, catalog facts, measured
outcomes, learned capabilities and strategy, plus visible/stale entity counts.
It was about 8.5–8.7k characters. All four full-state queries chose save; all four
compact-state queries chose Marine. Eight Jev calls cost $0.002827. Confidence was
low, and this is four paired single samples, not a statistical result or proof of
better gameplay. The archived probe includes options and full distributions.

Apply this general context filter only to the investment question. Combat and
producer/site questions retain their spatial input. This changes no purchase
priority and supplies no mission-specific instruction. The experiment directly
implements the documented recommendation to filter state to the question's needs:
https://docs.typesafe.ai/model-jaggedness/jev-1.13 .


## Lab 069: unattended opening-sequence evaluation

The unchanged Outlaws continuation ended at 1,000 calls ($0.527087), without a
verified win. Lab 068 was committed after that process ended, so it was not tested
live there. Preserve the replay and summary, then evaluate the generic sequence
runner from the first opening mission, with the same latest player throughout.
This is a generalization/regression test across scenarios, not erasure of the
previously verified Liberation Day victory. Only explicit own-player wins advance
the new local evaluation journal. Budget: 1,500 calls total, 600 seconds per attempt,
at most two attempts per mission. The two-map fixture does not stand for the full
three-campaign goal.


## Lab 070: Jev chooses the grouping of heterogeneous forces

The opening regression showed many Marine-to-hero and hero-to-Marine regroup
orders with little progress. Type selections were introduced to separate workers
and buildings from combat controls, but also split mixed combat armies. Offer Jev
a grouping choice alongside its existing strategic question: type selections, or
one mixed selection of units with move/attack controls and no observed harvesting
or building capabilities. All other selections remain separate. This is a general
control abstraction, with no mission/unit-name checks or destination choice.

The mixed selection can receive a shared order or Jev can choose individual
control. Economic type facts remain separate so mixed grouping cannot falsely
report that a purchase's unit type is absent. A regression test uses arbitrary
unit-type names and verifies that Jev can choose a joint attack-move. No extra
sequential inference stage is added. Twenty-five tests pass.


## Lab 071: autonomous advancement verified; retain completed mission checkpoints

The unattended sequence received own-player Victory for Liberation Day after 305
calls ($0.069482), saved its replay/result, wrote the completed checkpoint, and
loaded The Outlaws without an assistant menu action or launch command. This is a
second verified opening win. Lab 070 reloaded near the end, so the victory does
not isolate mixed grouping as its cause. The new Outlaws attempt is live.

The user clarified that failed attempts should restart only their mission, never
reset the campaign. The runner already retries the current mission and resumes a
completed prefix. Improve extension behavior too: adding later missions to a
manifest preserves verified prior wins, provided completed mission definitions
are unchanged. It refuses to transfer a victory to a changed completed scenario.
A test verifies an appended third mission runs alone after the first two wins.
Twenty-six tests pass. The current checkpoint is
`runs/campaign-lab069/progress.json`; the earlier fresh opening was an explicit
regression evaluation, not ordinary failure recovery.


## Lab 072: repair an omitted in-selection regroup option

Common-action intersection removed `join_TAG` whenever TAG belonged to the
selection, because that unit had no self-join candidate. Mixed combat selections
therefore could regroup at outsiders such as buildings but not at their own
members. Expose every legal in-selection anchor as an explicit Jev choice:
anchor uses its offered Hold Position, followers use their offered point moves.
No anchor is selected in Python. The complete effect is described in the choice;
no unoffered command is synthesized. This fixes a general action-interface gap,
not a mission route. A test verifies the legal two-unit combination.


## Lab 073: named savings goals for currently unaffordable projects

A purchase-description probe had only one eligible recorded state offering four
purchases, including a higher-cost production building. The two queries both
chose Marine; shorter direct-effect descriptions reduced question text from
3,870 to 1,711 characters and changed confidence, but did not establish a better
choice. Preserve that negative/limited result rather than claim a strategic fix.

A more fundamental limitation is that the project menu used only resource-legal
abilities. Cheap purchases could consume resources before an expensive project
ever appeared. Add a second read-only ability query with resource checking ignored
for discovery. Only supported Train/point-Build products enter potential-project
facts; the original resource-checked query still exclusively supplies executable
commands and engine-checked placements. Jev can now explicitly choose to save for
a named unavailable project, with resource shortfalls computed in Python. That
choice submits no action, and its intent is shown at the next decision; Jev may
reconsider at any time. There is no fixed saving target or automatic purchase.

The live policy also gets shorter observed-capability purchase descriptions.
Tests verify unaffordable projects never become executable commands and named
saving produces no command. Twenty-nine tests pass. The observation change takes
effect at the next harness start; a player-only reload cannot replace that module
in the currently running harness.

The first autonomous Outlaws attempt ended incomplete at 1194 calls ($0.597970), reason: Jev call budget reached. No defeat or victory is inferred. Resume the same campaign checkpoint for another Outlaws attempt with the new observation fields; the verified Liberation Day win remains completed.


## Lab 074: sample investment uncertainty and retain named intent

The named-project run initially chose no savings targets. Many prior investment
answers have low confidence and a spread of probability over several projects;
always taking the maximum can repeatedly suppress the alternatives. Test sampling
investment choices directly from Jev's positive probabilities over offered options,
using persistent RNG seed 20260918. No Python investment preference or uniform
random alternative is added. Log top choice, sampled choice and weights. A test
ensures zero-weight and invalid options cannot be sampled. This is exploration,
not a claim that the probabilities represent long-term strategic utility.

Consulted earlier sampling trials: navigation sampling changed routes but also
ended in defeat. This experiment applies the principle to budget allocation,
leaving combat choices unchanged. Keep the prior negative outcome in mind.
Also store previous investment intent as a named project and mode, not an index
into a menu that changes between observations. Thirty tests pass.


## Lab 075: hot-reload the observation adapter atomically with the player

Extend committed-source reload to `jev_sc2/view.py` as well as `player.py`. Both
new modules must compile and expose the required callables before either replaces
the active pair. A failed adapter edit therefore cannot leave a new policy paired
with stale observations. Socket, game, model client and memory remain in the
harness. The command validation entry point remains in the harness.

A test commits a valid pair, a broken adapter with a changed player, and a repaired
pair; it verifies retention and atomic replacement. Thirty-one tests pass. This
loader/harness change itself takes effect on the next controller process start;
subsequent observation-adapter edits will no longer require a controller restart.


## Lab 076: short-lived Jev investment commitments

The trace showed a named Barracks savings choice at loop 3323, followed by an SCV
purchase at 3403; another at 5850 was followed by Marine purchase at 5925. Naming
an intent alone did not preserve it long enough to fund the selected project.

Change the meaning of a named savings option explicitly: Jev commits the purchase
budget to that project for at most 224 game loops, or until an executable candidate
appears. During that interval no new investment is chosen; other control decisions
continue normally. If the chosen project becomes executable, request that same
purchase and let Jev choose its producer/site when needed. At expiry or loss of
the offered capability, ask Jev again. No target or project preference is in code.
A carried request is logged as `carried_jev_commitment`, never as a new model answer
or confirmed completed construction. The test verifies waiting and requesting
only the model-selected project. Thirty-two tests pass.


## Lab 077: preserve live missions across controller budget boundaries

A development call budget is not a mission defeat. Add checked continuation of
an incomplete checkpoint: `--resume-current` attaches to the existing API game,
verifies the engine-reported local map filename before action/result handling,
and records a resumed segment without consuming a new-attempt slot. Missing or
mismatched map identity stops rather than attributing another scenario's result.
The original create/join path remains for genuine new attempts. Thirty-four tests
pass, including continuation after an attempt cap and rejection of wrong/unknown
map identities.

The preceding run ended at 1,499 calls with no win. Read-only live inspection
confirmed `The Outlaws`, `traynor02.SC2Map`, status `in_game`. Resume that same game
with a longer 3,000-call budget instead of discarding its economy and army. This
controller start also enables the previously committed atomic observation reload.


## Lab 078: compact shared action descriptions and control the full force

The resumed large-base run produced `max_tokens_exceeded`. One successful combat
question was already 43,113 characters beside a 29,369-character state. Shared
orders concatenated per-unit descriptions, often repeating the same target with
only a different distance. Normalize that repeated distance text and provide the
computed travel-distance range instead. Keep representative semantic variants,
and keep every unit's actual offered command in the selected plan.

Remove the old first-64-units cap from shared and round-robin control. A test with
80 owned units verifies all receive the model-selected shared action while its
description stays compact. Also expose order progress from the existing protocol
field; this enables future production observations without inferring completion
from a queued order. Thirty-five tests pass. The observation change is intended
as the first live check of the new adapter reload.

TypeSafe documents 64k tokens for a request and 32k for state plus its longest
question: https://docs.typesafe.ai/models . Character measurements are diagnostic
proxies, not token counts or a guarantee that every future request fits.


## Lab 079: Outlaws victory and continuation to Zero Hour

The resumed Outlaws game returned Victory for controlled player 1 after 390
additional Jev calls ($0.183502704). Result and replay are saved in
`runs/20260918T233326.859613Z/`; the public measured summary is
`docs/experiments/054-outlaws-victory.json`. The run continued the existing
mission after its controller budget boundary. Both completed missions remain
in the sequence checkpoint.

Lab 078 was committed after this victory, so its request compaction and removal
of the 64-unit cap cannot explain this win. Request-size failures occurred in
the winning segment; victory does not establish that the policy is robust.

Append Zero Hour with only its scenario objective, “Hold out for evacuation,”
and load it through the same sequencer. No completed mission is replayed.
Verified defeats retry only the pending mission; budget exhaustion allows
checked attachment to that same live game. No mission-specific tactics added.

## Lab 080: expose support actions and cargo state

Zero Hour is running from the preserved checkpoint; at loop 2647 it had 43 owned
units, with no terminal result. Adapter inspection found no repair, heal, load or
unload candidates. This omission would limit any mission using support units or
transports regardless of Jev's decisions.

Add support candidates only for abilities offered by the engine's resource-aware
query. Repair/heal recipients must be visible owned damaged units with the
matching Mechanical/Biological catalog attribute. Load candidates require an
owned visible ground unit with a positive cargo size that fits. Unload requires
occupied cargo. These are candidate filters, not a guarantee of engine-specific
target legality: range and mod filters remain subject to action results. No
recipient, timing or tactical preference is selected in Python. Jev chooses
through the existing ability branch. Expose owned cargo/passengers and energy in
its observation state. No hidden or snapshot target is introduced.

The official protocol documents ability target kinds and unit attributes in
https://github.com/Blizzard/s2client-proto/blob/master/s2clientprotocol/data.proto
and owned cargo/passengers in
https://github.com/Blizzard/s2client-proto/blob/master/s2clientprotocol/raw.proto .
Thirty-six tests pass, including unavailable abilities, hidden targets, full
cargo, and undamaged recipients. Commit this adapter/player pair during the
running game to verify atomic live reload. This expands controls; effectiveness
of Jev's support decisions is still unproven.

## Lab 081: show capability meaning before hierarchical selection

Lab 080's committed player and adapter reloaded at runtime (revision 76d588d),
and subsequent requests contained cargo observations without a restart. The
Bunker contribution question now offered `other`, proving support candidates
were present, but its description was merely “Use another available ability.”
In the first inspected post-reload sample, all 21 Bunker contribution choices
were `continue`. This does not prove a model weakness: the hierarchy concealed
what the new category could do until after Jev selected it.

Expose deduplicated support capability descriptions in selection facts and in
the `other` contribution option. Preserve all competing choices and leave the
specific order/recipient to Jev. This is an information-preservation fix for
hierarchical decisions, applicable to support abilities in every scenario.
Thirty-seven tests pass; a test checks that the capability and cargo state are
visible at the contribution decision, before choosing the concrete order.

### Live evidence after labs 080–081

The same game recorded both reloads without reconnecting. In the archived
snapshot, lab 080 had 65 Bunker contribution choices, all `continue`; lab 081
had 47 `other` and one `continue`. Later observations contained actual Marine
passengers in a bunker. Repair commands were also chosen, with some immediate
`NotEnoughMinerals` responses. This is a sequential live observation, not a
controlled causal comparison or a completed-mission result. The adapter and
question wording were a real limitation before judging Jev's support behavior.
Measured phase evidence: `docs/experiments/055-live-support-affordances.json`.
The current policy does not yet receive all immediate action-result feedback;
this remains a general observability gap to address without interrupting this
healthy run. Zero Hour's result is still pending.

## Lab 082: stream camera follows local action

User requested a more watchable stream. Replace the average-owned-position
camera with a presentation-only director. Frame visible engagements, weapon fire,
new damage and moving forces; use quiet local overviews between action. Hold
shots for seven seconds, allowing earlier cuts after 2.5 seconds for new damage
elsewhere. Local framing avoids an empty midpoint between base and army.

Camera memory is separate from Jev policy memory, consumes only its fair view,
and emits camera moves only. It never supplies tactics or unit orders. Commit
reload now includes the camera module atomically with the player and adapter.
Forty tests pass, including a distant fight against a large base, shot dwell,
damage interrupts, movement, and exclusion of fog snapshots from camera targets.
The harness integration requires one controller reconnect to the same current
mission, without loading a map or discarding completed campaign checkpoints.

### Camera deployment verified

Reconnected to the same Zero Hour game after recording the interrupted segment
(954 observed successful calls, $0.610474662; in-flight billing may differ).
Checked map identity before issuing actions. New run
`runs/20260918T234914.185918Z` began at loop 10010, not a restarted mission.
Camera-shot events and two SC2 screenshots confirm scene changes, including a
visible Zerg attack on burning structures. Evidence is in
`docs/experiments/056-live-camera.json`. Forty-one tests pass, including retention
of the prior camera module if a committed replacement fails to compile.

## Lab 083: Jev assigns support executors and receives engine rejections

Zero Hour's first attempt ended in a UI-confirmed Defeat: “All of your structures
have been destroyed,” with the game clock at 12:22 and 07:47 evacuation time left.
The API omitted player results and stalled instead. Record UI evidence explicitly;
do not invent protocol results. Two prior completed missions remain untouched.

The first segment's worker choices changed from mostly continue/friendly moves
(before loop 5000) to shared repairs: 40 repairs at one target and 25 at other
targets during loops 5000–8000. Those commands redirected the whole worker group.
Multiple bunkers also requested the same passenger. These are representation and
coordination limitations, not proof that Jev independently chose a sound allocation.

Collect support actions across eligible members, including cases where a full
carrier differs from empty carriers. After Jev chooses the action/target, a compact
assignment query selects one executor, all eligible executors where meaningful,
or no change. Loading offers only a single carrier because a passenger cannot
enter several simultaneously. Unselected units retain existing orders. No unit,
recipient, quantity or action is chosen by Python. The extra Jev query adds latency
and must be measured. Also expose the last eight engine submission outcomes,
including named rejections and stale discards, to subsequent Jev decisions.
Accepted requests are not represented as completed tasks.

Forty-three tests pass. Retry Zero Hour with this general policy and camera;
completed Liberation Day and Outlaws checkpoints persist. The saved first-attempt
replay and measured summary are retained (057). This change makes no claim of
improving the outcome before the retry runs.

## Lab 084: a choice key changed Jev's strategic answer

Hypothesis: the `hold` strategy key collides with “Hold out” in the objective,
although its description means continuing current tasks. Run three paired offline
queries on recorded fair states, changing only that key to `continue_operations`
and preserving descriptions/state. Alternate pair order. All three original-key
queries chose hold (probability .72, .74, .60); all three renamed queries chose
protect (.74, .49, .50). Six calls cost $0.003594066. These are tiny sequential
samples, not a statistical result or gameplay advantage. They establish useful
sensitivity evidence without sending any game commands.

Rename the key for semantic precision across all missions. No option is removed
and no strategy is selected in Python. Full paired probabilities are in
`058-choice-label-probe.json`, with reproducible script `scripts/probe_choice_labels.py`.
The live retry also exposes a cost of lab 083: 22 of its first 33 ticks were stale,
and the extra assignment query often returned continue. Support allocation needs
a cheaper representation; do not credit it with tactical improvement yet.

## Lab 085: collapse small support assignment menus into one Jev call

Lab 083 added a serial model call after target selection. For menus with at most
80 eligible target/executor pairs, offer exact single-executor assignments in the
existing concrete-order query, plus all-eligible assignments when meaningful.
The model still selects target and participants. Larger menus retain the staged
path rather than truncating candidates. Loading never offers duplicate carriers
for a single passenger. The threshold governs request representation only.

Forty-three tests pass. This reduces one sequential inference for small support
menus without relaxing observation freshness or replacing any choice with a
script. Evaluate live latency and accepted commands after the commit reload;
do not assume fewer requests automatically improve survival.

## Lab 086: distinguish resource balance from income

The prior defeat screen showed zero assigned mineral workers. The policy had
balances and net resource changes, but these combine income with spending and
cannot establish whether income exists. Expose own-player collection-rate
estimates (minerals/vespene per minute) and owned structures' assigned/ideal
harvesters. Missing protocol fields remain null rather than becoming zero.
These are observations, with no worker-allocation rule or production preference.
The official definitions are in
https://github.com/Blizzard/s2client-proto/blob/master/s2clientprotocol/score.proto .
No enemy kill scores or hidden information are added. Forty-four tests pass.

The current retry reloaded labs 084–085. Strategy choices changed to protect;
concrete support choices include single workers. The first 17 lab-085 ticks still
included 11 stale decisions (median 1458ms), so collapsing small menus alone did
not resolve latency. Larger support menus retain the extra executor query. This
remains an unresolved throughput issue, not a claimed improvement in survival.

## Lab 087: compact strategic and contribution context

A live sample had median strategy and contribution request states near 37k
characters, with median call latencies 472ms and 481ms. Concrete-order calls took
493ms median beside roughly 19k-character questions. Repeating full per-unit and
map data at every hierarchy level consumed the freshness budget before action.

Use compact context for strategy and contribution queries, retaining objective,
resources, current orders, health/dispersion, capabilities, observed outcomes,
engine feedback, and visible/stale entity counts. Add computed selection centers,
nearest visible enemy distance, nearby visible threat counts, cargo totals and
harvester assignments. Concrete order queries retain the full detailed view.
No option or action is chosen by summarization. This does lose exact individual
positions at the abstract stages; those remain available at concrete selection.
Forty-five tests pass. Measure actual latency and stale ticks after reload rather
than treating smaller character counts as proof of better real-time control.

Correction: the first lab-087 commit was made before inspecting the completed test
output; one test had failed because the economic compactor intentionally replaces
mixed control selections with type selections. Add a separate control-context
wrapper retaining both views. All 45 tests now pass. The initial pass claim above
applies to this correction, not the first commit. Retain this mistake in the lab
record rather than rewriting deployed history.

### Lab 087 measured continuation

In the archived live snapshot, pre-compaction revision 1cce5da dropped 28/73 ticks
as stale (median 1281ms, median purpose state 39407 characters). Corrected ae3b5f6
dropped 4/50 (median 1015.5ms, purpose state 21676 characters). Different force
sizes/threats and sequential timing prevent causal attribution. This is practical
freshness evidence, not a victory or proof of robust strategy. The force continued
shrinking while Jev chose support despite zero reported mineral income. Future
work must distinguish actionable feedback from data the model fails to connect.
Full phase counts, including the intermediate buggy revision, are in
`docs/experiments/059-compact-control-context.json`.

## Lab 088: name rejected actions instead of requiring numeric joins

At loop 10260 the live retry again requested six repairs with zero minerals;
all six were rejected. Feedback identified only ability 316, while the control
menu describes Repair. The model had to connect an opaque identifier to an action.
Join failures to ability descriptions already observed in the candidate menus,
retain labels when the ability disappears, and aggregate identical rejections
with counts and affected unit types. This reports what happened without selecting
a replacement action or suppressing choices. Forty-six tests pass. Observe
whether the more explicit feedback changes behavior; no improvement is assumed.

## Lab 089: second Zero Hour defeat; evaluate current policy from the start

The second attempt ended in UI-confirmed Defeat at 12:25 (07:44 evacuation time
remaining), again with all structures destroyed. The API omitted player_result
and stopped on a stalled clock. Explicit UI evidence is attached to the local
checkpoint/result; the public measured API summary remains honest about its
missing terminal result. Survival was essentially unchanged from the first
12:22 defeat, despite fewer stale decisions. This is not campaign progress.

Lab 088 loaded just before the loss, too late to evaluate named rejection feedback.
Retry only Zero Hour using the complete current policy from the beginning,
preserving prior wins and both failed attempts. No opening tactic is hardcoded.
The camera director and player-only observation rules remain in force.

## Lab 090: negative strategy-hint probe and bounded contribution sampling

Three paired offline contribution queries all chose positioning with and without
the global protect hint. Removing only `strategy_chosen_by_jev` did not change the
top choice; this small probe does not support deleting that hierarchy. Six calls
cost $0.001977948; full distributions are in `061-strategy-hint-probe.json`.
The unchanged queries assigned income .22, .36, .38, yet deterministic top-choice
selection never exercised that alternative in these samples.

Test sampling positive finite probabilities over offered contribution options,
with fixed reproducible seed 20260919. Tell Jev that its selected contribution is
a commitment for up to 224 game loops, with reconsideration on priority change,
expiry, or unavailable controls. Concrete orders remain fresh Jev choices. This
lets sampled work persist long enough to have an effect and saves repeated role
queries. No contribution receives a Python preference, and no unit allocation or
resource-gathering rule is scripted. The ten-second commitment may respond too
slowly to threats; measure that risk rather than assume it helps.

Forty-seven tests pass, including retention of a sampled choice, exclusion of
unoffered/zero-probability choices, and reconsideration when controls disappear.
Also prepared the next local map asset (`ttychus01.SC2Map`, 43 components) without
loading it or feeding its scripts to Jev. Zero Hour must be won before advancing.

## Lab 091: two small probes did not change contribution choices

A general one-minute evaluation horizon plus opportunity-cost instruction did
not change the top answer in any of three recorded-state pairs. Income remained
low (.01/.00/.06 original versus .02/.01/.07 changed). Six calls: $0.001491126.
See `062-contribution-horizon-probe.json` and its reproducible script.

A separate probe replaced “SCV units” with “resource-harvesting SCV workers,”
asserting actual harvesting capability in every sampled state. Income probability
rose .18→.35, .04→.12 and .03→.08, but positioning remained the top answer in all
pairs. Six calls: $0.001420062. See `063-capability-label-probe.json`. This specific
unit-name substitution exists only in the offline diagnostic, not the player.

Neither wording change is applied to the live policy. Samples are small, taken
from evolving pressured states, and do not establish that gathering was feasible
or optimal in those particular moments. The earlier economic failure and later
survival reactions must not be conflated. Evaluate the current sampled commitment
policy from the beginning of another attempt if this one fails; its mid-mission
introduction cannot establish fresh-run performance.

## Lab 092: third defeat; freeze policy for a fresh full attempt

The third Zero Hour attempt ended in UI-confirmed Defeat at 9:44, with 10:25
remaining until evacuation. All structures destroyed. This is worse survival
than the prior 12:22 and 12:25 attempts; it is not progress toward a win. The API
again omitted a terminal player result. Its 925 successful Jev calls cost
$0.534900030; replay and explicit UI evidence remain local, with public measured
summary 064. Lab 090 was introduced partway through the attempt.

Run one fresh attempt with the entire current policy from the start, keeping the
policy unchanged for this evaluation. Raise this invocation's attempt cap from
three to four to permit the next authorized retry. Earlier mission victories
remain preserved. Distinguish full-run evidence from post-hoc reasoning about
mid-run patches and evolving damage.

## Lab 093: reporting cleanup during the frozen-policy attempt

The fourth run opened with an income commitment. Early observations reported
160 minerals/minute and 60 minerals on hand; a later reporting snapshot reached
180/minute. Income was intermittent (latest snapshot zero), so this is an early
mechanical observation, not a stable economy or mission success. The report saw
seven income commitments and accepted actions, alongside 35
CantTargetUnderConstructionUnits rejections. Inspect that adapter limitation
after this frozen-policy evaluation; no runtime policy change is made here.

Extend the report with latest resources, peak observed income estimate, contribution
commitment counts, support executor choices, named engine results, camera reasons,
and any explicit result.json (including separately labeled UI evidence). Verify
its output on the active trace. Refresh README and the consolidated experiment
report: two wins, three Zero Hour defeats, atomic camera reload, checked resume,
and remaining model/harness limitations. These are reporting/documentation changes
only; the current policy remains unchanged.

## Lab 094: smaller contribution context was not clearly better

TypeSafe's Jev 1.13 guidance recommends reducing irrelevant context and indirection:
https://docs.typesafe.ai/model-jaggedness/jev-1.13 . Test this locally rather than
assuming all filtering helps. On the first three worker-contribution states from
the frozen run, retain only the queried selection in four type/capability fact
dictionaries while leaving other fields and the question unchanged.

State size fell from 20–22k characters to 5–7k. Income probabilities changed
.22→.06, .11→.13, .24→.18; one top answer changed from support to positioning,
with the other two unchanged. These six calls ($0.001323294) do not support this
filter as an improvement. Other groups' facts can contain useful economic and
support context; smaller input alone is not an accuracy guarantee. Do not deploy
this probe transformation. Evidence: `065-selection-context-probe.json`.
The live player remains frozen throughout this attempt.

## Lab 095: frozen policy lost; correct unfinished-construction controls

The unchanged-policy fourth attempt ended in UI-confirmed Defeat at 10:02,
with 10:07 remaining for evacuation. It made 918 successful Jev calls costing
$0.554785476. Income commitments yielded intermittent income but not survival.
Runtime source stayed unchanged from f17432b throughout this attempt; intervening
commits changed only reports/docs/offline probes. Full outcome and measurements:
`066-zero-hour-frozen-policy-defeat.json`. No campaign advancement is claimed.

The engine rejected repairs on unfinished structures. Exclude those repair
candidates. Offer the normal Smart/context interaction on owned unfinished
structures only when Smart is engine-advertised and the actor has an observed
building capability (including resource-ignored capability discovery). The engine
determines contextual behavior; this is not a guarantee that every builder/race
can resume construction. Jev selects the target/executor, and no command is sent
from capability discovery alone. This addresses a general action-interface gap,
not a mission-specific build rule. Forty-eight tests pass. Live Smart availability
and successful resumed construction remain to be verified in the next attempt.

## Lab 096: explicit weapon/target facts and live construction evidence

Lab 095's Smart interaction is present in live Jev menus and has been selected.
Observed SupplyDepot 4395368449 progressed from .054 at loop 1191 to complete at
1680; Jev issued Smart interactions for it. Bunker 4358144002 also progressed
(.008 at 1811 to .902 at 2240). This proves the affordance was offered and used,
and construction completed/progressed; it does not isolate whether an original
builder would have completed it without the additional interactions.

Earlier runs logged MustTargetAirUnits. Attack descriptions named targets but
required a separate join to catalog weapon facts. Add target altitude and catalog
weapon classes directly to each visible unit-target attack description, and
expose is_flying for visible entities. Do not infer a complete target-legality
predicate: catalog omissions, garrisons and special target rules exist. The engine
remains authoritative; Jev still chooses commands. Forty-nine tests pass.
This is a general observation/action-description change, not a target preference.

## Lab 097: expose unit-target gas construction

The fifth attempt's initial post-lab-096 sample had 675 accepted action results
and no rejections. This is not a controlled test of the description change and
not proof that all invalid targeting is solved.

A broader interface audit found that construction only supported point targets.
Python-sc2's source documents that gas buildings require the geyser unit as target:
https://github.com/BurnySc2/python-sc2/blob/develop/sc2/unit.py . Add unit-target
Build candidates for engine-advertised gas-building products (catalog has_vespene)
on currently visible neutral geysers with remaining gas. The command uses target_tag,
never substitutes the geyser's coordinates. Resource-ignored discovery supplies
only potential-project facts; executable choices require the resource-aware query.
No hidden/snapshot geyser is offered. Final target validity remains the engine's
responsibility. Jev chooses whether to invest and which worker/geyser to use.

Fifty-one tests pass, including unaffordable discovery and hidden/snapshot targets.
This closes a command-shape gap relevant to later missions and all races; live
gas construction, race-specific cost accounting and full later-campaign behavior
are still unverified. It is not a scripted gas-building trigger.

## Lab 098: bounded unattended stall recovery and prepared next scenario

Add opt-in `--retry-stalls` to the sequencer. A harness clock-stall stop can restart
only the pending mission within existing call/attempt caps. Keep the recorded
status incomplete with explicit recovery metadata; never convert a stall into a
defeat or advance it as a win. Other unknown/budget failures still stop. Default
behavior remains unchanged. Tests verify bounded retries, shared budget, preserved
completed prefix, and no retry for budget stops. Fifty-three tests pass.

This is administrative recovery, not tactical control. It can also restart a
legitimate paused mission, so opt-in use and caps matter. It does not solve native
UI result recognition or permit counting an unverified campaign completion.
The new sequencer option takes effect on the next controller invocation.

Append the prepared fourth scenario, Smash and Grab, to the manifest. Read-only
installed metadata confirmed `DocInfo/Name=Smash and Grab` for ttychus01. Its input
objective is to secure the artifact before the zerg, as described by the public
mission reference https://starcraft.fandom.com/wiki/Smash_and_Grab . No route,
location, build or target prescription is added. Assets were repackaged unchanged;
live loading remains unverified. Earlier wins must remain intact and Zero Hour
must receive verified Victory before this fourth map is played.

## Lab 099: fifth defeat, live gas verification, reject a mistaken bug diagnosis

The fifth attempt ended in UI-confirmed Defeat at 11:58 (08:11 remaining), with
all structures destroyed. It made 1111 successful Jev calls costing $0.713233584.
Earlier wins persist. Summary with explicit UI result source: 067.

The new gas interface was exercised: Jev selected Refinery, observed unit
4321181704 appeared at loop 8753 with .01 build progress and completed at 9251.
The gas balance later rose from 100 to 108. This verifies a Terran gas-building
path in a live campaign map, not all races or successful resource allocation.

An initial commentary misdiagnosed repeated carried Refinery requests as reuse
of one savings commitment. Inspection disproved that: the code already changes
its mode to request_purchase, and new Jev save_for choices at loops 9222 and 9368
preceded the requests at 9251 and 9386. No fix was made for a nonexistent bug.
Retain this correction as part of the experiment record.

Start another bounded batch with the current general policy and --retry-stalls,
allowing up to three further fresh attempts (historical cap eight), sharing 6000
calls. Only the pending mission restarts. Recovery records remain unknown unless
separate evidence confirms an outcome. Only verified Victory advances to the
prepared fourth mission. Observe actual automatic recovery before calling that
path live-verified.

### Lab100 — retain rejection evidence across contribution commitments

The live sixth Zero Hour attempt remained active during this change. Engine feedback
previously contained only eight harness cycles, shorter than a 224-loop contribution
commitment at fast decision rates. Player now retains rejection-bearing entries for
672 game loops, capped at 32 entries, merged by observation loop with current feedback.
It clears retained evidence when the clock resets. This supplies historical facts;
it does not forbid actions, choose tactics, or assume a rejection remains applicable.
54 tests pass, including retention, deduplication, expiry and clock-reset coverage.
No gameplay improvement is claimed before observing the deployed policy.

### Lab101 — movement preference survives a choice-key rename

Confirmed lab100 active in the seventh fresh Zero Hour run
`20260919T003856.465157Z`. Sixth attempt stopped incomplete after a clock stall;
automatic recovery started the same map and preserved both verified prior wins.
The sixth result remains incomplete, not an inferred defeat.

Early seventh-attempt telemetry showed 19 shared worker regroup choices, four
continue choices and four individual choices. A sampled purpose state had seven
idle workers, no visible enemies and zero estimated mineral income. This suggests
investigating the movement preference rather than assuming missing income facts.

Generalized the existing offline choice-label probe to accept a question and key
pair. In three recorded purpose_SCV states, renamed only `positioning` to
`relocate_units`, preserving every criterion description and state field. All
three pairs retained the movement top choice. Income probabilities original vs
renamed were .21/.24, .23/.22, .12/.13. Six calls cost $0.002153046.
Unlike the earlier hold/continue_operations probe, this rename did not change the
decision category. Do not deploy it as a fix. Artifact:
`docs/experiments/068-positioning-key-probe.json`. No game commands were issued.

### Lab102 — clarify ordinary Move semantics

Observed repeated worker Move-to-CommandCenter choices at distances 2.8–3.9,
while these commands cannot themselves initiate mining. Tested a literal action
clarification in three recorded purpose states. All top choices remained movement;
income probabilities changed .22→.31, .22→.31, .15→.17. Six calls $0.002157708;
artifact 069. This does not establish a gameplay improvement. Deploy the mechanical
clarification because it describes what the offered command does, without choosing
a role, destination, worker allocation or mission tactic.

An initial six-call pilot ($0.002157960) used an overbroad sentence saying all
positioning orders only change/hold location, overlooking Hold's combat behavior.
Discarded that wording and reran the three pairs with the statement explicitly
restricted to ordinary Move. Only the corrected wording enters the player.

### Lab103 — expose observed movement outcomes

The seventh attempt confirmed revision 090651e live. Existing recent_outcomes
summarized resource and health changes but not movement. Added per-type mean net
displacement and sampled travel distance, restricted to tags observed at every
sample in the existing 672-loop history. Missing positions (including pre-reload
history) omit the measurement rather than inventing zero. Round trips have zero
net displacement but nonzero sampled travel; the description explicitly says
neither metric alone proves success/failure. No stagnation threshold, automatic
rerouting or role override is added. Jev remains responsible for interpreting it.
55 tests pass, including round-trip, stationary, intermittent visibility and
clock-reset cases. Gameplay effect unmeasured at deployment.

### Lab104 — Jev may organize selections by existing jobs

Recent seventh-attempt worker choices included whole-selection gas gathering and
regrouping, with zero measured mineral income. The existing by-type grouping makes
one shared order affect every worker, while individual control adds calls. Add an
optional Jev-selected middle granularity: each type split by first observed order
and unit target, with idle units separate. No worker quotas, resource preference,
new destinations or assignments are encoded. Grouping only partitions owned units;
Jev still chooses every command and may retain by-type or mixed-combat grouping.
Point coordinates are not grouping keys, avoiding splitting each relative move.
Existing economic facts remain type-based. This can increase question count and
job groups can change as orders cycle; latency and adoption need live measurement.
56 tests pass, including split/merge by existing target, unchanged input orders,
and preservation of by-type mode. No gameplay improvement claimed.

### Lab105 — live adoption of job grouping, economy still failing

Partial seventh-attempt measurement at loop 8144: revision64567af produced48ticks,
median630ms,3stale ticks. Jev chose by_current_order three times and by_type five
times in this segment. Separate SCV idle and Move selections received distinct
choices, confirming the new grouping reaches concrete execution. However latest
minerals and mineral income were both zero, vespene208, supply used10. This is
working control plumbing, not an economic or mission success. Force shrinkage
and evolving game state confound latency comparisons. Artifact070 preserves the
partial sample. Keep runtime policy unchanged while observing this attempt.

### Lab106 — seventh attempt incomplete; eighth starts with current policy

Seventh run20260919T003856.465157Z ended after a ten-second game-clock stall,
with no API player_result. Preserve status incomplete; UI was not inspected before
automatic recovery, so no defeat claim.808calls,$0.522373404,median tick1028.5ms,
75stale ticks,peak observed mineral income300/min. Engine results included190
NotEnoughMinerals,4MustTargetAirUnits and2YouCantControlThatUnit; accepted commands
are not proof of useful completion. Full report071. Previous two victories remain
unchanged. The orchestrator automatically started eighth fresh attempt
20260919T004542.876416Z, verified advancing at loop804 with40 owned units.
This attempt starts with current runtime policy; leave it unchanged for evaluation.

### Lab107 — distinguish harvest cycles from interrupted work

Read-only inspection of eighth-run full-state unit records through loop3371 found
27 observed Gather→Return and22 Return→Gather worker-order transitions, plus10
Gather→Move and5 Return→Move transitions. Repeated state snapshots are not
independent samples or a time-weighted utilization measure. Natural gather/return
cycles demonstrate the harvest control works; some later movement interrupts it.
The new by_current_order grouping treats gather and return as different jobs and
unit targets also differ between deposit and resource. Thus stable work can change
selection identity, undermining retained contribution commitments. This is a
control abstraction limitation to address after the frozen trial, not evidence
that every return transition is an interruption. Runtime policy remains unchanged.

### Lab108 — unchanged-policy eighth attempt defeated

Controller session20437 exited normally at the configured attempt limit. UI
inspection confirmed DEFEAT, all structures destroyed, clock7:33, evacuation12:36.
API again omitted player_result. Recorded UI evidence separately in result and
checkpoint without fabricating protocol results. Full report072. Runtime player
policy stayed unchanged throughout this fresh attempt; later commits only journaled
observations. The intermittent income recovery did not sustain the force. Two
prior victories remain saved. Next experiment should stabilize harvest job identity
across natural gather/return phases before spending on another bounded trial.

### Lab109 — preserve observed harvest assignments across cargo return

Normalize gather/return phases to a Harvest cycle selection, keyed by the last
actually observed gathering target. Track that target under every grouping mode,
so switching grouping does not discard known work. Return-to-base targets are
never treated as resources. Unknown return assignments stay separate by unit;
interrupted orders and absent units clear their cached targets. New observed
gather targets replace old assignments. This changes selection identity only,
not any command, worker quota or resource priority. Jev chooses grouping and actions.
57 tests pass, covering phase continuity, resource switching, interrupted work,
unknown return targets, absent-unit cleanup and unchanged legacy grouping.
Launch one further bounded fresh attempt (maximum attempt9,2500calls) on Zero Hour.

### Lab110 — ninth trial request-size failure; split large question batches

Ninth run20260919T005251.873352Z stopped incomplete after five HTTP400
max_tokens_exceeded responses, not a mission result. Prior requests showed concrete
state around62k characters plus52k question characters as job selections expanded.
Add recursive parallel splitting of multi-question requests above80k serialized
characters, preserving state and every criterion exactly. This is a conservative
size heuristic, explicitly not a token guarantee; an oversized single question
can still fail. It adds calls and repeats state, so cost/latency need observation.
58 tests pass including no dropped questions/criteria and normal call accounting.
Resume same pending mission rather than resetting its progress after infrastructure
failure; fresh attempt slot is not consumed. Runtime SDK change needs reconnect.

### Lab111 — splitting alone fails; deduplicate job capability context

Resumed run20260919T005637.401840Z stopped after five token-limit failures despite
39 batch-split events. Six successful ticks, four stale, median1929.5ms. Batch
splitting alone is not a sufficient fix. Remove repeated project/support/build
lists from per-selection facts sent for role and concrete-order decisions. Keep
complete type-level capability facts, actual criteria, unit positions/orders and
visible entities. Source state remains intact for constructing legal criteria.
59 tests pass; reconnect to same pending mission to verify actual endpoint behavior.

### Lab112 — make campaign freshness cutoff experimentally configurable

After context deduplication, resumed segment initially produced15ticks with no
token-limit errors, one timeout and7stale ticks (median1352ms). Minerals1869 with
260/min income while Jev requested purchases: staleness is now a distinct possible
execution bottleneck. Campaign runner hardcoded32loops although the single-mission
CLI already exposed a cutoff. Thread --max-age-loops through the campaign runner,
keeping default32 and all fresh ownership/visibility/command validation. This enables
a bounded later64-loop experiment; it does not change the currently running trial.
60 tests pass including propagation to the runner. No evidence yet that a longer
cutoff improves performance; it accepts older strategic context as a tradeoff.

### Lab113 — ninth attempt defeated; start 64-loop freshness trial

UI confirmed all structures destroyed at12:45, evacuation07:24. Final resumed run
20260919T005814.542606Z recorded as defeat with separate UI evidence; API omitted
player_result. Report073 covers only that resumed segment. Ninth fresh attempt
also contains the initial token-limit failure and one failed splitting-only resume;
do not treat its duration as a clean controlled comparison against attempt8.
Two earlier victories remain intact. Start attempt10 from the same pending mission,
2500call budget,64-loop age cutoff, unchanged player policy. This tests whether
allowing older Jev decisions to reach fresh command validation reduces starvation.
Ownership/visibility validation and engine legality remain enforced. No tactical
orders or mission-specific logic added. Policy benefit remains unproven.

### Lab114 — verify 64-loop execution and correct reporting

Attempt10 connected event confirms max_age_loops64. Early live sample has10ticks
older than32loops, none older than64;77 commands from decisions older than32loops
passed normal validation and were submitted. This verifies the experimental
mechanism, not better play. Reports now expose configured_max_age_loops and counts
older than that actual limit, retaining the32-loop count only for comparison.
Verified report output on the active run. Runtime player policy unchanged.

### Lab115 — inline resource balance does not change three gas-worker decisions

A live idle-worker menu showed gas probability.77 with minerals0 and gas368.
Probe the last three available recorded gas-gather menus with identical state and
choices, appending each gathered resource's current balance and literal effect
(only that balance increases) to its description. These selected samples were
already-working gas groups at gas520/524/532, not the earlier idle worker. All
three pairs chose continue in both variants. Six calls,$0.005615148,artifact074.
This does not test the earlier idle case or establish the general irrelevance of
balance placement. No player change deployed. Probe script initially rejected a
non-string criterion locally before any model call; fixed string handling.

### Lab116 — targeted idle-worker balance probe remains negative

Added optional exact question filtering to the resource-label probe and reran it
on the last three recorded `SCV / idle` gather menus. Balances were50minerals/140gas,
0/184 and0/368. Original and inline-balance variants all selected the same Refinery
(gas target4395106305). Six calls,$0.005568234,artifact075. This closes the sampling
gap in lab115: the negative result also holds for these idle-worker states, not only
already-working gas groups. No runtime description change deployed. Attempt10
remained live at loop5272 with36 owned units during this analysis.

### Lab117 — resource-category choice changes two of three idle decisions

After balance-placement probes failed, test a different action abstraction on the
same last three idle-worker gather menus: replace nine mineral-location options
and one gas-location option with mineral category, gas category and continue.
Preserve full recorded state and instructions; later location selection is not
executed in this offline probe. Original choices all selected gas. Category choices
selected minerals in two states (.66,.62), gas in the third (.62). Six calls,
$0.005470584,artifact076. This changes menu semantics/size and descriptions together,
so it does not isolate choice-count bias. It supports testing a Jev-only resource
then-location hierarchy, with no scripted resource priority. No live policy change
yet; attempt10 still runs the freshness comparison.

### Lab118 — tenth defeat; deploy Jev resource-then-location selection

UI confirms tenth attempt defeated10:19, evacuation09:50,all structures destroyed.
Gas1028 and minerals0 were visible on the final screen. Report077 and checkpoint
retain separate UI evidence.64-loop cutoff allowed more execution but did not win.
Add the abstraction tested in lab117: only when a concrete menu offers both mineral
and gas gathering (plus continue), Jev first chooses resource category, then chooses
an exact offered target within that category. No default resource, allocation ratio,
new command or mission-specific rule. Continue/invalid responses issue no command.
Other control menus retain their existing path.61 tests pass, including preserving
all mineral targets and requiring Jev to select category and exact target.
Start fresh attempt11 with2500calls and64-loop cutoff; added stage may increase
latency and remains a measured tradeoff, not a proven improvement.

### Lab119 — eleventh defeat without resource-category exposure

UI confirmed defeat7:21, evacuation12:48,all structures destroyed. Report078.
No refinery/gas gathering menu appeared in the monitored trial and no
resource_category_choice events were recorded. Thus this failure does not test
the new mineral-versus-gas hierarchy; income interruptions and military attrition
still occur without gas overinvestment. Record UI evidence separately from absent
protocol player_result. Run one more bounded fresh attempt12 with identical policy,
64-loop cutoff and2500call budget. Do not force construction just to activate the
experimental branch, and do not credit any result to an unexercised branch.
