# Lab 578: visible dialogue is missing from model context

During trial577 native screenshot at1:26, a transmission and subtitles were
visible while the mission introduced units. Current mission_context exports only
timers/objectives; these spoken messages are absent from Jev's structured input.
No manually selected tactical advice was injected, and trial577 is unchanged.

Installed native declarations inspected in the existing local extraction:
`mods/core.sc2mod/base.sc2data/triggerlibs/natives.galaxy` declares
TransmissionSendForPlayer with recipient playergroup, soundlink, speaker,
subtitle, duration, waitUntilDone and owningPlayer arguments. SoundSubtitleText
exists for sound-derived text. NativeLib's TransmissionSend and
TransmissionSendAdvanced delegate to TransmissionSendForPlayer.

A possible general bridge would intercept runtime sends, retain only messages
actually delivered to the controlled player, and export localized text with a
bounded sequence history. It must preserve original arguments/return values and
blocking behavior, resolve null subtitle fallback, and validate when queued
messages become visible. Merely seeing a send call is not proof the message is
already displayed. Do not dump dialogue catalogs or future script text to Jev.

Before enabling: isolated timing/recipient/cancellation probes and comparison to
native subtitles are required. This is an identified input gap, not a working
bridge or evidence it improves decisions. No paid probe calls.

Protocol reference: https://github.com/Blizzard/s2client-proto/blob/master/s2clientprotocol/sc2api.proto
The present Python reader was also inspected directly; no dialogue field exists
in its emitted mission_context object.
