# Jev plays StarCraft II: first session

The infrastructure works. Jev makes real-time decisions in a retail SC2 campaign
mission, through the ordinary player API, while the game appears on a live stream.
The policy has not won the mission. Its most persistent difficulty is converting
local actions into sustained objective progress.

## What ran

Jev 1.13 via OpenRouter Decisions; SC2 5.0.16.97563 on Apple Silicon through Rosetta.
Battle.net launches the game with the API enabled. Python attaches, supplies map
bytes, joins as a player, filters observations, constructs legal action candidates,
and submits only Jev-derived commands. Fog stays enabled; no debug commands or
hidden enemy observations are used. Raw control is information-fair, but bypasses
human mouse/selection mechanics. See [the procedure](PROCEDURE.md).

Two scenarios ran: Blizzard's MarineMicro and the installed first Liberty campaign
mission, repackaged without changing its base/English components. The latter is a
standalone mission, not a verified recreation of campaign progression.

## Experiments and measured lessons

| Change | Observation | Limit of the evidence |
| --- | --- | --- |
| Move per-unit facts into each question | Marines still stayed largely stationary and all died | One trial per variant; not a statistical comparison |
| Describe movement's distance consequences | Movement appeared, but survival did not improve | Useful action selection is more than geometric clarity |
| Supply campaign objective and recent local history | Repeated approaches to a neutral dog persisted | Correct objective text did not overcome local salience |
| Split squad intent from individual actions | Dog-following stopped; northward movement stalled | Hierarchy changed behavior without solving navigation |
| Add measured displacement history | Jev eventually changed direction | Longer trial crossed the same corridor repeatedly |
| Add visited-area counts | A different route emerged | Units spread apart; centroid movement hid separation |
| Offer regroup intent and friendly-unit movement | Local friendly approaches occurred; squad intent never selected regroup | Ended with Raynor and two wounded Marines; no victory |
| Sample navigation probabilities | Implemented with recorded seed and weights | **Untested:** account credit exhaustion prevented inference |

Successful calls in these live trials had per-run median latency between 355 and
450 ms. These are measured run medians, not a service guarantee. Two-stage decisions
add latency; stale observations are rejected. The successful-call limit initially
overshot by one in the 300-call trial; it now checks before every inference, with a
regression test. Billing errors stop immediately and preserve a replay.

The individual run summaries are in [experiments/](experiments/), and `git log`
contains the hypotheses, outcomes and next steps. Full decision distributions,
observations and replays remain local under `runs/`.

## Interpretation

The current evidence supports using Jev for bounded choices with explicit facts.
It does not support assuming reliable spatial reasoning, navigation memory,
coordination, or tactical survival merely because decisions are fast. Repeatedly
adding prompt detail sometimes changes actions, but does not reliably improve the
mission outcome. The distinction matters: accepted commands, distance traveled,
and units still alive are separate measurements from completing an objective.

These experiments are sequential and mostly resume an evolving mission. They are
not controlled A/B trials. Policy memory survives commit reloads but resets when
the harness restarts. SC2 continues in real time during those gaps; a unit can die
between trials. Later policies therefore inherit different positions and damage.
No causal ranking of policies or generalized claim about Jev's limits is justified.

The next trial is probability sampling of squad intent. All weights come from Jev;
there is no scripted route or uniform-random escape policy. If it runs, measure
whether it explores new areas, preserves Raynor, and avoids repeated routes. A
single lucky movement is not enough to call it an improvement.

## Remaining work

- Fund the OpenRouter account to resume inference; the dedicated key cap is separate.
- Evaluate the committed sampling policy and compare fresh mission runs if useful.
- Improve the observation/action representation based on measured failures, while
  keeping every tactical choice with Jev.
- Mission victory, build/train mechanics, and full campaign progression remain
  unachieved. Research, armory and unlock state are not implemented.

The public stream was verified with the API-controlled game and conversation
visible together, plus SC2 application audio. Microphone and webcam toggles remain
under user control. See [stream controls](STREAMING.md).
