local EnemyCodes = {
    MushroomEnemy="slay_shrooman", MushroomBrute="slay_shrooman_brute",
    SlimeBlob="slay_orange_slime", AggressiveSlimeBlob="slay_red_slime",
    CavelingSkirmisher="slay_caveling_skirmisher", CavelingSpearman="slay_caveling_spearman",
    ClayWormSegment="slay_clay_burrower", ["Larva@0"]="slay_larva",
    ["BigLarva@0"]="slay_big_larva", ["Larva@1"]="slay_hive_larva",
    ["BigLarva@1"]="slay_big_hive_larva", AcidLarva="slay_acid_larva",
    Caveling="slay_caveling", CavelingShaman="slay_caveling_shaman",
    CavelingBrute="slay_caveling_brute", AFPestElectric="slay_electro_pest",
    RoyalSlimeBlob="slay_royal_slime", CavelingHunter="slay_caveling_hunter",
    CavelingGardener="slay_caveling_gardener", PoisonSlimeBlob="slay_purple_slime",
    InfectedCaveling="slay_infected_caveling", MoldTentacle="slay_mold_tentacle",
    CrabEnemy="slay_bubble_crab", SmallTentacle="slay_tentacle",
    SlipperySlimeBlob="slay_blue_slime", CavelingScholar="slay_caveling_scholar",
    AncientGolem="slay_core_sentry", BombScarab="slay_bomb_scarab",
    CavelingAssassin="slay_caveling_assassin", CavelingMummy="slay_caveling_mummy",
    LavaSlimeBlob="slay_lava_slime", LavaButterfly="slay_lava_butterfly",
    Mimite="slay_mimite", OrbitalTurret="slay_orbital_turret",
    WormSegment="slay_nilipede", CrystalBigSnail="slay_crystal_snail",
    AmoebaWormSegment="slay_sulfur_worm", AmoebaGiantSegment="slay_colossal_amoeba",
    CicadaNymph="slay_cicada_nymph", GoldenBombScarab="slay_gold_scarab",
    RobotMiner="slay_geobot_miner", RobotPatroller="slay_geobot_patroller",
    RobotSwarmer="slay_geobot_scourer", VoidLarva="slay_void_larva",
    VoidCaveling="slay_void_caveling", VoidCavelingShaman="slay_void_caveling_shaman",
    VoidCavelingBrute="slay_void_caveling_brute",
}

local Bosses = {
    SlimeBoss={code="defeat_glurch", name="Glurch", suffix="the Abominous Mass"},
    BossLarva={code="defeat_ghorm", name="Ghorm", suffix="the Devourer"},
    KingSlime={code="defeat_king_slime", name="King Slime", style="king"},
    LarvaHiveBoss={code="defeat_hive_mother", name="Hive Mother", suffix="the Brood Sovereign"},
    ShamanBoss={code="defeat_malugaz", name="Malugaz", suffix="the Corrupted"},
    BirdBoss={code="defeat_azeos", name="Azeos", suffix="the Sky Titan"},
    PoisonSlimeBoss={code="defeat_ivy", name="Ivy", suffix="the Poisonous Mass"},
    OctopusBoss={code="defeat_omoroth", name="Omoroth", suffix="the Sea Titan"},
    SlipperySlimeBoss={code="defeat_morpha", name="Morpha", suffix="the Aquatic Mass"},
    ScarabBoss={code="defeat_ra_akar", name="Ra-Akar", suffix="the Sand Titan"},
    LavaSlimeBoss={code="defeat_igneous", name="Igneous", suffix="the Molten Mass"},
    SnakeBossSegment={code="defeat_atlantean_worm", name="Atlantean Worm", suffix="the Eunicid Leviathan"},
    HydraBossNature={code="defeat_druidra", name="Druidra", suffix="the Wild Titan"},
    HydraBossSea={code="defeat_crydra", name="Crydra", suffix="the Ice Titan"},
    HydraBossDesert={code="defeat_pyrdra", name="Pyrdra", suffix="the Fire Titan"},
    CoreBoss={code="defeat_core_commander", name="Core Commander", style="commander"},
    WallBoss={code="defeat_urschleim", name="Urschleim", suffix="the Primordial Monolith"},
    GiantCicadaBoss={code="defeat_nimruza", name="Nimruza", style="queen"},
    HydraBossVoid={code="defeat_oblidra", name="Oblidra", suffix="the Void Lord"},
    RobotBoss={code="defeat_sahabar", name="S.A.H.A.B.A.R", style="dotted"},
}

local function bare_name(record)
    return string.gsub(record.definition.name, "^Slay ", "")
end

local function boss_title(slot_name, replacement)
    if replacement.style == "king" then return "King " .. slot_name end
    if replacement.style == "commander" then return "Commander " .. slot_name end
    if replacement.style == "queen" then return slot_name .. ", Queen of the Burrowed Sands" end
    if replacement.style == "dotted" then
        local letters = string.upper(string.gsub(slot_name, "[^%w]", ""))
        return string.gsub(letters, ".", "%0.")
    end
    if replacement.suffix then return slot_name .. " " .. replacement.suffix end
    return slot_name
end

local function reset_reveals()
    for _, record in pairs(CK_CHECKS_BY_ID) do
        if record.randomized then
            record.randomized = nil
            record.item.Name = record.definition.name
            CK_INVALIDATE_CHECK_VISUAL(record.definition.id)
        end
    end
end

function CK_CONFIGURE_RANDOMIZER_REVEALS(slot_data)
    reset_reveals()
    if not slot_data then return end

    if slot_data["randomize_enemies"] == true then
        for source, target in pairs(slot_data["enemy_randomizer_map"] or {}) do
            local source_record = CK_CHECKS_BY_CODE[EnemyCodes[source]]
            local target_record = CK_CHECKS_BY_CODE[EnemyCodes[target]]
            if source_record and target_record then
                source_record.randomized = {
                    icon_id = target_record.definition.id,
                    hidden_name = bare_name(source_record) .. " (???)",
                    revealed_name = bare_name(source_record) .. " (" .. bare_name(target_record) .. ")",
                }
                CK_INVALIDATE_CHECK_VISUAL(source_record.definition.id)
            end
        end
    end

    if slot_data["randomize_bosses"] == true then
        for source, target in pairs(slot_data["boss_randomizer_map"] or {}) do
            local source_boss = Bosses[source]
            local target_boss = Bosses[target]
            local source_record = source_boss and CK_CHECKS_BY_CODE[source_boss.code]
            local target_record = target_boss and CK_CHECKS_BY_CODE[target_boss.code]
            if source_record and target_record then
                source_record.randomized = {
                    icon_id = target_record.definition.id,
                    hidden_name = source_boss.name .. " (???)",
                    revealed_name = boss_title(source_boss.name, target_boss),
                }
                CK_INVALIDATE_CHECK_VISUAL(source_record.definition.id)
            end
        end
    end

    CK_REFRESH_ACCESS_LOGIC()
end
