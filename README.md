# Jev plays StarCraft II

An experiment in fast, probabilistic decisions. Jev chooses actions; Python handles
observations, geometry, validation, transport and logging. No other inference model
participates in the game loop. This is an experimental player, not a complete campaign bot.

Read [the experiment report](docs/EXPERIMENT_REPORT.md) for measured
results and failed approaches. The [progression journal](docs/CAMPAIGN_PROGRESS.md)
contains the latest experiments and current limitations.

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
that the full campaign has been completed; verified mission outcomes are listed below.

## First campaign mission

The installed first Liberty mission can be repackaged and played through the API;
follow [the extraction instructions](docs/CAMPAIGN.md), then run:

```sh
uv run python -m jev_sc2 --attach --map maps/traynor01.SC2Map --follow-camera \
  --objective 'Destroy the Logistics Headquarters. Raynor must survive.'
```

Omit `--map` to resume the running mission. Liberation Day has a fresh **UI-verified
victory at 3:44**, using the objective compatibility adapter (lab169). The Outlaws
also has a fresh **UI-verified victory at 27:57** (lab183). Earlier API-only results
remain unreliable: an isolated test proved that
completing or failing a bonus objective can report victory or defeat for every
player and terminate API control while the main objective remains active. Zero
Hour remains uncompleted after eighteen fresh attempts. The progression journal
preserves the evidence and diagnostic experiments. All three campaigns remain
the target; no campaign is complete. Native research/unlock persistence is not
implemented.

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
that sequence after its process exits, use the same `--state` path. Liberation Day
and The Outlaws are now independently verified; their review gate is cleared. Historical
attempts are preserved; failures in Zero Hour do not
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

## Spending governor

All requests through `jev_sc2.jev.Jev` share a persistent five-minute dollar ledger
at `runs/jev-spend.sqlite3`, including offline probes and recursive request splits.
Concurrent requests reserve an estimated cost before dispatch; successful replies
replace that reservation with reported actual cost. Unknown/cancelled/failed replies
retain their reservation for five minutes. This is a **soft** cap: the provider bills
after dispatch, so an unexpectedly expensive response can exceed its reservation.
The ledger then blocks further dispatch until room returns. This is not an
OpenRouter account-wide cap and cannot limit other applications or direct SDK calls.

Default allowance: `JEV_USD_PER_5_MIN=0.10` ($1.20/hour at a sustained rate).
An optional `runs/jev-budget.json` overrides it and is reread on each admission:

```json
{
  "start_usd_per_5_min": 0.42,
  "target_usd_per_5_min": 0.10,
  "ramp_seconds": 10800,
  "started_at": 1789840000
}
```

`started_at` is the actual Unix timestamp when the taper starts; do not copy this
example timestamp for a new taper. The allowance interpolates linearly, then stays
at the target. Restarting the controller does not reset the clock or spending.
Use equal start/target values for a constant allowance. Malformed settings fail
closed. The active experiment's settings live in that ignored local JSON file.

The harness paces new decision cycles according to measured decision cost and
60% of the current allowance, leaving headroom for concurrent request reservations
and variable decision costs. This reduces planned decision frequency; it does not
guarantee admission. Planned pacing is explicit in `spend_pacing`: target interval,
requested interval and planned idle seconds. Reports expose median/maximum target
interval and total planned idle time; these are not measures of tactical success.

A denied request is a **controller error**, not a deferred decision. The harness
emits `budget_error` to stderr and the event log, discards the partial decision,
saves its replay/result, and exits with status 2. It does not automatically retry.
SC2 stays running with existing orders, so this is not a game pause. Fix request
rate before reconnecting; never raise/reset the allowance to hide a failure.
Reports include budget errors alongside other errors. No paid fallback is used.


## Bounded production jobs

Jev can choose a three-request training commitment lasting up to 2016 game loops.
With the production executor enabled, Jev also chooses the initial producer. The
same producer and training command remain fixed for that job. The initial command
must be accepted before the remaining requests can execute between paid decisions.
Execution makes no extra model calls and does not reset or increase the dollar limit.

Requests are at least 112 game loops apart and require the exact command to remain
advertised, with sufficient observed resources and supply. A fresh observation
still checks ownership and command age. Unavailable or unaffordable commands wait
within the original deadline. The framework never picks another producer or unit
type. Rejected or stale submissions cancel the job without automatic retry.
Producer disappearance, deadline, clock rewind, changed strategy, or exhausted
attempts also end it. Requests are attempts, not guaranteed completed units.

Inspect `production_job_armed`, `production_job_request`,
`production_job_execution`, `production_job_wait`, and `production_job_released`
in the run's `events.jsonl`. The framework executor lives in `jev_sc2/jobs.py`;
changes to it or the controller require a controller restart. Player decisions
still reload on commits. Older controller processes keep the previous batching
semantics rather than silently acquiring a new execution mode.
