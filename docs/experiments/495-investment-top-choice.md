# Lab495: separate product disagreements; optional returned-choice mode

Refining lab494's fixed snapshot: different product/no-purchase selections account for27/49reviews in468,31/51in479,19/31in486; same-product different contracts account for2,3,3respectively. In486 four returned Marine choices sampled Barracks. These are intentions, not alternate successful trajectories.

Add --investment-top-choice, off by default. Use Jev's returned choice unchanged, including Save or a bounded batch when returned. Invalid returned choices fail loudly. No new model calls, hand-selected unit priorities, probability sharpening, or automatic production. Dedicated event/source distinguishes it from sampling. Investment scoring, if explicitly enabled separately, still follows its existing branch.

Current493 did not enable this flag; its behavior remains unchanged. Next experiment can enable it and assess live effects rather than infer victory from recorded states. Targeted tests verify purchase, save, and invalid returns despite conflicting probability mass, without initializing the sampling RNG.
