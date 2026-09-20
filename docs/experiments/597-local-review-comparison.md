# Lab 597: fewer worker questions did not accelerate combat reviews

Compared the opening observations through game loop 1800 in trials 592 and 596.

| Measurement | Trial 592 | Trial 596 |
| --- | ---: | ---: |
| Requests | 31 | 31 |
| Accounted cost | $0.021422436 | $0.020968920 |
| Mean combat review gap (loops) | 411 | 413 |

Combat review loops were 46, 499, 764, 1404, 1690 versus 53, 504, 780, 1435, 1705. Skipping individual questions inside batches has not reduced the request count or accelerated combat reviews in this opening window. The approximately 2.1% cost difference is observational, not evidence of a causal benefit.

Native visual check of trial 596 at 7:35: Zerg surround the burning Command Center, selected health 144/1500; workers are gathering near the mineral line; 1196 minerals, zero gas, supply 5/11, relics 0/4. This is a live observation, not a verified mission outcome. No manual gameplay orders were issued.

Next scheduling work needs to measure whole-request frequency and elapsed time between consequential reviews, rather than counting omitted questions as saved requests.
