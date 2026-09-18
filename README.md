# Jev plays StarCraft II

An experiment in fast, probabilistic decisions. Jev chooses actions; Python handles
observations, geometry, validation, transport and logging. No other inference model
participates in the game loop. This is an early combat prototype, not a complete bot.

## Run

1. Install StarCraft II using Battle.net and launch it once to finish downloading data.
2. `uv sync` and put `OPENROUTER_API_KEY` in `.env` (see `.env.example`).
3. `uv run python -m jev_sc2 --doctor`
4. Provide a local single-player `.SC2Map`:
   `uv run python -m jev_sc2 --map /absolute/path/mission.SC2Map`
   Add `--opponent` only for a melee map requiring a computer opponent.
5. To reuse an API-enabled game: `uv run python -m jev_sc2 --attach`.
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

`uv run pytest -q` checks committed-source reload and command/visibility boundaries.

See [the researched procedure and limits](docs/PROCEDURE.md). Nothing here claims
that stock campaign progression or combat performance has already been validated.
