# Three-campaign objective

Scope confirmed by the user: Wings of Liberty, Heart of the Swarm, and Legacy of
the Void. No campaign has been completed. Liberation Day has a fresh, UI-verified
victory (lab169). The Outlaws has a fresh, UI-verified victory at27:57 (lab183),
replacing reliance on the historical false-positive-prone API result.

The user subsequently authorized individual campaign missions played in sequence
with progression recorded here. Native campaign controls and account achievement
credit are not required. The standalone-map route is therefore the active route.
Only verified victories advance this journal; merely loading a later map does not.

| Campaign | Mission | Current evidence |
| --- | --- | --- |
| Wings of Liberty | Liberation Day (`traynor01`) | **Verified victory**, actual mission score screen, 3:44; fresh Jev run with objective compatibility adapter, lab169 |
| Wings of Liberty | The Outlaws (`traynor02`) | **Verified victory**, native mission score screen,27:57; fresh continuous Jev attempt across three controller segments, lab183 |
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

### Lab120 — twelfth defeat; stop repeating an unexercised branch experiment

UI confirmed defeat7:08, evacuation13:01,all structures destroyed. Report079;
checkpoint/result record UI evidence separately from empty API results. The
resource-category stage again had zero logged invocations. Two unchanged-policy
trials now failed without exercising the gas/mineral hierarchy. Thus gas preference
is not the sole cause of poor economy: role selection and regroup/continue behavior
prevent sustained work even when only mineral harvesting is available. Do not
attribute these defeats to the unexercised branch or repeat identical runs merely
to hope for branch coverage. Controller has exited; both earlier victories remain
saved. Next experiment must target general role/continuation reasoning, using
recorded fair states before another live trial. Campaign completion remains unproven.

### Lab121 — literal continuation consequences do not change role choices

Offline paired probe of first three purpose_SCV states with idle units in run12.
Append observed idle/total counts and current orders to continue criterion, explaining
that it assigns no new task to idle units while automatic behavior may continue.
Same state/all other options, alternating pair order. Idle counts5/5,4/5,5/6.
Top choices remained positioning,other,continue in both variants. Continue
probabilities .08→.17,.19→.16,.44→.31; income .35→.36,.06→.11,.16→.19.
Six calls,$0.001994496,artifact080. No consistent decision-level benefit; do not
deploy as a fix or restart a live trial on this basis. Controller remains stopped
after verified twelfth defeat; next work is a different general abstraction probe.

### Lab122 — pairwise role tournament does not recover income selection

Offline first three idle-containing purpose_SCV states from run12. Compare original
menu against all unordered pairs with identical descriptions, instructions and
state. Aggregate selected pair winners by win count; report ties without a manual
resource preference. Original winners positioning/other/continue; pairwise winners
positioning/other/other. Income won2,1,3 individual pairs respectively but never
the tournament. Six calls,$0.002213946,artifact081. This is a changed decision
structure rather than another wording tweak, but gives no evidence of economic
recovery. Do not deploy increased question volume on that basis. No game commands
issued; current controller remains stopped after the verified defeat.

### Lab123 — computed shortfalls: limited negative evidence

Test adding exact catalog resource deficits for previously observed Train/Build
products, without selecting any resource or role. Filter run12 for idle-containing
worker purpose states with fewer than50minerals. Only one recorded state qualifies,
so this is a one-state probe, not the intended three-state comparison. Original
and augmented decisions both selected other; income probability .07→.06 in first
pair. Expanding the filter to worker-job prefixes found the same one state; second
pair also retained other. Each pair2calls,$0.000679266; artifacts082/083 preserve
both measurements. Catalog deficits explicitly do not certify current ability
cost, prerequisites, producer, placement or supply. No deployment justified by
these limited results. Do not count repeated queries as independent game states.

### Lab124 — close the missing research-control path

The adapter requested units/abilities but not upgrades, and offered no research
purchases. Official protocol UpgradeData supplies upgrade_id,name,costs,research_time
and ability_id: https://raw.githubusercontent.com/Blizzard/s2client-proto/master/s2clientprotocol/data.proto
Request upgrade data and offer only exact engine-advertised no-target research
abilities, excluding owned completed upgrade IDs. Resource-ignored availability
may describe a future investment; only resource-aware legal abilities become
executable candidates. Research enters the same Jev shared-budget/producer flow as
other purchases, with zero supply and explicit upgrade—not unit—description.
No undocumented combat effects are invented from names; generic ability remaps
are not guessed across upgrade levels.62 tests pass covering costs, exact offered
ability, completion exclusion and unsupported target forms. This closes a real
control gap; it does not prove the active campaign map offers research or that
research solves the prior defeats. Start attempt13,2500calls,64-loop cutoff.

### Lab125 — expose own completed upgrades to Jev

Attempt13 confirmed live and offering infantry research, with no research selection
in the early sample. Add observed own-player completed upgrade IDs and catalog
names to the fair view and both full/compact decision contexts. This distinguishes
completed research from merely requested or accepted research; no effect magnitudes
are inferred and no opponent upgrades are exposed.62 tests still pass. Changes
hot-reload with the normal player/view pair. Live completion remains to be observed.

### Lab126 — resource-category path exercised live

Attempt13 now invokes the previously unexercised hierarchy. Partial report at
loop3302:84continue and13gather_minerals category selections, no gather_vespene;
minerals6,gas160,income estimates120minerals/min and48gas/min.342calls,$0.245717346,
zero ticks beyond64-loop cutoff. This establishes live branch exposure, not causal
improvement: continue can preserve gas assignments and this is an evolving single
run with research controls also added. Artifact084. Reports now expose resource
category counts and latest own completed-upgrade observations (which can include
initial campaign upgrades; do not mistake them for newly researched upgrades).

### Lab127 — thirteenth defeat despite live resource-category exposure

UI confirmed defeat7:16, evacuation12:53,all structures destroyed. Report085;
699calls,$0.534815316,zero ticks beyond configured64-loop cutoff. The hierarchy
was exercised:129continue and14gather_minerals choices, no explicit gather_vespene.
Initial gas assignments can still persist through continue. Neither intermittent
income nor eliminating stale discards sustained the force. Infantry research was
offered but never selected, so research execution/completion remains unverified.
Do not credit pre-existing campaign upgrade IDs as research performed by this bot.
Controller exited. Two earlier victories remain saved; all three campaigns remain
incomplete. Next experiment must address useful task persistence/allocation beyond
mere execution speed or adding more available controls.

### Lab128 — distinguish started work from completed construction

Add build_progress to observation history. Report only transitions from observed
incomplete to complete as completions, and report each currently incomplete owned
project's progress delta over its contiguous observed history. Missing/disappearing
units break that interval; fresh complete arrivals are not credited to construction.
Short zero-delta intervals are explicitly not proof of abandonment. Selection
facts now separate incomplete_count from damaged_count for completed units, avoiding
labeling natural low construction health as damage needing repair. No automatic
worker reassignment or project priority.63 tests pass with starts, completion,
clock reset and discontinuous observation coverage. Start attempt14,2500calls,
64-loop cutoff. More truthful task feedback is the change under examination;
performance benefit remains unproven.

### Lab129 — recover from authoritative batch token-limit rejection

Attempt14 stopped incomplete after five consecutive max_tokens_exceeded errors,
874 successful calls costing $0.687209544. No victory or defeat is inferred.
The last successful concrete requests carried about 63k characters of state;
character sizing is not a reliable token boundary. Add recursive batch splitting
on the server's specific token-limit rejection, preserving identical state and
all question choices/criteria. Single-question rejection still fails explicitly;
log state and per-question character sizes to distinguish the remaining cause.
Release the parent call reservation before retrying children. Tests exercise a
server rejection below the heuristic threshold, exact question preservation,
budget accounting, and terminal single-question rejection. All64tests pass.
Resume the same mission to test recovery; no gameplay policy changed.

### Lab130 — reduce spatial precision in model context only

Lab129 diagnostics caught a single concrete question rejected with 63,483
characters of state plus 13,818 characters of criteria. Batch splitting cannot
resolve this case. Round position/center arrays in concrete-order context to two
decimals, retaining all entities and facts. The exact observed coordinates and
candidate command tables remain unchanged, as do unit tags and non-spatial
numbers. This removes floating-point representation noise without introducing
an action preference.65tests pass including source immutability. Commit reloads
this policy during the resumed attempt; improvement remains to be measured.

### Lab131 — concrete questions need their own job summaries

Lab130 remained incomplete: Bunker/idle alone exceeded the request limit with
63,507 state characters and15,337 question characters. Rounding alone did not
solve it. Concrete order requests now retain selection_facts only for selections
actually named by the request. All raw own units, visible entities, type summaries,
resources and outcomes remain available. This removes unrelated duplicate job
aggregates without dropping enemy targets or action choices.66tests pass,
including preservation of world facts and source immutability. Resume the same
attempt; no victory/defeat inferred from request failure.

Lab131 reconnect returned the controlled player's API Defeat immediately, before
any new Jev call: runs/20260919T014615.161270Z. This verifies attempt14 ended in
loss, unlike the earlier request failures which were correctly incomplete.
Start attempt15 to evaluate scoped job context. Earlier two wins remain intact.

### Lab133 — count request failures separately from gameplay decisions

Reports now count request rejections, single-question rejections, maximum rejected
state size, affected question names and split reasons. Verify against lab130:
10 rejected requests,8 single-question rejections,19 heuristic splits and2
server-triggered splits. Early attempt15 snapshot:113 successful calls,zero
rejections; this is not yet evidence under late-mission load. Latest mineral
income estimate remains zero, so successful transport does not imply sound play.

### Lab134 — fifteenth attempt ends in API defeat without token rejection

runs/20260919T014635.114048Z returned player1 Defeat.1463 successful Jev
calls,$1.138453596,zero request rejections,309 heuristic batch splits,5 decision
errors and6 ticks beyond the64-loop age limit.2972 successful action results,
33 TargetIsOutOfRange,11 NotSupported,1 TooMuchLife. All94 strategic choices were
protect. Latest observed snapshot still contained2CommandCenters (combined health
2169.15),other buildings,22SCVs and3Marines; this does not establish why the map
ended. Do not infer all-structures-destroyed from the API result alone. Inspect
mission UI/defeat explanation before changing policy on that assumption. The
context fix survived this run; it did not yield victory. Two earlier wins remain.

### Lab135 — API terminal result conflicts with continuing campaign simulation

Read-only UI inspection after attempt15 showed game clock14:04 then14:36,
evacuation06:05 then05:33, workers gathering and no defeat overlay. Two fresh
API observations reported status ended and all9players Defeat, yet game_loop
advanced13897→13908. An empty RequestAction (no gameplay command) was rejected
with Game has already ended. Thus API control really is unavailable, but the
previous claim of campaign gameplay defeat is not established by the UI. Preserve
raw result and add result_discrepancy evidence to both result.json and checkpoint.
Do not advance the mission or silently replace protocol results. Official protocol
state table allows observation in ended but actions only in_game:
https://github.com/Blizzard/s2client-proto/blob/master/s2clientprotocol/sc2api.proto
The cause of the early API termination remains unresolved. Do not change Jev
strategy based on an invented all-structures-destroyed explanation.

### Lab136 — inspect termination plumbing without tactical map leakage

SC2 client sends only allowlisted requests and has no end-game/debug request.
Official state table confirms actions unavailable after ended; reconnecting did
not restore control. Read-only local MapScript inspection was restricted to
DefeatBaseDead/Defeat handlers: the map tests whether any owned PreventDefeat
units remain, displays MissionFailed, then invokes EndCampaignMission. This
explains the normal scripted loss path but does not establish that it ran here.
Do not feed map script, enemy plans or trigger locations into player context.
Keep the live simulation for further UI outcome observation rather than restarting
and erasing the evidence. No new gameplay policy or mission advancement.

### Lab137 — separate early API control loss from later visible defeat

Add a read-only terminal-state probe, used only while controller is stopped.
Seven samples over60seconds: API remained ended/all9Defeat while game_loop
advanced17256→17920, then froze18012; owned unit count fell21→1. Subsequent
SC2 UI showed DEFEAT, All of your structures have been destroyed, at18:45 with
01:24 evacuation remaining. Attach later_ui_outcome to result/checkpoint while
preserving the earlier discrepancy. API stopped accepting actions around12500,
roughly5500loops before actual visible defeat. This trial therefore does not
measure uninterrupted Jev control through the full mission. No win recorded.
The probe requests only observations, records own-unit count/results/clock and
never sends actions or changes a game. Live execution verified its output and
clean exit. Cause of premature API termination remains an infrastructure target.

### Lab138 — capture the exact request that first reports terminal status

Official sc2api.proto documents an end-of-time ceiling of1<<19 simulation loops
and restart hard-reset guidance, but current observed mission loops are far lower;
this is not a demonstrated explanation. Existing process uptime about4h19m.
https://github.com/Blizzard/s2client-proto/blob/master/s2clientprotocol/sc2api.proto
Add status-transition telemetry with request name/id, previous/current status;
result events now include exact observation loop and API status.66tests pass.
Start attempt16 with unchanged Jev policy to gather first-transition evidence,
2500call budget,64loop age limit and camera enabled. No mission data modified.

### Lab139 — reproject job summaries after recursive request splitting

Attempt16 reached61owned units, then concrete questions again exceeded tokens:
59,946state characters plus17,399question characters in a single-question retry.
The caller scoped state to the original batch, but transport splitting retained
all of that batch's job summaries. Reapply exact-name selection_facts projection
inside ask at every recursion. Only apply when every question name exactly matches
a summary; strategic/purpose/investment requests remain unchanged. Preserve all
raw units, enemies, type facts and choices.67tests pass, including split-state
projection and source immutability. SDK wrapper requires controller reconnect.

### Lab140 — reproduce early API termination near the same mission loop

Attempt16 resumed segment runs/20260919T020844.782490Z first transitioned
in_game→ended on observation request574 at loop12531. All9players returned
Defeat. Preceding tick12463 still had55owned units and35submitted commands,
including successful actions. UI afterwards showed13:24 elapsed,06:45evacuation,
a living base and no defeat overlay. This repeats attempt15's control loss near
12500loops; it is not a five-error controller stop. Recursive context projection
allowed508successful resumed calls with no decision errors before termination.
The controller has exited. Keep the discrepancy distinct from a later UI outcome.
Read-only termination-plumbing inspection found campaign autosave calls, but no
causal connection is established; do not alter map triggers based on speculation.

### Lab141 — second visible defeat occurs well after API control loss

Attempt16 UI eventually showed DEFEAT, All of your structures have been destroyed,
at19:13 with00:58 evacuation remaining. Preserve later_ui_outcome in checkpoint
and resumed result alongside API discrepancy. No victory. As with attempt15,
API control ended minutes before the visible loss. Next experiment should use a
fresh SC2 process with unchanged map and Jev policy, to separate process-state
accumulation from a mission-specific API cutoff. Do not interpret this as proof
that a process restart will fix it.

### Lab142 — fresh-process comparison for repeated API cutoff

Quit old SC2 through RequestQuit after the visible defeat and completed probe.
Relaunch through Battle.net Play. Verified new PID73800 (13seconds uptime when
checked), API ping5.0.16.97563,status launched. Start attempt17 with same map,
Jev policy and64-loop cutoff,2500calls. This tests process-state accumulation;
no assertion that it is the cause. Preserve two verified campaign victories.

### Lab143 — fresh process does not remove the approximately12500-loop cutoff

Attempt17 runs/20260919T021911.054534Z returned all9players Defeat at12504,
first terminal response observation1815. Previous tick12464 had28owned units.
Fresh-process PID73800 rules against the simple accumulated-process-state
hypothesis for this reproduction. UI still showed13:21 elapsed,06:48evacuation,
no defeat overlay. Record discrepancy without advancing the mission. Controller
exited after1434Jev calls. Future investigation should target a per-game/API
limit or mission interaction; neither is established yet. Repeating the same
process restart is not a justified next experiment.

### Lab144 — duration-setting search yields no supported workaround

Read-only installed-client string search exposed generic Battle.net duration fields
but no verified configurable API12500-loop limit. Do not set guessed variables.
Paginated all upstream s2client-proto issues and searched campaign/time-limit/
premature-end/12500 terms; no matching issue identified. Local map component
inventory contains only terrain GameData, not a map-local gameplay duration XML
override. This narrows the next inspection to dependency/MapInfo configuration or
protocol behavior; it does not rule either out. No map content or gameplay policy
changed. No additional full-length trial started on these negative findings.

### Lab145 — installed protocol schema exposes a recovery candidate

Read-only decoded the FileDescriptorProto embedded in installed Base97563 binary
at byte69656712 (12034bytes). RequestCreateGame,RequestJoinGame,
RequestObservation,InterfaceOptions fields match current client; no extra duration
field identified. Installed Request/Response include warmstart_game field23,
absent from our published Python package. RequestWarmstartGame fields are
replay_data1(bytes),player_id2(int32),disable_fog3(bool),is_host4(bool),
map_data5(bytes). Response has error1(enum LoadReplayFailed=1),error_details2.
This is evidence of a possible replay-based recovery interface, not evidence that
it works or preserves campaign triggers. No warmstart request sent yet. Any test
must be isolated, keep fog enabled, preserve original replay/results, and not
credit progression unless the actual mission is verified won. Embedded schema
inspection does not provide implementation semantics or official support.

### Lab146 — replay warmstart rejects campaign player configuration

Attempt17 visible defeat confirmed13:43,06:26evacuation remaining. Added later
UI evidence to checkpoint/result. Then tested installed warmstart field23 using
original replay/map,player1,is_hostTrue,disable_fogFalse. Response nested error1
LoadReplayFailed: Not a two-player replay. API remained ended; no gameplay action
was sent. Preserve response bytes locally. Added isolated probe with nested error
parsing; verified parser against actual response. No fake second player or replay
modification attempted. This interface is not a working campaign recovery path;
do not repeat it without new evidence about supported player configurations.

### Lab147 — isolate campaign triggers from API lifetime

