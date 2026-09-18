# Stock mission experiment on this Mac

The Mac editor fails during video initialization. We instead used
[CascLib](https://github.com/ladislav-zezula/CascLib) to read the installed game
and [StormLib](https://github.com/ladislav-zezula/StormLib) to package a local MPQ
map. Game files are not modified. The output and replays remain ignored by Git.
This is a repackaged stock mission, not verified stock campaign progression.

Tested library revisions:

- CascLib: `2a280f5a231966dc5d1b534978dd9f9f04a374cd`
- StormLib: `44ebfbfc109d76e2a85bbd5d8b0c949df7e65c6f`

Build in a temporary working directory (the example uses `/tmp/jev-research`):

```sh
git clone https://github.com/ladislav-zezula/CascLib.git /tmp/jev-research/CascLib
git -C /tmp/jev-research/CascLib checkout 2a280f5a231966dc5d1b534978dd9f9f04a374cd
cmake -S /tmp/jev-research/CascLib -B /tmp/jev-research/CascLib/build -DCASC_BUILD_SHARED_LIB=ON -DCMAKE_BUILD_TYPE=Release
cmake --build /tmp/jev-research/CascLib/build -j 4
git clone https://github.com/ladislav-zezula/StormLib.git /tmp/jev-research/StormLib
git -C /tmp/jev-research/StormLib checkout 44ebfbfc109d76e2a85bbd5d8b0c949df7e65c6f
```

For StormLib on this compiler, change `PRIVATE "-framework Carbon"` to
`PRIVATE "SHELL:-framework Carbon"` in its CMakeLists.txt. Otherwise CMake passes
an invalid single compiler argument. Then:

```sh
cmake -S /tmp/jev-research/StormLib -B /tmp/jev-research/StormLib/build -DBUILD_SHARED_LIBS=ON -DSTORM_USE_BUNDLED_LIBRARIES=ON -DCMAKE_BUILD_TYPE=Release
cmake --build /tmp/jev-research/StormLib/build -j 4
uv run python scripts/extract_campaign.py --casc /tmp/jev-research/CascLib/build/casc.framework/casc --storm /tmp/jev-research/StormLib/build/storm.framework/storm --mission traynor01
```

The extractor refuses to overwrite an existing map. It preserves component bytes,
includes base and English locale components, and omits other locales. The first
mission produced 37 components and a 1,738,887-byte MPQ. It does not read tactical
script contents into the policy. Only live player observations go to Jev.

Start SC2 using Battle.net with `-listen 127.0.0.1 -port 5001 -displayMode 0` in
its Additional command line arguments. With that process running:

```sh
uv run python -m jev_sc2 --attach --map maps/traynor01.SC2Map --follow-camera --seconds 90 --max-calls 120 --objective 'Destroy the Logistics Headquarters. Raynor must survive.'
```

This loaded the opening cinematic and mission. After the cinematic, the engine
accepted Jev movement commands. The visible mission objectives are transcribed
above. The initial run had six units alive after 120 calls, costing $0.014349426;
it did not complete the mission. During the cinematic the engine returned
`YouCantIssueCommandsToThatUnit`, which is logged. Queries alone do not guarantee
that a cinematic unit accepts commands.

Resume without reloading the map using `--attach` alone. Load another mission with
`--attach --map ...`. A campaign sequencer can use this boundary, but Hyperion,
research, difficulty selection, mission unlocks and persistence between maps are
not implemented or verified. Do not claim the whole vanilla campaign works.
