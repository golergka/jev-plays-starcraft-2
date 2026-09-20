# Lab 579: synthetic transmission probe prepared

`scripts/transmission_timing_probe.galaxy` replaces the mission script only in
ignored local `maps/transmission-timing-lab579.SC2Map`. It sends two synthetic
player-one messages and one player-two message, clears the second message after
two seconds, and records per-player activity/completion flags plus the native
active-conversation-sound getter every half second. No campaign gameplay or
model calls; never credit this map as a mission result.

Native signatures checked against installed natives.galaxy. Archive packaging
succeeded (1,739,601 bytes). Compilation, empty-sound subtitle behavior, portrait
zero behavior, queuing, recipient filtering, and cancellation remain UNVERIFIED.
Initial invalid transmission IDs must not be interpreted as delivered messages.
The fixed diagnostic bank is local-only; compare only fresh samples from a run.

Do not launch until trial577 terminates and its outcome is verified. Then use
one API controller and native screenshots to correlate the bank timeline with
actual displayed text. Do not enable a gameplay subtitle bridge based solely on
these declaration checks or the successful archive write.
