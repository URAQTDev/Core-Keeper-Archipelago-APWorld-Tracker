local ItemMap = {
    [8405000] = "progressive_workbench_license",
    [8405002] = "progressive_anvil_license",
    [8405003] = "progressive_furnace_license",
    [8405004] = "progressive_automation_table_license",
    [8405005] = "progressive_alchemy_table_license",
    [8405006] = "progressive_jewelry_workbench_license",
    [8405007] = "pouch_workbench_license",
    [8405008] = "boat_workbench_license",
    [8405009] = "fishing_workbench_license",
    [8405010] = "egg_incubator_license",
    [8405011] = "key_casting_table_license",
    [8405012] = "salvage_and_repair_station_license",
    [8405013] = "ancient_hologram_pod_license",
    [8405014] = "table_saw_license",
    [8405029] = "cooking_pot_license",
    [8405015] = "carpenter_s_table_license",
    [8405016] = "distillery_table_license",
    [8405017] = "electronics_table_license",
    [8405018] = "railway_forge_license",
    [8405019] = "go_kart_workbench_license",
    [8405020] = "loom_license",
    [8405021] = "music_workbench_license",
    [8405022] = "livestock_workbench_license",
    [8405023] = "glass_workbench_license",
    [8405024] = "painter_s_table_license",
    [8405025] = "progressive_smithing_table_license",
    [8405026] = "glass_smelter_license",
    [8405027] = "rift_statue_license",
    [8405028] = "upgrade_station_license",
}
local Progressive = {
    progressive_workbench_license = 7,
    progressive_anvil_license = 7,
    progressive_jewelry_workbench_license = 2,
    progressive_alchemy_table_license = 2,
    progressive_automation_table_license = 2,
    progressive_smithing_table_license = 2,
    progressive_furnace_license = 3,
}
local MinimumMode = {
    progressive_workbench_license = 1,
    progressive_anvil_license = 1,
    progressive_furnace_license = 2,
    progressive_automation_table_license = 2,
    progressive_alchemy_table_license = 2,
    progressive_jewelry_workbench_license = 2,
    pouch_workbench_license = 2,
    boat_workbench_license = 2,
    fishing_workbench_license = 2,
    egg_incubator_license = 2,
    key_casting_table_license = 2,
    salvage_and_repair_station_license = 2,
    ancient_hologram_pod_license = 2,
    table_saw_license = 2,
    cooking_pot_license = 2,
    carpenter_s_table_license = 3,
    distillery_table_license = 3,
    electronics_table_license = 3,
    railway_forge_license = 3,
    go_kart_workbench_license = 3,
    loom_license = 3,
    music_workbench_license = 3,
    livestock_workbench_license = 3,
    glass_workbench_license = 3,
    painter_s_table_license = 3,
    progressive_smithing_table_license = 3,
    glass_smelter_license = 3,
    rift_statue_license = 3,
    upgrade_station_license = 3,
}
local CurrentIndex = -1
local CurrentEnabledLicenses = {}

local LicenseNames = {
    progressive_workbench_license = "Progressive Workbench License",
    progressive_anvil_license = "Progressive Anvil License",
    progressive_furnace_license = "Progressive Furnace License",
    progressive_automation_table_license = "Progressive Automation Table License",
    progressive_alchemy_table_license = "Progressive Alchemy Table License",
    progressive_jewelry_workbench_license = "Progressive Jewelry Workbench License",
    pouch_workbench_license = "Pouch Workbench License",
    boat_workbench_license = "Boat Workbench License",
    fishing_workbench_license = "Fishing Workbench License",
    egg_incubator_license = "Egg Incubator License",
    key_casting_table_license = "Key Casting Table License",
    salvage_and_repair_station_license = "Salvage and Repair Station License",
    ancient_hologram_pod_license = "Ancient Hologram Pod License",
    table_saw_license = "Table Saw License",
    cooking_pot_license = "Cooking Pot License",
    carpenter_s_table_license = "Carpenter's Table License",
    distillery_table_license = "Distillery Table License",
    electronics_table_license = "Electronics Table License",
    railway_forge_license = "Railway Forge License",
    go_kart_workbench_license = "Go-Kart Workbench License",
    loom_license = "Loom License",
    music_workbench_license = "Music Workbench License",
    livestock_workbench_license = "Livestock Workbench License",
    glass_workbench_license = "Glass Workbench License",
    painter_s_table_license = "Painter's Table License",
    progressive_smithing_table_license = "Progressive Smithing Table License",
    glass_smelter_license = "Glass Smelter License",
    rift_statue_license = "Rift Statue License",
    upgrade_station_license = "Upgrade Station License",
}

