# Lab 590: restore recent verified attempt history

Found a schema mismatch: episodes.py required ui_verification.result, while recent
independent native-screen reconciliations record ui_verification.outcome with
uppercase DEFEAT/VICTORY. Thus these runs were omitted even on the same filename.

Reader now accepts either explicit recorded UI label, requires agreement with
terminal result status, and rejects conflicting labels when both exist. It still
requires a fresh joined/restarted full episode and early tick evidence. It does
not infer UI verification from instrumentation or add any new victory credit.

Ten history tests passed, including native-screen schema and conflicting labels.
Read-only audit of real runs now loads three context-adapter attempts with observed
loop spans46–21849,47–16530,48–19987 and one dialogue-adapter attempt50–4083.
Previous policy comparisons cannot assume these recent summaries were supplied.
The filename boundary remains; provenance-based cross-adapter matching is pending.
No model calls, game restart, or gameplay directives in this change.
