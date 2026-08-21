# Feature Inventory

This is the accepted user-facing scope inherited from the prototype. It is a
requirements list, not permission to copy prototype implementation or data.

## Goals

- Lower Wall.
- Defeat Core Commander (default).
- Defeat S.A.H.A.B.A.R.
- Defeat All Bosses, including optional bosses regardless of their toggle.
- Goal scope removes checks that cannot be reached before completion.

## Check groups

Default groups: raw materials, refined materials, unique materials, key items,
locked chests, seeds, food, enemies, and optional bosses.

Default-off non-sanity groups: Merchants, Pets, Fish, Blocks, Golden Food,
Critters, and Cattle Mutilation. Cattle Mutilation remains last in that block.

Opt-in sanity groups: Skillsanity, Figurinesanity, Cardsanity,
Valuablesanity, Toolsanity, Weaponsanity, Jewelrysanity, Accessanity, and
Armorsanity.

Each group must expose an accurate generated count and examples. The tracker
must reflect only checks actually present in the connected multidata, using
documented PopTracker behavior.

## Rewards

- License modes: None, Workbench/Anvil (default), Important Crafting, All.
- Progressive crafting licenses and individual station licenses.
- Weighted raw material, refined material, potion, pet, money, and automation
  caches. Weights are relative and safe for any combination, including all 0
  and all 100.
- Goal-scaled randomized legendary caches, including Soul Seeker; maximum-stage
  duplicate progressives do nothing.
- Optional unique filler pools: tools, weapons, jewelry, accessories, armor.
- `Empty Cache` fills otherwise unfillable item slots.
- Skillsanity adds level-threshold checks only. The independent default-off
  Skill Points reward option adds +5 skill-point rewards and suppresses
  ordinary level-granted spendable points; disabling Skill Points restores
  unmodified game behavior regardless of the Skillsanity setting.

AP-delivered objects must never satisfy natural acquisition checks, even after
drop and pickup. A genuinely natural receipt removes that object's delivery
restriction. Rewards stack into normal inventory and pouch stacks; full
inventories queue rewards in persistent state rather than dropping them.

## Crafting licenses

Unlicensed stations remain interactable and show accessible lower-tier tabs,
but prohibited crafting, insertion, quick insertion, processing, and output
paths are blocked. Logic for craftable checks includes the authoritative station
license and recursively validated ingredient access. Natural drops may provide
a sequence-break route when the game data proves one exists.

## Quality of life

- Skill XP multiplier from 1x through 10x in 0.5x steps; default 2x. It changes
  earned XP, not initial class levels.
- Infinite merchant stock, while preserving ordinary unlock gates. Stock text
  is hidden if infinity cannot be rendered correctly.
- Merchant Sells Crown Summon: add Crown Summoning Idol to a second Cloaked
  Merchant tab with Giant Slime Idol price, limit, and restock behavior; move
  Caveling Bread to an open Fishing Merchant slot if required.
- Early Repair and Salvage placement.
- Prevent AP-classified progression/priority items in sanity checks where
  possible, with overflow allowed when necessary.
- Connection settings visible only after the main menu, with reconnect and
  persisted delivery behavior.

## Enemy randomizer

- A seeded one-to-one permutation of eligible ordinary enemy spawn slots.
- Avoid the source biome and heavily weight swaps by progression distance.
- Exclude bosses, livestock, pets, merchants, scripted encounters, cocoons, and
  child/attack entities.
- Parent spawners create the replacement for the child slot.
- Replacements inherit the source slot's health, damage budget, and drop table,
  including projectile, explosive, spawned-child, contact, and special attacks.
- Killing a replacement checks the original slot.
- Tracker text is `Slay Original (???)` before completion and reveals the
  replacement name and checked replacement icon after completion. With the
  randomizer disabled, no suffix is shown.

## Tracker

- Text category tabs and four variants ordered Medium, Small, Large, XL.
- Selection and sizing behavior follows the chosen variant without unsupported
  runtime layout mutation.
- Licenses show progressive stages; the Basic Workbench is stage zero, while
  other progressives retain their true locked stage zero.
- Icons come from the installed game, remain pixel-crisp, and use no wiki asset
  when a game asset is available.
- Native access status presentation: red inaccessible, yellow sequence break,
  green accessible, grey checked. Disabled/non-present checks are visually
  distinct and noninteractive through supported PopTracker mechanisms.
- Manual checks immediately recompute dependent logic.

## Logic

The detailed progression, goal, crafting, drop, biome, boss, merchant, pet,
skill, chest/key, and sequence-break requirements described during prototype
development are requirements candidates. They enter the main catalog only
after validation against game configurations/assemblies or a pinned reproducible
test-world observation. No prototype table is authoritative by itself.
