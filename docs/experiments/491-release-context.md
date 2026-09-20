# Lab491: clear released commitment from next purchase context

Integration review of lab490 found that state was assembled before its optional release question. Removing the reservation from memory did not remove the old production_commitment value from that already-built state. Refresh the purchase context from current memory before asking Jev for a replacement purchase. This also avoids stale context after normal expiry. Original shared input state remains untouched.

Nine targeted tests pass. New integration test exercises actual choose_investment: Jev releases, then receives production_commitment=None and independently chooses save; submitted orders are not canceled. No new model calls in this verification.

Live486 remained active at native15:11; three Barracks, little army, zero displayed mineral/gas balance, Command Center617/1500 health,0/4relics. Logged rolling spend atloop14243 was $0.056859936, total $0.111941970/184successfulcalls. Three model timeout events recovered. No add-on request observed at this checkpoint. Outcome not yet established.
