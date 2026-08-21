# Performance and Size Policy

## Client runtime

- React to authoritative game events; do not sweep all entities or inventory
  containers every frame.
- Coalesce inventory changes and AP messages into bounded queues.
- Cache resolved component types, methods, object IDs, and catalog lookups.
- Persist received-item index, pending rewards, natural-acquisition state, and
  unsent checks atomically.
- Limit fallback reconciliation scans to infrequent, measured recovery paths.
- Instrument work per frame and reject changes that exceed the agreed budget.

## Archipelago generation

- Build immutable lookup tables once.
- Express shared progression through regions/entrances instead of duplicating
  milestone checks on every location rule.
- Test logic functions directly; reserve broad randomized-generation testing
  for the release workflow as recommended by Archipelago.

## Tracker runtime

- Register static resources once during pack initialization.
- Handle AP callbacks in bulk updates protected by `pcall`, always restoring
  `Tracker.BulkUpdate`.
- Recalculate only dependent state and avoid recreating items or layouts.
- Target installed PopTracker 0.35.3; do not depend on APIs added later.

## Release size

- Store canonical facts once and generate consumer-specific compact outputs.
- Deduplicate sprites by pixel hash after deterministic crop.
- Preserve nearest-neighbor scaling and package only referenced images.
- Exclude raw game assets, extraction caches, diagnostics, and test worlds from
  release archives.
- Report unpacked and compressed sizes for APWorld, mod, and tracker separately.
