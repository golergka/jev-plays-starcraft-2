# Lab496: distinguish returned and sampled purchase selections in audits

Update read-only investment audit to join investment_top_choice as well as investment_sample. Preserve legacy sampled fields, add selected_choice/description and selection_mode, and report the chosen mode in summaries. This prevents the upcoming direct-choice trial from appearing to lack a selection merely because no sampling event exists. No gameplay or model changes.

Verified against ongoing493 events: sampled selections retain their original join. Native7:48 shows1/4relics,133minerals50gas9/19supply; latest nearby tick7045 lists9SCVs,Refinery,CommandCenter,SupplyDepot and no Barracks/combat units. No stalled_commitment_review event yet. Engine logged one CouldntReachTarget construction error at5839. At7692 the recorded investment top choice is Save while sampling selects SCV. Thus direct-choice mode may preserve saving behavior too; do not assume all sampling deviations are harmful.