Read-only binary constant inspection did not establish a12500-loop limit; no
executable edits. Start separate infrastructure diagnostic, not a campaign attempt:
copy maps/traynor03.SC2Map to ignored maps/api-lifetime-probe.SC2Map, replace only
MapScript.galaxy with void InitMap(){}. Original map remains untouched. This
intentionally removes mission triggers, so no outcome can count toward campaign
progress. API create/join realtime,fog enabled; issue observations only, no Jev
calls or gameplay commands. Sample every10seconds up to65samples (~640seconds),
stop early if APIended. Early sample in_game,loop1,36owned units. Process session
65274; output /tmp/jev-lifetime-probe.log. This tests whether the cutoff survives
without the campaign trigger script; a negative result would not identify which
trigger or dependency caused it. Compare to unchanged stock runs, not win rates.

### Lab148 — preserve the API lifetime experiment as a runnable probe

Add scripts/probe_api_lifetime.py with explicit source map/output and optional
--without-triggers-copy/--storm. Refuses existing map-copy/output destinations,
uses realtime/fog-enabled create/join and observations only. Never changes a
campaign checkpoint. Port the setup and observation loop already executing in
lab147; CLI import/help verified, no second game launched. The existing diagnostic
continues unchanged. This is infrastructure isolation, not a no-Jev campaign bot.

### Lab 149 — camera follows the story without issuing orders

User reports the stream camera lingered around the base. The director previously
held world coordinates between cuts, allowing a moving subject to leave the shot;
quiet combat units also tied with buildings and workers. Track the selected unit
at most once per second after two world units of displacement, without resetting
the shot's dwell timer. Prefer combat units during quiet moments; persist movement
interest for four seconds across observation samples. Frame the subject instead
of averaging it with nearby workers, count shield loss as damage, and apply revisit
penalties to nearby scene cells to encourage spatial variety. All inputs remain
owned units and currently visible enemies. Camera output contains only position
and reason; Jev's strategic and tactical authority is unchanged.

Validation: 70 tests pass, including tracking while preserving cut dwell, army
framing beside a crowded base, shield-damage cuts, quiet-scene rotation, existing
fog filtering and atomic camera reload. Camera module is part of the existing
commit-triggered reload; visual quality still needs observation in an active
campaign run. The separate trigger-free lifetime diagnostic is still running and
has passed loop 12,980 in_game; this is not campaign progress.

### Lab 150 — trigger-free API survives the stock mission cutoff

The read-only, zero-action lifetime probe completed normally (process exit 0):
65 samples, loops 1 through 14,324, all status in_game, 36 owned units, no player
results. Output: /tmp/jev-lifetime-probe.log. This exceeds the reproducible stock
Zero Hour cutoff near 12,500. It weakens the generic API lifetime-limit hypothesis
and implicates something initialized by the original map script; it does not
identify a particular trigger or prove a repair. No campaign progress credited.

Started a second isolated copy, maps/api-libraries-probe.SC2Map, retaining stock
map assets but replacing MapScript.galaxy with the three original includes
(NativeLib, LibertyLib, CampaignLib) and InitMap calling libNtve_InitLib,
libLbty_InitLib, libCamp_InitLib. This separates shared library initialization
from mission-specific globals/triggers. Same observation-only 65-sample protocol,
output /tmp/jev-libraries-probe.jsonl. Initial sample in_game, loop 1, 36 owned.
Original maps and progression checkpoint unchanged; no Jev spend on these tests.

Read-only CASC extraction of installed CampaignLib found its explicit defeat
GameOver call in the AbortMission event handler, rather than a visible duration
limit. This is a search result, not proof that the library cannot cause the cutoff.
Local diagnostic builders and extracted copyrighted sources stay outside Git.

### Lab 151 — shared-library initialization also survives

The libraries-only probe exited 0 after 65 samples, ending at loop 14,311 with
status in_game, 36 owned units and no player results throughout. Evidence:
/tmp/jev-libraries-probe.jsonl. Initializing NativeLib, LibertyLib and CampaignLib
alone did not reproduce stock Zero Hour's approximately 12,500-loop termination.

Next isolated diagnostic: maps/api-campaign-data-probe.SC2Map adds a MapInit event
callback invoking the original libCamp_gf_LoadCampaignData(MapTRaynor03) to those
same library initializers. No original mission combat/objective triggers run.
This function enables CampaignMode and loads tech, bank and UI state, so this
boundary distinguishes campaign setup from the remaining mission script. Output
/tmp/jev-campaign-data-probe.jsonl, same observation-only 65-sample protocol.
The source map remains untouched; this is not an attempt or campaign win.

### Lab 152 — campaign-data setup survives; isolate mission startup

The campaign-data-only probe completed (exit 0), 65 samples through loop 14,338,
all in_game with 36 owned units and no results. Output:
/tmp/jev-campaign-data-probe.jsonl. A UI inspection during the run showed the
map without a visible script-error dialog. No mission credit.

Next diagnostic copies the stock map and retains its entire script except the
single initialization handoff `TriggerExecute(gt_IntroSequence, true, false)`.
That call is replaced with a comment, so original library/global/trigger setup,
LoadCampaignData and the seven mission initialization routines execute, but the
intro's StartAI and StartGame handoffs do not. Registered periodic/event handlers
remain; this is deliberately a broader boundary than the previous probe.
Map: maps/api-mission-init-probe.SC2Map; output:
/tmp/jev-mission-init-probe.jsonl. No player orders, no Jev calls, no checkpoint
updates. This is diagnostic isolation, not a proposed easier campaign version.

### Lab 153 — mission initialization passes; restore intro/timers without AI startup

Mission-initialization probe completed, exit 0, 65 samples through loop 14,371,
all in_game and no player results. UI independently showed the initialization's
400 minerals, 100 gas and night lighting, supporting that the intended startup
routines executed. Evidence: /tmp/jev-mission-init-probe.jsonl.

Next diagnostic retains the original complete map script except the one
`TriggerExecute(gt_StartAI, true, false)` call in IntroSequence. IntroSequence
and StartGame now run, including mission timers and registered events; StartAI's
campaign AI starts, attack-wave routines and difficulty research are withheld.
Map: maps/api-without-ai-probe.SC2Map. Output: /tmp/jev-without-ai-probe.jsonl.
This remains an observation-only isolation test, never a campaign attempt.
These negative tests do not yet exclude an interaction with the player harness:
none issue its normal action/query traffic. No claim of a specific root cause.

### Lab 154 — speed up subsequent isolation experiments

Add optional --stepped to the standalone lifetime probe: create a non-real-time
single-player game and advance 256 loops between observations. The default
remains real-time; records now identify mode. Production SC2 client and campaign
runner retain their request allowlist (step forbidden) and real-time behavior.
This mode does not issue unit orders or update campaign progress. It permits
faster exploratory isolation, but a stepped negative result cannot exclude a
real-time-specific failure; any proposed repair needs real-time confirmation.
Validation: CLI help loads and 70 existing tests pass. Stepped integration has
not yet run because the real-time no-AI probe still owns the live game/socket.

### Lab 155 — timing mode matters; test stock map without controller traffic

No-AI-handoff real-time probe exited 0 at loop 14,153, all samples in_game,
36 owned units, no results (/tmp/jev-without-ai-probe.jsonl). UI confirmed the
holdout objective and running evacuation timer, so StartGame executed.
Stepped counterpart passed through 16,384 with 36 owned units and no results
(/tmp/jev-without-ai-stepped.jsonl).

A second copy replaces the withheld StartAI handoff with its three original
AICampaignStart calls, retaining other mission startup but withholding scripted
wave/research routines. Stepped test passed through 16,384, 35 owned, no results
(/tmp/jev-native-ai-stepped.jsonl). This does NOT exclude a real-time AI issue.

Unmodified stock map, stepped, observation only: passed through 16,384 despite
0 owned units in the final samples, no API results (/tmp/jev-stock-stepped.jsonl).
This demonstrates that stepped timing does not reproduce the real-time failure
under this setup. The script uses real-time waits as well as game-time waits;
therefore these fast negative probes cannot identify or clear a root cause.

Started unmodified stock map in real time with observation traffic only, no
Jev calls, actions or queries: /tmp/jev-stock-realtime-idle.jsonl. This controls
for player-harness traffic, a confound shared by all earlier isolation probes.
Losing an idle stock map is expected; compare terminal loop, owned-unit count
and visible UI state rather than treating any defeat as the API defect.
All these runs are infrastructure diagnostics and leave campaign checkpoint
unchanged. No weakened map is being proposed for actual campaign play.

### Lab 156 — stock idle defeat is visible but absent from API results

Stock-map real-time observation-only baseline finished all 65 samples (exit 0).
The idle force lost its structures; UI explicitly showed DEFEAT, 'All of your
structures have been destroyed', game clock 10:58 and evacuation 09:11. API
observations froze at loop 10,540 with four owned units, status in_game and no
player results, persisting through the end of /tmp/jev-stock-realtime-idle.jsonl.
Thus this run ended visibly BEFORE the approximately 12,500-loop cutoff. It
cannot exclude controller traffic as a cause of that later phenomenon.

After the probe closed, a separate connection issued ping, observation, empty
query, empty action (zero commands), observation. All returned in_game; both
observations remained at 10,540 with no results. Evidence:
/tmp/jev-idle-terminal-requests.json. The API/UI disagreement can therefore go
in both directions. Do not infer campaign victory/defeat solely from a stall.

Next real-time probe uses api-native-ai-probe.SC2Map: full mission sequence,
three original AICampaignStart calls, but withheld scripted attack-wave/research
routines. This controls the stepping-mode confound from lab155 and aims to reach
the cutoff without early idle defeat. Output /tmp/jev-native-ai-realtime.jsonl.
No campaign credit, unit orders, Jev calls or changes to the stock map.

### Lab 157 — native AI and post-cutoff view queries remain healthy

Native-AI-only real-time probe completed, exit 0, 65 samples through loop 14,153,
36 owned units, all in_game, no results (/tmp/jev-native-ai-realtime.jsonl).
So native AICampaignStart plus mission timers does not reproduce the cutoff
without the scripted wave/research routines and normal player action traffic.

After the probe closed, the same game received the normal game_info/data and
make_view observation/query pipeline for 20 iterations, with no unit commands.
It remained in_game through loop 14,987 after 83 requests, 36 owned units and no
results (/tmp/jev-post-cutoff-view-pipeline.jsonl). This rules out an immediate
termination merely from asking for the rich view after the numerical cutoff;
it does not test long-running query traffic from mission start.
GameInfo confirms player 1 Participant and players 2–9 Computer under our current
single Participant create_game configuration; extra computer setup is not needed
simply to obtain those player types.

Re-read prior failure logs: attempts 15/16/17 retained two CommandCenters at their
last pre-terminal tick, plus differing other structures and workers. Visible
allied Marines also remained. No evidence supports a simple 'no town hall' or
'all allies gone' explanation. Attempts 16/17 terminated about 560 seconds after
join_game despite different connection/request histories. Root cause unresolved.
Do not turn the isolated diagnostic map into a campaign solution.

### Lab 158 — restore full Jev/controller traffic on isolated native-AI map

Started the unchanged normal player harness against api-native-ai-probe.SC2Map,
with real-time control, camera following, max age 64, 650 seconds and 2,500-call
ceiling. Run: runs/20260919T035753.415530Z; stdout:
/tmp/jev-native-ai-controller.log. This restores ordinary Jev decisions, raw unit
actions, query traffic and camera actions to the configuration that passed the
observation-only test. It is a diagnostic, not a stock mission attempt; its run
folder contains diagnostic.json with campaign_credit=false and the campaign
runner/checkpoint are not involved. No tactical instructions or player patches.

Initial telemetry confirms successful decisions and camera army overview plus
tracking moving force shots. No initial decision errors. This run also provides
live validation of lab149 camera integration, though the lack of scripted waves
means it cannot assess camera behavior in a full campaign battle.

### Lab 159 — full Jev traffic passes without scripted waves

Diagnostic runs/20260919T035753.415530Z exited normally at its 650-second limit,
last controlled tick 14,500 with 67 owned units. No API ended transition and no
player results. 1,658 Jev calls cost $1.1538156; four transient TimeoutErrors,
all recovered. Result correctly remains incomplete, reason time limit reached;
diagnostic.json excludes campaign credit. No progression checkpoint touched.

This restores normal player choices, unit actions, query traffic, camera actions
and live reload on the native-AI-only configuration and passes the former cutoff.
Thus normal controller traffic alone is insufficient to reproduce the failure.
The remaining comparison includes scripted wave/research routines and the combat
outcomes they induce; interaction with controller behavior is still possible.
No production change has been established as a fix.

Camera integration: 30 army overviews, 31 moving-force shots, 31 tracking moves,
one visible engagement and one firing shot. The final UI inspection showed a
running mission at 15:13, evacuation 04:56. This validates live camera actions,
but combat cinematography still needs validation under the full stock attack load.

### Lab 160 — ordinary API bookmark restores campaign world; opt-in recovery trial

Installed AI.galaxy declares AIAttackWaveSend as native, so its implementation
is not available in extracted scripts. Rather than weaken stock mission waves,
test the documented API QuickSave/QuickLoad bookmark as infrastructure recovery.
On the existing diagnostic campaign world, both calls succeeded. API loop reset
from 18,499 to 2 while the UI retained the built-up world, resources and mission
countdown (19:27 elapsed, 00:42 remaining shortly after). Evidence:
/tmp/jev-bookmark-probe.json. Loading from actual API ended state is UNVERIFIED.

Add --api-bookmark-recovery, disabled by default, to runner and campaign CLI.
Save every 45 seconds while active; permit at most one restore when API says
ended, at least two player results all say Defeat, and an owned completed live
structure remains. Preserve the raw terminal observation in the journal event.
Never restore a victory/mixed result or retry a failed restore. Clear policy,
action-feedback and camera memory after restore because API loops reset; discard
pending commands and observe afresh. Paid call/time budgets do not reset. The
player policy itself receives no save/load controls or tactical instructions.
This uses a save/load feature rather than changing waves, resources or fog.

74 tests pass, covering opt-in behavior, save throttling, one-restore limit,
exclusion of victories/mixed results/missing structures, and failed-load limits.
Next trial is the unmodified Zero Hour map with this experimental recovery on;
no claim that a bookmark fixes the premature end until verified there.

### Lab 161 — timeout ceiling prevented testing recovery; resume same mission

Attempt 18 stopped incomplete after five consecutive outer decision timeouts,
last submitted tick 9,919 (59 units), last bookmark 10,319. 1,114 Jev calls,
$0.826080696. Run runs/20260919T041506.465238Z. No API end or restore occurred.
Successful subrequests near the stop typically took 0.6–0.8 seconds, occasionally
1.45 seconds; the decision pipeline has multiple sequential stages and split
requests. The fixed three-second outer deadline can cancel otherwise successful
stages repeatedly as the view grows.

Let the outer deadline follow the configured observation-age budget (22.4 loops
per real-time second), retaining the old three-second minimum. Resume this same
mission with max age 128 rather than 64, giving about 5.7 seconds for the complete
pipeline. Every command still undergoes fresh legality/ownership/target validation;
stale decisions beyond the configured age remain discarded. This tests the
latency/recency tradeoff, not a mission-specific tactical change. Remaining call
budget for the resume is 2,086, preserving the original combined 3,200-call cap.

### Lab 162 — bookmark restores control briefly, repeats failure; keep results without replay

Attempt 18 resume runs/20260919T042410.044420Z saved at loop 12,057. API all-player
Defeat appeared at 12,563. QuickLoad succeeded and restored in_game at loop 2;
Jev issued fresh validated orders after memory reset. About 21 seconds later,
the same all-player Defeat returned at new loop 478 (roughly the same mission
point). The one-restore ceiling correctly stopped further restores. This is NOT
a durable fix. Resume used 114 calls, $0.085138074; combined attempt 1,228 calls,
$0.91121877. Later UI still showed active play at 15:53, evacuation 04:16.

QuickLoad disabled replay recording; SaveReplay returned 'Not currently recording
a replay. May be caused by using RequestQuickLoad.' That exception previously
prevented finished/result.json and checkpoint accounting. Preserve the outcome
and cost even if replay saving fails, recording replay=null and replay_error.
A regression test exercises terminal attach with replay failure and verifies the
persisted result. Reconstructed this interrupted resume summary and checkpoint
entry directly from events, explicitly labeled, retaining API/UI discrepancy.

New concrete hypothesis: failing the optional rescue objective may be interpreted
as terminal by the API. The script marks that objective failed on a rebel-group
loss; the UI later displays that bonus objective in red while main holdout remains
active. This is correlation, not proof. A small isolated objective-state test can
check the engine behavior without another full Jev run. Do not yet change stock
objectives or credit this attempt as won/lost from the contradictory API alone.

### Lab 163 — reproduced: objective state alone terminates API, including bonuses

A tiny isolated map script creates an optional objective, waits five game seconds,
then marks it Failed. At the next sample (loop 225), API changed in_game to ended
and reported Defeat for all nine players, with all 36 owned units unchanged and
no combat. Repeated with a separate main objective explicitly still Active:
same result. Repeated with optional objective Completed: all nine players instead
reported Victory at loop 226. Control keeping both objectives Active remained
in_game through loop 674. Evidence files:
/tmp/jev-objective-failure-probe.jsonl,
/tmp/jev-objective-mixed-failure-probe.jsonl,
/tmp/jev-objective-mixed-complete-probe.jsonl,
/tmp/jev-objective-active-control.jsonl.
Disabling InterfaceOptions.score did NOT prevent this (/tmp/jev-objective-no-score.jsonl).

This directly reproduces the premature API termination without waves, combat,
Jev or controller actions. Zero Hour's ObjectiveRescueFailed calls this native
ObjectiveSetState on the bonus rescue objective; the observed mission UI showed
that bonus failed while main holdout continued. This explains the earlier negative
isolation probes: they avoided the combat that failed the optional objective.
The recovery bookmark repeats the same mission event, so cannot fix it.

Preserve a reusable reproduction: scripts/probe_objective_result.py copies a
local source map, replaces only its diagnostic script, and runs four real-time
samples. --state Active/Failed/Completed selects the control or terminal variant.
These copies never count as campaign missions. Example:
uv run python scripts/probe_objective_result.py maps/traynor03.SC2Map maps/new-objective-test.SC2Map --storm /tmp/jev-research/StormLib/build/storm.framework/storm --output /tmp/new-objective-test.jsonl --state Failed

