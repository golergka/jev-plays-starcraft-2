# Jev plays StarCraft II

An experiment in fast, probabilistic decisions. Jev chooses actions; Python handles
observations, geometry, validation, transport and logging. No other inference model
participates in the game loop. This is an early combat prototype, not a complete bot.

Read [the first-session experiment report](docs/EXPERIMENT_REPORT.md) for measured
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
`runs/` and stay out of Git. The dedicated local OpenRouter key has a $5 total cap.

## Live experiments

Edit **player.py**, then commit. The orchestrator loads the source from the new Git
commit at the next decision boundary while keeping the socket and `memory` dict.
Uncommitted edits do not run. A syntax/import error retains the previous policy.
Changes to harness modules require restarting the harness and using `--attach`.

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
accepted Jev commands; it has not yet produced a mission victory. Stock campaign
progression, research and unlocks are not implemented.

The policy now asks Jev for a squad intent periodically, then asks Jev for each
unit's action. In the first trial this stopped repeated dog-following but produced
a northward movement plateau. Accepted commands are not evidence of useful motion.
Reports include squad centers, navigation choices and engine action-result codes;
the commit journal records hypotheses and outcomes.
