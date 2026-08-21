import pathlib
import json
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]


class RuntimeHookContractTests(unittest.TestCase):
    def test_location_checks_are_not_buffered_before_room_identity_is_known(self) -> None:
        connection = (ROOT / "client" / "ArchipelagoConnection.cs").read_text(encoding="utf-8")
        queue_method = connection.split("public void QueueLocationCheck", 1)[1].split(
            "private void SetGoalAchieved", 1
        )[0]
        self.assertIn("if (!HasRoomScope(roomKey))", queue_method)
        self.assertLess(
            queue_method.index("if (!HasRoomScope(roomKey))"),
            queue_method.index("pendingChecks.Add(locationId)"),
        )

    def test_world_entry_inventory_is_checked_after_warmup(self) -> None:
        inventory = (ROOT / "client" / "Runtime" / "NaturalInventoryObserver.cs").read_text(
            encoding="utf-8"
        )
        enemies = (ROOT / "client" / "Runtime" / "EnemyDeathObserver.cs").read_text(
            encoding="utf-8"
        )
        for source in (inventory, enemies):
            self.assertIn("WorldEntryWarmupSeconds = 2f", source)
            self.assertIn("baselineReadyAt", source)
            self.assertIn("Time.unscaledTime < baselineReadyAt", source.replace(">=", "<"))
        self.assertIn("counts.Clear();", inventory)
        self.assertNotIn("Snapshot(counts);", inventory)
        self.assertIn("snapshotInitialized && objectData.amount > previous", enemies)

    def test_wood_uses_authoritative_inventory_delta(self) -> None:
        source = (ROOT / "client" / "Runtime" / "NaturalInventoryObserver.cs").read_text(
            encoding="utf-8"
        )
        targets = (ROOT / "client" / "CheckTargets.cs").read_text(encoding="utf-8")
        self.assertIn("Snapshot(nextCounts)", source)
        self.assertIn("CheckTargets.IsNaturalTarget", source)
        self.assertIn("ObjectID.Wood", targets)
        self.assertIn("8406004", targets)
        self.assertIn("gained > suppressed", source)
        self.assertIn("SuppressReward", source)

    def test_early_ores_share_the_verified_natural_inventory_path(self) -> None:
        targets = (ROOT / "client" / "CheckTargets.cs").read_text(encoding="utf-8")
        for object_name, location_id in (
            ("CopperOre", "8406101"),
            ("TinOre", "8406102"),
            ("IronOre", "8406103"),
            ("GoldOre", "8406104"),
        ):
            with self.subTest(object_name=object_name):
                self.assertIn(f"ObjectID.{object_name}", targets)
                self.assertIn(location_id, targets)

    def test_every_promoted_natural_check_is_in_the_generated_target_table(self) -> None:
        catalog = json.loads(
            (ROOT / "data" / "canonical_catalog.json").read_text(encoding="utf-8")
        )
        objects = {record["key"]: record for record in catalog["objects"]}
        targets = (ROOT / "client" / "CheckTargets.cs").read_text(encoding="utf-8")
        for check in catalog["checks"]:
            if check["trigger"]["kind"] != "natural_acquisition":
                continue
            target = objects[check["trigger"]["target_key"]]
            with self.subTest(check=check["key"]):
                self.assertIn(f"ObjectID.{target['internal_name']}", targets)
                self.assertIn(str(check["stable_id"]), targets)

    def test_enemy_kills_use_exact_object_variations(self) -> None:
        observer = (ROOT / "client" / "Runtime" / "EnemyDeathObserver.cs").read_text(encoding="utf-8")
        targets = (ROOT / "client" / "CheckTargets.cs").read_text(encoding="utf-8")
        game_health = (
            ROOT / "build" / "decompiled-pug-other" / "UpdateHealthFromBufferSystem.cs"
        ).read_text(encoding="utf-8")
        self.assertIn("KilledEnemiesBuffer", observer)
        self.assertIn("objectData.amount > previous", observer)
        self.assertIn("snapshotInitialized", observer)
        self.assertIn("objectData.variation", observer)
        self.assertIn("EnemyRandomizer.OriginalFor(key.objectID, key.variation)", observer)
        self.assertIn("KillLocations(originalId, originalVariation)", observer)
        self.assertIn(
            "if (isServerLocal && (entity2 != Entity.Null || bossLookup.HasComponent(entity)))",
            game_health,
        )
        self.assertIn("buffer.ElementAt(index).objectData.amount++", game_health)
        self.assertIn("(ObjectID.Larva, 0)", targets)
        self.assertIn("(ObjectID.Larva, 1)", targets)
        self.assertIn("8406359", targets)
        self.assertIn("8406361", targets)

    def test_cattle_kills_accept_runtime_dynamic_variations(self) -> None:
        database = json.loads(
            (ROOT / "data" / "runtime_database.raw.json").read_text(encoding="utf-8")
        )
        records = {record["object_id"]: record for record in database["records"]}
        targets = (ROOT / "client" / "CheckTargets.cs").read_text(encoding="utf-8")
        self.assertIn("DynamicVariationKills", targets)
        for object_id, object_name, location_id in (
            (1300, "Cow", "8406687"),
            (1302, "Goat", "8406688"),
            (1303, "RolyPoly", "8406689"),
            (1307, "Turtle", "8406690"),
            (1309, "Dodo", "8406691"),
            (1311, "Camel", "8406692"),
        ):
            with self.subTest(object_name=object_name):
                self.assertTrue(records[object_id]["variation_is_dynamic"])
                self.assertIn(f"ObjectID.{object_name}", targets)
                self.assertIn(location_id, targets)

    def test_natural_inventory_snapshot_includes_pouch_ranges(self) -> None:
        observer = (ROOT / "client" / "Runtime" / "NaturalInventoryObserver.cs").read_text(
            encoding="utf-8"
        )
        equipment = (
            ROOT / "build" / "decompiled-pug-other" / "EquipmentHandler.cs"
        ).read_text(encoding="utf-8")
        player = (
            ROOT / "build" / "decompiled-pug-other" / "PlayerController.cs"
        ).read_text(encoding="utf-8")
        self.assertIn("for (int index = 0; index < objects.Length; index++)", observer)
        self.assertIn("pouchInventorySlotsHandlers", observer)
        self.assertIn("pouch.GetContainedObjectData(index)", observer)
        self.assertIn("new InventoryHandler(entityMonoBehaviour, world, isBuyInventory: false, j + 1)", equipment)
        self.assertIn("pouchInventorySlotsHandlers = ImmutableArray.Create(array2)", equipment)
        self.assertIn("equipmentHandler.pouchInventorySlotsHandlers[i]", player)
        self.assertIn("index - inventoryHandler.startPosInBuffer", player)

    def test_prototype_station_inventory_gates_are_ported(self) -> None:
        runtime = (ROOT / "client" / "Runtime" / "RuntimeHooks.cs").read_text(
            encoding="utf-8"
        )
        for contract in (
            'method.Name == "CanPlaceInSlot"',
            'method.Name.IndexOf("Move"',
            'method.Name == "SetAmount"',
            'method.Name != "Upgrade"',
            'method.Name != "RepairOrReinforce"',
            "SlotErrorPostfix",
            "owner.CanUseCraftingTier(objectId)",
        ):
            self.assertIn(contract, runtime)
        self.assertNotIn("__instance is not Furnace", runtime)

    def test_authoritative_pickup_path_catches_transient_natural_items(self) -> None:
        runtime = (ROOT / "client" / "Runtime" / "RuntimeHooks.cs").read_text(
            encoding="utf-8"
        )
        observer = (ROOT / "client" / "Runtime" / "NaturalInventoryObserver.cs").read_text(
            encoding="utf-8"
        )
        self.assertIn('"ProcessInventoryChange"', runtime)
        self.assertIn("Inventory.InventoryAction.PickUpObject", runtime)
        self.assertIn("RecordAuthoritativePickup", runtime)
        self.assertIn("rpc.objectID != ObjectID.None ? rpc.objectID : data.objectID", runtime)
        self.assertIn("rpc.amount > 0 ? rpc.amount : data.amount", runtime)
        self.assertIn("int suppressed = ConsumeWholeAway(objectId, amount)", observer)
        self.assertIn("gained < away", observer)
        self.assertIn("return amount > suppressed", observer)

    def test_ap_item_messages_use_native_feed_and_rewards_skip_new_item_message(self) -> None:
        connection = (ROOT / "client" / "ArchipelagoConnection.cs").read_text(
            encoding="utf-8"
        )
        entry = (ROOT / "client" / "ModEntryPoint.cs").read_text(encoding="utf-8")
        rewards = (ROOT / "client" / "Runtime" / "RewardDispatcher.cs").read_text(
            encoding="utf-8"
        )
        self.assertIn("target.MessageLog.OnMessageReceived += OnMessageReceived", connection)
        self.assertIn("message is not ItemSendLogMessage", connection)
        self.assertIn("itemMessage.IsRelatedToActivePlayer", connection)
        self.assertIn('itemMessage.Item.LocationDisplayName', connection)
        self.assertIn('HarmonyLib.AccessTools.Method(typeof(ChatWindow), "RenderText"', entry)
        self.assertIn("Manager.saves.SetObjectAsDiscovered", entry)
        self.assertIn("markRewardDiscovered(objectId);", rewards)

    def test_recipe_license_gate_preserves_ctrl_multiplier_and_station_tabs(self) -> None:
        runtime = (ROOT / "client" / "Runtime" / "RuntimeHooks.cs").read_text(
            encoding="utf-8"
        )
        self.assertIn("RecipeLicenseVisualPatch", runtime)
        self.assertIn("CraftingUIBase.ActivateRecipeSlot", runtime)
        self.assertIn("nameof(CraftingHandler.HasMaterialsInCraftingInventoryToCraftRecipe)", runtime)
        self.assertIn("typeof(System.Collections.Generic.List<Entity>)", runtime)
        self.assertIn("internal static bool Prefix(int recipeIndex, ref bool __result)", runtime)
        self.assertNotIn("__instance.icon.color", runtime)
        self.assertIn("ReferenceEquals(instance, crafting.outputInventoryHandler)", runtime)

    def test_nonstackable_rewards_use_native_initial_state(self) -> None:
        rewards = (ROOT / "client" / "Runtime" / "RewardDispatcher.cs").read_text(
            encoding="utf-8"
        )
        self.assertIn("int storedAmount = stackable ? amount : 1", rewards)
        self.assertIn("int provenanceAmount = stackable ? amount : 1", rewards)
        self.assertIn("suppressReward(objectId, provenanceAmount)", rewards)

    def test_pet_hatches_use_the_verified_egg_cracked_egg_pet_chain(self) -> None:
        database = json.loads(
            (ROOT / "data" / "runtime_database.raw.json").read_text(encoding="utf-8")
        )
        records = {record["object_id"]: record for record in database["records"]}
        candidates = json.loads(
            (ROOT / "data" / "check_candidates.json").read_text(encoding="utf-8")
        )["checks"]
        pets = [row for row in candidates if row["group"] == "petsanity"]
        for egg, hatch in zip(pets[::2], pets[1::2]):
            egg_id = egg["trigger"]["object_id"]
            pet_id = hatch["trigger"]["object_id"]
            cracked = next(
                record for record in records.values()
                if record["internal_name"] == egg["trigger"]["internal_name"] + "Cracked"
            )
            with self.subTest(pet=hatch["display_name"]):
                self.assertEqual("CastingItem", cracked["object_type"])
                self.assertEqual(1800.0, cracked["crafting_time"])
                self.assertEqual([{"object_id": egg_id, "amount": 1}], cracked["ingredients"])
                self.assertEqual("Pet", records[pet_id]["object_type"])

    def test_merchants_use_the_successful_base_npc_interaction(self) -> None:
        game_npc = (ROOT / "build" / "decompiled-Pug.Objects" / "NPC.cs").read_text(encoding="utf-8")
        hook = (ROOT / "client" / "Runtime" / "MerchantInteractionPatch.cs").read_text(encoding="utf-8")
        runtime = (ROOT / "client" / "Runtime" / "RuntimeHooks.cs").read_text(encoding="utf-8")
        targets = (ROOT / "client" / "CheckTargets.cs").read_text(encoding="utf-8")
        interact = game_npc.split("public virtual void Interact()", 1)[1].split("public void OnPlayerLeft()", 1)[0]
        self.assertIn("SetActiveBuyInventoryHandler(inventoryHandler)", interact)
        self.assertIn("Manager.ui.OnVendorOpen()", interact)
        self.assertIn("typeof(NPC), nameof(NPC.Interact)", runtime)
        self.assertIn("postfix: new HarmonyMethod(postfix)", runtime)
        self.assertIn("GetComponentData<ObjectDataCD>", hook)
        for merchant in ("SlimeMerchant", "CavelingMerchant", "FishingMerchant", "CrystalMerchant", "VoidMerchant"):
            self.assertIn(f"ObjectID.{merchant}", targets)

    def test_merchant_quality_of_life_uses_current_ecs_inventory_contracts(self) -> None:
        source = (ROOT / "client" / "Runtime" / "MerchantStockController.cs").read_text(
            encoding="utf-8"
        )
        hooks = (ROOT / "client" / "Runtime" / "RuntimeHooks.cs").read_text(
            encoding="utf-8"
        )
        for contract in (
            "MerchantCD",
            "ContainedObjectsBuffer",
            "MerchantItemInfoBuffer",
            "ObjectDataCD",
        ):
            self.assertIn(contract, source)
        self.assertIn("merchantState.previousAmountOfItems", source)
        self.assertIn("ContainedObjectsBuffer[]", source)
        self.assertIn("item.objectData.amount < original.objectData.amount", source)
        self.assertIn("!Contains(stock, ObjectID.KingSlimeSummoningItem)", source)
        self.assertIn("merchantData.amount = 0", source)
        self.assertIn("merchants.IsEmptyIgnoreFilter", source)
        self.assertIn("ObjectID.CavelingBread", source)
        self.assertIn("hasBreadTemplate", source)
        self.assertIn("ObjectID.KingSlimeSummoningItem", source)
        self.assertIn("ObjectID.FishingMerchant", source)
        self.assertIn("!candidate.IsCreated || !candidate.IsServer()", source)
        self.assertNotIn("API.Server.World", source)
        self.assertIn('typeof(InventoryHandler), "GetCoinValue"', hooks)
        self.assertIn("ObjectID.SlimeBossSummoningItem", hooks)

    def test_drop_pickup_provenance_limit_is_grounded_in_game_code(self) -> None:
        utility = (
            ROOT / "build" / "decompiled-pug-other" / "Inventory" / "InventoryUtility.cs"
        ).read_text(encoding="utf-8")
        drop = utility.split("public static void DropItem", 1)[1].split(
            "public static void SplitItemAndDropFromMover", 1
        )[0]
        pickup = utility.split("public static void PickUpObject", 1)[1].split(
            "public static void MoveAmount", 1
        )[0]
        self.assertIn("auxDataIndex = value.auxDataIndex", drop)
        self.assertIn("componentData.objectID", pickup)
        self.assertNotIn("auxDataIndex", pickup)

    def test_locked_chest_uses_game_success_effect(self) -> None:
        hook = (ROOT / "client" / "Runtime" / "LockedChestUnlockPatch.cs").read_text(
            encoding="utf-8"
        )
        game_source = (
            ROOT.parent
            / "mainline"
            / "build"
            / "decompiled-pugother"
            / "EffectEventExtensions.cs"
        ).read_text(encoding="utf-8")
        self.assertIn("EffectID.OpenChest", hook)
        self.assertNotIn("RecordCopperChestUnlock", hook)
        self.assertIn("RecordSuccessfulLockedChestUnlock", hook)
        entry = (ROOT / "client" / "ModEntryPoint.cs").read_text(encoding="utf-8")
        for chest, location in (
            ("CopperKey", "UnlockLockedCopperChest"),
            ("IronKey", "UnlockLockedIronChest"),
            ("ScarletKey", "UnlockLockedScarletChest"),
            ("OctarineKey", "UnlockLockedOctarineChest"),
            ("GalaxiteKey", "UnlockLockedGalaxiteChest"),
            ("SolariteKey", "UnlockLockedSolariteChest"),
            ("ReluciteKey", "UnlockLockedReluciteChest"),
        ):
            with self.subTest(chest=chest):
                self.assertIn(f"ObjectID.{chest}", entry)
                self.assertIn(f"LocationIds.{location}", entry)
        observer = (ROOT / "client" / "Runtime" / "NaturalInventoryObserver.cs").read_text(
            encoding="utf-8"
        )
        self.assertIn("previousKeyCount - nextKeyCount", observer)
        self.assertIn("pendingSuccessfulChestUnlocks", observer)
        self.assertIn("recordConsumedChestKey", observer)
        self.assertIn("recentlyConsumedKeys", observer)
        self.assertIn("correlationWindowSeconds = 1f", observer)
        open_chest_case = game_source.split("case EffectID.OpenChest:", 1)[1].split(
            "break;", 1
        )[0]
        self.assertIn("uiOpenLockedChestSfx", open_chest_case)

    def test_workbench_license_blocks_recipe_activation_not_station_interaction(self) -> None:
        hooks = (ROOT / "client" / "Runtime" / "RuntimeHooks.cs").read_text(
            encoding="utf-8"
        )
        game_ui = (
            ROOT / "build" / "decompiled-pug-other" / "CraftingUIBase.cs"
        ).read_text(encoding="utf-8")
        building = (
            ROOT / "build" / "decompiled-pug-other" / "CraftingBuilding.cs"
        ).read_text(encoding="utf-8")
        self.assertIn("CraftingUIBase.ActivateRecipeSlot", hooks)
        self.assertIn("handler.GetRecipeInfo(visibleSlotIndex).objectID", hooks)
        self.assertIn("IsRecipeAtUnlockedLowerTier", hooks)
        self.assertIn("ObjectID.WoodenWorkBench", hooks)
        policy = (ROOT / "client" / "Runtime" / "LicenseAccessPolicy.cs").read_text(
            encoding="utf-8"
        )
        self.assertIn("TryGetRequirement", policy)
        self.assertIn("ObjectID.CopperAnvil", policy)
        self.assertIn("Progressive Anvil License", policy)
        self.assertNotIn("CraftingBuilding.Use", hooks)
        self.assertIn("public virtual void ActivateRecipeSlot", game_ui)
        self.assertIn("SetActiveCraftingHandler(craftingHandler)", building)

    def test_every_reported_recipe_station_uses_the_license_policy(self) -> None:
        policy = (ROOT / "client" / "Runtime" / "LicenseAccessPolicy.cs").read_text(
            encoding="utf-8"
        )
        for station in (
            "KeyCraftingTable", "CattleWorkbench", "GlassWorkbench", "PaintersTable",
            "RailwayForge", "Carpenter", "BoatWorkbench", "ElectronicsTable",
            "AutomationTable", "AlchemyTable", "FishingWorkBench",
        ):
            with self.subTest(station=station):
                self.assertIn(f"ObjectID.{station}", policy)

    def test_license_persistence_is_batched_per_update(self) -> None:
        entry = (ROOT / "client" / "ModEntryPoint.cs").read_text(encoding="utf-8")
        dispatcher = (ROOT / "client" / "Runtime" / "RewardDispatcher.cs").read_text(
            encoding="utf-8"
        )
        self.assertIn("MarkLicenseStateDirty", entry)
        self.assertIn("if (licenseStateDirty)", entry)
        self.assertNotIn("API.Config.Set", dispatcher)

    def test_skill_xp_multiplier_uses_authoritative_server_buffer(self) -> None:
        source = (ROOT / "client" / "Runtime" / "SkillExperienceMultiplier.cs").read_text(
            encoding="utf-8"
        )
        connection = (ROOT / "client" / "ArchipelagoConnection.cs").read_text(
            encoding="utf-8"
        )
        self.assertIn("PugMod.API.Server.World", source)
        self.assertIn("HasBuffer<SkillBuffer>", source)
        self.assertIn("naturalGain * (multiplier - 1.0)", source)
        self.assertIn("skills[index] = value", source)
        self.assertIn('"skill_xp_multiplier"', connection)
        self.assertIn("value >= 1.0 && value <= 10.0", connection)

    def test_skill_points_are_gated_independently_from_skillsanity(self) -> None:
        options = (ROOT / "apworld" / "core_keeper" / "options.py").read_text(encoding="utf-8")
        world = (ROOT / "apworld" / "core_keeper" / "world.py").read_text(encoding="utf-8")
        hooks = (ROOT / "client" / "Runtime" / "RuntimeHooks.cs").read_text(encoding="utf-8")
        self.assertIn('display_name = "Skill Points"', options)
        self.assertIn('"skill_points": bool(self.options.skill_points)', world)
        self.assertIn("!owner.SkillPointsEnabled", hooks)
        self.assertIn("owner.AwardedSkillPoints(skillTreeID) - spent", hooks)

    def test_all_nonstackable_checks_are_counted_by_inventory_slot(self) -> None:
        observer = (ROOT / "client" / "Runtime" / "NaturalInventoryObserver.cs").read_text(
            encoding="utf-8"
        )
        self.assertIn("!info.isStackable ? 1 : contained.amount", observer)
        self.assertNotIn("IsStatefulTool", observer)

    def test_official_client_build_enables_runtime_websocket_deflate(self) -> None:
        preparation = (ROOT / "tools" / "Prepare-OfficialClientSource.ps1").read_text(
            encoding="utf-8"
        )
        transport = (ROOT / "vendor" / "CompressedWebSocketClient.cs").read_text(
            encoding="utf-8"
        )
        self.assertIn("CompressedWebSocketClient", preparation)
        self.assertIn("client_no_context_takeover", transport)
        self.assertIn("server_no_context_takeover", transport)
        self.assertIn("Sec-WebSocket-Accept", transport)
        self.assertIn("MaximumMessageBytes", transport)
        self.assertIn("RandomNumberGenerator.Create()", transport)

    def test_reward_provenance_is_persisted_per_room_across_restart(self) -> None:
        entry = (ROOT / "client" / "ModEntryPoint.cs").read_text(encoding="utf-8")
        observer = (ROOT / "client" / "Runtime" / "NaturalInventoryObserver.cs").read_text(
            encoding="utf-8"
        )
        ledger = (ROOT / "client" / "State" / "RewardProvenanceLedger.cs").read_text(
            encoding="utf-8"
        )
        self.assertIn('"RewardProvenance"', entry)
        self.assertIn("BindRewardProvenanceRoom", entry)
        self.assertIn("SaveRewardProvenance", entry)
        self.assertIn("SnapshotProvenance", observer)
        self.assertIn("RestoreProvenance", observer)
        self.assertIn("snapshot.Held", observer)
        self.assertIn("Dictionary<string, RewardProvenanceSnapshot>", ledger)

    def test_salvage_inherits_provenance_from_every_physical_ap_reward(self) -> None:
        observer = (ROOT / "client" / "Runtime" / "NaturalInventoryObserver.cs").read_text(
            encoding="utf-8"
        )
        hooks = (ROOT / "client" / "Runtime" / "RuntimeHooks.cs").read_text(
            encoding="utf-8"
        )
        self.assertIn("objectId != ObjectID.None && amount > 0", observer)
        self.assertIn("Consume(confirmedRewardArrivals, item.objectID, amount)", observer)
        self.assertIn("Consume(pendingRewardArrivals, item.objectID, amount)", observer)
        self.assertIn("pendingRewardSalvagePolls = 20", observer)
        self.assertIn("!candidate.IsServer()", observer)
        self.assertIn("Inventory.InventoryAction.SalvageAll", hooks)
        self.assertIn("RecordSalvageOperation", hooks)
        self.assertIn('typeof(InventoryHandler), "SalvageAll"', hooks)
        self.assertIn("RecordSalvageContents", hooks)

    def test_same_process_world_reentry_reconciles_held_rewards(self) -> None:
        observer = (ROOT / "client" / "Runtime" / "NaturalInventoryObserver.cs").read_text(
            encoding="utf-8"
        )
        self.assertIn(
            "int retainedHeld = establishingBaseline ? Math.Min(gained, alreadyHeld) : 0",
            observer,
        )
        self.assertIn("establishingBaseline = false", observer)
        self.assertIn("int newlyHeld = suppressed - retainedHeld", observer)
        self.assertIn("held + newlyHeld", observer)

    def test_ap_feed_messages_have_an_independent_longer_fade(self) -> None:
        entry = (ROOT / "client" / "ModEntryPoint.cs").read_text(encoding="utf-8")
        self.assertIn('AccessTools.Field(typeof(ChatWindow), "fadeEffects")', entry)
        self.assertIn("ApMessageFadeSeconds = 5f", entry)
        self.assertIn("ApMessageHoldSeconds = 2f", entry)
        self.assertIn("ExtendLatestApMessage", entry)
        self.assertIn("latest?.GetComponent<PugText>()", entry)
        self.assertIn("text.style.supportColorTags = true", entry)
        self.assertIn("EnableReceivedColorTags", entry)
        self.assertIn("ApColoredGlyphFade", entry)
        self.assertIn("color.a *= alpha", entry)
        self.assertIn("text.SetOutlineColor(outlineColor)", entry)
        self.assertIn("alpha <= 0.001f", entry)
        self.assertIn("? (PugTextStyle.Outline)0", entry)
        self.assertIn("text.glyphs[index].color = color", entry)
        self.assertIn("nativeFade?.ResetEffect(rewind: true)", entry)
        self.assertIn("nativeFade?.FadeOut()", entry)
        self.assertNotIn("NativeCurrent.SetValue(nativeFade, visibleAlpha)", entry)
        self.assertIn("Time.unscaledDeltaTime", entry)
        self.assertIn("nativeFade.fadeOutCurve.Evaluate", entry)
        self.assertNotIn("gameObject.SetActive(false)", entry.split("internal sealed class ApColoredGlyphFade", 1)[1])

    def test_native_discovery_messages_are_suppressed_at_their_actual_entrypoint(self) -> None:
        hooks = (ROOT / "client" / "Runtime" / "RuntimeHooks.cs").read_text(
            encoding="utf-8"
        )
        self.assertIn('target.Name == "AddInfoText"', hooks)
        self.assertIn("typeof(ChatWindow.MessageTextType)", hooks)
        self.assertIn('typeName.IndexOf("NewItem"', hooks)
        self.assertIn('typeName.IndexOf("Talent"', hooks)

    def test_ap_feed_direction_and_player_names_are_color_coded(self) -> None:
        connection = (ROOT / "client" / "ArchipelagoConnection.cs").read_text(
            encoding="utf-8"
        )
        self.assertIn('Colorize("Received", "75E68AFF")', connection)
        self.assertIn('Colorize("Sent", "FFB45CFF")', connection)
        self.assertIn('self ? "EE00EEFF" : "FAFAD2FF"', connection)
        self.assertIn("ColorizePlayerName(itemMessage.Sender.Name)", connection)
        self.assertIn("ColorizePlayerName(itemMessage.Receiver.Name)", connection)
        self.assertIn('itemMessage.Item.LocationDisplayName', connection)

    def test_ap_feed_item_names_use_official_classification_colors(self) -> None:
        connection = (ROOT / "client" / "ArchipelagoConnection.cs").read_text(
            encoding="utf-8"
        )
        self.assertIn('ItemFlags.Advancement) != 0 ? "AF99EFFF"', connection)
        self.assertIn('ItemFlags.NeverExclude) != 0 ? "6D8BE8FF"', connection)
        self.assertIn('ItemFlags.Trap) != 0 ? "FA8072FF"', connection)
        self.assertIn(': "00FFFFFF"', connection)
        self.assertIn("ColorizeItem(itemMessage.Item.ItemDisplayName", connection)

    def test_ap_feed_messages_have_a_scoped_dark_outline(self) -> None:
        entry = (ROOT / "client" / "ModEntryPoint.cs").read_text(encoding="utf-8")
        self.assertIn('AccessTools.Method(typeof(PugText), "UpdateOutline")', entry)
        self.assertIn('AccessTools.Method(typeof(PugText), "UpdateOutlineSides")', entry)
        self.assertIn("PugTextStyle.Outline.top | PugTextStyle.Outline.bottom", entry)
        self.assertIn("new UnityEngine.Color(0.03f, 0.03f, 0.03f, 0.65f)", entry)
        self.assertIn("UpdateOutline.Invoke(value, Array.Empty<object>())", entry)
        self.assertIn("private void OnDisable()", entry)
        self.assertIn("text.style.outline = originalOutline", entry)

    def test_legendary_cache_feed_omits_contents_parentheses(self) -> None:
        entry = (ROOT / "client" / "ModEntryPoint.cs").read_text(encoding="utf-8")
        self.assertIn("legendaryCache ? string.Empty", entry)
        self.assertIn('" (+" + cacheContents + ")"', entry)

    def test_connection_settings_use_native_settings_menu(self) -> None:
        entry = (ROOT / "client" / "ModEntryPoint.cs").read_text(encoding="utf-8")
        native = (ROOT / "client" / "ArchipelagoNativeSettings.cs").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("CoreKeeperArchipelagoSettingsPanel", entry)
        self.assertIn("options.menuOptions.Insert(creditsIndexInMenu, entry)", native)
        self.assertIn('controls.transform.parent, "Archipelago"', native)
        self.assertIn("text.usePooledResources = usePooledGlyphs", native)
        self.assertIn('LogEntryGeometry("before Settings Activate")', native)
        self.assertIn('LogEntryGeometry("after Settings Activate and rerender")', native)
        self.assertIn('layoutKeeper?.ApplyNow()', native)
        self.assertIn('SetText(diagnosticEntry.labelText, "Archipelago")', native)
        self.assertIn('"Server", ConnectionSettings.DisplayServer(settings.Server)', native)
        self.assertIn('"Slot", settings.Slot', native)
        self.assertIn('"Password", settings.Password', native)
        self.assertIn('"Save and Connect"', native)
        self.assertIn("options.autoPositioning = false", native)
        self.assertIn("AddComponent<ArchipelagoSettingsLayoutKeeper>()", native)
        self.assertNotIn('SetText(entryLabel, "Archipelago")', native)
        self.assertNotIn("effect.ResetEffect(rewind: true)", native)
        self.assertIn("status.Clear(temporaryClear: true, bypassSetActive: true)", native)
        self.assertIn("credits.transform.localPosition = creditsPosition + nativeRowStep", native)
        self.assertIn("input.radicalMenuOptionToggleVisibility = null", native)
        self.assertIn("input.pugText.isHidden = false", native)
        self.assertIn("menuEntryStartPositionY = 1.8f", native)
        self.assertIn("new Vector3(0f, position.y, position.z)", native)
        self.assertIn("CloneCleanTextRow", native)
        self.assertIn("GetComponentsInChildren<SpriteRenderer>(true)", native)
        self.assertIn("text.glyphs.Clear()", native)
        self.assertIn("text.glyphTransforms.Clear()", native)
        self.assertIn("effect.isDanceWhenSelected = false", native)
        self.assertIn("ActivatePrefix(RadicalOptionsMenuOption_GoToControlMapper __instance)", native)
        self.assertIn("ConnectInputPrefix(RadicalMenuOptionTextInput __instance)", native)
        self.assertIn('saveButton.SetInputText("Save and Connect")', native)
        self.assertIn("entry.activeInTitle = true", native)
        self.assertIn("entry.activeInSPStage = true", native)
        self.assertIn("target.style.fontFace = source.style.fontFace", native)
        self.assertIn("buttonObject.SetActive(true)", native)
        self.assertIn("buttonObject.name = ConnectName", native)
        self.assertIn("input.readOnly = true", native)
        self.assertIn("popsOtherActiveMenus = true", native)

    def test_native_archipelago_logos_are_packaged_and_bound_to_menus(self) -> None:
        logos = (ROOT / "client" / "ArchipelagoMenuLogos.cs").read_text(encoding="utf-8")
        ready = (ROOT / "client" / "Runtime" / "MainMenuReadyPatch.cs").read_text(encoding="utf-8")
        package = (ROOT / "tools" / "Package-Client.ps1").read_text(encoding="utf-8")
        settings = (ROOT / "client" / "ConnectionSettings.cs").read_text(encoding="utf-8")
        project = (ROOT / "client" / "CoreKeeperArchipelago.Mainline.csproj").read_text(encoding="utf-8")
        self.assertTrue((ROOT / "client" / "Assets" / "ArchipelagoLogo.png").is_file())
        self.assertIn("ArchipelagoMenuLogos.EnsureInstalled", ready)
        self.assertIn("ArchipelagoMenuLogos.OnMenuDeactivated(__instance)",
                      (ROOT / "client" / "ArchipelagoNativeSettings.cs").read_text(encoding="utf-8"))
        self.assertIn("inactiveMenu is not RadicalMainMenu", logos)
        self.assertNotIn("else\n            instance.displayState = DisplayState.Hidden;", logos)
        self.assertIn("GetManifestResourceStream", logos)
        self.assertIn('LogicalName="CoreKeeperArchipelago.ArchipelagoLogo.png"', project)
        self.assertIn('new[] { "Awake", "Start", "OnEnable" }', ready)
        self.assertIn("LayoutMainLogo", logos)
        self.assertNotIn("LayoutSettingsLogo", logos)
        self.assertIn("SelectTitleFade", logos)
        self.assertNotIn("follower.loadFaderOffset", logos)
        self.assertNotIn("nativeTitle.color.a", logos)
        self.assertNotIn("FindObjectsByType<AlphaFollowLoadFader>", logos)
        self.assertNotIn("FindFirstObjectByType<RadicalMainMenu>", logos)
        self.assertNotIn("MainMenuFadeDuration", logos)
        self.assertIn("BindNativeTitleRenderer", logos)
        self.assertIn('GameObject.Find("LogoAndIcons/titleLogo")', logos)
        self.assertNotIn("TITLE_DIAGNOSTICS_BEGIN", logos)
        self.assertIn('Shader.Find("Sprites/Default")', logos)
        self.assertIn("Color color = nativeTitleRenderer!.color", logos)
        self.assertNotIn("nativeTitleRenderer.GetPropertyBlock", logos)
        self.assertNotIn("mainLogo.SetPropertyBlock", logos)
        self.assertIn("LayoutMainLogoBesideNativeTitle", logos)
        self.assertIn("titleBounds.size.y * 0.38f", logos)
        self.assertIn("logoWidth * 0.5f + 0.20f", logos)
        self.assertIn("mainLogo.gameObject.layer = nativeTitleRenderer.gameObject.layer", logos)
        self.assertIn("logoCamera.enabled = false", logos)
        self.assertNotIn("TITLE_FADE_TRACE", logos)
        self.assertIn("new Vector3(0.476f, 0.680f", logos)
        self.assertNotIn("texture.Apply(true, false)", logos)
        self.assertIn("texture.filterMode = FilterMode.Bilinear", logos)
        self.assertIn("color.a *= Mathf.Clamp01(Manager.load.GetFadeValue())", logos)
        self.assertIn('Assets\\ArchipelagoLogo.png', project)
        self.assertIn('mainLogo = CreateSpriteRenderer("ArchipelagoMainMenuLogo", transform)', logos)
        self.assertIn("EnsureLogoCamera", logos)
        self.assertIn("logoCamera.depth = ui.depth - 0.01f", logos)
        self.assertIn("logoCamera.cullingMask = mask", logos)
        self.assertNotIn("ArchipelagoSettingsLogo", logos)
        self.assertIn("client\\Assets\\ArchipelagoLogo.png", package)
        self.assertIn('DefaultServer = "archipelago.gg:"', settings)

    def test_reward_delivery_binds_room_before_suppressing_natural_checks(self) -> None:
        entry = (ROOT / "client" / "ModEntryPoint.cs").read_text(encoding="utf-8")
        delivery = entry.split("private bool DeliverItem(ItemInfo item)", 1)[1].split(
            "private void SuppressRewardDiscoveryMessage", 1
        )[0]
        self.assertLess(
            delivery.index("BindRewardProvenanceRoom()"),
            delivery.index("rewards.TryDeliver("),
        )


if __name__ == "__main__":
    unittest.main()
