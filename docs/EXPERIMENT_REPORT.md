# Jev plays StarCraft II: experiment report

The infrastructure works. Jev makes real-time decisions in a retail SC2 campaign
mission, through the ordinary player API, while the game appears on a live stream.
**Liberation Day, The Outlaws and Zero Hour are verified won.** Zero Hour's
native victory screen reports 20:12, after 42 independently UI-verified defeats.
The winning run cost $0.192928932 for 261 successful Jev requests. No later
mission is verified won; all three campaigns remain incomplete.

## Current evidence through lab386; trial387 running

Smash and Grab has three independently verified defeats:

| Trial | Native mission time | Relics | Successful requests | Request cost |
| --- | --- | --- | --- | --- |
| 376/378 | 7:50 | 2/4 | 114 | $0.068998482 |
| 381 | 13:16 | 0/4 | 177 | $0.116499978 |
| 383 | 19:22 | 0/4 | 242 | $0.155562708 |

The longer attempts sustained workers, construction and repairs without restoring
an effective army or completing the primary objective. Survival time is not a
success metric for this mission. Trial383 also had an initial upstream 503;
its first completed decision was at loop1307, limiting causal comparison.

The adapter missed the campaign ability name MedicHeal. That was corrected, and
trial381 delivered a healing choice to Jev, which proposed it once. Historical
logs could not identify whether that specific proposal survived validation.
New logs record actual submitted commands and individual engine results;
trial383 submitted no MedicHeal commands. Native autocast remains unmeasured.
API acceptance does not prove completion, and aggregate healing can include repairs.

Capability descriptions now distinguish attack-order availability from catalog
weapons. Generic support choices expose observed target distance and explicitly
available cast range. These are interface corrections, not demonstrated gameplay
improvements. Autocast toggling exists in the protocol, but raw unit observations
do not expose its current state; no blind toggle was introduced.

Two small paired probes were negative: primary/bonus wording in tactical menus
did not establish better pursuit ($0.004431168), and recent own-player score
deltas did not establish better investment ($0.002888340). Neither was deployed.
The strategic menu previously described its offensive option solely as destroying
the enemy base. Adding a general primary-objective pursuit option changed all
three sampled strategic choices ($0.002523990). Trial387 is testing that option,
alongside the support geometry and grouping-description changes. Its outcome and
any improvement remain unverified; it cannot isolate a single causal factor.

The rolling $0.10/five-minute cap remains unchanged. Listed costs are successful
requests for those runs/probes, not total account spending or conservative pending
reservations. The first three missions remain the only verified victories.

## Zero Hour evidence through lab375 (historical)

The winning trial supplied observed decision cadence to strategic requests, kept
full combat menus, and loaded three prior same-map attempts. Jev chose 672-loop
role commitments in all 22 strategic reviews; 20 received measured cadence.
Median paced decision interval was 25.62 seconds. One late token-limit decision
error occurred; the controller recovered and continued to the verified victory.
No root tactical orders or policy changes were made during the attempt.

This is a verified outcome, not causal evidence that timing context caused the
win. The army dwindled, many structures were lost, and thousands of minerals
remained unspent. The native summary reports 307 enemies killed, 33 units lost,
26 structures salvaged or lost, and no rebel squads rescued. Combat coordination
and investment remain weak even though this attempt survived evacuation.

A three-state paired probe measured 54.88% lower combat-menu costs for one full
Choice request versus a complete tournament. Full-menu-first is now the default,
with explicit token-limit fallback. Whole-run costs and cadence did not improve
in the first live trial of that change. A separate $0.003657108 cadence probe
changed review intervals in recorded states; its live benefit remains unisolated.

The next configured mission is Smash and Grab. Campaign progression beyond these
standalone missions, between-mission choices and all-three-campaign completion
remain unverified. The rolling $0.10/five-minute cap is unchanged.

## Evidence recorded through lab366 (historical)

The persistent difficulty is converting local choices into coordinated, sustained
objective progress. Native screenshots show the army gathering near one Command
Center while other structures are attacked. Native checks in trial344 showed fighting near the Command Center, then
enemies in the mineral line and eventual destruction of every structure. Legal actions and an abstract
“protect” decision do not establish effective defense.

