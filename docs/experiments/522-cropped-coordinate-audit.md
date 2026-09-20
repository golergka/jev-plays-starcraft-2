# Lab 522: no simple cropped-grid size/offset mismatch

With trial512 terminal and no gameplay controller running, opened one read-only
SC2 connection, requested game_info and observation, then closed it. No game
orders, restarts, or model calls. The attached JSON records the returned facts.

raw_crop_to_playable_area is true. Playable bounds are [0,0,184,96]; visibility
and static pathing images are both 184x96. Both remaining owned units fall on
static walkable pixels. Their visibility value is 1 in the ending observation;
this is not evidence about visibility during active play. Earlier recorded model
states use the same zero-origin bounds.

Blizzard documents that cropping changes raw coordinates relative to the
playable area and adjusts map_size/playable_area:
https://raw.githubusercontent.com/Blizzard/s2client-proto/master/s2clientprotocol/sc2api.proto
This rules out the simple hypothesis that view.py uses the old uncropped map
offset with cropped unit positions. It does not prove pixel orientation, every
individual target, dynamic pathing, or the safety of routes. Do not invent a
coordinate correction or use this audit to claim all navigation is correct.
