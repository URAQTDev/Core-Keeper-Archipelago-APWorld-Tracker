# Main-Version Architecture

One generated canonical catalog is the boundary between Core Keeper data and
the three consumers.

```text
Core Keeper files + assemblies + test observations
                       |
                 validated extractors
                       |
              canonical versioned catalog
                /          |          \
          APWorld       game client    PopTracker
```

The catalog owns stable semantic identities, provenance, acquisition paths,
recipes, drops, spawn slots, logic milestones, sprite references, and option
membership. Consumers may add presentation or protocol data, but may not
redefine game facts.

## Evidence layers

- `runtime_database.raw.json` is exported from Core Keeper's managed
  `PugDatabase` on the pinned build. It supplies exact objects, variations,
  recipes, and crafting-station contents.
- `game_config.raw.json` is extracted directly from the shipped configuration
  directory. `game_evidence_index.json` losslessly indexes its loot, spawn, and
  fishing object references, including the distinct `fish` field used by all
  direct fishing definitions.
- `game_enums.raw.json` is extracted from the pinned `Pug.Base.dll` and
  `game_reference_semantics.json` uses those exact enum values to name spawn
  biomes, tilesets, tile types, and loot biome filters. Numeric values are not
  interpreted by hand.
- `check_candidates.json` and `reward_object_audit.json` are quarantine layers:
  they prove target identity but cannot enter the canonical catalog until their
  acquisition and progression logic is verified.
- `license_policy.json` binds the requested AP licenses to exact runtime station
  objects and true progressive stages.
- `crafting_routes.json` joins every checked craftable to its exact recipe
  ingredients and every station capable of producing it, including the
  station's license mode and progressive stage.
- `progression_policy.json` records the user-approved boss and milestone graph
  against runtime-verified boss identities. It remains separate from derived
  acquisition routes until the full solver is validated.

The client check dispatch tables are generated from canonical trigger records.
Inventory and destroyed-entity observers are bounded to 10 Hz and scan only the
local player's inventory or the game's transient destroyed-entity query. They
never scan the world each frame.

## Build properties

- deterministic output from pinned inputs;
- schema validation before code generation;
- stable IDs kept separately from display names;
- no runtime fuzzy name matching;
- no duplicated hand-maintained item lists across components;
- content hashes embedded in AP slot data and client/tracker diagnostics;
- incremental event processing instead of repeated global scans;
- only referenced tracker sprites enter release archives.

## Compatibility

Game build changes require a fresh extraction and hook validation. An unknown
game build presents a clear incompatibility message rather than attempting a
best-effort patch.
