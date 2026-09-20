# Jev plays StarCraft II: experiment report

The infrastructure works. Jev makes real-time decisions in a retail SC2 campaign
mission, through the ordinary player API, while the game appears on a live stream.
**Liberation Day and The Outlaws are verified won.** As of lab284, the checkpoint
contains 25 independently UI-verified Zero Hour defeats. The current trial tests
delayed engine-error feedback. The most
persistent difficulty is converting local choices into coordinated, sustained
objective progress. Earlier sections below retain the unsuccessful trials; the
latest results appear at the end.

## Current evidence through lab284

The latest completed Zero Hour attempt survived15:46 and cost$0.128141286 for
206 successful calls. It lost all structures with04:23 remaining. Jev selected
672-loop strategic review intervals:16 strategic reviews across34 tactical ticks,
costing$0.007608174. This validates less frequent strategic review, not a causal
survival improvement. Recent comparable attempts varied from10:03 to14:53.

The spending governor remains$0.10 per rolling five minutes, with pacing targeting
60% of that allowance and loud termination if admission exceeds the cap. This
keeps spending bounded but creates a slower control regime than model latency
alone suggests. In the latest completed run, median decision spacing was487
game loops;30 of33 gaps exceeded the224-loop contribution commitment. Most
retained worker roles therefore expired before the next decision. Extending actual
commitment duration is a distinct, still-untested hypothesis from the earlier
failed prompt-only evaluation-horizon probe.

Native screenshots showed a dwindling army, intermittent mining and spending on
additional structures without maintaining a surviving force. Successful commands
are not proof of useful allocation. Background execution of Jev-selected training
batches has been verified, but it has not solved the mission.

Lab283 corrects a separate feedback omission: asynchronous engine execution
failures now reach Jev alongside immediate acknowledgments. The new live trial
has that harness change; its benefit is unproven. No policy change forces worker
allocation, purchases, bunker loading or routes. The sections below preserve
earlier experimental observations and must not be read as current trial counts.

## What ran

Jev 1.13 via OpenRouter Decisions; SC2 5.0.16.97563 on Apple Silicon through Rosetta.
Battle.net launches the game with the API enabled. Python attaches, supplies map
bytes, joins as a player, filters observations, constructs legal action candidates,
and submits only Jev-derived commands. Fog stays enabled; no debug commands or
hidden enemy observations are used. Raw control is information-fair, but bypasses
human mouse/selection mechanics. See [the procedure](PROCEDURE.md).

The scenarios include Blizzard's MarineMicro and installed Liberty campaign
missions, repackaged without changing their base/English components. The first three Liberty missions have loaded through the API. These are standalone missions,
not a verified recreation of campaign progression.

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
| Name a regroup anchor | Four surviving units ended close together with unchanged health | Sequential trial; no victory |
| Offer stop and hold commands | Jev selected both; the engine accepted them | Fixes an action-interface gap, not a demonstrated strategy improvement |
| Explain building costs and supply effects | Jev built a depot; capacity rose 19 to 27 | Multiple depots in progress suggest overproduction risk |
| Sample navigation probabilities | Initial run selected regroup and moved north; sustained run lost Raynor | Runs 015–016; UI-confirmed defeat, despite missing protocol result |

Successful calls in these live trials had per-run median latency between 353 and
450 ms in the small combat/navigation batches. Economic batches approached one
second median and produced more stale observations and occasional timeouts. These are measured run medians, not a service guarantee. Two-stage decisions
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

The policy uses probability sampling of squad intent. All weights come from Jev;
there is no scripted route or uniform-random escape policy. Measure
whether it explores new areas, preserves Raynor, and avoids repeated routes. A
single lucky movement is not enough to call it an improvement. The sustained
follow-up did end in defeat. A fresh-mission trial now adds nearby static terrain
labels, masked by current player visibility; it does not compute a route.

## Remaining work

- Keep inference within the dedicated key cap; account credit availability is separate.
- Evaluate sustained sampling behavior and compare fresh mission runs if useful.
- Improve the observation/action representation based on measured failures, while
  keeping every tactical choice with Jev.
- Full campaign progression remains unachieved. Liberation Day and The Outlaws are won. Training,
  mineral gathering and visible engine-checked building sites are available;
  research, armory and unlock state are not implemented.

The public stream was verified with the API-controlled game and conversation
visible together, plus SC2 application audio. Microphone and webcam toggles remain
under user control. See [stream controls](STREAMING.md).

## Request latency versus attention frequency

The six-unit round-robin trial (024) reduced per-call median latency to 488 ms,
compared with 996.5 ms in the earlier full economic batch trial (022). One tick was
older than 32 loops, versus sixteen in the earlier trial. These are sequential
runs with different unit populations, not a controlled benchmark.

The cost is per-unit attention: 31 distinct units were scheduled, with median
79 game loops between scheduling events and maximum 119. Those are attempted
updates, not a guarantee of successful commands. Smaller requests alone do not
provide fast reactions for every unit. Concurrent small batches are a possible
next experiment, but would need a strict shared call budget and measured cost.

