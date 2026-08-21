using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Collections;
using System.Reflection;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using PugMod;
using Unity.Entities;
using UnityEngine;

namespace CoreKeeperArchipelago.Extractor;

public sealed class ExtractorMod : IMod
{
    private const int SteamBuildId = 23543556;
    private static readonly HashSet<string> SkillSpriteNames = new(StringComparer.Ordinal)
    {
        "skill_icons_mining",
        "skill_icons_running",
        "skill_icons_melee",
        "skill_icons_vitality",
        "skill_icons_blacksmithing",
        "skill_icons_ranged",
        "skill_icons_gardening",
        "skill_icons_14",
        "skill_icons_16",
        "skill_icons_magic",
        "skill_icons_summoning",
        "skill_icons_demolition",
    };
    private bool completed;
    private int attempts;

    public void EarlyInit()
    {
    }

    public void Init()
    {
        Debug.Log("[Core Keeper Archipelago Extractor] Waiting for PugDatabase.");
    }

    public void Update()
    {
        if (completed || ++attempts % 60 != 0)
        {
            return;
        }

        for (int worldIndex = 0; worldIndex < World.All.Count; worldIndex++)
        {
            World world = World.All[worldIndex];
            if (!world.IsCreated)
            {
                continue;
            }

            EntityQuery query = world.EntityManager.CreateEntityQuery(
                ComponentType.ReadOnly<PugDatabase.DatabaseBankCD>());
            try
            {
                if (query.IsEmptyIgnoreFilter)
                {
                    continue;
                }

                Export(world, query.GetSingleton<PugDatabase.DatabaseBankCD>());
                completed = true;
                return;
            }
            catch (Exception exception)
            {
                Debug.LogError("[Core Keeper Archipelago Extractor] " + exception);
            }
            finally
            {
                query.Dispose();
            }
        }
    }

    public void Shutdown()
    {
    }

    public void ModObjectLoaded(UnityEngine.Object obj)
    {
    }

    public bool CanBeUnloaded() => true;