Consequences for verification: both previously credited opening wins used
unanimous API Victory, which is now proven insufficient. Preserve the historical
records but mark completion verification under review; checkpoint has an explicit
review gate before further progression. README and journal headline corrected.
Unanimous multi-player Victory/Defeat now yields incomplete rather than a verified
mission result. 77 tests pass, including rejection of these false terminal results
and prevention of advancement from a checkpoint awaiting independent review.
Independent evidence must establish real mission completion; do not assume those
wins were either genuine or false solely from this reproduction.

Attempt 18 later truly lost: UI DEFEAT at 19:17, evacuation 00:52, all structures
destroyed. Added this independent outcome to its raw API/recovery record.

### Lab164 — camera cuts when combat starts, replaces lost subjects

Continue the presentation-only director from lab149: moving-force tracking,
army preference over idle bases, visible engagement framing and shield/health
damage cuts. A quiet shot previously held for seven seconds even when another
force began firing. Now permit that transition after 2.5 seconds, while holding
between simultaneous fights to avoid rapid cuts. Immediately replace a subject
that disappears instead of watching its empty location for the remaining dwell.
Nine camera tests pass, including these transitions and committed-module reload
failure recovery. No unit orders or Jev decision policy changed. This incremental
change is test-verified, not yet validated in a new live campaign run; campaign
control still needs the objective/API compatibility fix described in lab163.

### Lab165 — invisible objectives still terminate control; banks inconclusive

Extended the isolated objective reproduction with --hide-before-update. Native
ObjectiveShow(objective, PlayerGroupAll(), false) immediately before marking the
bonus Failed still produced ended / all-nine Defeat at loop 224 with 36 owned
units. Evidence: /tmp/jev-objective-hidden-lab165.jsonl. This is a diagnostic map,
not a campaign attempt. Together with score=False in lab163, this rules out two
simple observation/display workarounds; no mission rules have been changed.

Read the local TCampaign, TRaynor01 and TRaynor02 banks. TCampaign has completed
age entries for maps 1 and 2, but MissionCompletion and MissionBestTime sections
are empty, and all three banks have recent diagnostic-era modification times.
Installed LibertyCampaignLib explicitly records difficulty completion and best
time from RunMissionVictorySequence via TS_SaveMissionCompletion. Current bank
contents therefore do not independently verify either earlier credited run;
leave the review gate intact. A replay/outcome audit or fresh instrumented stock
run remains necessary. No gameplay calls or paid Jev calls during this probe.

### Lab166 — objective state bridge passes minimal live proof

Explicit Computer in CreateGame did not bypass objective termination: hidden
Failed diagnostic still ended at loop 225, all nine Defeat, 36 owned. Evidence:
/tmp/jev-objective-computer-lab166.jsonl. Added --explicit-computer to the lifetime
probe so this negative result is reproducible.

New scripts/objective_state_bridge.galaxy is an experimental pair of wrappers,
not yet installed in campaign maps. SetState stores the exact requested state in
a separate data-table key; GetState returns it. Native presentation stays Active
for Completed/Failed with an explicit name prefix, avoiding the API terminal hook.
An isolated script sets a bonus state, waits, and checks the wrapper getter. Only
a matching getter result then invokes a native Completed diagnostic end signal;
a mismatch invokes Failed. These are artificial test outcomes, never campaign
credit or weakened gameplay missions.

Live Failed case: API still in_game at loop 225, then expected Victory at 449.
Live Completed case: still in_game at 225, then expected Victory at 450. Both kept
36 owned units. Baseline native calls ended at 224-226. Evidence:
/tmp/jev-objective-bridge-lab166.jsonl and
/tmp/jev-objective-bridge-complete-lab166.jsonl. Screenshot confirmed the diagnostic
objective label exists. 79 Python tests pass; the Galaxy evidence is the live
probe, not those tests. No paid Jev calls.

Before campaign integration this proof needs full lifecycle support (creation in
terminal states, name changes, destruction/ID reuse), interception of reads and
writes in every included campaign library, and a separate genuine mission-ending
signal. Leaving any native state readers unadapted could change mission behavior.
Do not apply this partial wrapper to a campaign yet. Preserve all trigger
conditions, objective states, combat and rewards; never count this diagnostic's
native Completed signal as a campaign victory.

### Lab167 — lifecycle proof and conservative source rewriting

Expanded the experimental objective adapter with terminal-state creation,
player-scoped creation, preserved LastCreated, original-name getters/renaming,
single destruction and native group destruction. Getters validate native IDs;
creation clears old cached state before any possible ID reuse. Terminal states
are still presentation-only Active plus a label, while script reads retain the
original state. This remains uninstalled in production campaign maps.

Live probe scripts/probe_objective_lifecycle.py covers creation Completed, state
Failed, renaming without losing state, Hidden/Active transitions, destroyed-ID
Unknown, scoped Failed creation, DestroyAll and a fresh Active creation. The first
diagnostic accidentally destroyed its own result objective with DestroyAll; it
stayed in_game through672 and did not prove assertions passed. Corrected the test
to create the result carrier after destruction. The corrected test remained
in_game at225 and emitted the expected all-player diagnostic Victory at449 only
after all assertions passed. Evidence: /tmp/jev-objective-lifecycle-lab167b.jsonl.
Neither diagnostic has campaign credit; no Jev calls or gameplay orders issued.

Added a lexical call rewriter with five tests: comments, strings and native
declarations remain unchanged; only known objective call identifiers change.
Unexpected user declarations or indirect references fail closed. Dry-running
against installed source found ten objective calls in Zero Hour's MapScript and
two state readers in CampaignLib. NativeLib and LibertyLib implementation/header
files have no affected calls. This confirms patching only the map would leave
campaign-library reads inconsistent. Packaging the full include closure and
independent genuine mission-end signaling still remain before campaign use.

### Lab168 — package the complete include audit and prove library interception

scripts/build_objective_bridge.py reads map dependencies and recursively resolves
all Galaxy includes from installed assets. It refuses ambiguous differing module
overrides, unresolved includes, indirect objective references and overwrites.
Records original/rewritten hashes and every replaced call in a local map sidecar.
It copies the original map, changing only objective call names plus bridge
includes and adding our adapter. Original triggers, conditions, units, terrain,
combat and rewards are retained; scripts are never given to Jev.

Zero Hour and Liberation Day each resolved 121 script files. Only MapScript and
CampaignLib need changes, plus the new adapter file. Root TriggerLibs archive
paths work. Zero Hour startup showed its normal evacuation objective, timer and
resources with no visible script error. Startup alone did not prove interception.

Added scripts/probe_campaign_bridge.py: synthetic mission objective Completed
through the adapter must still be native Active, while the UNCHANGED existing
CampaignLib all-objectives-completed helper must return true. The first test
assigned a constant and failed to execute, so its empty-UI/in_game result is not
success. Removed that invalid test assignment. The corrected probe stayed active
at225 and emitted expected diagnostic Victory at450, proving the embedded library
override actually executes and reads the shadow state. Evidence:
/tmp/jev-campaign-library-bridge-lab168c.jsonl. A Base.SC2Data placement variant
was built during diagnosis but is unused; reverted builder to the proven root
layout. No diagnostic counts as campaign completion.

Prepared maps/traynor01-bridge-lab168.SC2Map and matching .bridge.json for a fresh
Jev-driven verification run of the disputed first win. Automatic credit remains
disabled; observe actual mission-ending UI and preserve replay/outcome evidence.
The per-map sidecars explicitly retain experimental=true and campaign_credit=false
until broader equivalence/outcome handling is verified. Two additional dependency
parser tests pass; no gameplay policy changes in this experiment.

### Lab169 — Liberation Day genuinely won; detect real campaign endings

Fresh unchanged Jev policy on the objective-adapted Liberation Day reached the
actual VICTORY score screen: mission time 3:44, Dominion Marines killed20/22,
civilians liberated59/61, units lost9, holoboards0/6, Raynor kills6. Verified via
computer-use screenshot, independently of API results. Run:
runs/20260919T045655.274174Z. 470 Jev calls, $0.162332226. Replay saved24781bytes;
map identity checked through GameInfo. ui-outcome.json records screen evidence;
result.json reconstructed from event totals and that independent ending evidence.
This verifies a fresh main-objective win, not the historical API-only win.
Removed Liberation Day from the checkpoint review gate; Outlaws remains under
review. No campaign is complete. Optional holoboards were not completed.

API remained in_game even on the victory screen (observed loop7966), and the
controller continued to spend calls. Stopped that owned controller with SIGINT
after preserving the UI evidence, then saved its replay via the API. This shows
we need a genuine ending channel as well as suppressing objective-based false
ends. Camera logs and screenshots showed mobile forces and combat, rather than
an idle base. Temporary loss of owned observations during a cinematic recovered.

Added optional --record-outcomes to the builder. For the audited Liberty campaign
library, a unique call to TS_SaveMissionCompletion inside RunMissionVictorySequence
is followed by a bank marker; original victory logic continues. Player1 GameOver
Defeat is similarly recorded before the original call. InitMap creates a unique
build-specific bank with active state. No objective success alone writes victory.
Other campaign libraries fail closed until their ending semantics are audited.

OutcomeMonitor verifies map hash and bank filename, requires a freshly observed
active state before any terminal marker, and tolerates incomplete XML writes.
The harness stops on the marker and saves the replay. Experimental sidecars still
have campaign_credit=false, so detected endings remain incomplete pending UI
verification; this avoids silently advancing from a new unvalidated hook.

Native marker tests passed for victory and player-defeat, each after fresh active:
/tmp/jev-outcome-victory-lab169c.json and /tmp/jev-outcome-defeat-lab169.json.
The first marker test could not find its bank: SC2 removes underscores from bank
filenames. Changed generated names to alphanumerics and retested. Raw native
DateTime value is now labeled engine_time, not a simulation loop. These synthetic
tests have no campaign credit and issue no Jev/unit orders.

The first transition away from the genuine victory screen disconnected and
exited SC2. Confirmed process absent, relaunched through Battle.net, then ran the
marker tests successfully. New process PID84249. Prepared Outlaws with preserved
mission rules and ending markers: maps/traynor02-outcomes-lab169c.SC2Map. Next run
will verify both the disputed second win and marker timing against actual UI.

### Lab170 — preserve ending monitoring on reconnect; probe investment sampling

Outlaws verification remains live under unchanged Jev policy in
runs/20260919T051054.128301Z, process session82717. At loop8852:51 owned units,
29SCVs,8Marines,5Barracks,7Depots,1Refinery,1CommandCenter;743 calls and no observed
controller errors. Jev changed its strategy to attack after prolonged strengthening.
No ending marker yet, no victory credited. Prepared Zero Hour with the same
objective/outcome adapter: maps/traynor03-outcomes-lab170.SC2Map.

Fixed a reconnect gap in the harness: --attach without --map now resolves the
current API map name to its local hash-checked bridge sidecar. A preexisting active
bank can arm the monitor; an already-terminal bank alone cannot produce credit.
No running controller restart was needed for this future reconnect fix. 92 tests
pass. Added exact build/run/reconnect commands and limitations to CAMPAIGN.md.

Observed a weak sampling decision at loop5022: with30 supply free, a7%-probability
save-for-SupplyDepot option was sampled and later purchased. This is a policy
sampling consequence, not proof that Jev's top choice requested that depot.
Consulted git log and labs068/074/076: pure argmax previously hoarded resources;
sampling and bounded named commitments were introduced deliberately. Do not
blindly revert to an already-stalled method.

New offline scripts/probe_investment_comparison.py selected the last three recorded
investment samples differing from Jev's top choice. Same recorded states; compared
full-menu replay to a two-option comparison between sampled/top alternatives;
alternated option and request order. Six calls,$0.001744848. All three full-menu
replays repeated the original top choice, and all three comparisons preferred it
over the sampled alternative (loops7696,7727,7773). Artifact:
docs/experiments/170-investment-comparison.json. This small descriptive probe does
not establish strategic utility or a better live policy; two preferred choices
were save. No game commands or live-policy change resulted from the probe.

### Lab171 — provider funding stop; preserve Outlaws for continuation

Outlaws run20260919T051054.128301Z ended incomplete when OpenRouter rejected paid
inference. Recorded1085 calls,$0.732872406; replay saved normally. The key still
has spending-cap room, but the account balance is exhausted (checked read-only;
account-wide billing details are not published here). Requested a top-up from the
user. No alternative model or non-Jev gameplay policy was substituted.

Last controlled tick11152:38SCVs,8Marines,9Depots,7Barracks,1Refinery,1CommandCenter.
Three isolated ReadTimeout errors occurred and recovered before the billing stop.
No campaign ending marker was observed. This is not a defeat or a verified win.
After confirming the controller process exited, opened the game menu to preserve
the running mission. UI13:44; two API observations one second apart both loop13191,
status in_game,68 owned units. Pause evidence saved in the run's paused.json.
Do not restart this mission simply because funding stopped.

Resume after confirming credits are available: return from the game menu, then
attach without --map to preserve this exact world. Use the same objective and
camera, with at most1915 additional calls to retain the original3000-call cap:
uv run python -m jev_sc2 --attach --seconds 690 --max-calls 1915 --max-age-loops 128 --follow-camera --objective 'Destroy the Dominion Base.'
The current map must remain traynor02-outcomes-lab169c.SC2Map. The new reconnect
monitor can arm from its active ending bank. Verify actual UI outcome before
clearing the remaining checkpoint review gate. All three campaigns remain the
goal; funding currently prevents further Jev-driven play.

### Lab172 — funded continuation exposes per-question context growth

Resumed the exact paused Outlaws world, without restarting the mission, after
confirming provider credits. Run20260919T074549.368696Z made616 calls,
$0.533949990, then stopped after five consecutive decision failures. Replay saved.
Single concrete-order questions reached about79k characters (52k state plus27k
criteria) and received max_tokens_exceeded. Batch splitting cannot fix a single
oversized question. No victory or defeat is credited.

Changed general order context to a columnar unit roster, retaining values and
explicit column names instead of repeating field names for every unit. On the
last recorded order batch, state size fell53782→44679 characters. A read-only
Jev replay answered all3 questions in1 call,$0.001008294; this establishes request
acceptance, not equivalent strategic quality or a universal token bound. All92
tests pass, including roster reconstruction and preserving command precision.

SC2 process84249 remains present but its window is black and an API observation
is pending. Do not infer a mission loss or restart from this observation alone.
Remaining original call allowance after both gameplay runs:1299 calls.

### Lab173 — recover ended client and test compact roster in a fresh attempt

The exact Outlaws outcome bank now contains defeat, engine_time1789807154,
after the controller had stopped on input-limit errors. Copied bank and recovery
evidence into runs/20260919T074549.368696Z. UI corroboration was unavailable:
window remained black, observation exhausted its120-second timeout, and normal
quit plus SIGTERM did not exit process84249. Forced termination only after this
evidence, verified process absence, then relaunched through Battle.net.

New client903 connected on the same API port and began loading the same adapted
Outlaws map. Fresh attempt uses1200seconds/3000calls with compact roster commit
97178b9 and otherwise unchanged Jev policy. Prior attempt remains incomplete in
its original result; the later defeat marker is separate evidence. No campaign
advancement or verified win claimed. This retries Outlaws, not Liberation Day.

### Lab174 — compare roster encodings without changing gameplay facts

Added scripts/probe_roster_encoding.py. Selected first/middle/last successful
object-roster order requests from run20260919T074549.368696Z, replayed identical
questions with object versus columnar rosters, alternating request order. Six
calls,$0.006584004. Across6 questions (1/2/3 per state), chosen actions matched6/6.
State character counts:43436→36366,46448→39485,53782→44679 for68/67/87 units.
Artifact docs/experiments/174-roster-encoding.json includes full answer distributions.
Single trials on successful recorded requests do not demonstrate identical policy
quality, universal token safety, or performance improvement. No game orders came
from the probe. This tests representational sensitivity, not a strategic override.

Fresh Outlaws attempt is still running. At loop1918 it has10SCVs,2Barracks,
1CommandCenter,1Refinery,2SupplyDepots and no Marines. No decision errors or
request rejections yet. Early army loss is evidence of a gameplay weakness;
compact context has not by itself solved campaign play. Retain unchanged policy
for this attempt while collecting the actual outcome.

### Lab175 — retain measured attrition beyond the short outcome window

Live Outlaws loop3221:12SCVs,3Marines,3Barracks,2Depots,1Refinery,1CommandCenter;
315calls,$0.176979642, no decision errors. Its recent_outcomes window reported
no disappearances because the initial army loss had aged out of the672-loop
window. This is a context limitation, not evidence that Jev would make better
choices with longer memory.

Added cumulative observed unit appearances/disappearances by type to the outcome
summary. Every observation transition is counted once; counts survive rolling
window pruning and reset on loop rewind. On hot reload only retained history is
seeded, with an explicit since_loop: discarded earlier evidence is not invented.
Counts are not presented as kills, deaths or production totals because transport,
morphs and triggers can change presence. Jev still chooses all gameplay actions.
This changes general temporal context, not a mission-specific strategic directive.
93 tests pass, including duplicate observations, window expiry and rewind.

### Lab176 — temper investment exploration without replacing Jev

At live loop5366:17SCVs,5Marines,4Barracks,5Depots,1Refinery,1CommandCenter;
551calls, no decision errors.47 of87 investment samples differed from Jev's top
choice. This is a policy-level intervention, not proof that every deviation was
bad. Reviewed labs068/074/076 and lab170: deterministic top-choice spending
previously stalled on save; unrestricted sampling can select low-ranked extra
capacity; pairwise preference probes alone did not establish better outcomes.

Experiment: square Jev's positive legal investment probabilities before sampling.
For example,.75/.25 becomes.9/.1, retaining non-top possibilities without making
them equally frequent as before. Normalize by the largest weight first to avoid
numerical under/overflow. Preserve original model probabilities and log the actual
sampling probabilities/exponent separately. No unit-specific weights, build order,
mission coordinates, or LLM-selected tactical commands. Savings commitments remain
unchanged. This is a heuristic exploration tradeoff, not calibrated utility.

