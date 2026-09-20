# Lab547: retain separate own collection and spending deltas

Trial545 visibly sustained repairs with almost no minerals while gas accumulated.
The model already saw estimated collection rates, net resource changes, individual
worker orders and repair opportunity-cost wording. Do not claim it lacked all
resource tradeoff information. However, recent_outcomes discarded the separate
own collected/spent counters already extracted by view.player_score_telemetry.

Retain only collected_minerals, collected_vespene, spent_minerals and spent_vespene
in the existing bounded observation history. Report endpoint differences only
when both values exist and the counter did not decrease. Old hot-reload history
without counters yields omitted values until a valid window exists. Never expose
kill/damage score fields through this change. No extra API or Jev requests.

Label these API counter deltas, not repair costs. Refunds, mission effects and
counter semantics can prevent reconciliation with balances. This supplies a
general resource-flow observation without recommending allocation or actions.
Live nonempty counter coverage and gameplay benefit still require verification.

94 focused/infrastructure tests pass, including missing/reset counters and old
history, plus equal collected/spent changes despite unchanged net balances.
Next trial retains trial545 settings and tests only this added history field.