    private static void Export(World world, PugDatabase.DatabaseBankCD database)
    {
        var records = new List<JObject>();
        var objectIcons = new JObject();
        var creatureIcons = new JObject();
        var bossSummonIcons = new JObject();
        var bossSummonObjects = new Dictionary<string, ObjectID>
        {
            ["defeat_glurch"] = (ObjectID)2503,
            ["defeat_ghorm"] = (ObjectID)2504,
            ["defeat_malugaz"] = (ObjectID)2506,
            ["defeat_hive_mother"] = (ObjectID)2505,
            ["defeat_king_slime"] = (ObjectID)2508,
            ["defeat_azeos"] = (ObjectID)150,
            ["defeat_ivy"] = (ObjectID)2503,
            ["defeat_omoroth"] = (ObjectID)8384,
            ["defeat_morpha"] = (ObjectID)2503,
            ["defeat_ra_akar"] = (ObjectID)151,
            ["defeat_igneous"] = (ObjectID)2503,
            ["defeat_druidra"] = (ObjectID)153,
            ["defeat_crydra"] = (ObjectID)154,
            ["defeat_pyrdra"] = (ObjectID)155,
            ["defeat_atlantean_worm"] = (ObjectID)152,
            ["defeat_core_commander"] = (ObjectID)2510,
            ["defeat_urschleim"] = (ObjectID)2511,
            ["defeat_nimruza"] = (ObjectID)2512,
            ["defeat_oblidra"] = (ObjectID)156,
            ["defeat_sahabar"] = (ObjectID)2515,
        };
        string directory = Path.Combine(Application.persistentDataPath, "CoreKeeperArchipelago");
        string creatureIconDirectory = Path.Combine(directory, "creature-icons");
        string objectIconDirectory = Path.Combine(directory, "object-icons");
        Directory.CreateDirectory(creatureIconDirectory);
        Directory.CreateDirectory(objectIconDirectory);
        ref Unity.Entities.BlobArray<PugDatabase.EntityObjectInfo> infos =
            ref database.databaseBankBlob.Value.objectInfos;
        for (int index = 0; index < infos.Length; index++)
        {
            PugDatabase.EntityObjectInfo info = infos[index];
            string internalName = Enum.GetName(typeof(ObjectID), info.objectID)
                ?? ((int)info.objectID).ToString(System.Globalization.CultureInfo.InvariantCulture);
            ObjectInfo? managedInfo = PugDatabase.GetObjectInfo(info.objectID, info.variation);
            if (managedInfo?.icon != null)
            {
                string iconFile = internalName + "_" + info.variation + "_icon.png";
                ExportSprite(managedInfo.icon, Path.Combine(objectIconDirectory, iconFile));
                objectIcons[internalName + ":" + info.variation] = new JObject
                {
                    ["object_id"] = (int)info.objectID,
                    ["variation"] = info.variation,
                    ["object_type"] = info.objectType.ToString(),
                    ["icon_sprite_name"] = managedInfo.icon.name,
                    ["icon_file"] = iconFile,
                };
            }
            if (info.objectType == ObjectType.Creature
                && (managedInfo?.icon != null || managedInfo?.smallIcon != null))
            {
                string? iconFile = null;
                string? smallIconFile = null;
                if (managedInfo?.icon != null)
                {
                    iconFile = internalName + "_" + info.variation + "_icon.png";
                    ExportSprite(managedInfo.icon, Path.Combine(creatureIconDirectory, iconFile));
                }
                if (managedInfo?.smallIcon != null)
                {
                    smallIconFile = internalName + "_" + info.variation + "_small.png";
                    ExportSprite(managedInfo.smallIcon, Path.Combine(creatureIconDirectory, smallIconFile));
                }
                creatureIcons[internalName + ":" + info.variation] = new JObject
                {
                    ["object_id"] = (int)info.objectID,
                    ["icon_sprite_name"] = managedInfo?.icon?.name,
                    ["icon_file"] = iconFile,
                    ["small_icon_sprite_name"] = managedInfo?.smallIcon?.name,
                    ["small_icon_file"] = smallIconFile,
                };
            }
            var ingredients = new JArray();
            if (managedInfo?.requiredObjectsToCraft != null)
            {
                foreach (CraftingObject ingredient in managedInfo.requiredObjectsToCraft)
                {
                    if (ingredient.objectID != ObjectID.None && ingredient.amount > 0)
                    {
                        ingredients.Add(new JObject
                        {
                            ["object_id"] = (int)ingredient.objectID,
                            ["amount"] = ingredient.amount,
                        });
                    }
                }
            }

            var stationRecipes = new JArray();
            Entity prefab = PugDatabase.GetPrimaryPrefabEntity(
                info.objectID,
                database.databaseBankBlob,
                info.variation);
            if (prefab != Entity.Null
                && world.EntityManager.Exists(prefab)
                && world.EntityManager.HasBuffer<CanCraftObjectsBuffer>(prefab))
            {
                DynamicBuffer<CanCraftObjectsBuffer> recipes =
                    world.EntityManager.GetBuffer<CanCraftObjectsBuffer>(prefab, true);
                for (int recipeIndex = 0; recipeIndex < recipes.Length; recipeIndex++)
                {
                    CanCraftObjectsBuffer recipe = recipes[recipeIndex];
                    stationRecipes.Add(new JObject
                    {
                        ["object_id"] = (int)recipe.objectID,
                        ["amount"] = recipe.amount,
                        ["entity_amount_to_consume"] = recipe.entityAmountToConsume,
                        ["allow_crafting_none"] = recipe.allowCraftingNone,
                        ["crafting_time_override"] = recipe.craftingTimeOverride,
                    });
                }
            }

            string displayName;
            try
            {
                displayName = PlayerController.GetObjectName(
                    new ContainedObjectsBuffer
                    {
                        objectData = new ObjectDataCD
                        {
                            objectID = info.objectID,
                            amount = 1,
                            variation = info.variation,
                        },
                    },
                    localize: true).text;
            }
            catch
            {
                displayName = internalName;
            }

            records.Add(new JObject
            {
                ["object_id"] = (int)info.objectID,
                ["internal_name"] = internalName,
                ["display_name"] = displayName,
                ["variation"] = info.variation,
                ["variation_is_dynamic"] = info.variationIsDynamic,
                ["object_type"] = info.objectType.ToString(),
                ["rarity"] = info.rarity.ToString(),
                ["level"] = managedInfo?.level ?? 0,
                ["icon_sprite"] = managedInfo?.icon != null
                    ? managedInfo.icon.name
                    : null,
                ["small_icon_sprite"] = managedInfo?.smallIcon != null
                    ? managedInfo.smallIcon.name
                    : null,
                ["icon_offset_x"] = managedInfo?.iconOffset.x ?? 0f,
                ["icon_offset_y"] = managedInfo?.iconOffset.y ?? 0f,
                ["sell_value"] = info.sellValue,
                ["buy_value_multiplier"] = info.buyValueMultiplier,
                ["is_stackable"] = info.isStackable,
                ["tileset"] = info.tileset,
                ["tile_type"] = info.tileType.ToString(),
                ["crafting_time"] = info.craftingTime,
                ["ingredients"] = ingredients,
                ["station_recipes"] = stationRecipes,
            });
        }

        JObject output = new JObject
        {
            ["schema_version"] = 1,
            ["core_keeper_steam_build_id"] = SteamBuildId,
            ["records"] = new JArray(records
                .OrderBy(record => (int)record["object_id"]!)
                .ThenBy(record => (int)record["variation"]!)),
        };
        Directory.CreateDirectory(directory);
        string destination = Path.Combine(directory, "runtime_database.raw.json");
        File.WriteAllText(
            Path.Combine(objectIconDirectory, "manifest.json"),
            objectIcons.ToString(Formatting.Indented));
        File.WriteAllText(
            Path.Combine(creatureIconDirectory, "manifest.json"),
            creatureIcons.ToString(Formatting.Indented));
        string bossSummonDirectory = Path.Combine(directory, "boss-summon-icons");
        Directory.CreateDirectory(bossSummonDirectory);
        foreach (KeyValuePair<string, ObjectID> summon in bossSummonObjects)
        {
            ObjectInfo? summonInfo = PugDatabase.GetObjectInfo(summon.Value, 0);
            if (summonInfo?.icon == null)
            {
                continue;
            }
            string file = summon.Key + ".png";
            ExportSprite(summonInfo.icon, Path.Combine(bossSummonDirectory, file));
            bossSummonIcons[summon.Key] = new JObject
            {
                ["object_id"] = (int)summon.Value,
                ["internal_name"] = Enum.GetName(typeof(ObjectID), summon.Value),
                ["sprite_name"] = summonInfo.icon.name,
                ["file"] = file,
            };
        }
        File.WriteAllText(
            Path.Combine(bossSummonDirectory, "manifest.json"),
            bossSummonIcons.ToString(Formatting.Indented));
        string skillIconDirectory = Path.Combine(directory, "skill-icons");
        Directory.CreateDirectory(skillIconDirectory);
        var skillIcons = new JObject();
        foreach (Sprite sprite in Resources.FindObjectsOfTypeAll<Sprite>())
        {
            if (!SkillSpriteNames.Contains(sprite.name) || skillIcons.ContainsKey(sprite.name))
            {
                continue;
            }
            string file = sprite.name + ".png";
            ExportSprite(sprite, Path.Combine(skillIconDirectory, file));
            skillIcons[sprite.name] = file;
        }
        File.WriteAllText(
            Path.Combine(skillIconDirectory, "manifest.json"),
            skillIcons.ToString(Formatting.Indented));
        ExportPetSkinEvidence(directory);
        File.WriteAllText(destination, output.ToString(Formatting.None) + Environment.NewLine);
        Debug.Log($"[Core Keeper Archipelago Extractor] Exported {records.Count} records to {destination}");
    }

