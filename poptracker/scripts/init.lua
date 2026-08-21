CK_VARIANT_SIZE = string.match(Tracker.ActiveVariantUID or "medium", "([%a]+)$")
    or "medium"
ScriptHost:LoadScript("scripts/asset_mode.lua")
Tracker:AddItems("items/logic.json")
Tracker:AddItems("items/checks.json")
ScriptHost:LoadScript("scripts/checks.lua")
Tracker:AddLocations("locations/locations.json")
Tracker:AddLayouts("layouts/tracker.json")
ScriptHost:LoadScript("scripts/check_runtime.lua")
ScriptHost:LoadScript("scripts/randomizer_reveals.lua")

ScriptHost:LoadScript("scripts/autotracking.lua")
ScriptHost:LoadScript("scripts/logic_autotracking.lua")
