# Verified experimental delivery

Checked 2026-09-18 against the repository, local game, run logs and public remote.
This records completion of the requested infrastructure and initial Jev
investigation, not completion of StarCraft II's campaign.

| Requested capability | Evidence |
| --- | --- |
| Document the API and exact local procedure | PROCEDURE.md links Blizzard protocol definitions and records the verified Battle.net/API launch sequence, map-byte transport, fog filtering and action validation |
| Install local SC2 and connect it | Retail 5.0.16.97563 answers live ping and observation requests on localhost:5001 |
| Launch missions through an orchestrator | MarineMicro, traynor01 and traynor02 loaded; CAMPAIGN.md documents extraction and commands |
| Python player with commit-triggered live reload | player.py is loaded from Git HEAD at decision boundaries; eight observed live reload events; rollback behavior tested |
| OpenRouter SDK, Jev only, local dotenv credential | SDK integration and model allowlist; all logged model versions are typesafe/jev-1.13-20260917; .env untracked with mode 0600 |
| Public GitHub repository and automatic push | Public golergka/jev-plays-starcraft-2; active post-commit hook; local HEAD matched remote main during audit |
| Autonomous Jev decisions, observability and experimentation | Forty-two numbered lab journal entries, decision probabilities/latencies/costs, legal-command checks, and 25 local saved replays |
| Honest account of results and limitations | EXPERIMENT_REPORT.md and individual JSON summaries; no mission victory claimed |
| Windowed API play and public livestream | OBS previously verified capturing SC2 and conversation together; current transmission about 6161 kbps; SC2 application audio enabled and user microphone muted |

Eleven tests pass. They cover committed-source reload, hidden information/action
boundaries, real local WebSocket/protobuf exchange, terrain masking, building-site
approval, and sequential/concurrent inference budget enforcement. These tests do
not establish game-playing competence.

The current game remains open in the second mission; the bounded inference run
has finished. The last audit observed 35 owned units. OBS is still streaming.
No further model spending happens unless the harness is started again.

## What this experiment established

Jev selected real movement, combat, gathering, training and construction. A
completed Supply Depot raised capacity from 19 to 27. Explicit consequences helped
where raw numbers or action names did not. Navigation probability sampling changed
behavior, and explicit regroup anchors sometimes brought the squad together.
Parallel small requests reduced measured scheduling gaps relative to sequential
small requests, with a documented cost tradeoff.

These are exploratory sequential trials, not controlled benchmarks. Jev also
followed a neutral dog repeatedly, wandered the same corridor, split its squad,
ignored generic regrouping, and lost Raynor. Successful API responses did not
always mean useful motion or completed actions; one tutorial panel froze a trial.

## Future campaign work remains

No mission victory, whole-campaign sequencer, Hyperion/research/armory progression,
gas-harvesting implementation, or full ability coverage is claimed. Direct binary
startup on this Mac remains unreliable; Battle.net launch plus attachment is the
verified route. Building candidates are only four nearby visible sites, and the
player has a 64-unit cap. Model memory resets on a harness restart. These are
explicit limits of the rough experimental setup, not hidden fallback strategies.

The original success criterion allowed useful lessons without strong game results.
The experiment achieves that research outcome while leaving these capabilities
as follow-up work rather than presenting an unfinished campaign bot as solved.
