"""Extract and deterministically render the vertical-slice tracker icons."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageOps


SPRITES = {
    "collect_yellow_glowbug": "lootsprite_fireflyPurple",
    "collect_blue_glowbug": "lootsprite_fireflyPurple",
    "collect_green_glowbug": "lootsprite_fireflyPurple",
    "collect_red_glowbug": "lootsprite_fireflyPurple",
    "collect_purple_glowbug": "lootsprite_fireflyPurple",
    "collect_blackbug": "blackbug_idle",
    "collect_larvlet": "larvlet_idle",
    "collect_moon_pincher": "moonCrab_idle",
    "collect_dusk_fairy": "butterflySunset_idle",
    "collect_dream_messenger": "butterflyDreamy_idle",
    "collect_citrus_pinion": "butterflyCitrus_idle",
    "collect_ice_wind": "butterflyIcy_idle",
    "collect_crimson_wing": "butterflyCrimson_idle",
    "collect_little_death": "scorpion_idle",
    "collect_leaf_hopper": "leafhopper_idle",
    "collect_earthworm": "worm_idle",
    "collect_manyleg": "manyleg_idle",
    "collect_pest_bug": "cockroach_idle",
    "collect_sun_pincher": "sunCrab_idle",
    "collect_gem_snail": "tinySnail_idle",
    "collect_snoot_fly": "snootFly_idle",
    "collect_shadow_newt": "newt_idle",
    "collect_drape_ray": "PassageFly_static",
    "collect_sniffling": "shrew_idle",
    "collect_void_larvlet": "lootsprite_larvaCritterVoid",
    "collect_bone_creole": "wall_loot_9",
    "collect_geode": "wall_loot_2",
    "collect_ammonite": "wall_loot_1",
    "collect_triangle_trinket": "wall_loot_10",
    "collect_rusty_spoon": "wall_loot_32",
    "collect_caveling_skull": "wall_loot_3",
    "collect_twisted_agate": "wall_loot_11",
    "collect_old_amulet": "wall_loot_6",
    "collect_ear_plate": "wall_loot_8",
    "collect_amber_fish_egg": "wall_loot_35",
    "collect_golden_starfish": "wall_loot_34",
    "collect_grub_knot": "wall_loot_13",
    "collect_golden_cocoon": "wall_loot_42",
    "collect_grub_pearl": "wall_loot_48",
    "collect_mucus_amoeba": "wall_loot_40",
    "collect_blood_skull": "wall_loot_12",
    "collect_parasite_fossil": "wall_loot_41",
    "collect_petrified_egg": "wall_loot_14",
    "collect_soft_sponge": "wall_loot_36",
    "collect_caveling_perfume": "wall_loot_38",
    "collect_adder_stone": "wall_loot_37",
    "collect_broken_core_idol": "wall_loot_4",
    "collect_enhydro_crystal": "wall_loot_39",
    "collect_precious_urn": "wall_loot_23",
    "collect_amber_chunk": "wall_loot_24",
    "collect_caveling_medal": "wall_loot_50",
    "collect_lost_paddle": "wall_loot_43",
    "collect_leaf_fossil": "wall_loot_0",
    "collect_petrified_coral": "wall_loot_25",
    "collect_mechanical_arm": "wall_loot_21",
    "collect_old_spore_mask": "lootsprites_202",
    "collect_golden_feather": "wall_loot_20",
    "collect_dry_butterfly": "wall_loot_22",
    "collect_hard_thorn": "wall_loot_16",
    "collect_ceremonial_flute": "wall_loot_45",
    "collect_feather_fish_scale": "wall_loot_49",
    "collect_giant_mite": "wall_loot_31",
    "collect_mold_dew": "wall_loot_26",
    "collect_mildew_leaf": "wall_loot_28",
    "collect_fungal_bone": "wall_loot_27",
    "collect_data_slate": "wall_loot_44",
    "collect_mold_shell": "wall_loot_46",
    "collect_chipped_plate": "wall_loot_29",
    "collect_balloon_spore": "wall_loot_17",
    "collect_giant_germ": "wall_loot_47",
    "collect_stone_cap": "wall_loot_30",
    "collect_sealed_beverage": "wall_loot_54",
    "collect_fish_fossil": "wall_loot_59",
    "collect_rusty_fishing_hook": "wall_loot_58",
    "collect_petrified_trilobite": "wall_loot_57",
    "collect_bubble_pearl": "wall_loot_52",
    "collect_forked_coral": "wall_loot_56",
    "collect_golden_needle": "wall_loot_121",
    "collect_opabinia_fossil": "wall_loot_122",
    "collect_fizzy_crystal": "wall_loot_60",
    "collect_giant_squid_eye": "wall_loot_124",
    "collect_polished_shell": "wall_loot_123",
    "collect_shark_tooth": "wall_loot_55",
    "collect_black_bubble_pearl": "wall_loot_53",
    "collect_blue_glass_kalimba": "lootsprites_valentine_52",
    "collect_crystal_sphere": "wall_loot_103",
    "collect_caveling_cup": "wall_loot_110",
    "collect_timeless_hourglass": "wall_loot_106",
    "collect_processor_chip": "wall_loot_105",
    "collect_bent_fork": "wall_loot_109",
    "collect_screen_device": "wall_loot_101",
    "collect_luxurious_handmirror": "wall_loot_104",
    "collect_incense_bowl": "wall_loot_135",
    "collect_blue_glass_shard": "wall_loot_131",
    "collect_caveling_sandal": "wall_loot_137",
    "collect_plume_ball": "wall_loot_132",
    "collect_broken_toy_ship": "wall_loot_158",
    "collect_bag_of_marbles": "wall_loot_143",
    "collect_broken_gourd": "wall_loot_156",
    "collect_kingfish_scale": "wall_loot_157",
    "collect_ancient_makeup_set": "wall_loot_136",
    "collect_ancient_golden_coin": "wall_loot_144",
    "collect_black_desert_diamond": "wall_loot_142",
    "collect_desert_diamond": "wall_loot_141",
    "collect_crystal_spearhead": "wall_loot_139",
    "collect_early_human_skull": "wall_loot_65",
    "collect_charred_caveling_skull": "wall_loot_133",
    "collect_starlight_shards": "wall_loot_162",
    "collect_melting_lava_wing": "wall_loot_140",
    "collect_pickaxe_head": "wall_loot_134",
    "collect_ancient_fishing_hook": "wall_loot_160",
    "collect_fusion_alloy": "wall_loot_161",
    "collect_worker_handcuff": "wall_loot_138",
    "collect_offspring_capsule": "lootsprites_crystal_12",
    "collect_homeworld_reminiscence": "lootsprites_crystal_15",
    "collect_catalyst_gemstone": "lootsprite_crystalCatalyst",
    "collect_chemical_ration": "lootsprites_crystal_16",
    "collect_deepspace_log": "lootsprites_crystal_14",
    "collect_triops_fossil": "lootsprites_crystal_17",
    "collect_suspended_butterfly": "lootsprites_crystal_18",
    "collect_crystal_bone": "lootsprites_crystal_19",
    "collect_agartha_report": "lootsprites_crystal_20",
    "collect_sparkle_opal": "lootsprites_crystal_21",
    "collect_disabled_datapad": "lootsprite_valuableExcavationDatapad",
    "collect_geobot_leg": "lootsprite_valuableExcavationRobotLeg",
    "collect_sahabar_idol": "lootsprite_valuableExcavationTotem",
    "collect_ancient_gem_plate": "wall_loot_67",
    "collect_antique_board_game": "wall_loot_68",
    "collect_mysterious_doll_set": "parsec_pals_dolls",
    "collect_ritual_goblet": "wall_loot_72",
    "collect_golden_whistle": "wall_loot_108",
    "collect_caveling_prophet_mask": "wall_loot_145",
    "collect_old_journal": "wall_loot_70",
    "collect_white_whistle": "wall_loot_164",
    "collect_caveling_effigy": "wall_loot_102",
    "collect_caveling_doll": "wall_loot_18",
    "collect_seismic_clock": "wall_loot_69",
    "collect_music_bowl": "wall_loot_71",
    "collect_frozen_flame": "wall_loot_146",
    "collect_golden_caveling_mask": "wall_loot_66",
    "collect_small_caveling_skull": "wall_loot_19",
    "collect_playing_dice": "wall_loot_107",
    "collect_pictographic_sketchbook": "lootsprite_owlunaeNotebook",
    "collect_shrooman_figurine": "wall_loot_126",
    "collect_shrooman_brute_figurine": "lootsprite_shroomanBruteTrophy",
    "collect_slime_figurine": "wall_loot_78",
    "collect_red_slime_figurine": "wall_loot_80",
    "collect_caveling_skirmisher_figurine": "wall_loot_165",
    "collect_caveling_spearman_figurine": "wall_loot_166",
    "collect_clay_burrower_figurine": "lootsprites_yearend_10",
    "collect_larva_figurine": "wall_loot_82",
    "collect_hive_larva_figurine": "wall_loot_84",
    "collect_big_larva_figurine": "wall_loot_83",
    "collect_big_hive_larva_figurine": "wall_loot_85",
    "collect_acid_larva_figurine": "wall_loot_81",
    "collect_cocoon_figurine": "wall_loot_116",
    "collect_caveling_figurine": "wall_loot_86",
    "collect_caveling_shaman_figurine": "wall_loot_89",
    "collect_caveling_brute_figurine": "wall_loot_91",
    "collect_electro_pest_figurine": "lootsprite_electroPestTrophy",
    "collect_caveling_hunter_figurine": "wall_loot_88",
    "collect_caveling_gardener_figurine": "wall_loot_87",
    "collect_snare_plant_figurine": "wall_loot_96",
    "collect_purple_slime_figurine": "wall_loot_79",
    "collect_floracada_figurine": "lootsprite_cicada_NatureTrophy",
    "collect_infected_caveling_figurine": "wall_loot_90",
    "collect_mold_tentacle_figurine": "wall_loot_95",
    "collect_bubble_crab_figurine": "wall_loot_118",
    "collect_tentacle_figurine": "wall_loot_94",
    "collect_blue_slime_figurine": "wall_loot_97",
    "collect_caveling_scholar_figurine": "wall_loot_119",
    "collect_core_sentry_figurine": "wall_loot_120",
    "collect_bomb_scarab_figurine": "wall_loot_152",
    "collect_caveling_assassin_figurine": "wall_loot_154",
    "collect_caveling_mummy_figurine": "lootsprite_cavelingMummyTrophy",
    "collect_lava_slime_figurine": "wall_loot_155",
    "collect_lava_butterfly_figurine": "wall_loot_153",
    "collect_mimite_figurine": "lootsprites_crystal_165",
    "collect_orbital_turret_figurine": "lootsprites_crystal_190",
    "collect_nilipede_figurine": "lootsprites_crystal_306",
    "collect_sulfur_worm_figurine": "lootsprite_sulfurWormTrophy",
    "collect_colossal_amoeba_figurine": "lootsprite_giantAmoebaTrophy",
    "collect_gold_scarab_figurine": "lootsprite_goldenBombScarabTrophy",
    "collect_cicada_nymph_figurine": "lootsprite_cicadaNymphTrophy",
    "collect_geobot_miner_figurine": "lootsprite_robotChargerTrophy",
    "collect_geobot_patroller_figurine": "lootsprite_robotPatrollerTrophy",
    "collect_geobot_scourer_figurine": "lootsprite_robotSwarmerTrophy",
    "collect_void_larva_cocoon_figurine": "lootsprite_cocoonVoidTrophy",
    "collect_void_larva_figurine": "lootsprite_larvaVoidTrophy",
    "collect_void_caveling_figurine": "lootsprite_cavelingVoidTrophy",
    "collect_void_caveling_shaman_figurine": "lootsprite_cavelingShamanVoidTrophy",
    "collect_void_caveling_brute_figurine": "lootsprite_cavelingBruteVoidTrophy",
    "collect_core_figurine": "wall_loot_100",
    "collect_glurch_figurine": "wall_loot_74",
    "collect_ghorm_figurine": "wall_loot_76",
    "collect_hive_mother_figurine": "wall_loot_77",
    "collect_malugaz_figurine": "wall_loot_93",
    "collect_king_slime_figurine": "wall_loot_127",
    "collect_azeos_figurine": "wall_loot_92",
    "collect_ivy_figurine": "wall_loot_75",
    "collect_omoroth_figurine": "wall_loot_115",
    "collect_morpha_figurine": "wall_loot_117",
    "collect_atlantean_worm_figurine": "lootsprites_crystal_78",
    "collect_ra_akar_figurine": "wall_loot_151",
    "collect_igneous_figurine": "wall_loot_150",
    "collect_druidra_figurine": "lootsprites_porting_8",
    "collect_crydra_figurine": "lootsprites_porting_7",
    "collect_pyrdra_figurine": "lootsprites_porting_6",
    "collect_core_commander_figurine": "lootsprites_porting_42",
    "collect_unleashed_core_commander_figurine": "lootsprites_porting_43",
    "collect_urschleim_figurine": "lootsprite_wallBossTrophy",
    "collect_nimruza_figurine": "lootsprite_nimruzaTrophy",
    "collect_sahabar_trophy": "lootsprite_robotBossTrophy",
    "collect_oblidra_figurine": "lootsprite_voidHydraTrophy",
    "collect_orange_cave_guppy": "lootsprites_290",
    "collect_blue_cave_guppy": "lootsprites_292",
    "collect_rock_jaw": "lootsprites_294",
    "collect_gem_crab": "lootsprites_296",
    "collect_dagger_fin": "lootsprites_316",
    "collect_pink_palace_fish": "lootsprites_318",
    "collect_teal_palace_fish": "lootsprites_320",
    "collect_crown_squid": "lootsprites_322",
    "collect_yellow_blister_head": "lootsprites_324",
    "collect_green_blister_head": "lootsprites_326",
    "collect_devil_worm": "lootsprites_328",
    "collect_vampire_eel": "lootsprites_330",
    "collect_mold_shark": "lootsprites_332",
    "collect_rot_fish": "lootsprites_334",
    "collect_black_steel_urchin": "lootsprites_336",
    "collect_azure_feather_fish": "lootsprites_338",
    "collect_emerald_feather_fish": "lootsprites_340",
    "collect_spirit_veil": "lootsprites_342",
    "collect_astral_jelly": "lootsprites_344",
    "collect_bottom_tracer": "lootsprites_585",
    "collect_silver_dart": "lootsprites_589",
    "collect_golden_dart": "lootsprites_587",
    "collect_pink_coralotl": "lootsprites_591",
    "collect_white_coralotl": "lootsprites_593",
    "collect_solid_spikeback": "lootsprites_863",
    "collect_sandy_spikeback": "lootsprites_865",
    "collect_gray_dune_tail": "lootsprites_867",
    "collect_brown_dune_tail": "lootsprites_869",
    "collect_tornis_kingfish": "lootsprites_871",
    "collect_dark_lava_eater": "lootsprites_873",
    "collect_bright_lava_eater": "lootsprites_875",
    "collect_verdant_dragonfish": "lootsprites_877",
    "collect_elder_dragonfish": "lootsprites_879",
    "collect_starlight_nautilus": "lootsprites_881",
    "collect_beryll_angle_fish": "lootsprites_crystal_100",
    "collect_glistening_deepstalker": "lootsprites_crystal_104",
    "collect_cosmic_form": "lootsprites_crystal_108",
    "collect_jasper_angle_fish": "lootsprites_crystal_102",
    "collect_splendid_deepstalker": "lootsprites_crystal_106",
    "collect_terra_trilobite": "lootsprite_terraTrilobite",
    "collect_litho_trilobite": "lootsprite_lithoTrilobite",
    "collect_greenhorn_pico": "lootsprite_greenhornPico",
    "collect_pinkhorn_pico": "lootsprite_pinkhornPico",
    "collect_riftian_lampfish": "lootsprite_riftianLampfish",
    "collect_dirt_block": "lootsprite_dirtBlock",
    "collect_turf_block": "lootsprite_turfBlock",
    "collect_sand_block": "lootsprite_sandBlock",
    "collect_meadow_block": "lootsprite_meadowBlock",
    "collect_clay_block": "lootsprite_clayBlock",
    "collect_larva_hive_block": "lootsprite_hiveBlock",
    "collect_stone_block": "lootsprite_stoneBlock",
    "collect_grass_block": "lootsprite_grassBlock",
    "collect_mold_block": "lootsprite_moldBlock",
    "collect_beach_block": "lootsprite_beachBlock",
    "collect_metropolis_block": "lootsprite_cityBlock",
    "collect_desert_block": "lootsprite_desertBlock",
    "collect_desert_temple_block": "lootsprite_desertTempleBlock",
    "collect_maze_block": "lootsprite_desertMazeBlock",
    "collect_lava_rock_block": "lootsprite_lavaBlock",
    "collect_crystal_block": "lootsprite_crystalBlock",
    "collect_alien_tech_block": "lootsprite_alienBlock",
    "collect_fossil_block": "lootsprite_passageBlock",
    "collect_oasis_block": "lootsprite_oasisBlock",
    "collect_excavation_block": "lootsprite_industrialWallRedBlock",
    "collect_industrial_block": "lootsprite_industrialPuzzleBlock",
    "collect_tuff_block": "lootsprite_industrialRockBlock",
    "collect_void_infused_tuff_block": "lootsprite_voidInfusedTuffBlock",
    "collect_ancient_coin": "lootsprites_160",
    "collect_wood": "lootsprite_wood",
    "collect_copper_ore": "lootsprite_copperOre",
    "collect_tin_ore": "lootsprite_tinOre",
    "collect_iron_ore": "lootsprite_ironOre",
    "collect_gold_ore": "lootsprite_goldOre",
    "collect_scarlet_ore": "lootsprites_216",
    "collect_octarine_ore": "lootsprites_348",
    "collect_galaxite_ore": "lootsprites_718",
    "collect_solarite_ore": "lootsprite_solariteOre",
    "collect_pandorium_ore": "lootsprite_pandoriumOre",
    "collect_relucite_ore": "lootsprite_reluciteOre",
    "collect_coral_wood": "lootsprites_354",
    "collect_gleam_wood": "lootsprite_gleamWood",
    "collect_ancient_gemstone": "lootsprite_ancientGemstone",
    "collect_jungle_emerald": "lootsprites_crystal_279",
    "collect_ocean_sapphire": "lootsprites_crystal_281",
    "collect_desert_ruby": "lootsprites_crystal_277",
    "collect_slime": "lootsprite_slimeOrange",
    "collect_poison_slime": "lootsprite_slimePoison",
    "collect_slippery_slime": "lootsprite_slimeSlippery",
    "collect_magma_slime": "lootsprite_slimeLava",
    "collect_fiber": "lootsprites_44",
    "collect_wool": "lootspritesAnimalUpdate_74",
    "collect_strolly_poly_plate": "lootspritesAnimalUpdate_82",
    "collect_mechanical_part": "lootsprites_162",
    "collect_scrap_parts": "lootsprite_scrapParts",
    "collect_ancient_feather": "lootsprites_200",
    "collect_sea_shell": "lootsprites_298",
    "collect_calcified_shell": "lootsprite_calcifiedBone",
    "collect_cytoplasm": "lootsprite_cytoplasm",
    "collect_corrupted_alloy": "lootsprite_corruptedAlloy",
    "collect_scarab_wingcover": "lootsprites_729",
    "collect_blasting_dung": "lootsprite_blastingDung",
    "collect_copper_bar": "lootsprite_copperBar",
    "collect_tin_bar": "lootsprite_tinBar",
    "collect_iron_bar": "lootsprite_ironBar",
    "collect_gold_bar": "lootsprite_goldBar",
    "collect_scarlet_bar": "lootsprite_scarletBar",
    "collect_octarine_bar": "lootsprite_octarineBar",
    "collect_galaxite_bar": "lootsprite_galaxiteBar",
    "collect_solarite_bar": "lootsprite_solariteBar",
    "collect_pandorium_bar": "lootsprite_pandoriumBar",
    "collect_relucite_bar": "lootsprite_reluciteBar",
    "collect_plank": "lootsprites_88",
    "collect_coral_wood_plank": "lootsprites_669",
    "collect_gleam_wood_plank": "lootsprites_crystal_215",
    "collect_glass_piece": "lootspritesAnimalUpdate_38",
    "collect_crystal_skull_shard": "lootsprites_508",
    "collect_chipped_blade": "lootsprites_451",
    "collect_clear_gemstone": "lootsprites_453",
    "collect_shutdown_protocol": "lootsprites_641",
    "collect_anomaly_report": "lootsprites_637",
    "collect_overwrite_transcript": "lootsprites_639",
    "collect_channeling_gemstone": "lootsprite_channelingGemstone",
    "collect_fractured_limbs": "lootsprite_fracturedLimbs",
    "collect_energy_string": "lootsprite_energyString",
    "collect_crystal_meteor_shard": "lootspritesAnimalUpdate_67",
    "collect_pink_hydra_eye": "lootsprites_porting_14",
    "collect_white_hydra_eye": "lootsprites_porting_15",
    "collect_oblivion_fragment": "lootsprite_oblivionFragment",
    "collect_coiled_branch": "lootsprite_legendCoiledBranch",
    "collect_magma_rod": "lootsprite_legendMoltenRod",
    "collect_frozen_orb": "lootsprite_legendFrozenOrb",
    "collect_void_forged_barrel": "lootsprite_legendVoidBarrel",
    "collect_sanctified_firing_core": "lootsprite_legendFiringCore",
    "collect_sahabar_mortar_housing": "lootsprite_legendHousingFrame",
    "collect_copper_key": "lootsprites_843",
    "collect_iron_key": "lootsprites_845",
    "collect_scarlet_key": "lootsprites_847",
    "collect_octarine_key": "lootsprites_849",
    "collect_galaxite_key": "lootsprites_851",
    "collect_solarite_key": "lootsprites_crystal_197",
    "collect_relucite_key": "lootsprite_reluciteKey",
    "collect_ghorm_horn": "lootsprites_86",
    "collect_glurch_eye": "lootsprites_112",
    "collect_stolen_crystal_heart": "lootsprites_116",
    "collect_admin_key": "lootsprites_653",
    "collect_azeos_feather_fan": "lootsprite_afSmallDestructible",
    "collect_omoroth_compass": "lootsprites_487",
    "collect_ra_akar_automaton": "wall_loot_147",
    "collect_brood_void_neuron": "lootsprite_voidNeuron",
    "collect_herald_void_neuron": "lootsprite_voidNeuronRobotBoss",
    "collect_heart_berry_seed": "lootsprites_77",
    "collect_glow_tulip_seed": "lootsprite_seedGlowTulip",
    "collect_bomb_pepper_seed": "lootsprite_seedBombPepper",
    "collect_carrock_seed": "lootsprite_seedCarrock",
    "collect_puffungi_seed": "lootsprite_seedPuffungi",
    "collect_root_seed": "lootsprite_seedWoodRoot",
    "collect_grub_kapok_seed": "lootsprite_seedGrubKapokFiber",
    "collect_coral_wood_seed": "lootsprite_seedCoralRoot",
    "collect_bloat_oat_seed": "lootsprite_seedBloatOat",
    "collect_pewpaya_seed": "lootsprite_seedPewpaya",
    "collect_pinegrapple_seed": "lootsprite_seedPinegrapple",
    "collect_sunrice_seed": "lootsprite_seedSunrice",
    "collect_lunacorn_seed": "lootsprite_seedLunacorn",
    "collect_gleam_wood_seed": "lootsprite_seedGleamwoodRoot",
    "collect_oracle_card_aura": "wall_loot_98",
    "collect_oracle_card_entity": "wall_loot_73",
    "collect_oracle_card_brilliance": "wall_loot_99",
    "collect_oracle_card_wisdom": "wall_loot_111",
    "collect_oracle_card_metropolis": "wall_loot_113",
    "collect_oracle_card_inspiration": "wall_loot_112",
    "collect_oracle_card_radiance": "wall_loot_128",
    "collect_oracle_card_temperance": "wall_loot_129",
    "collect_oracle_card_endurance": "wall_loot_130",
    "collect_oracle_deck": "lootsprites_859",
    "collect_mushroom": "lootsprite_mushroom",
    "collect_giant_mushroom": "lootsprite_giantMushroom",
    "collect_glowing_mushroom": "lootsprite_glowingMushroom",
    "collect_heart_berry": "lootsprites_66",
    "collect_glow_tulip": "lootsprites_80",
    "collect_bomb_pepper": "lootsprites_84",
    "collect_carrock": "lootsprites_230",
    "collect_puffungi": "lootsprites_234",
    "collect_bloat_oat": "lootsprites_687",
    "collect_pewpaya": "lootsprites_693",
    "collect_pinegrapple": "lootsprites_699",
    "collect_sunrice": "lootsprites_crystal_201",
    "collect_lunacorn": "lootsprites_crystal_203",
    "collect_larva_meat": "lootsprites_118",
    "collect_dodo_egg": "lootsprite_egg",
    "collect_marbled_meat": "lootspritesAnimalUpdate_76",
    "collect_meadow_milk": "lootsprite_meadowMilk",
    "collect_amber_larva": "lootsprites_123",
    "collect_atlantean_worm_heart": "lootsprites_crystal_86",
    "collect_paradise_fruit_basket": "lootsprite_fruitBasket",
    "collect_splendid_amalgam": "lootsprite_liquidMetal",
    "collect_oblidra_heart": "lootsprite_hollowHeart",
    "collect_golden_heart_berry": "lootsprites_471",
    "collect_golden_glow_tulip": "lootsprites_473",
    "collect_golden_bomb_pepper": "lootsprites_475",
    "collect_golden_carrock": "lootsprites_477",
    "collect_golden_puffungi": "lootsprites_479",
    "collect_golden_bloat_oat": "lootsprites_689",
    "collect_golden_pewpaya": "lootsprites_695",
    "collect_golden_pinegrapple": "lootsprites_701",
    "collect_golden_sunrice": "lootsprites_crystal_209",
    "collect_golden_lunacorn": "lootsprites_crystal_211",
    "collect_shiny_larva_meat": "lootsprites_122",
    "slay_shrooman": "shrooman",
    "slay_shrooman_brute": "shroomanBrute_idle",
    "slay_orange_slime": "slimeBlob_orange_idle",
    "slay_red_slime": "slimeBlob_red_idle",
    "slay_caveling_skirmisher": "cavelingSkirmisher_idle",
    "slay_caveling_spearman": "cavelingSpearman_idle",
    "slay_clay_burrower": "worm_idle",
    "slay_larva": "larva_idle",
    "slay_big_larva": "bigLarva_idle",
    "slay_hive_larva": "larva_move",
    "slay_big_hive_larva": "bigLarva_move",
    "slay_acid_larva": "acidLarva_idle",
    "slay_cocoon": "cocoon_idle",
    "slay_caveling": "caveling_idle",
    "slay_caveling_shaman": "cavelingShaman_idle",
    "slay_caveling_brute": "cavelingBrute_idle",
    "slay_electro_pest": "pet_electropest_enemy_icon",
    "slay_royal_slime": "slimeBlob_royal_idle",
    "slay_caveling_hunter": "cavelingHunter_idle",
    "slay_caveling_gardener": "cavelingGardener_idle",
    "slay_snare_plant": "snarePlant_idle",
    "slay_purple_slime": "slimeBlob_poison_idle",
    "slay_infected_caveling": "infectedCaveling_idle",
    "slay_mold_tentacle": "tentacleEnemy_mold_idle",
    "slay_bubble_crab": "bubbleCrab_idle",
    "slay_tentacle": "tentacleEnemy_idle",
    "slay_blue_slime": "slimeBlob_slippery_idle",
    "slay_caveling_scholar": "cavelingScholar_idle",
    "slay_core_sentry": "ancientGolem_idle",
    "slay_bomb_scarab": "bombScarab_idle",
    "slay_caveling_assassin": "cavelingAssassin_idle",
    "slay_caveling_mummy": "cavelingMummy_",
    "slay_lava_slime": "slimeBlob_lava_idle",
    "slay_lava_butterfly": "lavaButterfly_idle",
    "slay_mimite": "lootsprites_creative_mode_238",
    "slay_orbital_turret": "orbitalTurret_moveEase",
    "slay_nilipede": "nilipedeHead",
    "slay_crystal_snail": "snailShellCrystal_healthy",
    "slay_sulfur_worm": "lootsprite_sulfurWorm",
    "slay_colossal_amoeba": "amoebaWormHead_",
    "slay_cicada_nymph": "cicadaNymph_idle",
    "slay_gold_scarab": "lootsprite_bombScarabGolden",
    "slay_geobot_miner": "lootsprite_robotCharger",
    "slay_geobot_patroller": "robotPatroller_idle",
    "slay_geobot_scourer": "robotSwarmer_idle",
    "slay_void_larva_cocoon": "cocoon_void_idle",
    "slay_void_larva": "larva_void_idle",
    "slay_void_caveling": "lootsprite_cavelingVoid",
    "slay_void_caveling_shaman": "lootsprite_cavelingShamanVoid",
    "slay_moolin": "cow_idle",
    "slay_bambuck": "goat_idle",
    "slay_strolly_poly": "rolyPoly_idle",
    "slay_kelple": "turtle_idle",
    "slay_dodo": "dodo_idle",
    "slay_drohmble": "camel_idle",
    "slay_void_caveling_brute": "lootsprite_cavelingBruteVoid",
    # A clean single-frame Glurch render is layered in the shipped animation
    # atlas. Use the exact in-game summon icon until the layer compositor is
    # evidence-validated; never substitute wiki art.
    "defeat_glurch": "summoningItem_glurch",
    "defeat_hive_mother": "lootsprite_hiveMotherScanner",
    "defeat_king_slime": "summoningItem_kingSlime",
    "defeat_ghorm": "summoningItem_ghorm",
    "defeat_malugaz": "summoningItem_shamanBoss",
    "defeat_azeos": "bossMural_Azeos",
    "defeat_ivy": "lootsprite_ivyThePoisonousMassScanner",
    "defeat_omoroth": "lootsprite_omorothTheSeaTitanScanner",
    "defeat_morpha": "lootsprite_morphaTheAquaticMassScanner",
    "defeat_ra_akar": "lootsprite_raakarTheSandTitanScanner",
    "defeat_igneous": "lootsprite_igneousTheMoltenMassScanner",
    "defeat_druidra": "hydraBait_nature",
    "defeat_crydra": "hydraBait_sea",
    "defeat_pyrdra": "hydraBait_desert",
    "defeat_atlantean_worm": "lootsprite_atlanteanWormScanner",
    "defeat_core_commander": "summoningItem_coreCommander",
    "defeat_urschleim": "lootsprite_urschleimScanner",
    "defeat_nimruza": "lootsprite_nimruzaScanner",
    "defeat_oblidra": "lootsprite_oblidraTheVoidLordScanner",
    "defeat_sahabar": "lootsprite_sahabarScanner",
    "unlock_locked_copper_chest": "chestCopperLocked",
    "unlock_locked_iron_chest": "chestIronLocked",
    "unlock_locked_scarlet_chest": "chestScarletLocked",
    "unlock_locked_octarine_chest": "chestOctarineLocked",
    "unlock_locked_galaxite_chest": "chestGalaxiteLocked",
    "unlock_locked_solarite_chest": "chestSolariteLocked",
    "unlock_locked_relucite_chest": "chestReluciteLocked",
    "collect_wood_pickaxe": "pickaxeWood_0",
    "collect_copper_pickaxe": "pickaxe_0",
    "collect_tin_pickaxe": "pickaxe_tin_0",
    "collect_hand_drill": "drilltool_blue_4",
    "collect_iron_pickaxe": "pickaxe_iron_0",
    "collect_scarlet_pickaxe": "pickaxe_scarlet_0",
    "collect_scarlet_hand_drill": "drilltool_red_4",
    "collect_ancient_pickaxe": "pickaxe_ancient_0",
    "collect_octarine_pickaxe": "pickaxe_octarine_0",
    "collect_galaxite_pickaxe": "pickaxe_galaxite_0",
    "collect_solarite_pickaxe": "pickaxe_solarite_0",
    "collect_copper_sledge_hammer": "sledge_copper_0",
    "collect_tin_sledge_hammer": "sledge_tin_0",
    "collect_iron_sledge_hammer": "sledge_iron_0",
    "collect_scarlet_sledge_hammer": "sledge_scarlet_0",
    "collect_octarine_sledge_hammer": "sledge_octarine_0",
    "collect_galaxite_sledge_hammer": "sledge_galaxite_0",
    "collect_wood_shovel": "ShovelWood_0",
    "collect_copper_shovel": "shovel_copper_0",
    "collect_tin_shovel": "shovel_tin_0",
    "collect_iron_shovel": "Shovel_0",
    "collect_scarlet_shovel": "shovel_scarlet_0",
    "collect_octarine_shovel": "shovel_octarine_0",
    "collect_galaxite_shovel": "shovel_galaxite_0",
    "collect_wooden_hoe": "hoe_wood_0",
    "collect_watering_can": "lootsprite_waterCan",
    "collect_copper_hoe": "hoe_copper_0",
    "collect_garden_trowel": "lootsprite_gardenTrowel",
    "collect_tin_hoe": "hoe_tin_0",
    "collect_iron_hoe": "hoe_iron_0",
    "collect_large_watering_can": "lootsprite_largeWaterCan",
    "collect_octarine_garden_trowel": "lootsprite_gardenTrowelOctarine",
    "collect_wood_fishing_rod": "fishing_rod_wood_0",
    "collect_tin_fishing_rod": "fishing_rod_tin_0",
    "collect_iron_fishing_rod": "fishing_rod_iron_0",
    "collect_scarlet_fishing_rod": "fishing_rod_scarlet_0",
    "collect_octarine_fishing_rod": "fishing_rod_octarine_0",
    "collect_galaxite_fishing_rod": "fishing_rod_galaxite_0",
    "collect_solarite_fishing_rod": "fishing_rod_solarite_0",
    "collect_scarlet_hoe": "hoe_scarlet_0",
    "collect_bug_net": "bug_net_0",
    "collect_wooden_sword": "sword_wood_0",
    "collect_copper_sword": "sword_copper_0",
    "collect_tin_sword": "sword_tin_0",
    "collect_slime_sword": "sword_slime_0",
    "collect_iron_sword": "sword_iron_0",
    "collect_scarlet_sword": "sword_scarlet_0",
    "collect_broken_handle": "broken_sword_legendary_0",
    "collect_poisonous_sickle": "poison_sickle_0",
    "collect_octarine_sword": "sword_octarine_0",
    "collect_slippery_slime_sword": "slippery_sword_slime_0",
    "collect_galaxite_sword": "sword_galaxite_0",
    "collect_solarite_sword": "lootsprite_solariteSword",
    "collect_hydra_bone_sword": "lootsprites_porting_26",
    "collect_atlantean_worm_sword": "lootsprites_crystal_85",
    "collect_rusty_dagger": "lootsprites_crystal_189",
    "collect_tin_dagger": "tin_dagger_0",
    "collect_scarlet_dagger": "scarlet_dagger_0",
    "collect_ritual_dagger": "ritual_dagger_0",
    "collect_galaxite_dagger": "lootsprites_1029",
    "collect_tin_axe": "tin_axe_0",
    "collect_battle_axe": "lootsprite_battleAxe",
    "collect_octarine_axe": "lootsprite_octarineAxe",
    "collect_anchor_axe": "lootsprite_anchorAxe",
    "collect_lava_battle_axe": "lootsprite_lavaAxe",
    "collect_pandorium_axe": "lootsprite_pandoriumAxe",
    "collect_hunting_spear": "hunting_spear_lootsprite",
    "collect_iron_halberd": "lootsprites_crystal_117",
    "collect_prehistoric_crystal_spear": "ancient_spear_lootSprite",
    "collect_larva_spike_club": "lootsprite_larvaSpikeClub",
    "collect_pipe_club": "lootsprite_pipeClub",
    "collect_crystal_shard_club": "lootsprite_shardClub",
    "collect_void_club": "lootsprite_voidClub",
    "collect_tentacle_whip": "tentacle_whip_0",
    "collect_obliteration_ray": "laserdrill_4",
    "collect_splintered_wooden_sword": "lootsprite_daresielSword",
    "collect_wood_bow": "lootsprites_575",
    "collect_iron_bow": "lootsprites_569",
    "collect_octarine_bow": "lootsprites_573",
    "collect_wood_crossbow": "lootsprites_crystal_122",
    "collect_scarlet_crossbow": "lootsprites_crystal_124",
    "collect_solarite_crossbow": "lootsprites_crystal_126",
    "collect_slingshot": "slingshot_0",
    "collect_flintlock_musket": "musket_0",
    "collect_blowpipe": "blowpipe_0",
    "collect_bubble_gun": "bubbleGun_0",
    "collect_scrapzooka": "hand_mortar_0",
    "collect_grubzooka": "grubzooka_0",
    "collect_shellzooka": "lootsprites_1028",
    "collect_burnzooka": "lootsprites_1031",
    "collect_stone_mortar": "lootsprite_mortarStone",
    "collect_volcano_mortar": "lootsprite_mortarMagma",
    "collect_throwing_daggers": "lootsprites_781",
    "collect_galaxite_chakram": "lootsprites_1013",
    "collect_ricochet_shuriken": "lootsprites_crystal_299",
    "collect_void_gun": "lootsprites_porting_59",
    "collect_quill_rifle": "lootsprite_quillRifle",
    "collect_scrap_minigun": "lootsprite_minigun",
    "collect_flamethrower": "lootsprite_flamethrower",
    "collect_simple_staff": "lootsprite_basicStaff",
    "collect_sticky_stick": "lootsprites_crystal_116",
    "collect_fireball_staff": "lootsprites_485",
    "collect_arcane_staff": "lootsprite_arcaneStaff",
    "collect_noxious_meteor_staff": "lootsprite_lesserMeteorStaff",
    "collect_scholar_s_staff": "Scholar_staff_lootsprite",
    "collect_sun_caller": "lootsprite_suncallerStaff",
    "collect_chaos_staff": "lootsprite_chaosStaff",
    "collect_corrupted_meteor_staff": "lootsprite_meteorStaff",
    "collect_zealot_s_scimitar": "lootsprite_zealotSword",
    "collect_tome_of_the_dark": "lootsprite_summoningTomeBat",
    "collect_tome_of_breach": "lootsprite_summoningTomePickaxe",
    "collect_tome_of_ashes": "lootsprite_summoningTomeFireMite",
    "collect_tome_of_the_dead": "lootsprite_summoningTomeSkull",
    "collect_tome_of_sprouts": "lootsprite_summoningTomePoisonPlant",
    "collect_tome_of_the_deep": "lootsprite_summoningTomeJellyfish",
    "collect_tome_of_decay": "lootsprite_summoningTomeHand",
    "collect_small_backpack": "lootspritesAnimalUpdate_60",
    "collect_miner_backpack": "lootsprites_282",
    "collect_explorer_backpack": "lootsprites_443",
    "collect_ghorm_s_stomach_backpack": "lootsprites_284",
    "collect_scarlet_shell_backpack": "lootsprites_286",
    "collect_octarine_backpack": "lootsprites_486",
    "collect_morpha_s_bubble_backpack": "lootsprites_581",
    "collect_scholar_backpack": "lootsprite_scholarBag",
    "collect_small_ore_and_block_pouch": "lootsprite_oreBlockPouch",
    "collect_medium_ore_and_block_pouch": "lootsprite_oreBlockPouchLarge",
    "collect_large_ore_and_block_pouch": "lootsprite_oreBlockPouchEpic",
    "collect_small_seed_and_crop_pouch": "lootsprite_plantPouch",
    "collect_medium_seed_and_crop_pouch": "lootsprite_plantPouchLarge",
    "collect_large_seed_and_crop_pouch": "lootsprite_plantPouchEpic",
    "collect_small_fish_pouch": "lootsprite_fishPouch",
    "collect_medium_fish_pouch": "lootsprite_fishPouchLarge",
    "collect_large_fish_pouch": "lootsprite_fishPouchEpic",
    "collect_small_valuable_pouch": "lootsprite_valuablePouch",
    "collect_medium_valuable_pouch": "lootsprite_valuablePouchLarge",
    "collect_large_valuable_pouch": "lootsprite_valuablePouchEpic",
    "collect_potion_pouch": "lootsprite_potionPouch",
    "collect_medium_potion_pouch": "lootsprite_potionPouchLarge",
    "collect_large_potion_pouch": "lootsprite_potionPouchEpic",
    "collect_critter_pouch": "lootsprite_critterPouch",
    "collect_medium_critter_pouch": "lootsprite_critterPouchLarge",
    "collect_large_critter_pouch": "lootsprite_critterPouchEpic",
    "collect_small_lantern": "lootsprites_445",
    "collect_lantern": "lootsprites_280",
    "collect_orb_lantern": "lootsprites_278",
    "collect_pearl_lantern": "lootsprites_crystal_118",
    "collect_soul_lantern": "lootsprite_soulLantern",
    "collect_wooden_shield": "armor_lootsprites_126",
    "collect_iron_shield": "lootsprites_crystal_187",
    "collect_toxic_defender": "armor_lootsprites_128",
    "collect_octarine_shield": "armor_lootsprites_140",
    "collect_sentry_shield": "armor_lootsprites_174",
    "collect_scorching_aegis": "lootsprites_779",
    "collect_hydra_bone_shield": "lootsprites_porting_27",
    "collect_swift_feather": "lootsprites_500",
    "collect_azeos_dash_feather": "lootsprites_679",
    "collect_rift_lens": "lootsprite_riftLens",
    "collect_blue_leather_tome": "lootsprites_514",
    "collect_royal_gel": "lootsprites_722",
    "collect_golden_jellyfish": "lootsprites_673",
    "collect_caveling_i_d": "lootsprites_677",
    "collect_turtle_shell": "lootsprites_675",
    "collect_concealed_blade": "lootsprites_819",
    "collect_moonstone": "lootsprite_moonstone",
    "collect_omoroth_s_beak": "lootsprites_681",
    "collect_smithing_glove": "lootsprites_821",
    "collect_crystal_meteor_chunk": "lootsprites_755",
    "collect_pet_rock": "lootsprites_crystal_219",
    "collect_core_iris": "lootsprites_899",
    "collect_hydra_tooth": "lootsprites_porting_28",
    "collect_trinity_heart": "lootsprites_porting_40",
    "collect_minion_kindler": "lootsprite_skeletonCrestMinor",
    "collect_minion_detonator": "lootsprite_skeletonCrest",
    "collect_scratched_stone": "lootsprite_scratchedRock",
    "collect_magnet": "lootsprite_magnet",
    "collect_remote_boom_clicker": "lootsprite_remoteDetonator",
    "collect_copper_cross_necklace": "armor_lootsprites_22",
    "collect_polished_copper_cross_necklace": "armor_lootsprites_22",
    "collect_iron_chunk_necklace": "armor_lootsprites_34",
    "collect_polished_iron_chunk_necklace": "armor_lootsprites_34",
    "collect_gold_crystal_necklace": "armor_lootsprites_48",
    "collect_polished_gold_crystal_necklace": "armor_lootsprites_48",
    "collect_octarine_necklace": "armor_lootsprites_176",
    "collect_polished_octarine_necklace": "armor_lootsprites_176",
    "collect_scarlet_chunk_necklace": "armor_lootsprites_178",
    "collect_polished_scarlet_chunk_necklace": "armor_lootsprites_178",
    "collect_coral_amulet": "armor_lootsprites_182",
    "collect_polished_coral_amulet": "armor_lootsprites_182",
    "collect_cave_guppy_necklace": "armor_lootsprites_90",
    "collect_fang_necklace": "lootsprites_crystal_34",
    "collect_heart_berry_necklace": "armor_lootsprites_38",
    "collect_blob_rosary_necklace": "armor_lootsprites_50",
    "collect_ammonite_necklace": "armor_lootsprites_44",
    "collect_grub_egg_necklace": "armor_lootsprites_28",
    "collect_neptune_necklace": "armor_lootsprites_154",
    "collect_bubble_pearl_necklace": "armor_lootsprites_92",
    "collect_skull_necklace": "armor_lootsprites_132",
    "collect_bomb_necklace": "lootsprite_bombNecklace",
    "collect_crescent_necklace": "lootsprite_crescentNecklace",
    "collect_rusted_necklace": "armor_lootsprites_196",
    "collect_wildwarden_necklace": "lootsprites_crystal_81",
    "collect_mold_vein_necklace": "armor_lootsprites_78",
    "collect_ancient_guardian_necklace": "armor_lootsprites_74",
    "collect_ancient_gem_necklace": "armor_lootsprites_108",
    "collect_azeos_beak_necklace": "armor_lootsprites_64",
    "collect_remedaisy_necklace": "armor_lootsprites_72",
    "collect_torc_necklace": "armor_lootsprites_194",
    "collect_bone_necklace": "armor_lootsprites_272",
    "collect_omoroth_s_necklace": "armor_lootsprites_160",
    "collect_conch_shell_necklace": "armor_lootsprites_184",
    "collect_oceanheart_necklace": "armor_lootsprites_180",
    "collect_black_necklace": "armor_lootsprites_274",
    "collect_nomad_necklace": "armor_lootsprites_270",
    "collect_flame_necklace": "armor_lootsprites_276",
    "collect_fusioned_chunk_necklace": "armor_lootsprites_284",
    "collect_ra_akar_s_necklace": "armor_lootsprites_278",
    "collect_pyrdra_s_necklace": "lootsprites_porting_44",
    "collect_atlantean_worm_necklace": "lootsprites_crystal_76",
    "collect_glass_bead_necklace": "lootsprites_crystal_218",
    "collect_tower_shell_necklace": "lootsprites_crystal_193",
    "collect_soul_medallion": "lootsprite_soulNecklace",
    "collect_black_charm_necklace": "lootsprite_shadowCharm",
    "collect_glow_tulip_ring": "armor_lootsprites_32",
    "collect_polished_glow_tulip_ring": "armor_lootsprites_32",
    "collect_swift_ring": "armor_lootsprites_36",
    "collect_polished_swift_ring": "armor_lootsprites_36",
    "collect_gold_crystal_ring": "armor_lootsprites_46",
    "collect_polished_gold_crystal_ring": "armor_lootsprites_46",
    "collect_magnetic_ring": "armor_lootsprites_192",
    "collect_polished_magnetic_ring": "armor_lootsprites_192",
    "collect_golden_spike_ring": "armor_lootsprites_190",
    "collect_polished_golden_spike_ring": "armor_lootsprites_190",
    "collect_octarine_ring": "armor_lootsprites_186",
    "collect_polished_octarine_ring": "armor_lootsprites_186",
    "collect_ring_of_stone": "armor_lootsprites_42",
    "collect_crescent_ring": "lootsprite_crescentRing",
    "collect_rusted_ring": "armor_lootsprites_86",
    "collect_melting_crystal_ring": "armor_lootsprites_52",
    "collect_clot_ring": "armor_lootsprites_24",
    "collect_larva_ring": "armor_lootsprites_26",
    "collect_hourglass_ring": "lootsprite_hourglassRing",
    "collect_boundary_ring": "lootsprite_boundaryRing",
    "collect_ring_of_rock": "armor_lootsprites_40",
    "collect_goldfish_ring": "armor_lootsprites_152",
    "collect_sea_foam_ring": "armor_lootsprites_88",
    "collect_skull_ring": "armor_lootsprites_130",
    "collect_wooden_ring": "armor_lootsprites_198",
    "collect_wooden_thorn_ring": "armor_lootsprites_30",
    "collect_wildwarden_ring": "lootsprites_crystal_80",
    "collect_puppet_ring": "lootsprite_puppetRing",
    "collect_caveling_mother_s_ring": "armor_lootsprites_68",
    "collect_petal_ring": "armor_lootsprites_70",
    "collect_ivy_s_ring": "armor_lootsprites_120",
    "collect_white_glass_ring": "armor_lootsprites_202",
    "collect_topaz_ring": "armor_lootsprites_200",
    "collect_mold_ring": "armor_lootsprites_76",
    "collect_vicious_ring": "lootsprite_viciousRing",
    "collect_sky_ring": "armor_lootsprites_66",
    "collect_lucky_ring": "armor_lootsprites_156",
    "collect_septum_ring": "armor_lootsprites_204",
    "collect_ancient_guardian_ring": "armor_lootsprites_162",
    "collect_bone_ring": "armor_lootsprites_260",
    "collect_noble_ring": "armor_lootsprites_282",
    "collect_ancient_gem_ring": "armor_lootsprites_106",
    "collect_omoroth_s_ring": "armor_lootsprites_158",
    "collect_morpha_s_ring": "armor_lootsprites_150",
    "collect_spine_ring": "armor_lootsprites_188",
    "collect_coral_ring": "armor_lootsprites_148",
    "collect_flame_ring": "armor_lootsprites_266",
    "collect_double_ring": "armor_lootsprites_280",
    "collect_nomad_ring": "armor_lootsprites_262",
    "collect_black_ring": "armor_lootsprites_264",
    "collect_bomb_ring": "armor_lootsprites_268",
    "collect_ring_of_sand": "armor_lootsprites_258",
    "collect_glass_bead_ring": "lootsprites_crystal_217",
    "collect_druidra_s_ring": "lootsprites_porting_46",
    "collect_crydra_s_ring": "lootsprites_porting_45",
    "collect_atlantean_worm_ring": "lootsprites_crystal_74",
    "collect_helical_ring": "lootsprite_screwNutRing",
    "collect_aether_ring": "lootsprite_burnerRing",
}
MAPPING_PATH = Path(__file__).parents[1] / "data" / "tracker_sprite_mappings.json"
if MAPPING_PATH.is_file():
    SPRITES.update(json.loads(MAPPING_PATH.read_text(encoding="utf-8")))
SKILL_SPRITES = {
    "mining": "skill_icons_mining",
    "running": "skill_icons_running",
    "melee_combat": "skill_icons_melee",
    "vitality": "skill_icons_vitality",
    "crafting": "skill_icons_blacksmithing",
    "range_combat": "skill_icons_ranged",
    "gardening": "skill_icons_gardening",
    "fishing": "skill_icons_14",
    "cooking": "skill_icons_16",
    "magic": "skill_icons_magic",
    "summoning": "skill_icons_summoning",
    "explosives": "skill_icons_demolition",
}
LEVEL_BADGES = {}
for skill_key, sprite_name in SKILL_SPRITES.items():
    for level in range(10, 101, 10):
        check_key = f"level_{level}_{skill_key}"
        SPRITES[check_key] = sprite_name
        LEVEL_BADGES[check_key] = str(level)
GLOWBUG_COLORS = {
    "collect_yellow_glowbug": ((55, 35, 0), (255, 238, 65)),
    "collect_blue_glowbug": ((0, 24, 55), (80, 205, 255)),
    "collect_green_glowbug": ((0, 45, 18), (85, 245, 105)),
    "collect_red_glowbug": ((55, 0, 8), (255, 90, 80)),
}
USAGE_STATUS = {
    "collect_amber_larva": "temporary_exact_game_food_sprite_pending_verified_inventory_sprite_link",
    "collect_pink_hydra_eye": "temporary_exact_game_hydra_asset_pending_verified_inventory_sprite_link",
    "collect_white_hydra_eye": "temporary_exact_game_hydra_asset_pending_verified_inventory_sprite_link",
    "defeat_glurch": "temporary_exact_game_asset_pending_clean_layered_boss_render",
    "defeat_hive_mother": "verified_exact_game_scanner",
    "defeat_king_slime": "temporary_exact_game_asset_pending_clean_layered_boss_render",
    "defeat_ghorm": "temporary_exact_game_asset_pending_clean_layered_boss_render",
    "defeat_malugaz": "temporary_exact_game_asset_pending_clean_layered_boss_render",
    "defeat_azeos": "temporary_exact_game_asset_pending_clean_layered_boss_render",
    "defeat_ivy": "verified_exact_game_scanner",
    "defeat_omoroth": "temporary_exact_game_asset_pending_clean_layered_boss_render",
    "defeat_morpha": "verified_exact_game_scanner",
    "defeat_ra_akar": "temporary_exact_game_asset_pending_clean_layered_boss_render",
    "defeat_igneous": "verified_exact_game_scanner",
    "defeat_druidra": "temporary_exact_game_asset_pending_clean_layered_boss_render",
    "defeat_crydra": "temporary_exact_game_asset_pending_clean_layered_boss_render",
    "defeat_pyrdra": "temporary_exact_game_asset_pending_clean_layered_boss_render",
    "defeat_atlantean_worm": "verified_exact_game_scanner",
    "defeat_core_commander": "temporary_exact_game_asset_pending_clean_layered_boss_render",
    "defeat_urschleim": "verified_exact_game_scanner",
    "defeat_nimruza": "temporary_exact_game_asset_pending_clean_layered_boss_render",
    "defeat_oblidra": "verified_exact_game_scanner",
    "defeat_sahabar": "temporary_exact_game_asset_pending_clean_layered_boss_render",
}
PROTOTYPE_FALLBACK_KEYS = {
    "collect_crystal_meteor_shard",
    "collect_white_hydra_eye",
    "collect_azeos_feather_fan",
    "collect_omoroth_compass",
    "collect_heart_berry_seed",
    "collect_amber_larva",
    "defeat_omoroth",
    "defeat_ra_akar",
    "defeat_nimruza",
    "defeat_sahabar",
    "defeat_hive_mother",
    "defeat_ivy",
    "defeat_morpha",
    "defeat_igneous",
    "defeat_atlantean_worm",
    "defeat_urschleim",
    "defeat_oblidra",
}
CRITTER_KEYS = {
    "collect_yellow_glowbug", "collect_blue_glowbug", "collect_green_glowbug",
    "collect_red_glowbug", "collect_purple_glowbug", "collect_blackbug",
    "collect_larvlet", "collect_moon_pincher", "collect_dusk_fairy",
    "collect_dream_messenger", "collect_citrus_pinion", "collect_ice_wind",
    "collect_crimson_wing", "collect_little_death", "collect_leaf_hopper",
    "collect_earthworm", "collect_manyleg", "collect_pest_bug",
    "collect_sun_pincher", "collect_gem_snail", "collect_snoot_fly",
    "collect_shadow_newt", "collect_drape_ray", "collect_sniffling",
    "collect_void_larvlet",
}
CRITTER_INVENTORY_FILES = {
    "collect_yellow_glowbug": "Yellow_Glowbug.png",
    "collect_blue_glowbug": "Blue_Glowbug.png",
    "collect_green_glowbug": "Green_Glowbug.png",
    "collect_red_glowbug": "Red_Glowbug.png",
    "collect_purple_glowbug": "Purple_Glowbug.png",
    "collect_blackbug": "Blackbug.png",
    "collect_larvlet": "Larvlet.png",
    "collect_moon_pincher": "Moon_Pincher.png",
    "collect_dusk_fairy": "Dusk_Fairy.png",
    "collect_dream_messenger": "Dream_Messenger.png",
    "collect_citrus_pinion": "Citrus_Pinion.png",
    "collect_ice_wind": "Ice_Wind.png",
    "collect_crimson_wing": "Crimson_Wing.png",
    "collect_little_death": "Little_Death.png",
    "collect_leaf_hopper": "Leafhopper.png",
    "collect_earthworm": "Earthworm.png",
    "collect_manyleg": "Manyleg.png",
    "collect_pest_bug": "Pest_Bug.png",
    "collect_sun_pincher": "Sun_Pincher.png",
    "collect_gem_snail": "Gem_Snail.png",
    "collect_snoot_fly": "Snoot_Fly.png",
    "collect_shadow_newt": "Shadow_Newt.png",
    "collect_drape_ray": "Drape_Ray.png",
    "collect_sniffling": "Sniffling.png",
    "collect_void_larvlet": "Void_Larvlet.png",
}


def use_prototype_fallback(key: str, object_type: str) -> bool:
    return (
        key == "collect_copper_pickaxe"
        or (
            object_type == "Texture2D"
            and key not in CRITTER_KEYS
        )
        or key in PROTOTYPE_FALLBACK_KEYS
        or key.startswith("hatch_")
        or key.startswith("level_")
    )


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def square(image: Image.Image) -> Image.Image:
    image = image.convert("RGBA")
    box = image.getchannel("A").getbbox()
    if box:
        image = image.crop(box)
    side = max(image.width, image.height)
    canvas = Image.new("RGBA", (side, side))
    canvas.alpha_composite(image, ((side - image.width) // 2, (side - image.height) // 2))
    return canvas


def variants(image: Image.Image) -> dict[str, Image.Image]:
    checked = square(image)
    grey = ImageOps.grayscale(checked).convert("RGBA")
    grey.putalpha(checked.getchannel("A"))
    unchecked = ImageEnhance.Brightness(grey).enhance(0.62)
    unavailable = ImageEnhance.Brightness(grey).enhance(0.25)
    return {"checked": checked, "unchecked": unchecked, "unavailable": unavailable}


def add_level_badge(image: Image.Image, label: str) -> Image.Image:
    # The game's skill sprites are 12x12. Draw the level on a nearest-neighbor
    # enlargement so the badge cannot cover and erase the underlying skill
    # identity (Mining pickaxe versus Running shoe).
    image = square(image).resize((48, 48), Image.Resampling.NEAREST)
    draw = ImageDraw.Draw(image)
    box = draw.textbbox((0, 0), label)
    width = box[2] - box[0]
    height = box[3] - box[1]
    x = max(0, image.width - width - 2)
    y = max(0, image.height - height - 2)
    draw.rectangle((x - 1, y - 1, image.width - 1, image.height - 1), fill=(32, 20, 10, 230))
    draw.text((x, y), label, fill=(255, 225, 65, 255))
    return image


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("game_root", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--unitypy", type=Path, required=True)
    parser.add_argument("--keys", nargs="*", default=[])
    args = parser.parse_args()
    sys.path.insert(0, str(args.unitypy))
    import UnityPy

    sources = [args.game_root / "CoreKeeper_Data" / "resources.assets"]
    bundle = args.game_root / "CoreKeeper_Data" / "StreamingAssets" / "aa" / "StandaloneWindows64" / "defaultlocalgroup_assets_all.bundle"
    if bundle.is_file():
        sources.append(bundle)
    selected = set(args.keys)
    active_sprites = {
        key: sprite for key, sprite in SPRITES.items()
        if not selected or key in selected
    }
    unknown = sorted(selected - set(SPRITES))
    if unknown:
        raise SystemExit("Unknown check keys: " + ", ".join(unknown))
    found: dict[str, tuple[Image.Image, Path, str]] = {}
    wanted = set(active_sprites.values())
    for source in sources:
        environment = UnityPy.load(str(source))
        for obj in environment.objects:
            if obj.type.name not in {"Sprite", "Texture2D"}:
                continue
            asset = obj.read()
            if asset.m_Name not in wanted:
                continue
            # A Texture2D may be the backing atlas for many named Sprite
            # objects. UnityPy crops Sprite.image to the sprite rectangle, so
            # always replace an atlas candidate when the real Sprite appears.
            existing = found.get(asset.m_Name)
            if existing is not None and (existing[2] == "Sprite" or obj.type.name != "Sprite"):
                continue
            try:
                found[asset.m_Name] = (asset.image.convert("RGBA"), source, obj.type.name)
                if wanted <= found.keys():
                    break
            except (FileNotFoundError, PermissionError, ValueError):
                continue
        if wanted <= found.keys():
            break
    missing = sorted(wanted - set(found))
    if missing:
        raise SystemExit("Missing exact game sprites: " + ", ".join(missing))

    root = Path(__file__).parents[1]
    catalog = json.loads((root / "data" / "canonical_catalog.json").read_text(encoding="utf-8"))
    checks_by_key = {
        row["key"]: row
        for row in catalog["checks"]
    }
    prototype_icons = root.parent / "poptracker" / "core_keeper" / "images" / "check-icons"
    critter_inventory_icons = root / "source-assets" / "critter-inventory-icons"

    args.output.mkdir(parents=True, exist_ok=True)
    existing_records = []
    if selected and args.manifest.is_file():
        existing_records = [
            row for row in json.loads(args.manifest.read_text(encoding="utf-8"))["assets"]
            if row["check_key"] not in selected
        ]
    records = list(existing_records)
    rendered_paths: dict[str, str] = {}
    referenced_paths: set[str] = {
        output["path"]
        for row in existing_records
        for output in row["outputs"].values()
    }
    for key, sprite_name in active_sprites.items():
        image, source, object_type = found[sprite_name]
        source_label = source.relative_to(args.game_root).as_posix()
        source_hash = sha256(source)
        usage_status = USAGE_STATUS.get(key, "verified_exact_game_sprite")
        if key in CRITTER_INVENTORY_FILES:
            inventory_icon = critter_inventory_icons / CRITTER_INVENTORY_FILES[key]
            if not inventory_icon.is_file():
                raise SystemExit(f"Missing Critter inventory sprite: {inventory_icon}")
            image = Image.open(inventory_icon).convert("RGBA")
            source_label = inventory_icon.relative_to(root).as_posix()
            source_hash = sha256(inventory_icon)
            object_type = "InventorySpriteReference"
            usage_status = "verified_exact_game_inventory_sprite"
        if use_prototype_fallback(key, object_type):
            prototype = prototype_icons / f"{checks_by_key[key]['stable_id']}.png"
            if not prototype.is_file():
                raise SystemExit(f"Missing prototype combat fallback: {prototype}")
            image = Image.open(prototype).convert("RGBA")
            source_label = prototype.relative_to(root.parent).as_posix()
            source_hash = sha256(prototype)
            object_type = "PrototypeTrackerImage"
            usage_status = "verified_prototype_game_asset_fallback"
        if key in GLOWBUG_COLORS and object_type != "InventorySpriteReference":
            alpha = image.getchannel("A")
            image = ImageOps.colorize(
                ImageOps.grayscale(image), *GLOWBUG_COLORS[key]
            ).convert("RGBA")
            image.putalpha(alpha)
            usage_status = "verified_exact_game_sprite_color_variant"
        if key in LEVEL_BADGES:
            image = add_level_badge(image, LEVEL_BADGES[key])
        outputs = {}
        for state, rendered in variants(image).items():
            buffer = io.BytesIO()
            rendered.save(buffer, format="PNG", optimize=True)
            payload = buffer.getvalue()
            digest = hashlib.sha256(payload).hexdigest()
            output_name = rendered_paths.get(digest)
            if output_name is None:
                output_name = f"{key}_{state}.png"
                if output_name in referenced_paths:
                    output_name = f"{key}_{state}_{digest[:12]}.png"
                (args.output / output_name).write_bytes(payload)
                rendered_paths[digest] = output_name
            referenced_paths.add(output_name)
            outputs[state] = {"path": output_name, "sha256": digest}
        records.append(
            {
                "check_key": key,
                "sprite_name": sprite_name,
                "unity_object_type": object_type,
                "source": source_label,
                "source_sha256": source_hash,
                "usage_status": usage_status,
                "outputs": outputs,
            }
        )
    for path in args.output.glob("*.png"):
        if path.name != "transparent.png" and path.name not in referenced_paths:
            path.unlink()
    order = {key: index for index, key in enumerate(SPRITES)}
    records.sort(key=lambda row: order[row["check_key"]])
    args.manifest.write_text(
        json.dumps({"schema_version": 1, "assets": records}, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
