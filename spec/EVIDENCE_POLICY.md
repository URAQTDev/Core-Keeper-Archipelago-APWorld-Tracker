# Evidence Policy

## Accepted evidence

Every game-facing fact must cite one or more of:

- a Core Keeper configuration record;
- a type, field, method, or system resolved from the installed game assemblies;
- a sprite or asset extracted from the installed game files;
- a reproducible observation from a version-pinned test world.

Wiki pages and prototype code may identify what to investigate, but cannot be
the final authority when the installed game contains the answer.

## Required provenance

Canonical records carry:

- Core Keeper Steam build ID;
- source path and SHA-256 hash;
- extractor version;
- source record/type/member identity;
- confidence status: `verified`, `observed`, or `blocked`.

`inferred`, name matching, fuzzy matching, and silent fallbacks are forbidden in
release data. A blocked mapping must fail validation with a useful report.

## Runtime hooks

A runtime hook is accepted only after its exact signature and owning assembly
are recorded for the pinned build. Reflection may be used for deliberate
compatibility probing, but a missing or ambiguous signature must disable the
feature loudly; it must not switch to guessed behavior.

## Test worlds

Test worlds may be generated for facts not encoded in static data, including
spawn behavior. Each observation must record world seed, game build, setup,
expected event, and result. Test-world evidence never overrides explicit game
data; discrepancies trigger investigation.

## Prototype quarantine

Prototype files may supply:

- requested feature names;
- expected user-visible behavior;
- known regressions;
- candidate identifiers to verify.

Prototype identifiers, logic rules, sprites, hooks, and workarounds are not
eligible for direct import.
