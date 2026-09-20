# Lab 517: initial production-duration calibration

The diagnostic hot reload activated during trial 512 at loop 16848, without
changing Jev inputs. Reported raw build_time values include Barracks 960,
Marine 400, CommandCenter 1600, SupplyDepot 480, and SCV 0.

Recorded Barracks 4375969816 progressed from 0.416 at loop 6870 to 0.856 at
loop 7293. The implied full duration is 423 / 0.440 = 961.4 loops, consistent
with catalog 960 given rounded progress observations. This supports game-loop
units for this Barracks in this campaign. It does not establish accuracy for
every unit or modifications, and zero-valued SCV duration must not be presented
as instant production. More samples are needed before general time conversion
or remaining-time predictions are claimed.

Source: runs/20260920T133712.486436Z/events.jsonl. Catalog values were logged at
16848; progress samples came from earlier model observations in the same run.
