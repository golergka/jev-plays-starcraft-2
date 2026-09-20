# Lab 582: native sound subtitle matches rendered dialogue

Diagnostic-only copy used one installed Liberty sound link,
TRaynor01Adjutant00019, with null explicit speaker/subtitle. SoundSubtitleText
returned a localized tutorial-review notification. Native screenshot at0:17 of
sound-subtitle-lab582b.SC2Map showed matching text with the Adjutant speaker label.
No catalog contents were supplied to Jev; zero model calls and no campaign credit.

Initial20-second fixture screenshot was too late to establish the visual match.
Repeated with120-second diagnostic duration; underlying gameplay assets unchanged.
The native runtime compiled and ran scripts/sound_subtitle_probe.galaxy.
This validates fallback text resolution for one real sound. It does not establish
all transmission routing, movie subtitles, or conversation visibility semantics.

Next bridge should capture runtime TransmissionSendForPlayer calls, filter the
controlled recipient, preserve native invocation/return/wait semantics, and bound
history. Export only resolved text of delivered calls, never all catalog dialogue.
Validate wrapper transparency and send-time visibility before enabling gameplay.
