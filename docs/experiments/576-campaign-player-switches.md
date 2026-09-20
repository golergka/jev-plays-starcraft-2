# Lab 576: preserve explicit player switches across missions

After trial 574's verified defeat, audited the sequencer before another paid run.
The standalone controller supported the current seven boolean policy switches,
but the sequencer constructed mission arguments without forwarding them. Thus
switching to sequence execution would silently revert these features to defaults.

The sequencer now accepts and forwards contribution-top-choice, event-reviews,
production-intentions, bottleneck-diagnosis, stalled-commitment-review,
investment-top-choice, and preserve-current-orders. Defaults remain false.
Options cannot override mission paths, objectives, or call budgets. Opaque labels
remain an environment opt-in; this does not endorse that unsuccessful experiment.

Validation: 17 campaign tests passed, including forwarding through a defeat retry
and a transition to another mission, and rejecting unknown/nonboolean options.
No paid model calls or new game attempt. Four-entry opening manifest, campaign
research/unlocks, and later campaign compatibility remain incomplete.
