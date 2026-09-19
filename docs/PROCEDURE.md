# Verified contracts and local procedure

Research date: 2026-09-18. Distinguish a documented API contract from a successful
local test; Battle.net launch and authentication succeeded; API connection through Battle.net succeeded; three realtime MarineMicro trials, accepted Jev actions and replay saving are verified.

## SC2 transport and player perspective

Blizzard ships the API in the retail Windows/Mac clients. It is **binary Protobuf
over WebSocket**, not a textual network protocol. Python converts the observations
to small JSON objects for Jev. The raw interface provides units visible to the
player and removes camera/selection mechanics. It is player-information fair, but
not a claim of human-equivalent mouse mechanics or APM. A strict screen/camera-only
experiment would instead use feature-layer actions and observations.

The API itself also contains cheating/debug features. Merely using the API does
not prevent cheating. Our wrapper permits only setup, player observations,
queries, ordinary actions and replay saving. An opt-in infrastructure experiment
(`--api-bookmark-recovery`, lab 160) additionally saves an in-memory bookmark every
45 seconds and allows one logged restore for an anomalous all-player API defeat
while owned structures remain. This can rewind recent play; it clears policy memory
and never supplies tactical orders. It is disabled by default and remains unproven
as a fix. No debug requests, map commands, observer slots, fog disabling, or resource
overrides. Both game creation
and observations explicitly set `disable_fog=False`. Cloaked/burrowed extras are
disabled. Hidden units and enemy orders are not sent to Jev. As of lab 046,
snapshots are exposed as explicitly stale type/location facts without health or
orders; they may receive point-targeted movement, never a live unit-tag attack.
Ability queries respect resource requirements; the engine remains the final arbiter.

