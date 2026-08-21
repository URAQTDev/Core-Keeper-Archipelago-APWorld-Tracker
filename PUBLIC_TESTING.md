# Core Keeper Archipelago public testing

Core Keeper Archipelago 1.0.1 is a custom-world community testing release. The
goal of this phase is to establish real play history across different players,
computers, option sets, and multiworlds before requesting inclusion in the
official Archipelago distribution.

## Getting started

1. Install the matching `core_keeper.apworld` from the
   [latest release](https://github.com/URAQTDev/Core-Keeper-Archipelago-APWorld-Tracker/releases/latest).
2. Install the Core Keeper mod from the game's in-game **Mods** menu.
3. Generate a fresh Core Keeper options YAML after installing the APWorld.
4. Generate a new room and use a new Core Keeper character for the test.

## Particularly useful coverage

- Local generation and hosted-room connection.
- Checks and rewards with both default and optional sanity settings.
- Sending items to and receiving items from other players.
- Disconnecting, completing checks offline, and reconnecting automatically.
- Closing and reopening the game with rewards in inventories, chests, or on the
  ground.
- Smelting, crafting, recycling, and salvaging Archipelago-delivered items.
- Crafting-station licenses, goal completion, Death Link, and PopTracker sync.

You do not need to test every item or location. A complete multiworld session,
a goal completion, or focused testing of one option group is useful evidence.

## Report format

Please include:

- Core Keeper Archipelago version.
- Archipelago version.
- Core Keeper platform and game version/build, if visible.
- Solo room or multiworld, including number of players and other games.
- Goal and important non-default options.
- What you tested and whether you completed the goal.
- Any disconnects, missing checks, duplicate rewards, crashes, or confusing
  behavior.
- Relevant logs or screenshots when reporting a problem.

Do not include room passwords, private server addresses, save files containing
personal information, or other players' private data.

## Reporting

Open an issue at
https://github.com/URAQTDev/Core-Keeper-Archipelago-APWorld-Tracker/issues and
choose **Public playtest report**. For mod-specific crashes, include the Core
Keeper player log when available.