local Groups = {
    "raw_materials", "refined_materials", "unique_materials", "key_items",
    "locked_chests", "seeds", "food", "critters", "enemies", "bosses",
    "cattle_mutilation", "golden_food", "skill_levels", "figurines",
    "oracle_cards", "fish", "valuables", "blocks", "merchantsanity",
    "petsanity", "toolsanity", "weaponsanity", "jewelrysanity",
    "accessanity", "armorsanity",
}
local SlotOptionKeys = {
    raw_materials = "raw_materials",
    refined_materials = "refined_materials",
    unique_materials = "unique_materials",
    key_items = "key_items",
    locked_chests = "locked_chests",
    seeds = "seeds",
    food = "food",
    critters = "critters",
    enemies = "enemies",
    bosses = "bosses",
    cattle_mutilation = "cattle_mutilation",
    golden_food = "goldensanity",
    skill_levels = "skillsanity",
    figurines = "figurinesanity",
    oracle_cards = "cardsanity",
    fish = "fishsanity",
    valuables = "valuablesanity",
    blocks = "blocksanity",
    merchantsanity = "merchantsanity",
    petsanity = "petsanity",
    toolsanity = "toolsanity",
    weaponsanity = "weaponsanity",
    jewelrysanity = "jewelrysanity",
    accessanity = "accessanity",
    armorsanity = "armorsanity",
}

local function reset(slot_data)
    Tracker.BulkUpdate = true
    CurrentIndex = -1
    CurrentEnabledLicenses = {}
    if slot_data and slot_data["enabled_licenses"] then
        for _, name in ipairs(slot_data["enabled_licenses"]) do
            CurrentEnabledLicenses[name] = true
        end
    else
        -- Compatibility with rooms generated before individual license toggles.
        local license_mode = slot_data and slot_data["licenses"] or 0
        local named_modes = {
            none = 0, workbench_anvil = 1, important_crafting = 2,
            major = 2, all = 3,
        }
        local mode = named_modes[license_mode] or tonumber(license_mode) or 0
        for code, name in pairs(LicenseNames) do
            if mode >= (MinimumMode[code] or 3) then
                CurrentEnabledLicenses[name] = true
            end
        end
    end
    for _, code in pairs(ItemMap) do
        local item = Tracker:FindObjectForCode(code)
        if item then
            local randomized = CurrentEnabledLicenses[LicenseNames[code]] == true
            if Progressive[code] then
                item.CurrentStage = randomized and 0 or Progressive[code]
                item.Active = not randomized
                    or code == "progressive_workbench_license"
            else
                item.Active = not randomized
            end
        end
    end
    for _, group in ipairs(Groups) do
        local option = Tracker:FindObjectForCode("option_" .. group)
        if option then option.Active = false end
    end
    if slot_data then
        for group, slot_key in pairs(SlotOptionKeys) do
            local option = Tracker:FindObjectForCode("option_" .. group)
            if option then option.Active = slot_data[slot_key] == true end
        end
        local bosses = Tracker:FindObjectForCode("option_bosses")
        if bosses then bosses.Active = slot_data["bosses"] == true end
        local goal_values = {
            lower_wall = 0,
            defeat_core_commander = 1,
            defeat_sahabar = 2,
            defeat_all_bosses = 3,
            [0] = 3, [1] = 2, [2] = 1, [3] = 0,
        }
        local goal = Tracker:FindObjectForCode("goal_scope")
        if goal then goal.CurrentStage = goal_values[slot_data["goal"]] or 0 end
    else
        for _, group in ipairs(Groups) do
            local option = Tracker:FindObjectForCode("option_" .. group)
            if option then option.Active = true end
        end
        local goal = Tracker:FindObjectForCode("goal_scope")
        if goal then goal.CurrentStage = 3 end
    end
    Tracker.BulkUpdate = false
end

local function item_received(index, id, _name, _player)
    if index <= CurrentIndex then return end
    CurrentIndex = index
    local code = ItemMap[id]
    local item = code and Tracker:FindObjectForCode(code)
    if not item then return end
    if CurrentEnabledLicenses[LicenseNames[code]] ~= true then return end
    if Progressive[code] then
        if not item.Active then
            item.Active = true
        else
            item.CurrentStage = math.min(item.CurrentStage + 1, Progressive[code])
        end
    else
        item.Active = true
    end
end

Archipelago:AddClearHandler("Core Keeper logic reset", reset)
Archipelago:AddItemHandler("Core Keeper logic items", item_received)
