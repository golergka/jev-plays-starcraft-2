# Stock mission experiment on this Mac

## Current API compatibility procedure

Lab163 showed that native objective Completed/Failed updates can end API control
before the campaign mission ends. Use the local objective adapter for continued
experiments. It preserves script-facing objective states and mission conditions,
while displaying terminal objectives with an explicit text label. Lab169 verified
Liberation Day's actual victory screen at3:44 with this adapter. Lab183 verified
The Outlaws at27:57 and corroborated the ending marker with its native victory UI.
See CAMPAIGN_PROGRESS.md for current evidence.

After extracting a source map with the procedure below, build a separate copy:

```sh
uv run python scripts/build_objective_bridge.py maps/traynor02.SC2Map maps/traynor02-api.SC2Map \
  --casc /tmp/jev-research/CascLib/build/casc.framework/casc \
  --storm /tmp/jev-research/StormLib/build/storm.framework/storm --record-outcomes
uv run python -m jev_sc2 --attach --map maps/traynor02-api.SC2Map \
  --follow-camera --seconds 1200 --max-calls 3000 --max-age-loops 128 \
  --objective 'Destroy the Dominion Base.'
```

The builder refuses overwrites and writes a `.bridge.json` provenance report
beside the ignored map. It audits the entire script include closure; unresolved
or ambiguous dependencies fail rather than silently leaving inconsistent reads.
The ending hooks currently support the audited Wings of Liberty library only.
They record the real victory-sequence call or player defeat in a unique native
bank. The controller requires a fresh active marker followed by a terminal one,
then stops and saves its replay. Experimental builds retain `campaign_credit=false`:
the detected ending still needs a UI check before advancement. An API result by
itself does not establish campaign completion.

Resume the same running mission with `--attach` and the same objective/budgets,
omitting `--map`. For maps in this repository's maps directory, the runner resolves
the current API map name to its hash-checked sidecar and retains ending monitoring.
An existing active bank can arm a resumed monitor; an already-terminal bank alone
cannot credit a win. Player/view/camera commits continue to hot-reload normally.

SC2 exited once when leaving an actual victory screen through the API. Its replay
and verified result had already been saved. Confirm process exit before relaunching
through Battle.net with the API arguments below; do not restart a still-live game
because a request merely timed out. Source maps and installed game files stay intact.

## Original extraction and smoke tests

