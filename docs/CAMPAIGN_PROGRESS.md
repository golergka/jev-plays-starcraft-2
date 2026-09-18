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