94 tests pass, including the ability to select a lower-ranked legal action and
matching telemetry for the actual sampling distribution. Compare subsequent
spending, saving stalls, army retention and verified outcome; mid-run context
changes and prior losses prevent treating this attempt as a controlled A/B test.

### Lab177 — correct asymmetric observed capability descriptions

While monitoring the tempered sampling trial, recorded investment criteria still
said Marine action capabilities had not been observed, despite earlier legal
movement/attack candidates. The capability accumulator retained only Train/Build
and gather candidates. Workers therefore received rich capability descriptions
while combat/support observations were omitted. Weapon catalog facts were present,
so the omission is not proof of the cause of poor investment decisions.

Added generic observed Move, Attack-visible, Attack-move and existing support
capability descriptions to the same accumulator. No invented powers or prescribed
unit ratios; these labels derive only from offered candidates.94 tests pass.
This corrects a factual presentation asymmetry across all missions. It also means
this run cannot isolate the sampling exponent's effect. At loop7871 before this
change:22SCVs,4Marines,4Barracks,8Depots,1Refinery,1CommandCenter;862 calls,
$0.53322255, no decision errors. Screenshot confirmed active Outlaws at8:31 and
substantial excess supply. No ending marker yet.

### Lab178 — observe army recovery; prepare the next unplayed map

Held gameplay policy at bf52b48. At loop10054:30SCVs,14Marines,5Barracks,
8Depots,1Refinery,1CommandCenter;1199calls,$0.78694203, no decision errors.
Since the capability-label correction, an intermediate sample contained34
investment samples,9 non-top selections,10 Marine purchase requests,2 SCV
requests,1 Refinery request and22 save decisions. Strategy selections included
strengthen3/attack5/assemble1. At loop11438 the army reached22Marines, with31SCVs.
No ending marker. These are observations, not proof of improvement caused by any
one patch: earlier sampling and memory changes confound this single live attempt.

Prepared maps/ttychus01-outcomes-lab178.SC2Map for later Smash and Grab using the
same objective/outcome adapter. Builder audited121 included scripts and changed
only MapScript, CampaignLib and our bridge. Sidecar provenance recorded locally.
The map has not been run or credited. Zero Hour remains the next mission after a
verified Outlaws win; no advancement or completed-prefix change made.

### Lab179 — larger army exposes the remaining context ceiling

Kept policy unchanged while observing the live process. At loop12774:30Marines,
33SCVs;1762calls,$1.261968372. Jev repeatedly chose attack. UI later showed many
units near the base, but recorded orders included attack-move toward remembered
locations, so a screenshot alone did not establish tactical inactivity. At
loop15484:43Marines;40 continuously observed Marines had mean net displacement6.9
and sampled travel15.7 over the recent window. No manual unit orders were issued.

At loop16371:47Marines,38SCVs,5Barracks,10Depots,1Refinery,1CommandCenter;
2390calls,$1.8154185. Single-question max_tokens_exceeded errors have reappeared:
about46–47k state characters plus29–30k question characters. Successful decisions
still occurred between errors; process session45217 remained live on polling.
The roster change delayed, but does not solve, scaling limits. Next investigation
must address large concrete choice menus as well as state representation. No
verified ending or campaign advancement. Do not restart this live mission solely
because some observations or inference calls fail.

### Lab180 — Jev-selected finalists for oversized concrete order menus

Run20260919T180813.430207Z stopped after five consecutive input-limit errors:
2597calls,$1.998187842, replay saved. Paused the same mission through the game
menu; UI clock19:22. No restart or mission credit.

Concrete order questions larger than16k characters now split their options into
halves recursively. Jev chooses a finalist in each half, then Jev chooses between
those finalists. Every original option is exposed; invalid finalists fail closed.
State and descriptions remain unchanged. The transport's existing call budget
and decision deadline still apply. No strategy/production menu change. This is
not mathematically equivalent to a full-menu choice: grouping/order may affect
preferences, and final probabilities refer only to finalists. Stage telemetry
records that limitation. Larger state alone can still exceed the provider limit.

95 tests pass, including full option coverage and Jev-only finalist selection.
Recorded-state probe (no commands): SCV / Move Move,27030 question characters,
46225 state characters, answered through3 calls,$0.003079062. Artifact
180-menu-tournament.json. Acceptance does not establish strategic improvement.
Resume same world with403 remaining calls from the initial3000-call allowance.

### Lab181 — staged menus survive the continuation; preserve the large army

Continuation runs/20260919T182412.951736Z stopped cleanly at the call allowance:
402 successful calls,$0.339882564, no decision errors. At an intermediate snapshot
29 menu tournaments had completed,115 owned units, maximum decision age76 loops
(below configured128). At final controlled loop21445:55Marines,44SCVs,10Depots,
4Barracks,1CommandCenter,1Refinery. No ending marker. Combined with the preceding
2597-call segment,2999 successful calls used the original3000 allowance (inflight
reservations can stop below the exact limit). Replay/result saved normally.

Started a fresh bounded continuation with --attach and no --map,1200seconds,
3000calls, same objective/camera. This extends the experiment allowance under the
ongoing campaign task; it does not restart the map or credit progress. Gameplay
policy unchanged from lab180. Controller memory starts fresh on reconnect, a
remaining continuity limitation separate from the preserved native game world.

### Lab182 — expose missing depot state controls to Jev

Continuation remains live; loop22777 had55Marines/44SCVs and no decision errors.
Investigating the dense base revealed a capability gap: the adapter offered no
supply-depot lower/raise actions. Added both ordinary player controls, only when
returned by the current legal ability query and catalogued as no-target. Jev
chooses the state and executor through the existing support/order machinery.
No automatic lowering, path choice, or mission-specific placement rule.

Source: Blizzard s2client-api/include/sc2api/sc2_typeenums.h documents
MORPH_SUPPLYDEPOT_LOWER556 and RAISE558, both Target None:
https://github.com/Blizzard/s2client-api/blob/master/include/sc2api/sc2_typeenums.h
Descriptions explain the movement consequence.96 tests pass, including absent
engine offers and incorrect target signatures. Building lift/land remain missing;
this does not claim a complete action space or prove depots caused the congestion.
A parallel read-only API connection was rejected during live control; did not
interrupt or restart the working controller because of that diagnostic failure.

### Lab183 — verified Outlaws victory; advance to Zero Hour

Native results screen explicitly showed VICTORY / THE OUTLAWS /27:57.31 enemy
units killed,149 units trained,53 units lost,17 structures built,0 medics trained,
0/9 resource pallets. Ending instrumentation reported victory and automatically
stopped inference before the cinematic. UI independently corroborated it. Final
segment runs/20260919T182630.478039Z:772calls,$0.68180889,replay77663bytes.
Three continuous segments total3771calls,$3.019879296 (lab173,180,181); no world
restart between them. Saved ui-outcome.json, updated final result, added verified
run and cleared Outlaws review gate in runs/campaign-lab069/progress.json.
Historical API-only attempts remain preserved rather than retroactively verified.

Jev chose depot lowering after that control became available; screenshot showed
the Marine column moving out, then victory followed. Some depot toggling persisted.
This supports investigating action-space completeness, but is not a controlled
proof that one change caused victory. All gameplay orders came from Jev-driven
code. No manual routing or mission-specific build order was supplied.

Attempting to leave the victory screen for Zero Hour caused SC2 process903 to
exit, as previously observed after Liberation Day. Verified absence and failed
controller exit before relaunching through Battle.net. Started Zero Hour with
maps/traynor03-outcomes-lab170.SC2Map,1500seconds/4000calls, unchanged policy.
This is the next uncompleted mission, not a restart of the campaign. No full
campaign is complete; all three main campaigns remain the goal.

### Lab184 — Zero Hour baseline reveals economic allocation failure

Fresh adapted Zero Hour attempt runs/20260919T183229.944090Z remains live under
unchanged lab182 player policy. Loop1740:16Marines,6SCVs,4Bunkers,4Turrets,
2Barracks,3Depots,1CommandCenter,1EngineeringBay;176calls,$0.112923174,no errors.
Jev chose protect in all15 strategic decisions at that snapshot. Concrete actions
were dominated by movement/stop, with no harvesting order yet.

At about loop2929, observed mineral and gas income were both zero; all7 SCVs had
repair orders. Jev received this income and current-order evidence. This is not
an absent-income-telemetry explanation; group allocation and preferences remain
suspects. Do not treat all disappearance as death or replace decisions with manual
harvesting. At loop4134:13Marines,1SCV,1Bunker,2Turrets,2Barracks,3loweredDepots,
1CommandCenter,1EngineeringBay;442calls,no decision errors,no ending marker.
No tactical patch during this observation interval. The fresh defensive trial is
not yet a completed mission or a verified defeat.

### Lab185 — let Jev choose independent worker roles

Reviewed labs083 and121 before changing worker control: support executors already
allow one or all eligible units; explicit idle-continuation wording previously
left top choices unchanged. Current repair-heavy defensive run is not explained
by absent income telemetry. A remaining representational constraint is that a
same-job worker cohort receives one contribution choice, encouraging all-or-none
role changes even though specific support executors are selectable afterward.

Added optional coordination choice individual_workers. Jev itself must select it.
Observed harvesting/building capabilities identify workers; each then receives an
independent contribution and concrete-order decision. Other units stay grouped by
type. No fixed miner/repairer counts, priority override or type-name whitelist.
Existing grouping modes remain. This exposes a finer decision space, at additional
inference cost; it neither guarantees Jev will use it nor fixes prior losses.
97 tests pass, including two workers with identical repair jobs getting distinct
selections while soldiers remain grouped. This is a general control experiment,
not a direction to harvest in this particular mission.

### Lab186 — verified defensive defeat; optional worker granularity unused

Zero Hour run20260919T183229.944090Z ended via genuine defeat instrumentation,
corroborated by native DEFEAT dialog at9:27: all structures destroyed, evacuation
still10:42 away.1022calls,$0.615295170,replay saved. Added UI evidence, marked
result defeat and appended checkpoint attempt. Opening victories remain intact;
retry Zero Hour only. No inference/controller exception caused this ending.

New scripts/probe_worker_grouping.py replayed first/middle/last recorded strategy
states with at least4 harvesting-capable workers, alternating original versus
added individual_workers option. Same state and other choices.6calls,$0.002333226.
All3 pairs chose by_type in both variants. Artifact186-worker-grouping.json.
This small negative probe does not establish model incapacity; it shows merely
adding the option did not change these choices. Live grouping also did not select
it before the force collapsed. Earlier repair allocation with zero income remains
a measured failure. Avoid re-running wording-only fixes or claiming the added
option solved staffing. Next experiment should evaluate finer decision granularity
as an interface design, retaining Jev decisions for every worker's actual task.

### Lab187 — test independent economic actors as the default interface

After lab186's negative grouping probe, changed control granularity for observed
harvesting/building actors: each always gets its own contribution and order
question. Jev still chooses every task, recipient, movement and purchase. No
minimum miner count, resource threshold, repair cap or mission-specific rule.
Non-economic grouping remains Jev-selected. Removed the redundant optional menu
entry and made the coordination instructions explicit about the new interface.
97 tests pass; same-job workers separate under type and current-order grouping,
while ordinary units can still share selections.

Hypothesis: independent choices can express simultaneous income and repair more
easily than the previous cohort-wide contribution. This may instead amplify
correlated wrong choices or increase latency/cost; live measurement is required.
Restart only the verified failed Zero Hour mission and compare income, role
allocation, casualties and real outcome against lab184–186. Preserve both opening
victories. No other policy change in this fresh attempt.

Lab187 launch note: native Restart Mission (Normal difficulty unchanged) exited
SC2 rather than restarting. Confirmed process absence, terminated the now-waiting
attach-only controller, relaunched through Battle.net, then loaded the same adapted
Zero Hour map. Log /tmp/jev-zero-hour-lab187b.log; session37919. Joined successfully.
At loop3, independent SCV contribution choices included income, positioning and
individual control. This verifies distinct decisions are reaching the interface;
it does not yet prove successful harvesting or better survival.

### Lab188 — independent worker decisions produce actual income

Live retry runs/20260919T184240.436736Z, session37919, policy unchanged since187.
At loop1130:6SCVs,16Marines,4Bunkers,4Turrets,2Barracks,3loweredDepots,
1Refinery,1EngineeringBay,1CommandCenter;137calls,no errors.5 submitted harvesting
commands; measured income80minerals/112gas per minute. Distinct contributions
therefore reached actual harvesting, not just verbal income intent.

Compare nearby opening times in the two recorded runs. Prior baseline loop1740:
6SCVs/16Marines/4Bunkers,noRefinery,176calls,0harvest commands,income0/0.
Current loop1734:10SCVs/17Marines/5Bunkers/1Refinery,205calls,6harvest commands,
income140/96. Observed resource balances differ because of spending. These are
single live attempts with stochastic choices, not a controlled efficacy estimate.
At loop3324 current run has13SCVs/18Marines/4Bunkers/2Turrets,406calls,no errors,
income220/48. Some defenses have disappeared; no ending yet. Keep policy fixed
for the defensive outcome rather than infer campaign success from early growth.

### Lab189 — user-directed rolling spending governor and gradual taper

User requested longer experiment runtime through a gentle five-minute rolling
dollar budget, then asked to measure current spend and taper over a few hours.
Paused native Zero Hour at5:13 while implementing; controller exited normally on
stalled clock and saved replay/result (615calls,$0.418819632). Preserve this world.
Measured repository Jev telemetry: last active5min615calls/$0.418820 (~$5.03/hour),
last active minute159calls/$0.113598 (~$6.82/hour burst), preceding wall-clock hour
5408calls/$4.053994. These are local logged calls, not account-wide charges.

Added shared SQLite admission ledger in runs/jev-spend.sqlite3, used by every
Jev wrapper instance including probes and recursive splits. Transactional
reservations prevent concurrent callers from independently spending the same
allowance. Responses settle actual provider cost; uncertain/failed/cancelled calls
retain conservative reservations. Import recent existing usage once. Ledger and
budget taper persist across reconnects. This is a soft cap because exact billed
cost is returned after dispatch; unexpectedly expensive responses may overshoot
reservations, then block new dispatch. Other apps/direct SDK use are not covered.

Active local runs/jev-budget.json starts at$0.42 per300seconds and linearly tapers
to$0.10 over10800seconds, then holds (~$1.20/hour). Nominal integrated allowance
about$9.36 over the taper; rolling-window burst headroom and post-response billing
mean this is not a hard cumulative cap. Config is reread at each admission and
never reset by controller restarts. Missing config defaults to$0.10/5min.
Harness additionally paces decision cycles by measured cost/current allowance.
Throttling preserves existing game orders, observes endings and controls camera,
without incrementing decision failure count or queuing stale tactical commands.
103 tests pass, including concurrent admission, actual-cost settlement, unknown
charges, rolling expiry, startup seeding, persistent taper and pre-SDK denial.
No gameplay-policy change. Resume the same paused Zero Hour with the governor.

### Lab190 — verify governed continuation and report cost alongside gameplay

Same Zero Hour world continues in runs/20260919T185136.024869Z, session28727.
No extra paid probes. Report snapshot at loop6708:133calls,$0.108992058,median
cost-paced decision interval4.30seconds,current allowance$0.413685/300seconds,
no admission throttles yet. Added run-local rolling300-second actual-spend peak,
throttle count,current allowance and median pacing interval to scripts/report.py.
Scope explicitly excludes other runs and unresolved reservations; the SQLite
ledger remains authoritative for shared admission. Generated and inspected the
report on the live log; the short-run peak equals measured total cost as expected.

At loop7695:17SCVs,16Marines,3Bunkers,2Turrets,2Barracks,3Depots,1Refinery,
1EngineeringBay,1CommandCenter. One decision TimeoutError recovered; no ending
marker and no spend-throttle event. Prior baseline around loop7517 had1SCV and
4Marines, but this is not controlled causal evidence (worker granularity changed,
then a pause/reconnect and spending governor were introduced). Continue within
the taper without increasing budget or adding tactical rules.

### Lab191 — governed play passes the former objective cutoff

Kept player and budget settings unchanged; no paid probes. Native screen showed
Zero Hour10:28 with9:41 until evacuation, beyond the previous fresh trial's9:27
defeat. Continued controller session28727 passed loop13020, where earlier
unadapted missions had ended API control around12500. No campaign-ending marker
or false API stop occurred. Remaining force at13020:9SCVs,5Marines,4Bunkers,
2Turrets,3Depots,1Refinery,1CommandCenter,1EngineeringBay,1Barracks. Defense is
shrinking; this does not establish survival to evacuation.

Live dollar admission activated: at recorded time1789844253.13463, rolling
charges/reservations$0.40370833 against$0.405255676 allowance, requested6.529s
wait. Existing orders continued and the harness did not treat budget admission
as a decision error or restart the game. This corroborates runtime throttling,
in addition to the unit tests. Exact billed cost and reservations remain distinct.
One earlier decision timeout recovered. Taper and target remain unchanged.


### Lab192 — budget denial is a failure, not a hidden wait

User correctly challenged silent deterioration under automatic budget deferral.
Admission rejection now emits budget_error to stderr and JSONL, records the
controller error in result.json, saves the replay, and exits status 2 without
retrying. Partial decision commands are discarded. SC2 remains running; this
is not a pause. The rolling ledger, taper start and target are unchanged.
Planned cost pacing remains explicit, now including requested interval and
planned idle time; reports show maximum interval and budget failure count.
This exposes reduced responsiveness but does not itself reduce requests per
meaningful decision. Do not mistake a lower bill from less frequent decisions
for improved efficiency. Next changes should reduce redundant deliberation and
use routine execution utilities while keeping hard choices with Jev, as the
user's revised objective explicitly permits.

The previous controller ended with a native instrumentation defeat marker at
loop15692, 760 calls/$0.588134316 in the resumed segment. No independent UI
verification yet, so campaign credit/result classification is unchanged.
Validation: 104 tests passed, including CLI nonzero exit/no retry on budget
failure. Generated the report on the completed segment without paid calls.


### Lab193 — continue observed harvesting without repeated target deliberation

Native UI verifies the latest Zero Hour defeat at16:20, evacuation03:49, all
structures destroyed. Two controller segments total1375calls/$1.006953948.
Checkpoint records defeat, retaining the two verified opening victories.
The resumed segment spent$0.450096738 of$0.588134316 (~77%) on concrete/other
questions, versus$0.057183126 on contributions,$0.043172430 investment and
$0.037682022 strategy. This coarse classification is not an attribution to
workers alone; serial executor and other questions share the largest category.

