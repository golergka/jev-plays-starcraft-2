# Lab 512: joint concrete order comparison

Trial 508 lost at 18:09 with 33 purchase assessments, no Bunker purchases, and
persistent reinforcement losses. Its tactical selection used order-family,
destination-category, and concrete-order stages. Choosing an abstract family
first can exclude competing concrete actions before their targets are compared.

This retry disables both optional tactical partition stages, retaining the
full existing concrete menu and every other trial-508 setting, including
purchase dependency assessments. Jev chooses the action and target jointly.
This is an ablation of the staged tactical policy, not a claim that either
individual stage caused defeat. Different trajectories preclude a clean causal
comparison from one run. Earlier full-menu experiments establish feasibility,
not reliable success; labs 450/478 introduced these optional stages and their
subsequent live trials also failed.

Measure native outcome, calls/cost, concrete selected orders, reinforcement
survival observations, and command rejection/staleness. No tactical targets,
unit preferences, or mission-specific orders are added by the framework.
