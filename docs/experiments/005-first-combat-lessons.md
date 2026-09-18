# First real combat trials

All trials used official Blizzard MarineMicro, real time, fog enabled, ten Marines,
Jev 1.13 through OpenRouter, and an opponent slot. Full replays and decision logs
remain local under runs/. Summaries alongside this document are public.

| Variant | First zero-unit loop | Calls | Median Jev latency | Cost | Movement choices |
| --- | ---: | ---: | ---: | ---: | ---: |
| Shared state / numeric unit tags | 198 | 16 | 446 ms | $0.005905 | 0 |
| Unit facts inside each question | 204 | 16 | 404.5 ms | $0.005487 | 0 |
| Explicit distance consequences | 190 | 15 | 450 ms | $0.005818 | 5 |

These are single trials, not statistical comparisons. Every run lost all Marines;
this reference map did not emit a terminal defeat result. No win is claimed.
The score in the protocol is not a reliable standalone measure of combat quality.

Question-local facts did not remove the preference for keeping current orders.
Spelling out geometric consequences elicited movement but did not improve survival.
This matches the earlier synthetic lesson: do not expect the model to infer useful
spatial implications reliably from numeric offsets. Clearer inputs alone do not
supply the tactical understanding needed to survive a swarm.

Next candidates: supply public unit mechanics (range, speed, weapon timing) and
compare narrow tactical questions with direct action selection. Every action must
remain Jev-selected; no hand-coded retreat or attack fallback. Improve outcome
telemetry before making claims about kills or damage.

Infrastructure verified: API connection through Battle.net, map bytes transport,
real-time player observations, engine acceptance, saved replays, and a new committed
player revision loaded in the first match without restarting SC2. The Mac editor
fails video initialization; stock campaign map access is a separate investigation.

## Campaign navigation: the dog trap

The repackaged first campaign mission loaded. The initial objective-free trial
survived, but a trial with the visible objectives (destroy Logistics Headquarters,
Raynor must survive) chose the same neutral target 263 times. A five-second history
with displacement and last four choices still chose it 246 times. The target was
a neutral **Dog**, confirmed from live unit data. These were 120-call trials,
costing $0.011806 and $0.013281 respectively, with six units remaining alive.

This is a specific failure of objective-directed navigation, not transport or
command legality: the commands succeeded, but did not pursue the objective.
More local facts and recent history did not overcome the salient nearby object.
Next test: a separate Jev decision for squad navigation intent, then Jev decisions
for unit actions. Do not implement a fixed route or an automatic unstuck policy.