First routine execution utility: after Jev selects income, visibly harvesting
units can keep their current engine orders without a concrete-order question
for at most112loops between reviews. Gather/return transitions count as the
same activity. Any visible enemy, health decline, changed membership, strategic
priority, role, idle state or clock rewind forces review. No worker assignment
or resource target is chosen by code. Initial observation requires review.
This conservative scope may save little during continuous combat; measure
routine_execution events before claiming cost savings. Report adds avoided
question count, not an invented dollar saving. Budget taper unchanged.

Validation:106tests pass, including expiration, harvest-return transitions,
health/threat/role/strategy invalidation, idle workers, membership and rewind.
No paid inference was used for this change. Live campaign benefit unproven.


### Lab194 — first live routine-execution evidence

Restarted only Zero Hour after independently verified defeat. Native Quit left
a black window; normal API RequestQuit completed and process absence was
verified before Battle.net Play. Fresh SC2 PID12194 connected and loaded the
same adapted map; controller session44407, run20260919T190649.332784Z.
Policy8223371, no direct gameplay orders. Taper start/target and ledger unchanged;
initial allowance$0.388771289/300seconds.

Early live report:68calls/$0.037606044,12 routine concrete questions avoided,
zero decision/budget errors. Median cost-paced target1.7598seconds,maximum3.1463,
planned idle3.1286seconds total. These are avoided questions, not necessarily
avoided API calls or measured dollar savings because requests can batch.
Mineral income estimate40/min,gas0 at this sample; early state is not evidence
of victory or improved economy. Continue observation under unchanged policy.


### Lab195 — routine savings resume between threats; expose role sampling

Verified controller session44407 remains live. Atloop3758:310calls/$0.198523500,
54 routine questions avoided, no controller/budget errors or ending marker.
Earlier skipped-question count stayed37 during visible threats, then resumed;
this guard deliberately limits savings in combat. Recent resource sample had
140 estimated minerals/minute,0gas. No direct commands or policy changes.

Worker contribution reviews at one snapshot:72, with32 sampled choices differing
from Jev's top choice. Across all selections at a later report snapshot:180reviews,
74 departures. This is a separate hypothesis about exploration versus stable
execution, not proof that top-choice selection would win; investment argmax
previously stalled saving, so do not conflate these different decision layers.
Added contribution_sampling reviews/departures/transition counts to report.py
and generated the report on real events. No paid probes. Keep current trial
policy and original spending taper unchanged while observing its outcome.


### Lab196 — campaign wrapper must not hide controller failure

While the unchanged Zero Hour trial runs, found campaign.py catches controller
exceptions and its CLI exits0 even for needs_attention. Budget-failed attempts
also lost their saved run/cost/replay reference in the sequence checkpoint.
Controller now attaches its completed run result to SpendThrottled after replay
and result persistence. Sequencer retains that attempt and stops without retry
or advancement. Its CLI exits2 for needs_attention. Shared ledger/taper unchanged.
108tests pass, including checkpoint persistence/no retry and CLI nonzero exit.
This harness change applies on next launch; current player policy is unchanged.

Verified live session44407 atloop8608:657calls/$0.454862730 total,
$0.353335962 actual cost in trailing300seconds,84 routine questions avoided.
No budget rejection or mission ending. Earlier total crossed the rolling limit
without rejection because older charges expired, as intended. This does not
imply the total experiment is capped at a single window allowance.


### Lab197 — stable-policy trial continues beyond optional-objective failure

Verified live controller44407 repeatedly; no restart or tactical intervention.
Native screenshot showed13:12 elapsed,06:57 until evacuation, main objective
active and optional rescue failed. The bridge again avoids the historical false
API ending. Laterloop13699:1025calls/$0.711525360 total,$0.342699462 in trailing
300seconds against$0.370026908 allowance,161 routine questions avoided, no
budget/controller termination. Actual useful dollar savings remain unmeasured
against a matched control. Raw force counts shrank and production was lost;
no claim of tactical success while the attempt remains unfinished.

Two logged asynchronous engine rejections were NotSupported on construction
abilities319 and323. These remain visible in telemetry; no blind retry override
or interpretation as victory. Kept policy unchanged to observe the trial outcome.


### Lab198 — verified defeat; test direct role choices with independent workers

Run20260919T190649.332784Z ended normally via native defeat marker atloop14572.
UI independently confirms15:10, evacuation04:59, all structures destroyed.
1087calls/$0.752170524;161 routine questions avoided; peak run-local rolling
actual cost$0.356429220; zero budget failures. Planned idle206.803seconds,
median target interval1.707seconds. Survival is worse than prior16:20, despite
lower total spend; different duration/taper/stochastic trajectory prevent causal
claims. Campaign checkpoint records the defeat and retains two verified wins.

Role reviews692, sampled departures from top293 (~42%). Next trial uses Jev's
returned offered choice directly, retaining the same224loop commitment. No
worker count, target, tactic, purchase, or mission-specific rule is prescribed.
Investment sampling and all other layers remain unchanged. Invalid role choices
raise a visible error. Telemetry labels selection_mode=top_choice while retaining
sampled_choice for report compatibility.

Lab090 cautions that prior grouped-worker top-choice policy neglected income.
This trial tests the different independent-worker regime introduced lab187;
monitor income and contribution diversity explicitly rather than assuming less
sampling is better.108tests pass including top-choice retention and re-review
when unavailable. No paid offline probes or budget reset.


### Lab199 — direct role trial has early income; repair future sequence paths

Verified live session91982,run20260919T192012.180852Z uses top_choice role mode.
Early matched-loop observation:prior sampled trial1390loops,137calls/$0.073345440,
80estimated minerals/minute;current1378loops,132calls/$0.069009906,200/minute.
Direct worker role reviews include income10,continue19,positioning4,other2.
Unlike the old grouped-worker result in lab090, no immediate complete income
neglect. This single uncontrolled comparison does not establish superiority.
Laterloop4009:327calls/$0.202917960,27 routine questions avoided,no ending or
budget failure;11SCVs,18Marines,2Bunkers,2Barracks among owned raw units.

The sequence manifest still referenced original next maps with known API outcome
incompatibility. Updated only Zero Hour and Smash and Grab to their prepared
lab170/lab178 adapters. Completed first-two definitions exactly match checkpoint;
both new local map hashes validate through OutcomeMonitor. No victory credit or
progression gate bypass, and no live mission reset. Updated campaign docs with
local asset and independent outcome verification requirements. Budget unchanged.


### Lab200 — direct role choices lose earlier; restore sampled baseline

Session91982 ended normally. Native UI confirms Zero Hour DEFEAT11:36 with08:33
until evacuation, all structures destroyed. Run20260919T192012.180852Z:
894calls/$0.540132684;39 routine questions avoided; peak trailing300sec actual
cost$0.329625198; zero budget failures. Planned idle148.395sec,median cost-paced
interval1.809sec,max6.521sec. Checkpoint records defeat and preserves two wins.
Published compact result in experiments/200-direct-role-result.json.

Direct role selection did maintain early income with independent workers, unlike
old grouped-worker tests, but survival was worse than sampled-role15:10 and
prior16:20. Not a causal estimate: one trial per variant, changing taper and
stochastic investment paths. No evidence to retain direct roles for survival.
Restore only the previous sampled role selector and its retention test, keeping
independent workers, routine harvesting, budget enforcement, diagnostics and
manifest fixes. Label sampled mode explicitly in telemetry.108tests pass.
No repeat of the same direct-role hypothesis is justified without a new reason.
Campaign completion remains unachieved. Next experiment should address another
measured failure mechanism rather than add mission-specific tactical orders.


### Lab201 — remove abstract role filtering for mobile combat selections

Measured Marine command requests in completed runs: sampled-role trial934Move,
243Hold,93Attack,17Stop;direct-role trial1387Move,251Hold,zeroAttack. These are
requested orders, not shots fired or proof movement caused defeat. Still, the
abstract positioning role excludes attacks before concrete Jev choice and is a
plausible decision-interface failure distinct from sampling temperature.

New general experiment: selections whose members all expose movement+attack
controls and lack observed economic/building capabilities bypass contribution
classification. Jev sees all their currently offered concrete orders, including
continue/individual, movement and attack alternatives. No automatic attack,
target, location or unit-type whitelist. Workers retain sampled contributions;
investment and all budget settings unchanged. Log direct_order_menu per choice.
This removes a role-question layer but can enlarge concrete menus; tournaments,
age validation and loud budget failure still apply. No guaranteed cost saving.
109tests pass, including a fictional combat unit that exposes both movement and
attack to the same Jev question and executes only Jev's selected command.


### Lab202 — distinguish issued attacks from actual fighting

Live lab201 trial session44504,run20260919T193228.381406Z initially still favors
regroup/hold despite direct access to attack options. At one sample36 Marine
menus contained attack choices; two recent menus offered19 attack options out
of43 yet selected join. This weakens role filtering as a sufficient explanation,
not proof it is irrelevant. Atloop2953:218calls/$0.145299420,120estimated mineral
income/minute,no terminal or budget failure. Policy remains unchanged.

Added telemetry-only player score summaries from the installed API protobuf:
damage dealt/taken/healed, lost minerals/gas, killed value and economy totals.
Capture present fields only; absent fields are not zeros. Log separately from
model context so this observation change does not alter policy decisions.
Report exposes latest score sample. Aggregate scores do not identify per-unit
shots, causes of loss or hidden locations.110tests pass, including explicit-zero
versus absent-field behavior. Hot reload enables measurement in this trial.


### Lab203 — loud budget failure exposes oversized batches and no headroom

Lab201 controller stopped with exit2 atloop6663:454calls/$0.319807110. Ledger
charges/reservations$0.329807110 versus$0.333832374 allowance; next reservation
denied,partial decision$0.000510174 discarded,no automatic retry. Saved replay.
Paused same native mission at7:15,evacuation12:54 for repair; no defeat or restart.
Last measured score interval4582–6437:damage dealt+791.41,taken+913.42.

Concrete requests duplicated large lists of visible entities and type facts across
split calls. Extend columnar encoding to visible/stale entities and homogeneous
type maps, retaining every value and type identity. Heterogeneous records remain
unaltered, preserving missing versus null. One reconstructed actual ten-question
batch shrinks91419→78897chars,state44949→32427,under the80000split heuristic.
No paid probe.112tests pass including roundtrip,idempotence,spatial precision and
existing selection/action behavior. Context representation can affect model
choices; lower billed cost is not yet established by this offline size result.

Cost pacing had targeted100% allowance, leaving no room for in-flight reservation
bursts. Target80% now,explicit pacing_budget_fraction telemetry; this is slower
planned decision frequency, not hidden deferral. Admission still fails loudly.
Original dollar cap,taper clock and target unchanged. Resume same mission with
remaining3546call allowance; do not erase prior spend or restart the scenario.


### Lab204 — verified10:51 defeat; complete friendly-anchor movement choices

Same lab201 mission ended in native defeat at10:51,evacuation09:18. Controller
95717 exited normally; independent UI agrees with ending marker. Two segments
643calls/$0.444082884 combined. Resumed segment189calls/$0.124275774 with no
further budget denial. Checkpoint records defeat. The pause, memory reset,
encoding and pacing changes prevent a clean isolated policy comparison.
Exposing all combat controls did not rescue this attempt; neither lower spend
nor successful API control is campaign success.

Found concrete action-space asymmetry: friendly anchor destinations offered only
ordinary Move, while map sectors/directional destinations offered Move and
Attack-move. Jev frequently chose those anchor options. Add attack-move variants
for every engine-legal friendly-anchor point, including the existing hold-anchor
plus followers construction for anchors within the selection. Both variants stay
available; Jev chooses mode and destination. No automatic attack orders or target
priorities. Queries still use fair owned positions and engine offered ability.
113tests pass, including attack-moving followers to an anchor while the anchor
holds and no self-targeted attack is synthesized. Live effect unproven.


### Lab205 — live anchor-option trial; distinguish finalists from executed orders

Fresh Zero Hour session52730,run20260919T194619.721038Z,policy11298a4.
Normal API quit completed and old process absence was checked before Battle.net
relaunch. Same adapted map,4000call/1800sec bounds,persistent taper untouched.
Atloop3650:256calls/$0.140078904,16Marines,8SCVs,4Bunkers,2Barracks among owned
units; no budget failure or terminal marker.

New attack-move-anchor options are visible to Jev and selected in intermediate
menu tournaments. Initial commentary counted four such answers as selections;
corrected after checking final group_choice events:zero final selections through
loop3650. Do not count tournament finalists as executed orders. Final combat
choices mostly continue/hold, with some ordinary regrouping. Earlier cumulative
score sample528.37damage dealt/60taken illustrates automatic fighting while
holding; not evidence that the new attack-move command itself helped.
Menu expansion creates additional tournament calls. Keep policy unchanged and
measure outcome/cost before deciding whether this interface is useful.


### Lab206 — fewer movement commands accompany better early damage balance

Verified live session52730 throughloop7168:474calls/$0.268258326,no ending or
budget error. Raw owned force includes15Marines,10SCVs,3Bunkers,2Turrets and
CommandCenter; production/supply structures have been lost, so do not infer a win.

Matched approximate early loops:prior lab201 at4996 requested592MarineMoves,
161Holds and reported1448.42damage dealt/6688.19taken;current lab205 at4922
requested157Moves,50Holds,16Stops,1464.52dealt/267taken. Zero final new anchor
attack-move selections at that comparison. Possible effect of changed menus on
holding/movement, but context encoding,pacing from start,stochastic investments
and varying trajectories confound causality. This is an observational comparison,
not evidence the unexecuted new command caused better damage exchange.
Keep policy fixed and observe the full attempt. Shared budget remains unchanged.


### Lab207 — verified11:09 defeat; observed construction interruption

Session52730 ended normally with native marker at10716loops. UI confirms Zero
HourDEFEAT11:09,evacuation09:00,all structures destroyed.653calls/$0.383468148,
no budget failure. Record in checkpoint; early better damage balance did not
translate to success. Campaign still has only two verified opening victories.

Concrete next hypothesis from events:worker4379901953 received BuildBunker at
[81.5,25.5] loop4010. At4207 its observed order was still BuildBunker at that
point; structure4338221060 was16.7% complete. A new BuildBunker at[81.5,17.5]
was then requested for that same worker. Similarly BuildSupplyDepot loop7168
at[82,25] was replaced at7368 by another depot at[82,31] while structure4346085389
was15.8% complete and the worker still had its first BuildSupplyDepot order.
These coordinates/tags are diagnostic evidence only, never policy constants.
Harness uses queue_command=False. Independent investment execution can interrupt
its own unfinished construction, despite current orders being shown in producer
criteria. Investigate preserving Jev-selected jobs or making interruption an
explicit separate choice. Do not infer all economic failure comes from this,
and do not keep repeating role-temperature/menu-only experiments unchanged.


### Lab208 — make construction replacement an explicit Jev choice

Address lab207's observed interrupted jobs without prescribing a build order.
Investment executor now detects candidates whose producer currently has an
observed Build order. A sole busy builder no longer auto-executes a new purchase;
Jev must choose its producer/site. Replacement criteria explicitly label the
interruption and show the old order. Alternative keep_construction makes no
purchase and preserves those workers' current jobs for this decision. That
explicit choice outranks parallel role orders for the same workers, avoiding
contradictory execution. Idle sole-producer shortcut remains. Jev may still
choose interruption; no permanent builder lock, forced construction completion,
worker type whitelist, coordinates or mission-specific rule.

Telemetry distinguishes construction_retained from construction_interruption_chosen.
114tests pass, including the single-busy-builder case, parallel conflicting move
suppression when Jev retains work, and explicit replacement when Jev chooses it.
Extra producer query can cost more in sole-busy cases; keep rolling budget intact.
Live efficacy still requires a new trial.


### Lab209 — Jev explicitly retains ongoing construction in live play

New trialsession35733,run20260919T195823.023203Z,policy593593a. Atloop3727,
249calls/$0.136148166; no budget stop or mission ending. Observed new bunkers
4395106305 and4388814850 reach completion at1159/2297 before the new branch
was exercised; do not attribute those completions to the interruption fix.

Then Jev selected construction_retained at3918 forworker4400349186 and4340
forworker4372824065. Matching tick command lists contained zero commands for
those retained workers, confirming the explicit choice survives parallel order
assembly. No construction_interruption_chosen event in this inspected sample.
This demonstrates execution behavior, not proof of eventual completion or win.
Two visible engine errors earlier:NotSupported ability340 andCouldntReachTarget
ability324 forworker4372561921. They remain logged rather than counted as success.
Keep policy and budget unchanged while the trial proceeds.


### Lab210 — retained construction reaches completion

Followed lab209 retained jobs using producer_site criteria and raw structure
progress. At3918worker4400349186 retained BuildRefinery; observed refinery
4399562760 at[75.5,14.5] was49.6%complete and reached1.0 at4340. At4340worker
4372824065 retained BuildMissileTurret at[84,33];structure4398776336 was20%complete
and reached1.0 at4710. Producer choice text provides the current order; do not
use an older unrelated concrete-state snapshot to infer an idle builder.
No simultaneous replacement orders were submitted at either retention tick.
This supports the execution path, not a counterfactual claim about winning.

Verified live session35733 at6922:428calls/$0.249360762 total,$0.225807792 in
trailing300seconds,no budget or ending event.13SCVs,11Marines,3Bunkers,2Barracks,
4Turrets,3Depots,1Refinery,1CommandCenter,1EngineeringBay in raw owned sample.
Policy and budget unchanged; continue to actual outcome before another change.


### Lab211 — verified16:37 defeat; no-purchase identifier probe is negative

Construction trialsession35733 ended normally at15964loops. Independent native
UI confirmsDEFEAT16:37,evacuation03:32,all structures destroyed.827calls/
$0.529390890. Checkpoint records defeat, retaining two verified wins. Longer
survival than recent trials and successful retained-job completions are useful
observations, but one trial does not isolate construction handling as the cause.
Army replacement remained poor despite available Marine purchase and accumulated
resources. No mission-specific instructions or manual unit control were applied.