The trial ended with 14 SCVs, 11 Marines, five Supply Depots, a Barracks and a
Command Center. No new building choice was made in that trial. More owned units
and better inference latency do not establish progress toward destroying the base.

The follow-up (025) used two concurrent six-unit requests per boundary. It recorded
497 ms median call latency, 705 ms median complete decision-cycle latency, and
45-loop median / 84-loop maximum scheduling gaps across 33 distinct units. Two
ticks exceeded the age limit. The shared reservation guard kept the run at exactly
150 calls; eleven tests include overlapping requests at a one-call cap.

The run cost $0.123215 for 834 unit answers, including navigation overhead. The
sequential trial cost $0.070643 for 528 unit answers. Normalized with that overhead,
these are about $0.148 versus $0.134 per thousand unit answers. Different game
states and request counts prevent a controlled cost comparison. Parallelism reduced
observed attention gaps; it did not establish better tactics or a mission victory.


## Campaign results through labs 059–061

Liberation Day ended in an API-confirmed Victory at loop 3512. The successful fresh
attempt made 190 Jev calls ($0.044435) before a cinematic temporarily hid the army.
A persistent Jev-selected shared attack-move continued and finished the mission.
The harness subsequently read the actual result and saved a replay. This is one
verified win, not a repeatability claim. The injured-force attempt before it lost
Raynor near the Headquarters.

Exposing fog snapshots supplied the Headquarters' last-known location without
manual coordinates. Shared force orders reduced the fragmentation seen with
independent per-unit decisions. Neither change alone was isolated experimentally.

The Outlaws adds an economy, and exposed several failures and interface omissions:

- Whole-force actions fit combat squads poorly once structures and workers appear.
  Type selections restored separate control, but Jev repeatedly sent workers into
  combat and lost the base.
- Contribution-before-action questions kept workers mining in subsequent trials.
  Distant visible mineral targets and legal single-builder options had previously
  been missing from the interface; those failures cannot fairly be blamed on Jev.
- Supply effects must reach the decision stage that chooses construction. Moving
  them into contribution facts led to additional completed Depots.
- The combined labs 059–060 continuation used 676 calls ($0.341030), grew to four
  Depots and about forty SCVs, but never built a sustained army or won. A rolling
  observation history exposed replacements and losses; changing strategic labels
  did not establish better execution.
- Lab 061 now tests a shared Jev investment choice rather than independent spending
  choices for each unit type. Outcome is pending; passing tests verify routing and
  control boundaries, not strategic competence.

These trials resume evolving games. Resource accumulation while the harness is
stopped, policy-memory resets on restart, and prior losses confound comparisons.
The public summary files and progression journal preserve those qualifications.


## Findings through lab 092

Two verified wins do not demonstrate a general campaign player. Zero Hour's three
losses at 12:22, 12:25 and 9:44 expose sustained resource/force-management failures.
The API returned no player_result for these losses; the actual defeat screens
were inspected and recorded separately. No ambiguous timeout is counted as defeat
or victory without supporting evidence.

| Experiment | Observed result | Practical limit |
| --- | --- | --- |
| Rename `hold` to `continue_operations`, same description/state | Three paired queries switched top choice from hold to protect | Choice keys affect answers; no demonstrated survival gain. [Data](experiments/058-choice-label-probe.json) |
| Reveal support capability before selecting its category | Bunker category changed from continue to other; actual passengers later observed | Sequential observation, not a controlled comparison. Missing controls must not be blamed on Jev. [Data](experiments/055-live-support-affordances.json) |
| Compact strategic/contribution context | Stale ticks fell from 28/73 to 4/50; median cycles 1281ms to 1015.5ms | Evolving force sizes confound comparison; economy still failed. [Data](experiments/059-compact-control-context.json) |
| Remove global strategy hint | No top-choice change in three pairs | Does not support deleting the hierarchy. [Data](experiments/061-strategy-hint-probe.json) |
| Add longer evaluation horizon | No top-choice change in three pairs | Generic planning language did not solve these states. [Data](experiments/062-contribution-horizon-probe.json) |
| Describe observed harvesting capability in the unit label | Income probabilities increased, top choices unchanged | A distribution shift is not demonstrated successful work. [Data](experiments/063-capability-label-probe.json) |

The current experiment samples Jev's offered contribution probabilities and
retains each contribution for at most 224 game loops. Concrete orders still come
from Jev. The fourth Zero Hour attempt is the first to use that policy from the
start; keep it unchanged for evaluation. It is not a scripted worker allocation.

The harness now exposes support actions, own income estimates, harvester counts,
cargo/passengers, and named engine rejection feedback. A repair request accepted
by the model is not necessarily affordable; an engine-accepted request is not
necessarily completed. UI defeat recovery remains supervised, cross-mission
upgrade/research state is missing, later campaigns remain unverified, and many
abilities are still absent. These are harness limitations, distinct from the
model's measured choice behavior.

Player, observation adapter and camera reload together from commits. Live logs
verified adapter changes without a reconnect. A separate presentation director
frames local visible action; it never selects unit orders. Source commits remain
the experiment journal, with full per-mission history in
[CAMPAIGN_PROGRESS.md](CAMPAIGN_PROGRESS.md).
