# Lab 513: route-distance information audit

The concrete menus expose straight-line distances and explicitly say actual
engine travel distance is unknown. Trial 508's repeated Marine destination
[43.73,13.04] produced later observations around [24.59,23.23] with the Move
order still outstanding. That is a reason to investigate geometry, not proof
of a coordinate bug or a particular route.

Official protocol evidence:
- https://raw.githubusercontent.com/Blizzard/s2client-proto/master/s2clientprotocol/query.proto
  defines batched pathing queries with a start point or unit tag, an endpoint,
  and a returned distance; zero means no path exists.
- https://raw.githubusercontent.com/Blizzard/s2client-api/master/include/sc2api/sc2_interfaces.h
  documents PathingDistance, including unit movement properties and batch use.
  It distinguishes static terrain pathability from blockers such as structures.

These declarations do not document whether hidden blockers can affect the
returned distance. A visible endpoint alone does not establish that the whole
route is revealed. No new pathing query or hidden-map data was supplied to Jev
in this investigation. The current visible/explored terrain filtering remains.

Before adding new movement-history summaries, inspect existing recent_outcomes:
player.py already supplies mean net displacement and mean sampled distance
travelled by type for continuously observed units. A duplicate summary would
not resolve missing route knowledge. Trial 512 continues unchanged while the
joint concrete menu hypothesis is measured.