Tested a narrowly isolated identifier hypothesis using first/middle/last recorded
investment top-save states with>=500minerals. Identical state,descriptions and
option order; only save→option_0,alternating pair request order. All3pairs still
choose no purchase. Its probability.42→.43,.59→.61,.81→.79. Six shared-governor
calls,$0.002281272,zero game commands. Script probe_investment_identifier.py and
result experiments/211-investment-identifier.json make the method reviewable.
Single draws,not statistical proof; no support for an identifier-only fix.
Do not apply a live rename or repeat this same hypothesis without new evidence.
Next investigate substantive decision/task structure rather than cosmetic keys.


### Lab212 — Jev can authorize a bounded production job

Identifier-only experiment was negative. Test a substantive task representation:
every currently executable Train project offers its existing single purchase and
an optional batch of up to3requests over672loops. Jev chooses type/commitment via
the existing investment distribution; no unit-type whitelist or hardcoded army
composition. Normal producer selection remains Jev-controlled. Executor reuses
the chosen investment while its controls are offered, waits without investment
calls if only potential controls remain, and releases on deadline,clock rewind,
changed strategic priority,unavailable project or three proposed requests.
No other new purchase overrides this bounded commitment while active.

Requests,not successful units,consume the three-attempt allowance:stale/rejected
proposals still count, preventing automatic unlimited retries. Normal fresh-state
validation/resource checks remain in force. Active commitment is visible in
subsequent policy context. Log chosen/request/wait events and report batch counts.
A batch avoids repeated investment deliberation but producer queries may remain;
no guaranteed savings or claim that three units were built. Construction retention
and persistent dollar taper unchanged.117tests pass, including cap,legal-control
wait,strategy cancellation,deadline and rewind. Live usefulness unproven.


### Lab213 — bounded production jobs execute; Jev initially favors workers

Verified live session14186,run20260919T201622.753722Z. First production batch
selected SCV at633,then requests at633/820/985 consumed remaining2/1/0.
Matching ticks submitted actions with all Success results,ages82/86/74loops
within128limit. The second and third investments were carried_jev_commitment,
not newly queried investments. Engine acceptance is not proof all units finished.
This confirms a bounded job can reduce repeated investment questions while
retaining Jev's initial allocation and normal action validation.

Through2931:180calls/$0.100523346; batches selected SCV at633,2129,2931,none
Marine yet.9SCVs,12Marines,2CommandCenters,2Barracks,2Bunkers among owned units.
No budget/mission terminal event. Job execution alone does not solve composition;
do not claim army replacement success merely because batches run. Keep policy
and persistent spending taper fixed while observing the attempt.

### Lab214 — visual checks reveal what command acceptance misses

User requested periodic direct visual inspection. Inspected the native SC2 window
with computer-use screenshots during live session14186 (run20260919T201622.753722Z).
At native8:37,1404minerals/712gas/24of46supply, Zerg and muzzle flashes were visible
inside the base beside Command Centers and bunker construction. Nearby tick8231
issued ordinary Move16 commands to nine Marines toward79.5,25.5,all accepted.
This suggests potentially disruptive repositioning during contact; acceptance
alone does not establish useful combat, and a still screenshot cannot prove the
moves prevented firing. No tactical intervention or policy change made.

Second screenshot at9:08 showed the local fight subsided, Marines clustered near
the bunker,1441minerals/752gas/26of46supply. Through8885:458calls/$0.284740512,
15SCVs/9Marines in the raw owned sample, no terminal/budget error. A Marine batch
was selected at3710, so the earlier worker-only selection pattern did not persist;
SCV batches returned at7987/8885. Large resource bank remains unresolved.
Continue periodic native visual checks alongside logs, particularly during combat
and after behavior changes; distinguish observations from causal conclusions.

### Lab215 — resource allocation sharpening magnifies saving

Same live trial, session14186 confirmed running. At11752 raw owned sample had
20SCVs and no Marines (passengers are not counted as losses);570calls/$0.364805364.
Native screenshot12:41 showed combat among base structures,2490minerals/984gas,
21of46supply,7:29 evacuation remaining. Production remains inadequate despite
legal Marine purchases/batches and idle Barracks in investment context.

Offline examination of six recent investment distributions: raw save probability
.45/.42/.53/.55/.49/.39 becomes .817/.767/.902/.900/.839/.712 under our squared
sampling rule. One no-purchase alternative competes against many distinct
purchases; sharpening amplifies this partition effect. This is a framework
contribution to inactivity, not evidence Jev alone insisted on 90% inactivity.
No paid probe or mid-trial policy change. Next allocation experiment should
remove or factor this sharpening while preserving Jev's purchase/type decisions;
compare against this completed trial, not just accepted command counts.

### Lab216 — 16:58 defeat; preserve Jev's purchase-versus-wait mass

Native defeat verified at16:58,evacuation3:11,all structures destroyed.
Run20260919T201622.753722Z:731calls/$0.488083722,replay saved,checkpoint attempt
appended; only first two missions remain credited. Bounded training jobs did not
solve army replacement. Twenty-one seconds later than the prior16:37 defeat is
not enough evidence of improvement; randomness and other decisions vary.

Next general experiment factors investment sampling into purchase (project/batch)
and wait (save/save_for) families. Preserve each family's total legal positive
Jev probability; square and renormalize preferences only within that family.
This avoids amplifying a single save option against many purchase alternatives,
while retaining the prior attempt to reduce low-ranked extra-capacity purchases.
No unit-specific preference,forced purchase,mission override or extra model call.
Log sampling_scope alongside actual distribution. Numerical scaling prevents
extreme finite values overflowing; tests cover family mass,conditional odds,
legal-option filtering,executed non-top choice and extreme ranges.118tests pass.
This is still a sampling heuristic, not a calibrated utility interpretation.
Persistent spending taper unchanged. Activate after baseline trial ended.

### Lab217 — factored allocation executes a Marine batch; outcome pending

Live session37394,run20260919T202955.161373Z,policyf3a8f7e. New sampler's
sampling_scope confirmed within_purchase_or_wait. At matched early loops3574
versus baseline3522, current raw sample14Marines/12SCVs/5Bunkers/1CommandCenter
versus13/11/2/2; costs$.106936830 versus$.113555778. These single snapshots are
not causal evidence; cargo, trigger changes and stochastic decisions matter.

Jev selected Marine batch4953, then carried requests5185/5405; all matching ticks
accepted actions,ages69/72/63 within128. Native5:54 screenshot showed supply27/27,
550minerals and combat near remaining Barracks. Through6513 raw sample15Marines,
11SCVs,oneBarracks,315calls/$0.189702114. This is more encouraging than accepted
requests alone, but appearances do not establish a production count. No budget
or terminal event. Keep trial unchanged and verify eventual native outcome.

### Lab218 — passenger orders can conflict with Jev boarding decisions

Current run20260919T202955.161373Z/session37394 remains live. Through9142,
428calls/$0.260495676. Native9:52 screenshot showed combat inside base and
923minerals/20of35supply. Examined executed command proposals, not just menu
choices: five LoadBunker407 requests. At4092 the same passenger also received
Attack23 point79.5,21.5; at4376/8232/8825 it received Hold18; at9142 no simultaneous
passenger command. All reported no action_errors. These parallel selection
outputs may interfere with boarding; engine acceptance does not prove entry.
Bunker group choices also include frequent explicit unloads, so empty bunkers
cannot be attributed solely to this conflict. Next general coordination test:
resolve Jev-selected multi-unit job participant conflicts instead of independently
issuing incompatible orders to both sides. Keep this allocation trial unchanged
until its outcome is verified. No hardcoded garrison tactic or unit preference.

### Lab219 — loud budget stop exposes unpaced failed-request reservations

Allocation trial20260919T202955.161373Z stopped with exit2 at10447:
473calls/$0.289111662,ledger$.222174832 against$.226497977 allowance; next
reservation refused. Partial decision$.001157394 discarded,no automatic retry.
Paused native game11:25,evacuation8:45. Not a mission outcome. Replay saved.

Inspection found pacing counted billed cost only while unknown/failed requests
retain reservations, and decision_error paths skipped pacing entirely. Add local
RollingSpend.charged accounting: admissions debit reserved estimate,known bills
reconcile once,unknown bills retain debit. Pace successful and failed decisions
using max(reported billing,accounted debit),still80% of current allowance. Log
accounted_usd and after_decision_error separately from actual bills. No cap,
ledger or taper reset; guard remains fatal.119tests pass, including reservation
retention and reconciliation without double accounting. Resume same world with
remaining3527calls. This interrupts controlled comparison; do not hide it.

### Lab220 — factored allocation ends in 16:27 defeat

Native defeat verified16:27,evacuation3:42,all structures destroyed. Segments
20260919T202955.161373Z(473calls/$.289111662) and
20260919T204018.344050Z(167calls/$.122339406),total640calls/$.411451068.
Recorded UI evidence and checkpoint attempt; no campaign advance. Last visual
checks showed worker-heavy defense collapsing despite resources being spent;
15:46 screenshot had0minerals,unlike prior large unspent endgame reserves.
Neither spending nor accepted training requests alone establishes effective force
allocation. Survival is31seconds shorter than prior16:58; one stochastic attempt
with a budget pause,policy-memory reset and pacing repair is not a causal ranking.
No further budget error in resumed segment. Next experiment addresses observed
boarding/passenger command conflicts. Preserve Jev's tactical choices; resolve
only contradictory execution requests and verify cargo entry in live evidence.

### Lab221 — coordinate Jev-selected boarding participants for one cycle

Use existing candidate exclusive_target metadata,not ability IDs or unit names,
to recognize selected multi-unit boarding jobs. After existing purchase/retained
construction priority, a selected job suppresses separate passenger commands in
that control cycle. No job is created automatically,no persistent boarding lock,
no unload restriction. Candidate description tells Jev this execution contract.
Jobs conflicting with protected work or sharing participants with another joint
job are rejected and logged instead of arbitrarily choosing a carrier. Other
orders remain unchanged. Log accepted/rejected jobs and discarded commands.
This is an execution-priority experiment; suppressing an escape order can matter,
and one-cycle coordination may not suffice for travel to the carrier. Jev must
still decide the tactic and can revise it next cycle.121tests pass, including
fictional ability,protected work,competing carriers and unchanged unrelated orders.
Test in fresh mission with factored investment and repaired spend pacing retained.

### Lab222 — actual passenger entry observed; conflict suppression not yet exercised

Run20260919T204546.942041Z/session98718 confirmed live. Boarding selections at
1961/2547/2922 targeted bunker4295491585. Subsequent Jev state observations
showed Marine4341104641 inside,then both4341104641 and4302569473 (cargo1 then2).
This verifies entry rather than just accepted requests. All three coordination
events had discarded_commands empty, so this does not yet demonstrate benefit
from conflict suppression. Third requested passenger4356308993 not yet verified
aboard.141calls/$0.081970854,no budget/terminal event. Native2:24 visual check
showed Zerg at the ramp and bunker nearby; no tactical intervention.

### Lab223 — suppressed conflicting hold followed by verified boarding

Same live run/session98718. At4570, Jev selected bunker4297850881 to load
Marine4342153217 while the Marine selection chose Hold18. Coordinator retained
Load407 and discarded that hold. Later model-state observations showed that exact
Marine inside that exact bunker,cargo1/4,health45. This exercises the conflict
path and verifies successful entry; not a counterfactual proof the hold would
have prevented it. Earlier loaded bunker4295491585 remained healthy but Jev
explicitly unloaded it at3705,demonstrating that coordination does not force
continued garrisoning. Through4941,$.134337798,no budget/terminal event.

### Lab224 — taper requires more burst headroom despite reservation accounting

Trial20260919T204546.942041Z stopped exit2 at13202,497calls/$.320468484.
Ledger$.191085046 against$.194664018 allowance; next reservation denied,
partialdecision$.001728804 discarded. Paused native13:57,evacuation6:12.
No mission outcome. Correct reservation accounting is not sufficient to guarantee
headroom for concurrent request bursts as allowance shrinks. Reduce planned
throughput from80% to60% of allowance on both successful/failed decisions; retain
charged accounting and fatal admission. Deliberate slower decisions,explicitly
logged; no silent retry,cap increase,ledger/taper reset.121tests pass. Resume
same world with remaining3503call allowance. This second interruption limits
survival comparisons; do not present this as an uninterrupted trial.

Lab224 follow-up: first resume20260919T205704.758812Z failed on retained rolling
history after3calls/$.001593480,exit2. Lower future pacing does not clear existing
charges; resuming immediately was premature. Paused again native14:35,
evacuation5:34. At inspection ledger$.174325312/currentlimit$.191665165;
read-only projection estimated119seconds until history falls below60% allowance.
Next resume must recheck actual ledger headroom first; do not reset it or assume
elapsed time alone guarantees admission. Remainingcall allowance3500.

### Lab225 — boarding trial reaches18:40 but still loses with3520minerals

Native defeat verified18:40,evacuation1:29,all structures destroyed. Three segments
20260919T204546.942041Z,20260919T205704.758812Z,20260919T210023.211320Z:
586calls/$0.383097708,total. UI evidence and checkpoint attempt saved; first two
missions remain the only credited wins. Last segment86calls/$.061035744,no
further budget error. This reached farther than recent trials,but interruptions,
policy-memory resets,pacing changes and stochastic choices prevent attribution
to boarding coordination. Actual boarding and conflict suppression are verified
mechanically; campaign success is not.

Persistent underspending deserves decision-interface investigation beyond more
execution patches. Current strategic choice frames protect as preserving owned
units/structures and strengthen as increasing force through production,though
these can be simultaneous means to survival. Hypothesis: mutually exclusive
labels bias downstream allocation. Test framing with recorded states before
another full run; do not issue a live tactical directive or assume causality.

### Lab226 — strategic-context ablation has mixed, modest effects

Six-call paired probe on first/middle/last eligible recorded investment decisions
from20260919T204546.942041Z (>=500minerals,recorded top save). Same question,
criteria/order,state except removal of strategy_chosen_by_jev; alternating request
order. Results in docs/experiments/226-investment-strategy.json and reproducible
scripts/probe_investment_strategy.py. Shared persistent governor applies.
Cost$.002468676. Save probabilities original→removed:.42→.35,.45→.35,.25→.27.
Save remains top choice in all six responses; removing protect does not clearly
redirect investment to the army. Three single pairs on selected states do not
establish significance or live benefit. Do not remove strategic context based on
this result. No gameplay commands or policy changes. Next investigate whether
joint purchase-versus-wait and project ranking in one large menu is the harder
representation problem; any new decomposition must still leave both decisions
to Jev and report added call cost.

### Lab227 — project-ranking then binary authorization reinforces waiting

Nine-call paired recorded-state probe on same three states aslab226. Conditional
ranking among executable project/batch options,then explicit binary purchase/wait
for Jev's top-ranked project. Ranking does not authorize spending; same observed
state and strategic context. Alternate original/staged order. No game commands.
Cost$.003476928,shared governor. Original save probabilities.48/.37/.30;
staged wait.87/.98/.88,all top wait. Proposed projects were Bunker,CommandCenter,
Bunker respectively. This tests top-project authorization,not every possible
investment or calibrated equivalence between multiclass and binary probabilities.
Three single pairs do not establish statistical significance. Nevertheless this
version adds a call without evidence it remedies underspending; do not deploy.
Script scripts/probe_investment_stages.py; full outputs in
 docs/experiments/227-investment-stages.json. Keep current live policy unchanged.

### Lab228 — compact investment context increases saving; retain current policy

Six-call paired lossy context ablation on same three recorded states. Retain
questions,objective,resources,force counts/health/orders/cargo,observed capabilities,
outcome history and strategy; omit catalog,raw action feedback,spatial dispersion
and duplicate project/support lists. State chars20704/20605/21013 become
9790/9865/9839. Save probabilities.42→.53,.41→.52,.26→.32;all top save.
Cost$.001962198. This is not equivalent-information compression and three pairs
cannot establish significance. No evidence for deploying it. Script and outputs
saved as probe_investment_compact.py and228-investment-compact.json.
Next full run retains current policy with60% pacing from startup to obtain an
uninterrupted comparison; prior18:40 attempt had two budget stops and memory
resets. No further paid framing probes until new live evidence changes the question.

### Lab229 — uninterrupted60% pacing survives budget but loses13:04

Run20260919T210819.747053Z/session39575 ended normally. Native defeat verified
13:04,evacuation7:05,all structures destroyed,801minerals remaining.305calls/
$.181441512,replay saved,UI evidence and checkpoint attempt recorded. No campaign
advance. No budget stop this run. Lower rate is operationally cheaper,but survival
worse than prior18:40 interrupted trial. Different random choices,pacing,memory
continuity prevent a one-variable attribution. Policy still failed to replace the
army and use defenses effectively. Repeating unchanged is not justified now.
Next inspect call distribution and routine execution expiry against actual
inter-decision time,then target general decision efficiency/combat behavior.
Do not compensate by increasing the dollar cap or injecting mission tactics.

### Lab230 — harvesting review expires before paced decisions can reuse it

Offline accounting of lab229:305calls/$.181441512. Strategy/grouping37calls/
$.014590422,investment32/$.011664786,roles36/$.017813838,orders/assignment200/
$.137372466(about76%).38ticks,median373loop interval,zero routine_execution
skips. Income continuation deadline112loops could never cover the median next
review. Nine of37 strategic snapshots had no currently visible enemy,so the
conservative global-threat veto also limits applicability. No paid probe needed.

Extend only existing harvest-cycle review window112→672loops. Preserve first
review,chosen income role,unchanged strategy/membership,no health loss,no visible
enemy,active engine harvesting,rewind and fixed-deadline expiry guards. Never
assign idle workers or select a resource automatically. Routine skips cannot
extend the deadline. This may save a small number of questions,not all worker
calls; batching means question savings are not equal to dollar savings.121tests
pass,including reuse at measured373loop spacing and expiry at672. Live impact
still requires measurement; no new tactical policy or budget change.

### Lab231 — harvesting reuse observed; visual checks distinguish empty defenses

