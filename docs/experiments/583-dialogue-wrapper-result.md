# Lab 583: bounded runtime dialogue wrapper

Added experimental visible_dialogue_bridge.galaxy, not enabled in campaign maps.
It forwards native arguments and return value, then records resolved subtitle
text only when the recipient group includes the controlled player and the native
return ID is valid. A sixteen-slot ring bounds retained history. Wait=true calls
are captured after native completion, never by changing native wait behavior.

Initial fixture failed to initialize because the sound parameter used a Galaxy
type name. Renaming it to soundValue allowed runtime execution in fixture583b.
Native screenshot0:17 showed the expected Adjutant line. The bank contained one
message matching that subtitle, sequence1, and return_matches_last=true. The
player-two-only synthetic message was excluded. Probe made zero model calls.

The checked-in diagnostic fixture is standalone and cannot credit campaign wins.
Coverage remains narrow: one nonblocking sound fallback plus excluded recipient.
Blocking calls, ring wrap, campaign include rewriting and Python reading remain
untested. The bridge must not be advertised as integrated or fully transparent.