    private static void ExportPetSkinEvidence(string directory)
    {
        string petDirectory = Path.Combine(directory, "pet-skins");
        Directory.CreateDirectory(petDirectory);
        var evidence = new JArray();
        int spriteIndex = 0;
        foreach (PetInfosTable table in Resources.FindObjectsOfTypeAll<PetInfosTable>())
        {
            evidence.Add(ReflectValue(table, petDirectory, ref spriteIndex, 0, new HashSet<object>()));
        }
        foreach (UnityEngine.Object asset in Resources.FindObjectsOfTypeAll<UnityEngine.Object>())
        {
            if (asset.GetType().Name.Contains("GradientMapDataBlock", StringComparison.Ordinal))
            {
                evidence.Add(ReflectValue(asset, petDirectory, ref spriteIndex, 0, new HashSet<object>()));
            }
        }
        var fixedPets = new JObject();
        foreach ((string name, ObjectID objectId) in new[]
        {
            ("PetElectric", (ObjectID)1258),
            ("PetMagic", (ObjectID)1253),
        })
        {
            ObjectInfo? info = PugDatabase.GetObjectInfo(objectId, 0);
            fixedPets[name] = ReflectValue(
                info, petDirectory, ref spriteIndex, 0, new HashSet<object>());
        }
        File.WriteAllText(
            Path.Combine(petDirectory, "fixed-pet-object-info.json"),
            fixedPets.ToString(Formatting.Indented));
        File.WriteAllText(
            Path.Combine(petDirectory, "manifest.json"),
            evidence.ToString(Formatting.Indented));
    }

