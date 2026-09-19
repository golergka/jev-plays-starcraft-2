# Jev plays StarCraft II

An experiment in fast, probabilistic decisions. Jev chooses actions; Python handles
observations, geometry, validation, transport and logging. No other inference model
participates in the game loop. This is an experimental player, not a complete campaign bot.

Read [the experiment report](docs/EXPERIMENT_REPORT.md) for measured
results, failed approaches, and current limitations.

## Run

1. Install StarCraft II using Battle.net and finish its download. On this Mac, set
   **Game Settings → Additional command line arguments** to
   `-listen 127.0.0.1 -port 5001 -displayMode 0`, then click Play.
   Battle.net launch is verified to expose the API; direct subprocess launch
   currently crashes before connecting. Use `--attach` below.
2. `uv sync` and put `OPENROUTER_API_KEY` in `.env` (see `.env.example`).
3. `uv run python -m jev_sc2 --doctor`
   Fetch the reference map: `uv run python scripts/fetch_map.py`.
   Blizzard's MarineMicro example uses a computer opponent:
   `uv run python -m jev_sc2 --attach --map maps/MarineMicro.SC2Map --opponent`.
4. Provide a local single-player `.SC2Map`:
   `uv run python -m jev_sc2 --attach --map /absolute/path/mission.SC2Map`
   Add `--opponent` only for a melee map requiring a computer opponent.
5. To reuse an API-enabled game: `uv run python -m jev_sc2 --attach`.
   To start a fresh scenario in that process, use `--attach --map maps/MarineMicro.SC2Map --opponent`.
   An ordinary Battle.net-launched game has no API socket; it cannot simply be attached.

Defaults: real time, 180 seconds, at most 300 successful Jev calls, no automatic
retries, and decisions older than 32 game loops discarded. SC2 keeps running after
the harness exits. Stop it through its UI when finished. Runs and replays live in
`runs/` and stay out of Git. The provider-side key spending cap is separate from the per-run call budget.

## Live experiments

Edit **player.py**, then commit. The orchestrator loads the source from the new Git
commit at the next decision boundary while keeping the socket and `memory` dict.
Uncommitted edits do not run. A syntax/import error retains the previous policy.
The observation adapter `jev_sc2/view.py` and stream director `jev_sc2/camera.py`
reload atomically with `player.py`; if any source is invalid, the previous set
remains active. Other harness modules require restarting the controller.

`--follow-camera` follows visible engagements, damage and moving forces, with
readable shot holds. It moves only the display camera and supplies no gameplay
decisions. Camera memory is separate from Jev policy memory.

Enable auto-push with `git config core.hooksPath .githooks`. Every commit is pushed
to origin. Failed pushes print an error and preserve the local commit and reload.
Read `git log --format=fuller` before choosing the next experiment. Commit messages
are the lab journal: hypothesis, measured outcome, failure, and next experiment.

Every decision logs its input, questions, full probabilities, model version, cost,
latency, policy revision, action results, and observation age to JSONL. Inspect it
with ordinary Python or `tail -f runs/<run>/events.jsonl`. No API keys are logged.
Use `uv run python scripts/report.py` for the latest run's measured summary.

`uv run pytest -q` checks committed-source reload and command/visibility boundaries.

See [the researched procedure and limits](docs/PROCEDURE.md). Nothing here claims
that stock campaign progression or combat performance has already been validated.

## First campaign mission

The installed first Liberty mission can be repackaged and played through the API;
follow [the extraction instructions](docs/CAMPAIGN.md), then run:

```sh
uv run python -m jev_sc2 --attach --map maps/traynor01.SC2Map --follow-camera \
  --objective 'Destroy the Logistics Headquarters. Raynor must survive.'
```

Omit `--map` to resume the running mission. This has loaded successfully and
produced a verified **Victory in Liberation Day**, recorded with an API result and
replay in [the progression journal](docs/CAMPAIGN_PROGRESS.md). **The Outlaws is also verified won**. Zero Hour has four recorded defeats; further experiments are ongoing. All three main campaigns are the target; stock campaign menus,
research and unlock persistence are not implemented.

The current policy asks Jev for a strategic priority, a contribution and concrete
order for each unit-type selection, and one shared investment across the economy.
All choices remain Jev decisions, including saving resources, selecting a builder,
and choosing individual control. A rolling observation history exposes unit
arrivals/disappearances and net resource changes without prescribing a response.
The individual-control fallback uses concurrent small batches and sampled Jev
navigation probabilities. Commit history records earlier policy designs.

Map observations include explored static terrain, currently visible entities and
explicitly stale fog snapshots. Hidden entities are excluded. Shared commands,
training, gathering and engine-checked construction are implemented; the complete
SC2 ability surface is not yet covered. See the progression journal for outcomes.

## Resume the current experiment

The pending mission is Zero Hour. After an incomplete controller run has exited,
and with that same game still open, resume through the checked sequence path:

```sh
uv run python -m jev_sc2.campaign campaigns/opening.json \
  --state runs/campaign-lab069/progress.json --resume-current --follow-camera \
  --seconds-per-attempt 1800 --call-budget 6000 --max-attempts 4
```

See [the progression journal](docs/CAMPAIGN_PROGRESS.md) and the experiment report
for what is working, what failed, and what remains for future campaign work.

## Autonomous mission sequencing

With SC2 already running in API mode:

```sh
uv run python -m jev_sc2.campaign campaigns/opening.json --follow-camera --call-budget 3000
```

The initial manifest contains three verified-loadable opening missions and the
prepared Smash and Grab map (not yet loaded); it is
not the full campaign inventory. The runner uses the same general player for each
mission, retries confirmed defeats, and advances only on its own player's API
Victory. It saves durable progress under `runs/campaign/progress.json`; rerunning
the same manifest skips verified completed missions. The call budget is shared
across the invocation, and retries are bounded. Timeouts, missing maps, ambiguous
results, and UI stalls stop with a recorded reason instead of inventing a result.

The manifest contains scenario inputs (map, race and primary objective), never
build orders, tactical locations or routes. General policy changes still reload
on commit during a mission. Later-campaign mission inventory, entitlement,
scenario dependencies, full ability coverage and unattended UI recovery remain
unfinished. Sequence completion means only the explicitly listed missions.

The active evaluation checkpoint is `runs/campaign-lab069/progress.json`. To resume
that sequence after its process exits, use the same `--state` path. Its verified
Liberation Day and Outlaws wins are preserved; failures in Zero Hour do not
return to the opening. Appending missions preserves the completed prefix when those completed
scenario definitions are unchanged.

Use `--resume-current` with that checkpoint after a budget/time stop to retain the
running mission and army. It checks SC2's reported map path before submitting any
orders or accepting a result. A continuation is recorded separately and does not
consume a new-attempt slot. Omitting the flag starts a fresh attempt at the pending
mission; completed missions stay skipped.

For bounded unattended recovery, `--retry-stalls` permits restarting the same
pending mission after the harness reports a stalled game clock. The attempt
remains recorded as incomplete/unknown; this does not establish defeat or victory.
Existing call and attempt caps still apply, and prior wins remain preserved.
Budget stops and other unknown failures do not trigger this recovery. A genuinely
paused mission can also meet the clock-stall condition, so this mode is opt-in.
