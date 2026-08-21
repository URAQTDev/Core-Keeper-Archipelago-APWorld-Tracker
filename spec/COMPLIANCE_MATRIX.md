# Compliance Matrix

Status values are `pending`, `verified`, and `blocked`. A release build fails if
any required row is not `verified`.

| Area | Requirement | Authority | Status |
|---|---|---|---|
| AP package | Lowercase `.apworld` root and valid `archipelago.json` | AP apworld specification | verified |
| AP package | Build through the supported APWorld packaging workflow | AP apworld specification | verified |
| World | Stable item/location IDs and collision checks | AP world API | verified |
| World | Equal generated item and location counts | AP adding games | verified |
| World | Reachable completion condition for every option combination | AP tests/world API | verified |
| World | Option-safe logic and generation tests | AP options/tests | verified |
| Client | Secure and unsecure WebSocket support | AP adding games/network protocol | verified |
| Client | Reconnect without duplicate join/leave churn | AP network protocol | verified |
| Client | Ordered `ReceivedItems` handling with index resync | AP network protocol | verified |
| Client | Offline-safe one-time location queue | AP adding games | verified |
| Client | Arbitrary duplicate item delivery | AP adding games | verified |
| Client | Goal completion sends the required status update | AP network protocol | verified |
| Tracker | Pack structure and supported manifest fields only | PopTracker PACKS | verified |
| Tracker | AP callbacks use documented interfaces | PopTracker AUTOTRACKING | verified |
| Tracker | `Tracker.BulkUpdate` restored after protected callbacks | PopTracker AUTOTRACKING | verified |
| Tracker | Manual click behavior uses supported item APIs | PopTracker PACKS + generated-definition tests | verified |
| Tracker | Non-present checks use native location visibility/access behavior | PopTracker PACKS + AP slot-data smoke test | verified |
| Tracker | Target runtime remains compatible with installed PopTracker 0.35.3 | Local runtime smoke test + PopTracker command-line docs | verified |
| Game data | Object and item identities derive from game files | Evidence policy | verified |
| Game data | Recipes, drops, spawns, and biomes derive from game files | Evidence index + runtime database tests | verified |
| Game hooks | Every hook resolves against pinned shipped assemblies | Pinned assembly extraction + compile/contract tests | verified |
| Assets | Packaged sprites originate from game files | Evidence policy + source-hashed extraction manifest | verified |
| Assets | Cropped assets are deduplicated and deterministic | Size policy | verified |
| Performance | No full inventory/entity scans per frame | Performance policy | verified |
| Performance | Network, checks, rewards, and tracker updates are batched | Performance policy | verified |
