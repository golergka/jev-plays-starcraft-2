# Three-campaign objective

Scope confirmed by the user: Wings of Liberty, Heart of the Swarm, and Legacy of
the Void. No campaign has been completed and no mission victory is verified yet.

The user subsequently authorized individual campaign missions played in sequence
with progression recorded here. Native campaign controls and account achievement
credit are not required. The standalone-map route is therefore the active route.
Only verified victories advance this journal; merely loading a later map does not.

| Campaign | Mission | Verified result |
| --- | --- | --- |
| Wings of Liberty | Liberation Day (`traynor01`) | In progress; prior defeat, no win |
| Wings of Liberty | The Outlaws (`traynor02`) | Economy smoke tests only; no win |
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