Sources: [Blizzard overview](https://github.com/Blizzard/s2client-proto),
[protocol and lifecycle](https://github.com/Blizzard/s2client-proto/blob/master/docs/protocol.md),
[exact message definitions](https://github.com/Blizzard/s2client-proto/blob/master/s2clientprotocol/sc2api.proto),
[raw unit definitions](https://github.com/Blizzard/s2client-proto/blob/master/s2clientprotocol/raw.proto).

## Exact process and request sequence

1. Download Battle.net from https://download.battle.net/en-us/desktop; install the
   Mac app, sign in, choose StarCraft II, and finish the game data download.
2. In Battle.net's SC2 Game Settings, enable Additional command line arguments:
   `-listen 127.0.0.1 -port 5001 -displayMode 0`. Click Play. Port 5000 is occupied
   by macOS Control Center on this host. The installed Intel binary runs under Rosetta.
3. Run `uv run python -m jev_sc2 --attach --map <local.SC2Map>` from this repository.
   The harness can locate and directly launch the highest installed Base version,
   but direct subprocess launch crashes on this Mac and is not the supported local
   procedure. Battle.net launch followed by attachment is verified. Window placement
   flags have not reliably placed the game on the external monitor; move it manually
   and reuse the same process across experiments.
4. Connect to `ws://127.0.0.1:5001/sc2api`. Send `RequestPing` and record version.
5. `RequestCreateGame(local_map.map_path=<map filename>, local_map.map_data=<map bytes>, realtime=True,
   disable_fog=False, player_setup=[Participant])`. For a melee map, add a Computer
   slot; do not add one to a scripted single-player scenario automatically.
6. `RequestJoinGame(race=Terran, options.raw=True, options.score=True, ...)` as a
   participant. Await completion. Fetch `RequestGameInfo` and `RequestData` for
   static catalog names. Do not reveal enemy starting locations to the model.
7. Loop: `RequestObservation`, visible-data filtering, `RequestQuery` for available
   abilities, Jev decision, fresh observation, stale/ownership/target validation,
   `RequestAction`. Real time advances while inference runs: **no RequestStep**.
   Requests are serialized so responses cannot get assigned to the wrong caller.
8. Stop on `player_result` or status `ended`. Save with `RequestSaveReplay`.
   Keep process/socket lifetime separate from player policy lifetime. An attached
   process must already have been launched with the API flags.

## Missions and campaign: what is and isn't guaranteed

Blizzard explicitly documents single-player map creation and joining. This proves
the scenario route, not automatic access to the stock campaign's mission selector,
Hyperion, research, armory, save profile, or unlock state. The protocol has no
campaign-navigation API. Do not advertise a fully automated vanilla campaign on
the strength of the map API alone.

The installed first Liberty mission has now been extracted without changing its
base/English components, repackaged, loaded and controlled through the API. See
[the reproducible campaign procedure](CAMPAIGN.md). Mission completion remains
unachieved. A future runner can sequence these maps and record results, but
preserving stock progression is separate work, not a solved feature here.
[Archipelago's SC2 client](https://github.com/ArchipelagoMW/Archipelago/blob/main/worlds/sc2/client.py)
demonstrates launching campaign-derived custom maps with `run_game(..., realtime=True)`.
Its modified maps and item/progression system are not the vanilla campaign and
must not be silently substituted or described as such. MarineMicro and the first two stock campaign missions have been loaded and
controlled; these results do not imply whole-campaign compatibility.

## Jev integration and experiment design

Use [OpenRouter's Python SDK Decisions API](https://openrouter.ai/docs/client-sdks/python/sdks/decisions/README.md),
`OpenRouter.alpha.decisions.create_async(model='typesafe/jev-1.13', state=..., questions=...)`.
The endpoint is `POST https://openrouter.ai/api/alpha/decisions`. In SDK 1.1.158,
set the method's `server_url='https://openrouter.ai'`: the default `/api/v1` base
otherwise produces a 404. Tested successfully with the dedicated key in `.env`.
The official `typesafe-sdk` is also installed for reference; its default endpoint
is TypeSafe's own `/v1/systemone`, not OpenRouter's Decisions route.

First authenticated smoke test: 695 ms total latency, 365 input tokens, reported
cost $0.00001533. Jev chose retreat for a critically wounded Marine next to a melee
attacker while its weapon cooled down. This is a synthetic connectivity probe,
not a measured StarCraft result or a general latency benchmark.

[TypeSafe's model limits](https://docs.typesafe.ai/model-jaggedness/jev-1.13): weak
arithmetic/counting, literal instructions, indirection and distracting state.
Therefore compute distances, health fractions and legality in Python; ask narrow
choices; use short local surroundings; record probability distributions. Questions
in a batch are independent, so don't assume one answer can inform another in that
same request. No fallback generative LLM and no traditional tactical policy after
an API failure: keep existing game orders, log the failure, and stop after five.

The current player supports movement, combat, stopping, holding position, mineral
gathering, training, and visible engine-approved building sites. It considers up
to 64 owned units, scheduling twelve per boundary as two concurrent six-unit Jev
requests. Squad intent is sampled from Jev probabilities. It has no scripted build
order or campaign route. Progress means observed lessons
about Jev, not hiding a conventional winning bot behind a token model call.

## Local runtime findings

The full installation completed. Direct subprocess launch crashed even with no API
flags, so that failure does not establish an API incompatibility. Launching through
Battle.net with additional arguments `-listen 127.0.0.1 -port 5001 -displayMode 0`
succeeded: RequestPing returned version 5.0.16.97563. The practical procedure on
this host is Battle.net Play followed by `--attach`. Keep that instance running
across player commits and scenario transitions. Direct launch needs further
diagnosis and must not be described as verified.

Map bytes are required by the verified local route: passing the repository map
path caused join_game to block in a file open. Sending map_data loaded immediately.
This is consistent with macOS protected-folder handling, but the underlying OS
cause is not proven. Three MarineMicro trials produced valid engine actions and
replays. Commit 6452cdb was loaded while the first match ran. This proves runtime
infrastructure, not campaign progression or good combat performance.

## Visible terrain input

The terrain input labels the four nearby compass destinations using the
static pathing grid only where the current player visibility byte is 2 (visible).
Fogged/unexplored destinations remain unknown. This provides local terrain facts,
not a route, target ranking or automatic replacement action. Buildings and dynamic
obstacles can still invalidate a static walkability label.

Packed 1-bit pixels use row-major indexing with the most significant bit first;
8-bit visibility uses one byte per cell. This agrees with the
[python-sc2 pixel reader](https://github.com/BurnySc2/python-sc2/blob/develop/sc2/pixel_map.py).
A regression test checks masking of hidden, fogged and out-of-bounds destinations.

The sustained sampling trial ended with the stock campaign's on-screen **DEFEAT /
Raynor has died** dialog, while the protocol continued returning in-game status
and no player_result. The harness now also stops after ten seconds with no owned
units, saves a replay, and asks for UI inspection. That diagnostic stop is not
itself classified as defeat: cinematics or mission scripts may remove units too.