    private static JToken ReflectValue(
        object? value,
        string petDirectory,
        ref int spriteIndex,
        int depth,
        HashSet<object> visited)
    {
        if (value == null)
        {
            return JValue.CreateNull();
        }
        Type type = value.GetType();
        if (value is string || type.IsPrimitive || type.IsEnum || value is decimal)
        {
            return new JValue(value.ToString());
        }
        if (type.IsGenericType && type.GetGenericTypeDefinition().Name == "DataBlockRef`1")
        {
            MethodInfo? get = type.GetMethod("Get", BindingFlags.Instance | BindingFlags.Public);
            object? resolved = get?.Invoke(value, null);
            return new JObject
            {
                ["$type"] = type.FullName,
                ["reference"] = ReflectFieldsOnly(value, petDirectory, ref spriteIndex, depth, visited),
                ["resolved"] = ReflectValue(resolved, petDirectory, ref spriteIndex, depth + 1, visited),
            };
        }
        if (value is Color color)
        {
            return new JObject { ["r"] = color.r, ["g"] = color.g, ["b"] = color.b, ["a"] = color.a };
        }
        if (value is Color32 color32)
        {
            return new JObject { ["r"] = color32.r, ["g"] = color32.g, ["b"] = color32.b, ["a"] = color32.a };
        }
        if (type.Name == "GradientMapDataBlock")
        {
            FieldInfo? arrayField = type.GetField("array", BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic);
            var colors = new JArray();
            if (arrayField?.GetValue(value) is IEnumerable palette)
            {
                foreach (object? entry in palette)
                {
                    if (entry is Color32 entryColor)
                    {
                        colors.Add(new JObject { ["r"] = entryColor.r, ["g"] = entryColor.g, ["b"] = entryColor.b, ["a"] = entryColor.a });
                    }
                }
            }
            return new JObject { ["$type"] = type.FullName, ["array"] = colors };
        }
        if (value is Sprite sprite)
        {
            string file = $"{spriteIndex++:D4}_{SanitizeFileName(sprite.name)}.png";
            ExportSprite(sprite, Path.Combine(petDirectory, file));
            return new JObject { ["sprite_name"] = sprite.name, ["file"] = file };
        }
        if (value is Texture2D texture)
        {
            string file = $"{spriteIndex++:D4}_{SanitizeFileName(texture.name)}.png";
            File.WriteAllBytes(Path.Combine(petDirectory, file), texture.EncodeToPNG());
            return new JObject { ["texture_name"] = texture.name, ["file"] = file };
        }
        if (depth >= 8 || (!type.IsValueType && !visited.Add(value)))
        {
            return new JValue(type.FullName);
        }
        if (value is IEnumerable enumerable)
        {
            var array = new JArray();
            foreach (object? entry in enumerable)
            {
                array.Add(ReflectValue(entry, petDirectory, ref spriteIndex, depth + 1, visited));
            }
            return array;
        }
        var output = new JObject { ["$type"] = type.FullName };
        foreach (FieldInfo field in type.GetFields(BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic))
        {
            try
            {
                output[field.Name] = ReflectValue(field.GetValue(value), petDirectory, ref spriteIndex, depth + 1, visited);
            }
            catch (Exception exception)
            {
                output[field.Name] = "<error: " + exception.Message + ">";
            }
        }
        return output;
    }

    private static JObject ReflectFieldsOnly(
        object value, string petDirectory, ref int spriteIndex, int depth, HashSet<object> visited)
    {
        var output = new JObject();
        foreach (FieldInfo field in value.GetType().GetFields(BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic))
        {
            output[field.Name] = ReflectValue(field.GetValue(value), petDirectory, ref spriteIndex, depth + 1, visited);
        }
        return output;
    }

    private static string SanitizeFileName(string value)
    {
        foreach (char invalid in Path.GetInvalidFileNameChars())
        {
            value = value.Replace(invalid, '_');
        }
        return value;
    }

    private static void ExportSprite(Sprite sprite, string destination)
    {
        Rect rect = sprite.textureRect;
        int width = Mathf.Max(1, Mathf.RoundToInt(rect.width));
        int height = Mathf.Max(1, Mathf.RoundToInt(rect.height));
        var output = new Texture2D(width, height, TextureFormat.RGBA32, false);
        RenderTexture renderTexture = RenderTexture.GetTemporary(
            width, height, 0, RenderTextureFormat.ARGB32);
        RenderTexture previous = RenderTexture.active;
        try
        {
            Graphics.Blit(
                sprite.texture,
                renderTexture,
                new Vector2(rect.width / sprite.texture.width, rect.height / sprite.texture.height),
                new Vector2(rect.x / sprite.texture.width, rect.y / sprite.texture.height));
            RenderTexture.active = renderTexture;
            output.ReadPixels(new Rect(0, 0, width, height), 0, 0);
            output.Apply();
            File.WriteAllBytes(destination, output.EncodeToPNG());
        }
        finally
        {
            RenderTexture.active = previous;
            RenderTexture.ReleaseTemporary(renderTexture);
            UnityEngine.Object.Destroy(output);
        }
    }
}
