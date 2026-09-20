# Player-visible mission context adapter

Audit lab328: the ordinary SC2 observation protocol does not expose structured
campaign objectives or timer-window contents. `Observation` contains game_loop,
player_common, alerts, abilities, score, raw_data, feature_layer_data, render_data,
and ui_data. `ObservationUI` contains groups, single, multi, cargo, production.
Confirmed against installed protobuf descriptors and Blizzard's source:

- https://github.com/Blizzard/s2client-proto/blob/master/s2clientprotocol/sc2api.proto
- https://github.com/Blizzard/s2client-proto/blob/master/s2clientprotocol/ui.proto

Do not derive a mission countdown from an assumed loop-to-second conversion or
read arbitrary campaign timers. A mission can pause, restart, or replace a timer.
The intended scope is information a player can see, not future scripted events.

## Implementable path, not yet verified

Installed Blizzard Galaxy natives provide TimerWindowCreate(timer, text title,
bool show, bool showElapsed), TimerWindowVisible(window, player), TimerGetRemaining,
TimerGetElapsed, TimerIsPaused, and BankValueSetFromText. There are also native
mutators TimerWindowDestroy, TimerWindowSetTimer, TimerWindowSetTitle, and
TimerWindowSetStyle (which can change showElapsed).

A general wrapper can retain the association between a timer window and its timer,
title, and elapsed/remaining mode while forwarding every native call unchanged.
Only export a value when TimerWindowVisible(window, controlledPlayer) is true.
Check native visibility each export; do not infer it merely from creation flags.
Destroyed windows must be removed; set-timer/title/style must update tracked data.
Track window IDs explicitly rather than assuming contiguous IDs or fixed bounds.
Do not write hidden timer values to the model-facing bank or logs. Unknown/untracked
windows remain unavailable rather than producing guessed state.

Use a dedicated bank and per-launch identity/freshness marker, following the
existing outcome bridge's stale-bank protections. Serialize title as text through
the native bank API; validate the resulting XML representation before consuming it.
Export the displayed mode's time only. Timer format/rounding and negative values
need native screen comparison; numerical timer values are not yet proven identical
to the visible rounded countdown. Custom dialog-based timers are outside this
initial adapter and must not be falsely reported as supported.

## Acceptance evidence required

1. Source rewriting preserves native declarations, comments, strings, and unrelated
   logic, with complete include closure and explicit wrapper injection.
2. A controlled visible/hidden timer fixture verifies visibility filtering, elapsed
   versus remaining mode, pause, replacement, title/style changes, and destruction.
3. A real mission's exported title/value agrees with periodic native screenshots.
4. Freshness rejects prior launches and clock rewinds; missing data stays explicit.
5. Only validated player-visible context reaches all relevant Jev decision stages.

No timer adapter has been deployed by this audit. This is a concrete next
implementation path, not evidence of campaign objective awareness or improved play.
