# Lab 586: opt-in map/controller dialogue integration

Builder --visible-dialogue redirects native TransmissionSendForPlayer call sites
through the tested wrapper, initializes a unique bank before map initialization,
and records its identity in the hash-checked sidecar. Controller resolves this
reader on launch/restart/attach and adds recent dialogue to mission_context for
the ordinary player input path. Older maps remain unchanged.

Built local ttychus01-dialogue-lab586.SC2Map from the original extracted map with
outcomes, timers, objectives and dialogue enabled. Include audit covered121
scripts. This is packaging/source-rewrite evidence, not runtime compatibility.

31 focused tests passed across dialogue reading, campaign sequence and source
rewriting. Includes tampered-map and invalid-bank-name rejection. Live campaign
compilation and observed dialogue reaching Jev remain pending. No model calls.