The Mac editor fails during video initialization. We instead used
[CascLib](https://github.com/ladislav-zezula/CascLib) to read the installed game
and [StormLib](https://github.com/ladislav-zezula/StormLib) to package a local MPQ
map. Game files are not modified. The output and replays remain ignored by Git.
This is a repackaged stock mission, not verified stock campaign progression.

Tested library revisions:

- CascLib: `2a280f5a231966dc5d1b534978dd9f9f04a374cd`
- StormLib: `44ebfbfc109d76e2a85bbd5d8b0c949df7e65c6f`

Build in a temporary working directory (the example uses `/tmp/jev-research`):

```sh
git clone https://github.com/ladislav-zezula/CascLib.git /tmp/jev-research/CascLib
git -C /tmp/jev-research/CascLib checkout 2a280f5a231966dc5d1b534978dd9f9f04a374cd
cmake -S /tmp/jev-research/CascLib -B /tmp/jev-research/CascLib/build -DCASC_BUILD_SHARED_LIB=ON -DCMAKE_BUILD_TYPE=Release
cmake --build /tmp/jev-research/CascLib/build -j 4
git clone https://github.com/ladislav-zezula/StormLib.git /tmp/jev-research/StormLib
git -C /tmp/jev-research/StormLib checkout 44ebfbfc109d76e2a85bbd5d8b0c949df7e65c6f
```

For StormLib on this compiler, change `PRIVATE "-framework Carbon"` to
`PRIVATE "SHELL:-framework Carbon"` in its CMakeLists.txt. Otherwise CMake passes
an invalid single compiler argument. Then:

```sh
cmake -S /tmp/jev-research/StormLib -B /tmp/jev-research/StormLib/build -DBUILD_SHARED_LIBS=ON -DSTORM_USE_BUNDLED_LIBRARIES=ON -DCMAKE_BUILD_TYPE=Release
cmake --build /tmp/jev-research/StormLib/build -j 4
uv run python scripts/extract_campaign.py --casc /tmp/jev-research/CascLib/build/casc.framework/casc --storm /tmp/jev-research/StormLib/build/storm.framework/storm --mission traynor01
```

The extractor refuses to overwrite an existing map. It preserves component bytes,
includes base and English locale components, and omits other locales. The first
mission produced 37 components and a 1,738,887-byte MPQ. It does not read tactical
script contents into the policy. Only live player observations go to Jev.

Start SC2 using Battle.net with `-listen 127.0.0.1 -port 5001 -displayMode 0` in
its Additional command line arguments. With that process running:

```sh
uv run python -m jev_sc2 --attach --map maps/traynor01.SC2Map --follow-camera --seconds 90 --max-calls 120 --objective 'Destroy the Logistics Headquarters. Raynor must survive.'
```

This loaded the opening cinematic and mission. After the cinematic, the engine
accepted Jev movement commands. The visible mission objectives are transcribed
above. The initial run had six units alive after 120 calls, costing $0.014349426;
it did not complete the mission. During the cinematic the engine returned
`YouCantIssueCommandsToThatUnit`, which is logged. Queries alone do not guarantee
that a cinematic unit accepts commands.

Resume without reloading the map using `--attach` alone. Load another mission with
`--attach --map ...`. A campaign sequencer can use this boundary, but Hyperion,
research, difficulty selection, mission unlocks and persistence between maps are
not implemented or verified. Do not claim the whole vanilla campaign works.

## Second mission smoke test

The same extractor CLI with `--mission traynor02` produced 41 components and a
1,246,964-byte MPQ. `--attach --map maps/traynor02.SC2Map` successfully joined it.
The player screen shows **Destroy the Dominion Base** and the starting Terran base.
No campaign unlock bypass command or modified trigger was used; this is another
standalone scenario load, not evidence of persistent campaign progression.

```sh
uv run python scripts/extract_campaign.py --casc /tmp/jev-research/CascLib/build/casc.framework/casc --storm /tmp/jev-research/StormLib/build/storm.framework/storm --mission traynor02
uv run python -m jev_sc2 --attach --map maps/traynor02.SC2Map --follow-camera --objective 'Destroy the Dominion Base.'
```

The player now offers engine-advertised training actions and gathering from visible
mineral fields. Jev decides whether and where to use them. Point-target building placement now offers four nearby, currently visible,
engine-approved sites. A Jev-selected Supply Depot completed and increased capacity
from 19 to 27; further depots were in progress. Gas harvesting, upgrades, research
and cross-mission progression are still absent.

The second mission opens a tutorial/help panel that pauses the game clock. During
that pause, API actions can report success without resource or unit changes until
play resumes. Close the panel through the game UI; this is menu handling, not a
model-controlled tactical choice. The harness now avoids inference on unchanged
game loops and stops after ten seconds of a stalled clock, requesting UI inspection.
The first economic trial remained at loop 354 and is not evidence of production.


## Installed later-campaign map inventory

Read-only CASC name enumeration found 41 Liberty map roots, 38 Swarm roots and
26 Void roots on this installation. These counts include story/tutorial/evolution
maps and are **not** counts of required campaign missions or proof of entitlement.
The root paths differ: Swarm and Void insert `swarm/` or `void/` under
`maps/campaign/`. The extractor now accepts `--campaign liberty|swarm|void` to
handle those observed main-map paths. Nested evolution maps are not covered by
that simple path construction. Later-campaign loading, dependencies, ownership
and progress remain unverified; no victory is inferred from installed assets.


The opening sequence now references the prepared outcome adapters for its two
uncompleted entries, Zero Hour and Smash and Grab. Completed prefix definitions
are preserved so the existing verified wins remain transferable. The local
adapter files and their sidecars are still required; they are not distributed
in this repository. Instrumented endings still require the documented independent
verification before victory credit. Changing these map paths does not grant
campaign completion or solve cross-mission unlock persistence.

## Same-process retry verified on Zero Hour (lab296)

After the controller exited and its native defeat screen was independently
verified, `RequestRestartGame` successfully restarted the adapted Zero Hour map
without quitting SC2 or moving its window. The API returned `in_game`,
`need_hard_reset=false`; observation loops reset11308→0 with36owned units, and
its outcome bank wrote a fresh active marker. This is verified for that installed
map/build, not all campaigns. Blizzard documents this request as single-player
reinitialization with the same player setup:
[protocol definition](https://github.com/Blizzard/s2client-proto/blob/master/s2clientprotocol/sc2api.proto).

Use the existing SC2 client after the prior controller has stopped; do not open a
second connection during play. Verify the current map with `game_info`, issue
`client.request('restart_game', sc.RequestRestartGame())`, and inspect the returned
`need_hard_reset` field. If true or the request fails, do not assume a retry began.
Verify a reset observation clock, opening units and fresh outcome marker, close
the probe connection, then attach the controller **without `--map`**. Passing a map
would create another game rather than continue this restarted one.

```sh
uv run python -m jev_sc2 --attach --follow-camera --seconds 1800 \
  --max-calls 4000 --max-age-loops 128 --objective 'Hold out for evacuation.'
```

The trial probe left a795-loop gap before controller attachment. Treat this as
restart infrastructure evidence, not a clean policy-from-opening comparison.
Atomic restart-and-control integration is still needed to eliminate that gap.

Lab297 adds an integrated controller path to avoid the separate-probe gap:

```sh
uv run python -m jev_sc2 --attach --restart \
  --expected-map traynor03-outcomes-lab170.SC2Map --follow-camera \
  --seconds 1800 --max-calls 4000 --max-age-loops 128 \
  --objective 'Hold out for evacuation.'
```

Use only after the previous controller has stopped and its mission outcome has
been recorded. `--restart` requires `--attach` and `--expected-map`, and rejects
`--map`; the map identity is checked before resetting. A required hard reset or
failure to rewind the clock stops loudly rather than silently relaunching. The
same socket continues into Jev control, and ending monitoring requires a marker
fresh since this restart. Local tests pass; the integrated path awaits a live
trial. The separate restart request itself was live-verified in lab296.