Live lab230 run20260919T212055.773706Z/session42746 remains active. Five
routine_execution events through loop5109 (1278,2502,2902,4620,5109) confirm
672-loop harvesting review can survive paced decision intervals. These avoid
concrete questions, not necessarily entire calls; no dollar-saving causal claim.
Read-only five-minute ledger snapshot was $.073500210 against $.142569458
allowance, including reservations. No cap, taper or policy change this check.

Native screenshots at4:41 and5:27 show Marines clustered beside the bridge and
an explicitly EMPTY BUNKER nearby. API support context at5109 reports one Marine
aboard across four bunkers (15 free slots). Earlier1679 load choice reserved its
passenger and suppressed that Marine's conflicting Hold order. Thus boarding
coordination is exercised, but an occupied bunker elsewhere does not establish
effective use of the visibly empty forward defense. Recent Marine choices were
repeated continue after holding, then a bunker-position join at5639. No manual
orders issued. Continue the unchanged trial and correlate later survival with
actual production and cargo, rather than interpreting accepted commands as success.

### Lab232 — remove redundant attack-move distance variants from group menus

Lab230 native8:46 shows command center under attack,1227minerals,25/11supply.
Recorded Marine context includes enemies throughout the base; repeated chosen
forward-bunker joins were submitted, not lost at the command boundary. Tournament
finalists repeatedly join/stop; this alone cannot prove tournament bias.

Found a concrete presentation bug while tracing these menus: shared-description
normalization removed comma-prefixed distance but not semicolon-prefixed distance
used by attack-move anchors. One option repeated four otherwise identical long
sentences plus a variation disclaimer, then also included the exact group distance
range (example597characters). Accept both separators in the existing normalization.
Keep all candidates, targeting, attack-move semantics and computed distance range.
No tactical choice or budget change.122tests pass; regression verifies one shared
description, range6–10, and unchanged exact per-unit commands. This changes menu
length and potentially tournament partitions, so the current trial becomes mixed
revision after commit; do not present its outcome as harvest-window-only evidence.
Savings and behavioral effect require live measurement.

### Lab233 — live menu compaction reduces tournament depth, defense still fails

Reload1b274e9 confirmed at1789853309.095170. Before: Marine decisions8258/9415
used5model calls each (whole decision13/11calls,$.00838921/$.00701807). After:
9993/10407 used3Marine calls each (whole decision8/7calls,$.004986702/$.00492227).
Different world states and candidate sets confound dollar attribution, but actual
live tournament depth fell. No assertion of controlled savings or better tactics.
Native10:46 still showed command center surrounded,658minerals,evac9:23. Jev's
choices included hold then another forward-bunker join. Context contains visible
base enemies, raw own unit facts and measured outcomes. At10819 outcomes record
CommandCenter disappearance and Marine mean sampled travel/net displacement0.6
over826loops despite repeated accepted joins. This raises a separate execution-
feedback/path-accessibility question: accepted orders do not establish arrival.
Do not assume Jev is simply choosing to stand still or inject a mission waypoint.
Next inspect general group-intent progress feedback and reachability support.
Current session42746 still live; no terminal outcome credited.

### Lab234 — verified12:23 defeat; position history weakens pathfinding hypothesis

Run20260919T212055.773706Z/session42746 exited normally. Native defeat at12:23,
evac7:46,349minerals,all structures destroyed.264calls/$.150865596. Ending bank
and native UI agree; saved ui-outcome,result and campaign attempt, no advance.
Harvest-window change plus midrun menu compaction make this a mixed trial.

Full position series corrects lab233's tentative movement interpretation. Marines
averaged5.6distance from selected bunker center at5639; after submitted join,
2.6at6249,remaining roughly2.6–2.8through10819. Near-building occupancy/group
spacing can explain residual distance. Low later displacement does not establish
path failure. Do not introduce arbitrary unstuck orders or suppress the target.
The supported failure is persistent choice of the same forward area despite
visible enemies destroying the base. General spatial context around offered
friendly anchors (health and currently visible nearby threats) is a potential
next experiment, giving Jev measured destination facts rather than human tactics.

### Lab235 — expose measured local conditions on friendly movement destinations

Add anchor health and visible enemy type counts within12map units to friendly
move/attack-move candidate descriptions. Same facts for every acting unit, computed
once per anchor. Uses only currently visible enemies; hidden,snapshot,ally and
outside-radius entities excluded. No threat score, route, priority, forced order,
mission identifier or unit-name policy. Empty neighborhood means none observed,
not safe. Keeps exact commands and all choices. Existing distance normalization
can still combine shared text. This adds context/cost; test whether clearer local
relations help choices enough to justify it.123tests pass, including visibility
and radius boundary. Prior trial terminal; next run uses this from startup.
Read-only retained ledger$.044499798/limit$.130777725 is below60%headroom threshold.

### Lab236 — destination-context trial changes opening; economy still collapses

Run20260919T213259.240534Z/session62605 active on69de773. Live requests contain
anchor health/local visible enemies. Marine choices3/438/845/1304 join the command
center; native0:47 confirms relocation. By5:07 Marines visibly fight near the base,
rather than the previous forward-bunker area. This is one trial with stochastic
choices, not causal proof.103calls/$.056853132 at4776; rollinglimit$.122040237.

Load2081 lost both loader/passenger from observations before2548, outcomeunknown.
Later bunker4395106305 contains Marines4301520897 and4303355905, verifying boarding.
At4776 Jev explicitly unloads it. SupplyDepot selected5126 completes by5808,
restoring19capacity; by native6:48 supply13/11 again. Last detailed worker snapshot
6141 has twoSCVs,onegathering andonerepairing; losses and repair allocation constrain
income. Do not mislabel every continue as idle or automatically replace Jev's work.
One engineCantBuildLocationInvalid for depotraise558 was logged; no budget failure.
Current survival unknown; keep policy unchanged to finish this comparison.

### Lab237 — destination context loses10:32; expose individual repair tradeoffs

Lab235 run20260919T213259.240534Z/session62605 terminal. Native10:32 defeat,
evac9:37,4minerals,all structures destroyed.225calls/$.108312540. Ending marker
and native UI corroborate; result,ui-outcome,checkpoint attempt recorded. Still
only two verified campaign wins. Positioning changed, survival did not improve
in this single trial. No budget interruption; lower total cost also reflects
shorter survival and fewer remaining units, not necessarily improved efficiency.

Repair concrete descriptions previously stated only health restoration, while
only multi-executor text mentioned shared resources. Add resource consumption and
foregone worker harvesting to both repair capability and concrete descriptions.
Use 'can consume' without a fabricated exact tariff; API view has no repair price.
Keep Heal separate, all legal targets and commands unchanged. No repair prohibition,
spending threshold or preferred target.123tests pass; existing compatibility test
now checks both repair descriptions and ensures Heal inherits no resource claim.
Next test this from startup under unchanged ledger/taper; current game is terminal.

### Lab238 — early timeout is a comparison confound; improve failure diagnostics

Repair-cost run20260919T214242.370076Z/session72032 started on76ee166. At585,
TimeoutError aborts decision after$.006602274known cost plus$.005unknown reservation.
Pacing accounts$.011602274,explicit46.93second idle. No retry or cap reset. Next
successful tick1765 proves controller resumed; no restart from a wait timeout.
This long early gap confounds comparison with preceding trial; record it rather
than attribute eventual survival solely to repair wording.

SDK failure log previously named only outer decision_error. Add jev_request_failed
with exception type,question names,state/question character counts,latency and
unknown-billing reservation note, then re-raise. No credentials/full payload added,
no retry or error suppression. Compile check passes. Harness-side wrapper change
activates next process, not this live trial; no player behavior change in this commit.

### Lab239 — verified12:33 defeat; give Jev factual memory of prior attempts

Run20260919T214242.370076Z/session72032 ended normally; native12:33 defeat,
evac7:36,203minerals,all structures destroyed.181successfulcalls/$.101484768reported
cost; early timeout had an unknown retained reservation, not included in reported
usage. UI and ending marker agree; checkpoint records defeat, no advance. Income
improved transiently, but replacements arrived late. Marine controls were available
during repeated saving/bunker purchases. Do not attribute survival difference to
repair wording alone given early47second decision gap and stochastic choices.

Add generic episode-history reader: latest3same-map-filename completed attempts
with matching independent UI result,fresh join and firstobservedtick<=128.
Exclude unverified results,other maps,current run,resumed-only terminal segments.
Whitelist own observed peak counts,role/strategy counts,purchase proposal counts,
last observed resources,loop span and decision errors. No enemy locations,hidden
map scripts,manual lessons or chosen strategy. Clearly label associations and
proposal-vs-completion ambiguity; changing policies/timing prevent causal claims.

Load once at controllerstartup and feed only strategy/coordination and investment
queries, not repeated concrete-order or contribution queries. Three real prior
attempts measured2394chars before adding the latest verified result.125tests pass,
covering filtering,boundedrecency,exclusion and no rawstate leakage. Startup/harness
change requires next process; never silently claims a lesson was learned. Next
trial will test whether this factual cross-attempt context changes choices.

### Lab240 — history reaches live decisions; retain saving and peak-resource evidence

History trial20260919T215406.476956Z/session58593 starts on70d42c1. Logs confirm
three attempts in strategy/coordination and investment requests. Openingprotect,
save thenMarine purchase; native1:44 shows18army units. No causal benefit claim.
The current trial keeps its startup-loaded history unchanged.

Audit found summary omitted save-choice frequency and peakminerals, which can hide
long stockpiling behind low terminal balances. Add investmentchoice counts grouped
as purchase/save/save_for_project and peak observed minerals alongside lastresources.
Counts describe logged decisions including carried proposals, not completed spending.
No heuristic recommendation or altered purchasing policy. Focused2episode tests
pass, including123→7mineral history and separate save/purchase counts. Loader change
only applies next controllerprocess. Current live run still tests originalsummary.

### Lab241 — paired history ablation modestly lowers saving, no top-choice change

New scripts/probe_episode_history.py samples first/middle/last recorded investment
states containing prior_attempts from live239run. Remove only previous_attempts,
retain exact question/allotherstate,alternate pairorder. Six calls through shared
persistent governor,$.002322222,no gamecommands. Withhistory saveprobabilities
.43/.43/.31 versus without .52/.48/.32;all six topchoices remain save. Artifact
241-episode-history.json. Small unreplicated probe,not calibrated utilities or
proof of improved survival. It supports at most a modest shift in these states;
early Marine purchases cannot simply be credited to history. Continue current
trial unchanged; do not crank sampling or spending to turn this into a win claim.

### Lab242 — remove redundant singleton executor prefixes from concrete choices

Current239run through7648 has133calls/$.075194658,15Marines,5SCVs,2Barracks,
3Bunkers,3Depots,EngineeringBay,CommandCenter. Native8:41 shows fighting near base,
341minerals. Largest concrete worker requests dominated by menu text, not history.

Offline exact-prefix measurement:1668recorded singleton options total321585chars;
removing 'Every one of the 1 <selection name> units receives: ' leaves226629,
saving94956chars across these options. This is cumulative description size,not
whole-request size or dollar savings. Question key/instructions already identify
that exact sole executor. Omit prefix only for singleton selections; preserve
multi-unit scope,all action text,IDs,targets and command tables.125tests pass.

Commit hot-reloads during current239trial. Record mixed revision,not a controlled
history-only outcome. Model wording and tournament partitions can affect choices
even though offered commands remain identical. Budget/cap/pacing unchanged.

### Lab243 — three-request production commitments expire between paced reviews

Audit of completed237/235runs and current239: batches at1304→1684,2305→2740,
8692→9196 and436→1036 made onlytwo requests before their672loop deadlines;
next decisions fall outside the window. Late terminal/ongoing batches cannot be
classified as expiry failures. Cheap batching is underused at current pacing.

Extend newly offered batch horizon672→2016loops (about90seconds), stillatmost3
proposals. Update Jev-visible description explicitly; no new purchases while
commitment active, stillreleaseson strategychange/unavailablecontrol/rewind/expiry.
Do not extend existing memory commitments retroactively or guarantee accepted
production. Longer commitment can delay a different needed purchase; Jev sees
that tradeoff before choosing. Existing command legality/freshness/budget unchanged.
125tests pass; boundedbatch test now exercises1/601/1201loop decisions, three
requests with one investment choice, then fresh choice. Actual liveeffect unproven.
Current239trial already mixedrevision; native11:31 shows base being overrun.

### Lab244 — visually verified 13:22 defeat; extended batch not yet exercised

Run20260919T215406.476956Z ends with native DEFEAT, all structures destroyed,
13:22 mission time,06:47 evacuation remaining,0 minerals.206 successful calls,
$0.114836988 reported. No decision/error events found. History loaded at startup
on70d42c1; singleton menu compaction c91a0ee loaded during play. This mixed trial
outlasts recent runs but does not establish a causal history benefit. Last tick
had five SCVs; remaining workers do not prevent defeat when all structures fall.

Correction/nuance for lab243: final old-window batch at11376 (deadline12048)
completed all three proposals by11960. The672-loop window can work when reviews
are close enough; its expiry problem is intermittent, not universal. f93a078 did
not load before this ending. Next fresh trial exercises2016-loop batches and the
expanded startup history. Retained rolling spend $.013785156 before restart;
cap/taper/pacing unchanged. Continue periodic native visual checks.

### Lab245 — visual check finds quiet turret counted as army camera subject

Fresh244trial20260919T220825.429214Z/session68563 starts on ebde548 and loads
three expanded historical summaries. Early decisions have no errors; no production
batch chosen yet. Native1:30 screenshot shows mostly empty approach. Camera log
at1352 identifies [60,49] as army overview; that is the observed stationary turret,
not the mobile army. Camera classified any attack capability as army interest.
Require observed movement capability as well for the quiet army score. Firing,
visible contacts and damage still override so a fighting turret remains watchable.
No gameplay order or Jev question changes. Nine camera tests pass, including quiet
stationary attack-capable structure versus actual mobile army. Commit hot-reloads
presentation only; batch and budget experiment remain unchanged.

### Lab246 — joint worker income-count probe does not justify deployment

Live244trial native4:21 shows two mining workers and combat at the main base.
Through3954:75calls/$0.039540690,15Marines,5SCVs,estimated120minerals/minute.
No batch selected yet. Camera-only245 is loaded. Do not infer worker deaths from
raw counts alone or treat visible firing as proof issued attack commands caused it.

New scripts/probe_worker_allocation.py compares independent income-role choices
with a joint0..N income-worker count on first/middle/last eligible239recordedstates.
Singleton scope validated from facts, exact same state for each pair, alternating
order, six calls through retained governor, no game orders. Cost$0.001992564.
Independent income probability sums2.26/1.83/.02 across5workers; joint top counts
0/1/0. Artifact246-worker-allocation.json retains full responses. This offers no
clear reason to deploy the extra allocation stage. Count choices do not select
identities or targets; other-role continue can preserve harvesting, so counts are
not actual miner totals. Three unreplicated pairs and probabilities are not a
calibrated causal outcome comparison. Keep live policy unchanged and let current
production-commitment trial continue. No budget increase or ledger reset.

### Lab247 — first extended batch loses its producer; log release reasons

Live244trial selects Marine batch at8201 with review_at10217, confirming2016-loop
horizon in real play. Requests at8201 and8439; by9169 only2SCVs,3Depots andCommandCenter
remain observed, so no Marine training control remains. Native9:27 shows base
overrun and36minerals. This does not demonstrate successful third-request reuse
or failure of the extended deadline: production became unavailable first.

Earlier Bunker proposals at5/3471/4893 retain BuildBunker in next observed worker
orders, and those next tick command lists do not overwrite the builder. The
observed failure is not evidence to rewrite construction protection. Jev mostly
selected bunkers before the late Marine batch; no direct strategy intervention.

Batch removal previously omitted its reason. Add production_batch_released event
with original loop/deadline/remaining count plus current_loop and cause: control
unavailable, deadline, rewind, exhausted requests, or strategy change. This changes
observability only, with no retry or relaxed commitment. Already-cleared livebatch
cannot retroactively emit the event. All125tests pass. Budget unchanged.

### Lab248 — extended-batch trial ends at9:58

Run20260919T220825.429214Z/session68563 terminal. Native DEFEAT independently
verified9:58,10:11 remaining,26minerals,all structures destroyed.171successful
calls/$0.085608810. Checkpoint records defeat, retains two verified mission wins.
First2016-loop Marine batch was late and lost its producer after two requests;
no demonstrated longer-window benefit in this attempt. Startup expanded history
and random trajectory differ from prior13:22 trial; not a controlled causal result.
Camera correction improved visual monitoring; observations expose weak early
production and later loss of mining rather than a transport/command failure.

### Lab249 — place observed cargo utilization beside purchase choices

Last completed244trial repeatedly purchases bunkers and loses its army before
late Marine production. Existing investment options mention loading capability
but omit current cargo occupancy from their local descriptions; the facts exist
elsewhere in context. Add observed occupied/available cargo slots and passenger
types to any owned cargo-capable type's purchase description. Explicitly state
that purchasing does not issue a loading command. No bunker-specific rule,
recommended purchase, automatic boarding, or assumed passenger combat effect.
This is factual context placement, not new information or proven policy benefit.
126tests pass, including fictional carrier and unknown-capacity cases. Next live
trial retains extended production batches, histories and all budget settings.
Retained rolling ledger $.044183538 before restart, below $.06 pacing target.

### Lab250 — cover catalog-known untargeted build controls

Live249run20260919T221748.437060Z/session74302 confirms investment description
contains0occupied/16available Bunker slots. Opening purchase SCV; native0:25 shows
two miners. This alone does not establish cargo wording benefit.

Audit for later-campaign controls finds Build abilities with target=None (1)
omitted, despite support for point builds and gas targets. Add no-target build
candidates only when currently offered with resources enforced and a catalog
product identifies costs. Include these in potential-project information when
only resource-ignored query offers them; never execute that availability alone.
No automatic addon purchase, guessed cost, target or ability ID. Engine execution
remains authoritative. Unknown product is omitted. New synthetic coverage initially
caught missing potential-project parity; fixed it.127tests pass. Actual campaign
addon availability/success not yet verified. Hot reload may change offered menus,
so ongoing run is no longer a cargo-wording-only comparison. Budgets unchanged.

