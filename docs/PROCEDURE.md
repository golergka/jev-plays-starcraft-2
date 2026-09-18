# Verified contracts and local procedure

Research date: 2026-09-18. Distinguish a documented API contract from a successful
local test; Battle.net launch and authentication succeeded; API connection through Battle.net succeeded; mission play remains under test.

## SC2 transport and player perspective

Blizzard ships the API in the retail Windows/Mac clients. It is **binary Protobuf
over WebSocket**, not a textual network protocol. Python converts the observations
to small JSON objects for Jev. The raw interface provides units visible to the
player and removes camera/selection mechanics. It is player-information fair, but
not a claim of human-equivalent mouse mechanics or APM. A strict screen/camera-only
experiment would instead use feature-layer actions and observations.

The API itself also contains cheating/debug features. Merely using the API does
not prevent cheating. Our wrapper permits only setup, player observations,
queries, ordinary actions and replay saving. No debug requests, map commands,
observer slots, fog disabling, quick-load, or resource overrides. Both game creation
and observations explicitly set `disable_fog=False`. Cloaked/burrowed extras are
disabled. Enemy snapshots/hidden units and enemy orders are not sent to Jev.
Ability queries respect resource requirements; the engine remains the final arbiter.

Sources: [Blizzard overview](https://github.com/Blizzard/s2client-proto),
[protocol and lifecycle](https://github.com/Blizzard/s2client-proto/blob/master/docs/protocol.md),
[exact message definitions](https://github.com/Blizzard/s2client-proto/blob/master/s2clientprotocol/sc2api.proto),
[raw unit definitions](https://github.com/Blizzard/s2client-proto/blob/master/s2clientprotocol/raw.proto).

## Exact process and request sequence

1. Download Battle.net from https://download.battle.net/en-us/desktop; install the
   Mac app, sign in, choose StarCraft II, install and finish game data download.
   Run the game once via Battle.net, then close it before our separate API launch.
2. Set SC2PATH to the installation root (default `/Applications/StarCraft II`).
   Select the numerically highest `Versions/BaseNNNNN` containing
   `SC2.app/Contents/MacOS/SC2`. This path follows
   [PySC2's Mac launcher](https://github.com/google-deepmind/pysc2/blob/master/pysc2/run_configs/platforms.py).
3. Launch that binary with the installation root as cwd and flags
   `-listen 127.0.0.1 -port 5001 -displayMode 0 -windowwidth 1280 -windowheight 800`.
   Also supply `-dataDir <installation-root>/ -tempDir <unique-temporary-directory>/`, as PySC2 does. Port 5000 is occupied by macOS Control Center on this host. On Apple Silicon the Intel binary needs Rosetta. Rosetta is present on this host;
   runtime compatibility still requires a real launch test.
4. Connect to `ws://127.0.0.1:5001/sc2api`. Send `RequestPing` and record version.
5. `RequestCreateGame(local_map.map_path=<absolute SC2Map>, realtime=True,
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

A future campaign runner can sequence local mission maps, record results and
carry a campaign manifest between runs. But extracting/authoring those maps and
preserving stock progression is separate work, not a solved feature here.
[Archipelago's SC2 client](https://github.com/ArchipelagoMW/Archipelago/blob/main/worlds/sc2/client.py)
demonstrates launching campaign-derived custom maps with `run_game(..., realtime=True)`.
Its modified maps and item/progression system are not the vanilla campaign and
must not be silently substituted or described as such. Start with a small, openly
available API test scenario; then verify a single campaign mission explicitly.

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

First player prototype chooses per-unit attack/movement/continue for up to 12
units. It has no build order or campaign strategy. Progress means observed lessons
about Jev, not hiding a conventional winning bot behind a token model call.

## Local runtime findings

The full installation completed. Direct subprocess launch crashed even with no API
flags, so that failure does not establish an API incompatibility. Launching through
Battle.net with additional arguments `-listen 127.0.0.1 -port 5001 -displayMode 0`
succeeded: RequestPing returned version 5.0.16.97563. The practical procedure on
this host is Battle.net Play followed by `--attach`. Keep that instance running
across player commits and scenario transitions. Direct launch needs further
diagnosis and must not be described as verified.
