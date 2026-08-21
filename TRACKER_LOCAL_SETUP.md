# Core Keeper Archipelago tracker setup

This download contains no Core Keeper artwork. The installer reads the tracker
icons from the player's own installed copy of Core Keeper and builds the
textured PopTracker pack locally.

## Requirements

- Windows 10 or newer
- Core Keeper installed through Steam
- PopTracker 0.35.3 or newer

## Install

1. Close Core Keeper and PopTracker.
2. Run `Install-Core-Keeper-Archipelago-Tracker.exe`.
3. Approve the Windows administrator prompt. This is needed only to place the
   temporary read-only extractor in Core Keeper's Mods directory.
4. Core Keeper opens automatically. Leave it open until setup says the local
   artwork export is complete.
5. Close Core Keeper when setup asks. The temporary extractor is then removed.
6. Setup builds and installs `core_keeper_poptracker_local.zip` in
   `Documents\PopTracker\packs`.
7. After verifying the textured pack, setup removes the replaced texture-free
   Core Keeper pack so PopTracker shows only one copy.
8. Open PopTracker and select **(Textured) Core Keeper Archipelago Mainline
   1.0.1**.

The installer never uploads game files or extracted artwork. Generated artwork
remains on the player's computer. Rerun setup after a supported tracker update
or if Core Keeper changes its relevant assets.

## Windows warning

The initial community release is not digitally signed, so Microsoft Defender
SmartScreen may display an unknown-publisher warning. Verify the SHA-256 value
in `SHA256SUMS.txt` before running it. A future signed build requires a trusted
code-signing certificate.

## Troubleshooting

- If Core Keeper is not found, setup asks for the folder containing
  `CoreKeeper.exe`.
- If export does not finish, close setup, ensure Core Keeper starts normally,
  and rerun it.
- Setup refuses to begin while Core Keeper is already open so it cannot replace
  a loaded extractor DLL.
