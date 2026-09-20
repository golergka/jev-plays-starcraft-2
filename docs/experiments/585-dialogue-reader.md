# Lab 585: validated Python dialogue reader

Added DialogueReader for the runtime bank. It returns the latest sixteen entries
in sequence order, labels them historical subtitles, and preserves whether capture
followed a blocking native call. Missing/in-progress files are unavailable;
previous-launch stamps and pre-launch mtimes are rejected. Changed launch IDs,
sequence rewind, mismatched ring slots and malformed records fail explicitly.
History can remain available after the bank stops changing within the same game.

Four focused tests passed. Also parsed the actual lab584 bank and verified its
sixteen ordered records6–21. This direct read was diagnostic-only, not a new-game
freshness test. Campaign builder/controller integration remains pending; no model
calls and no live gameplay behavior changed.