Independent descriptive Score ratings changed investment preferences relative to
Choice, but their live trial lost at 8:56. Jev selected Bunkers 14 times; five new
Bunkers were observed complete, with only zero to two occupied cargo slots across
sampled investment states. These are not calibrated utilities or win probabilities.
Adding all competing investment descriptions made the rating probe prefer waiting
in three states. Neither result demonstrates improved play.

Three requested boarding jobs were confirmed by exact passenger/carrier tags in
later observations. Three others remained unconfirmed; missing evidence does not
prove failure or death. Unload choices now name their observed passengers. 
Trial321 exercised that wording twice and still lost. There is no evidence
that the wording improves outcomes.

Full combat menus, explicit ordinary-Move semantics, and choosing order kind
before destination did not resolve the repeated safe-anchor preference in small
recorded-state probes. These negative results do not prove that all formulations
fail or that Jev cannot play the mission. They do argue against repeating those
same hypotheses without new evidence.

A Jev-selected three-Marine training batch produced three newly observed completed
Marine tags in trial298. Low-level utilities can execute Jev commitments between
paid decisions; no policy forces a build order, worker allocation, bunker loading,
or movement route. Exact loop deadlines avoid unverified seconds conversions.
The current decision objective is “Complete the player-visible mission objectives.”
Native visible objective names, descriptions, primary/bonus flags and lifecycle
states now accompany the visible countdown. Hidden objectives are excluded before
their text is read. A native fixture verified creation, visibility, state changes,
destruction and stale-section cleanup; trial358 verified delivery in a real mission.
205 of its 213 requests contained objectives, including 40 containing the failed
bonus objective. It still lost at 15:49. No hidden wave schedule is supplied.

Trial365 adds a bounded startup wait for objective initialization and explicit
controlled-unit identities. The startup gate opened after about five seconds;
the first 19 successful requests all followed it and carried member identities.
This verifies delivery, not improved reasoning. Trial365 remains in progress.

The spending governor remains $0.10 per rolling five minutes, with pacing targeting
60% of that allowance and loud termination if admission exceeds the cap. The 40 verified-defeat
result files total $7.487440506 in recorded request costs. This excludes other
runs, wins, probes and unresolved billing; it is not an account balance or lifetime
total. Model latency alone does not describe the budget-constrained control rate.
In a partial trial365 audit, Marine-only requests consumed $0.030827454 of
$0.095639670, about 32%; large combat menus use a three-request tournament.
Recent cycles were paced about 29 seconds apart. A bounded paired cost comparison
is prepared but not yet run; full-menu savings have not been established.

A separate combat-kind Score trial (344) also lost. Its 25 rating requests cost
$0.019556208, 17.7% of the trial total. They selected Move 15 times, Hold 9 times,
and individual control once; never Attack or Attack-move. Median winning margin
was 0.12, not a confidence measure. It remains opt-in, not the default policy.

Three elementary explicit-outcome controls passed with both Choice and Score.
That rules out a blanket inability to select Attack in those simple cases, but
says little about inferring consequences in SC2. Adding observed type-distance
tables did not change the highest-rated kind in three recorded states. Desired
force-count questions matched existing counts, even zero Marines after the force
was gone. Neither probe was deployed as gameplay policy.

Lab350 fixed an actual episode-memory bug: verified API restarts emitted a
different event from fresh map joins and were excluded from history. Trial350
loaded two verified attempts on its exact map, and all 40 relevant requests
contained those histories. It lost at 14:39. Trial358 used a newly instrumented map
filename and therefore loaded no exact-map history; trial365 loads one verified
attempt on that map. Delivery is established; learning or better play is not.

Unseen delayed execution errors remain in a bounded 32-entry queue until first
included in context. Trial318's invalid-placement error at loop8087 appeared in a
subsequent investment request, exercising the feedback path live. Context inclusion
does not prove that Jev responded effectively.

The integrated same-socket restart is live-verified: reset to loop0, native window
retained, and eventual ending markers checked against the actual defeat screen.
Only the first two missions are verified wins. Full campaign progression,
between-mission choices, and all-three-campaign completion remain unverified.
Earlier sections below preserve historical observations and may describe older
revisions. The lab journal records the successive changes and negative results.

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
