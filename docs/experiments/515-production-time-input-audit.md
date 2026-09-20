# Lab 515: missing production-duration input

A source search found no build_time, training_time, or production_time fields
in the player observation projection or purchase menus. Unit costs, queues and
progress are exposed, but catalog production duration is not.

Blizzard's protocol defines optional UnitTypeData.build_time and
UpgradeData.research_time:
https://raw.githubusercontent.com/Blizzard/s2client-proto/master/s2clientprotocol/data.proto
The C++ interface describes build_time as how long the unit takes to build and
explicitly describes research_time in GameLoops:
https://raw.githubusercontent.com/Blizzard/s2client-api/master/include/sc2api/sc2_data.h
The inspected declarations do not specify the unit for build_time. Do not label
it seconds or convert it without verifying against actual engine observations.

Next useful diagnostic: record present catalog duration fields via the existing
controller's data object, then compare them with observed production progress.
This requires no hidden enemy state and no preferred purchase. It may improve
cost/time comparisons, but no effect on Jev decisions is yet established.
Trial 512 remains unchanged while this input omission is investigated.