### Lab251 — extended production commitment completes beyond old deadline

Live249run first SCV batch chosen atloop5 with deadline2021. Requests at5,448,813;
last two explicitly carried_jev_commitment rather than new investment choices.
The old672-loop window would have ended at677, before third request813. Commands
receive success codes with no action errors at these ticks; observed SCVs5→6→7
then8 by2292 corroborate actual production. This verifies bounded reuse at paced
intervals, not a survival benefit or causal cargo-wording improvement.

Through2292:47successful calls/$0.026995458,16Marines,8SCVs,260 estimated mineral
income/minute. Native2:57 shows619minerals and two miners at that instant. Three
historical episodes and changing choices mean this is not a controlled baseline.
Untargeted-build adapter6c60033 is loaded; no engine-defined-location option found
in recorded Jev questions yet, so actual addon execution remains unverified.
Continue the live trial without an additional gameplay-policy change.

### Lab252 — audit missing controls from actual advertised abilities

Current249run remains active through3555 with15Marines/8SCVs,63calls/$0.037235394
and no decision errors. To avoid guessing later-campaign coverage, view now reports
engine-advertised resource-legal abilities with no offered command candidate,
grouped by owned type and ability ID/name/target. Player emits control_coverage
only when this diagnostic changes. No extra API/model request and no automatic
command. This can mean missing adapter support OR no valid visible target/site;
it is not proof the action could execute. Potential-only unaffordable abilities
are excluded.127tests pass; synthetic addon coverage distinguishes unknown-product
omission from a correctly represented purchase and an unaffordable ability.
Diagnostic stays out of Jev's strategic state. Use live evidence to prioritize
future adapters instead of adding arbitrary mission-specific behavior.

### Lab253 — observed addon target type is PointOrNone

Live control_coverage at5285 identifies Barracks421 BuildTechLabBarracks and422
BuildReactorBarracks as target5, so lab250's target1-only path cannot cover them.
Blizzard's official data.proto documents PointOrNone=5 explicitly including addons:
https://raw.githubusercontent.com/Blizzard/s2client-proto/master/s2clientprotocol/data.proto
Extend no-target build and potential-project branches to1/5, retaining known-product
cost requirement and engine-advertised resource-legal ability gating. Parameterized
synthetic coverage now exercises both types;128tests pass. No chosen addon, guessed
producer, or strategic directive. Live exposure and execution still need evidence.
Other observed gaps include rally, lift, salvage, patrol and cancel; report does
not authorize automatically issuing them. Current249trial remains mixedrevision.

### Lab254 — expose advertised resource-return control

Coverage at6907 reports HarvestReturnSCV296 as available without a candidate.
Add generic HarvestReturn no-target commands to the income action family when
currently engine-advertised. No automatic return, guessed carried amount, fixed
worker-type selector or assumed subsequent harvesting. Existing gathering and
return orders continue mechanically when Jev chooses to keep them.129tests pass;
coverage verifies only the advertised worker gets the exact untargeted command.
Native8:05 shows remaining CommandCenter under attack,17minerals,zero assigned
miners. This capability addition does not demonstrate it would avert the defeat.
The live trial remains mixedrevision; budget and decision selection unchanged.

### Lab255 — visually verified8:23 defeat despite completed worker batch

Run20260919T221748.437060Z/session74302 terminal,129successful calls/$0.071061438.
Native DEFEAT8:23,11:46 evacuation remaining,0minerals,all structures destroyed.
Checkpoint records defeat and retains two verified wins. Three SCV requests really
completed across the extended window, but the force still collapsed. Cargo-context
placement has no demonstrated survival benefit; multiple adapter/diagnostic
reloads and changed history prevent clean causal attribution. Next fresh run can
validate advertised addon coverage from startup; no claim of full-campaign readiness.

### Lab256 — addon projects reach the live investment menu

Fresh run20260919T222529.029740Z/session24185 starts on5c95c98, after retained
rolling spend$.044065980 headroom check. Atloop5 Jev's actual investment criteria
include BarracksReactor50minerals/50gas and BarracksTechLab50minerals/25gas from
engine catalog. Coverage no longer lists421/422 as unrepresented. No guessed
product mapping was needed. OpeningchoiceBunker,then save498; no addon selected
or completed yet, no decision errors. This verifies interface exposure only.
The standalone campaign/control-coverage work still does not establish full
campaign progression or later-campaign readiness. Keep policy/budget unchanged.

### Lab257 — catalog prerequisites explain otherwise opaque technology purchases

Fresh256trial through1406 has20successful calls/$0.011803638,16Marines,5SCVs,
5Bunkers. One ProviderOverloadedResponseError529 logged; later decisions succeed.
Native1:54 shows fighting around an empty bunker. No concealment or manual orders.

Addon options currently say action capabilities unobserved, without their catalog
technology relationships. Expose available unit types whose tech_requirement
matches the product ID or explicit tech_alias; preserve requires_attached flag.
Both potential and executable project descriptions say other requirements and
appropriate producers may still be needed. Never claim full unlock/current
trainability, prescribe a purchase, or infer hidden entities. Source semantics:
Blizzard data.proto UnitTypeData tech_requirement/require_attached/tech_alias.
130tests pass, including exact/alias matches, unavailable/unrelated exclusions and
conditional wording. Actual catalog can omit relationships; do not fabricate them.
Commit hot-reloads during256trial; no isolated survival attribution or budget change.

### Lab258 — Jev-selected Reactor completes in the live mission

Run256 chooses BarracksReactor at1896. Observed addon tag4388814850 appears at2383
with build_progress.519 and reaches1.0/400health at2922, stillpresent3351. This
verifies actual addon construction through the new no-target path, not merely an
accepted action or a test fixture. Selection belongs to Jev; no forced purchase.
Through3351:52successful calls/$0.029042076,16Marines,7SCVs,5Bunkers,2Barracks.
One earlier529 provider overload remains the only decision error observed so far.
Native3:49 shows forward empty-bunker prompts and560minerals/50gas.

No 'Satisfies a catalog' purchase text found after257reload: current catalog has
not supplied matching available-unit relationships. Do not credit prerequisite
text for the reactor choice or fabricate absent data. Construction success does
not establish efficient utilization, survival benefit, or campaign completion.

### Lab259 — inspect actual request costs before further scheduling changes

Live256run through4374 has14Marines,9SCVs,completedReactor; recent purchases are
SCVs2383/2922/3351/3832/4374. No tick action_errors recorded. Native6:00 shows
821minerals and ongoing combat at a damaged forward bunker. No survival claim.

Read-only successful-request usage aggregation: exact Marine question category
$0.019127 (rounded), strategy/coordination$.004477, investment$.002702. Broader
worker-containing mixed menus$.009686 and role menus$.004865 at the earlier same
inspection. Mixed menus cannot attribute their entire cost to workers. This
contradicts assuming worker roles dominate current costs and does not justify a
worker-only rate cut. No paid probe or policy change; preserve the live trajectory.

### Lab260 — state shared executor scope once per order question

Current256trial Marine-only request totals at inspection:34calls,967100statechars,
322571questionchars. State repetition dominates; do not promise dramatic savings
from descriptions. Across1410 recorded Marine options, repeated executor prefix
accounts43000chars of279636descriptionchars. Existing singleton compaction does
not cover multi-unit selections.

Move the universal shared-order scope into question instructions once: every unit
receives it unless the option explicitly says otherwise. Preserve exact candidates,
command maps, distance facts, singleton/individual behavior and explicit subset
exceptions (such as one anchor holds while followers move). No action removed or
new tactical selector.130tests pass. Less repeated text can change tournament
partitions and model choices; this is not behavior-identical inference or a proven
survival gain. The modest character savings are cumulative, not dollar savings.

### Lab261 — distinguish decision pacing from execution of authorized jobs

Live256run at8517 has8Marines,10SCVs,twoBarracks andReactor;121successful calls/
$0.075467406. Native9:15 shows1552minerals and seven miners. Menu compaction is
loaded. No new execution failure observed beyond earlier provider529.

Code audit: production batches retain authorization but choose/issue their next
request only inside the next paid decision cycle. Long2016window fixes expiry,
not execution cadence. Candidate next experiment: Jev explicitly chooses bounded
quantity and producer, then a mechanical executor fulfills that exact job between
model reviews with fresh advertised ability/resources/supply/freshness checks.
No automatic choice of replacement producer, unit or new job; cancellation and
budget accounting must remain visible. This is a hypothesis, not implemented here.
Current multiple-command validation intentionally rejects repeated unit tags, so
blindly emitting three same-frame commands would not implement it. Do not silently
change existing commitments' meaning or call selection delays transport errors.

### Lab262 — fixed-producer jobs execute between paid reviews

Run256 terminated; native DEFEAT independently verified13:15,06:54remaining,
1546minerals,allstructuresdestroyed.172successful calls/$0.108483480 plus earlier
unknown529 reservation. Checkpoint records defeat, still only two verified wins.

New controller enables explicit fixed-producer batch semantics. Jev sees that its
first producer remains fixed and up to two remaining requests can execute between
paid reviews, at least112loops apart, within original2016deadline. First request
must receive engine success before arming. Executor matches exact observed owned
producer/command/project, checks advertised candidate and resources/supply, uses
fresh-observation validation, consumes bounded attempts, logs execution. No new
producer/type selected. Missing producer, rewind, strategy change, deadline or
exhaustion releases it; unavailable/unaffordable command waits visibly. Rejected
or stale submission cancels without retry. Decision failure cannot arm a partial
job. Old controllers lack feature flag, so their existing commitments retain old
semantics. Requires next controller process; not tested live yet.

Full suite134passed before final added integration test; focused5job tests pass
including explicit Jev batch authorization, initial success gating, fixedproducer,
spacing, exhaustion, expiry, rewind, strategy, missingcontrols and affordability.
No extra Jev calls, dollar-limit change, queue-command bypass or unit-tag duplicate.

### Lab263 — Jev-built Tech Lab is followed by Medic availability

Run26220260919T223706.942817Z/session97960 is live. Jev selects BarracksTechLab
at2182. At2713 investment projects first include Medic; previous recorded lists
through2182 did not. Native3:47 shows the attached lab and fighting at the base,
512minerals/75gas,two assigned miners. This verifies a newly reachable control
path, not forced research or a claim that Medic production has occurred. One
ConnectTimeout earlier; later decisions complete. Through2713 reportedcost$.023653686.
No production_job events yet: executor mechanism remains unverified live until
Jev chooses a batch. Keep trial stable; do not force a convenient validation choice.

### Lab264 — correct operational pacing docs and document job execution

Run262 confirmed live through6357,95successful calls/$0.056179620,12Marines,
5SCVs,twoBarracks,TechLab,twoBunkers. No production_job event yet. Preserve trial
rather than forcing authorization. README incorrectly retained80% pacing from an
older experiment; corrected to implemented60%. Documented bounded fixed-producer
job semantics, acceptance gating, fresh checks, release causes, observability and
controller-restart boundary. Documentation only; no runtime policy/budget change.

### Lab265 — retain executor attempts separately in episode summaries

Run262 still active through7753,7Marines/5SCVs; no batch authorized. Audit found
previous_attempts counts investment_choice but would omit background job requests.
Add separate background_training_attempt_counts and background_training_accepted_counts
using the armed project's identity until release. Initial purchase stays in the
existing proposal count; no double counting. Explicitly distinguish attempted,
engine-accepted and completed production. Malformed/unarmed request events do not
invent a project attribution. Three episode tests pass including one success,one
rejection and a post-release event. Startup history loads only on next controller;
current trial unchanged. No extra model calls or policy selection changes.

### Lab266 — first executor-enabled trial ends without authorizing a job

Run26220260919T223706.942817Z/session97960 ends with native DEFEAT11:34,
08:35remaining,0minerals,allstructuresdestroyed.166successful calls/$0.093748410;
one earlier ConnectTimeout with unknown billing retained under governor.
No production batch selected and no production_job execution; do not label this
an executor success or failure. TechLab completed and Medic became available,
but no resulting victory. Stable runtime policy after startup; later commits
changed journal/docs and future history summaries. Verified checkpoint retains
two completed missions. Next test must retain explicit Jev authorization rather
than forcing a batch solely to obtain execution evidence.

### Lab267 — remove framework sharpening that suppresses job probability

Offline last262run:27investment samples. Before producer losses, raw Jev batch
mass mostly.08–.17; within-family squaring often reduces it to.013–.111 (one.169).
No selected batch is not evidence Jev assigned zero probability. Lab176 introduced
squaring to reduce low-ranked capacity purchases;216 preserved purchase/wait mass
but retained conditional sharpening. Neither established a controlled survival
benefit, and today's fixed-producer executor adds a materially different option.

Next trial uses normalized legal positive Jev weights directly, preserving every
relative odd rather than specifically boosting jobs or units. Stable scaling
handles extreme finite weights. Log exponent1/scopejev_legal_distribution. This
can increase low-ranked extra-capacity choices—the old reason for sharpening—so
monitor rather than promise improvement. No forced batch, changed seed, hardcoded
tactic, additional model call or higher spending limit.136tests pass, covering
relative odds, family totals, extreme values and existing execution boundaries.

### Lab268 — visual inspection and first authorized background training

Ongoing stable lab267 run20260919T224749.369540Z: native screenshot at9:59
shows1mineral,404gas,7/35supply,CommandCenter1/27workers,Refinery0/3.
Tick9646 includes two SCVs moving toward each other's observed positions;
accepted commands alone do not establish useful coordination. This is a general
coordination observation, not a directive to select a mission-specific tactic.
Continue periodic native visual inspection alongside telemetry, as requested.

First live executor evidence: Jev Marine batch armed6265, exact same Barracks
4382261250/ability560 requested again6382 (117loops later), engine accepted,
freshness3loops. Final remaining request unavailable/unaffordable6500; deadline
8281 reached8284 and job released without retry or producer substitution.
A previously unseen Marine tag appears7024, but concurrent losses prevent a
simple count-based attribution of every training completion. No forced batch
or extra model decision was used to exercise the executor. Army loss thereafter
means execution success is not strategic success. At10045,162successful calls
cost$0.091197330; run not yet terminal. No policy changes in this entry.

### Lab269 — verified defeat; retain individual history across paced reviews

Lab267 run20260919T224749.369540Z ended with native DEFEAT12:27,
07:42remaining,0minerals,allstructuresdestroyed.193successful calls cost
$0.104546274. Independent UI verification recorded in ignored run/checkpoint;
only first two campaign missions remain completed. Raw investment sampling
allowed a batch this time, but one episode does not establish a survival benefit.

Offline audit found reciprocal SCV move pairs at9646and9867. All6 individual
unit questions in this attempt lacked recent_progress. Individual history expired
at112loops, shorter than many paced review intervals. Extend its factual window
to672loops (same as aggregate outcomes), bound to8prior samples, reject future
samples after rewind, and label prior selections as not proof of execution.
No automatic regrouping, assigned worker roles, new model calls or spending
increase. This addresses missing context, not proven cause of defeat; individual
questions are a small fraction of this run's decisions. Test suite passes136.

### Lab270 — verify paced-history behavior without paid probes

Regression drives the actual individual decision path using a deterministic
fake Jev: first observation5 has no invented history; review305 receives the
prior continue selection across a300loopgap; review1000 expires stale history;
rewind2 excludes future observations. No action is synthesized in any case.
Targeted test passes. This proves context plumbing, not improved model decisions.
Live lab269 session60910 remains running; no runtime policy change in this commit.

### Lab271 — history delivered live; verified defeat at11:22

Run20260919T225822.677784Z/session60910 terminal with native DEFEAT11:22,
08:47remaining,0minerals,allstructuresdestroyed.166successful calls cost
$0.097955844; zero decision errors. Independent UI result/checkpoint saved.
Seven individual questions, one with recent_progress: extended history reached
live Jev, but no survival benefit established. No background training executions.
Most control remained cohort-level, limiting scope of the individual-history fix.
Visual inspections found fluctuating worker utilization, force concentrated near
base, construction including another CommandCenter, and eventual army collapse.
Do not infer tactical effectiveness from accepted requests or completion alone.
Stable runtime policy throughout; lab270 added only regression test/journal.
First two missions remain the only verified campaign victories.

### Lab272 — describe no-purchase by actual effect

Last269run investment top answer was save on20of23reviews (including late empty
menus); sampled construction/training often had much lower individual probability.
This does not prove a calibration problem or justify forcing a purchase. Earlier
rank-then-buy and strategy ablations failed to remove waiting reliably.

One wording confound remains: save unconditionally says to let existing production
finish, even when none exists. Replace with literal effects: requests no new unit,
structure or upgrade, leaves resources available and existing orders unchanged.
Keep all options, distributions, sampling, producer selection, budget and jobs.
Hypothesis only: reduced implicit benefit for waiting; no causal claim before
trial.137tests pass. No paid probe calls.

### Lab273 — first fully executed background batch observed

Live lab272 run20260919T231030.247545Z/session63654: Jev authorized SCV batch
at6, initial request accepted/armed. Same CommandCenter4299948033 ability524
accepted background requests at120and238 (114/118loop spacing, freshness4/5).
Allowance exhausted and released250. Observed SCVs5at6,6at471,8at1006.
This is live evidence of a full three-request batch and corresponding increased
worker count, without new model decisions for the two background requests.
Native screenshot1:24 shows24/35supply and4miners. It does not establish that
changed save wording caused the selection or that the economy/mission will
succeed. Trial remains running; this commit changes only the journal.

### Lab274 — neutral-save trial ends13:19; execution is not allocation

Run20260919T231030.247545Z/session63654 terminal with native DEFEAT13:19,
06:50remaining,385minerals,allstructuresdestroyed.181successful calls cost
$0.114435048; zero decision errors; six background training execution events.
Verified UI outcome saved to run and campaign checkpoint. Only first two missions
completed. Stable policy throughout; lab273 changed journal only.

Full first SCV batch verified inlab273. Later visual checks showed higher mineral
income, lost supply capacity then recovery through construction, substantial
unspent minerals/gas and shrinking army.13:19 vs previous11:22 is one uncontrolled
episode difference, not proof neutral wording improves survival. The main unresolved
problem remains allocation and coordination, not merely failed API execution or
lack of workers. Do not respond by forcing a mission-specific production plan.
