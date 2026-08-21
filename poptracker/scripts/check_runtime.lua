local LocationMap = require("scripts/location_map")

CK_CHECKS_BY_ID = {}
local ByCode = {}
CK_CHECKS_BY_CODE = ByCode
local Present = {}
local VisualStates = {}
local RefreshQueue = {}
local RefreshCursor = 1
local RefreshDelayFrames = 0
local FullRefreshDelayFrames = -1
local SuppressCodeWatch = false

local function icon(id, checked)
    if CK_LOCAL_TEXTURES_ACTIVE == false then
        local fallback = checked and "fallback-icon-disabled.png" or "fallback-icon.png"
        return ImageReference:FromPackRelativePath("images/" .. fallback)
    end
    local folder = checked and "check-icons-disabled" or "check-icons"
    return ImageReference:FromPackRelativePath(
        "images/" .. folder .. "/" .. tostring(id) .. ".png"
    )
end

local function section_for(record)
    return Tracker:FindObjectForCode(
        "@" .. record.mapping[1] .. "/" .. record.mapping[2]
    )
end

local function sync_checked_state(record)
    local section = section_for(record)
    if section then
        section.AvailableChestCount = record.item.Active
            and 0 or section.ChestCount
    end
end

local function refresh(record)
    local section = section_for(record)
    if not section then return end
    local checked = record.item.Active == true
    local present = Present[record.definition.id] ~= false
    local state
    if not present then
        state = "absent"
    elseif checked then
        state = "grey"
    elseif section.AccessibilityLevel == AccessibilityLevel.Normal then
        state = "green"
    elseif section.AccessibilityLevel == AccessibilityLevel.SequenceBreak then
        state = "yellow"
    else
        state = "red"
    end
    if VisualStates[record.definition.id] == state then return end
    VisualStates[record.definition.id] = state
    local display_icon_id = record.definition.id
    if record.randomized then
        if checked then display_icon_id = record.randomized.icon_id end
    end
    if state == "absent" then
        if CK_LOCAL_TEXTURES_ACTIVE == false then
            record.item.Icon = ImageReference:FromPackRelativePath(
                "images/fallback-icon-absent.png"
            )
        else
            record.item.Icon = ImageReference:FromPackRelativePath(
                "images/check-icons-absent/" .. tostring(display_icon_id) .. ".png"
            )
        end
    else
        record.item.Icon = ImageReference:FromImageReference(
            icon(display_icon_id, checked),
            "overlay|images/accessibility-indicator-" .. state .. "-"
                .. CK_VARIANT_SIZE .. ".png"
        )
    end
end

function CK_REFRESH_ACCESS_LOGIC()
    FullRefreshDelayFrames = -1
    RefreshQueue = {}
    RefreshCursor = 1
    for _, record in pairs(CK_CHECKS_BY_ID) do
        table.insert(RefreshQueue, record)
    end
    table.sort(RefreshQueue, function(a, b)
        return a.definition.id < b.definition.id
    end)
    Tracker.BulkUpdate = true
    for _, record in ipairs(RefreshQueue) do sync_checked_state(record) end
    Tracker.BulkUpdate = false
    RefreshDelayFrames = 2
end

function CK_INVALIDATE_CHECK_VISUAL(id)
    VisualStates[id] = nil
end

local function queue_record(record)
    RefreshQueue = { record }
    RefreshCursor = 1
    RefreshDelayFrames = 2
    sync_checked_state(record)
end

function CK_SET_CHECK_STATE(id, present, checked)
    local record = CK_CHECKS_BY_ID[id]
    if not record then return end
    Present[id] = present == true
    SuppressCodeWatch = true
    record.item.Active = checked == true
    SuppressCodeWatch = false
    VisualStates[id] = nil
    queue_record(record)
end

for _, definition in ipairs(CK_CHECK_DEFINITIONS) do
    local mapping = LocationMap[definition.id]
    local item = Tracker:FindObjectForCode(definition.code)
    if mapping and item then
        local record = { definition = definition, mapping = mapping, item = item }
        CK_CHECKS_BY_ID[definition.id] = record
        ByCode[definition.code] = record
    end
end

ScriptHost:AddWatchForCode("Core Keeper check clicks", "*", function(code)
    if SuppressCodeWatch then return end
    local record = ByCode[code]
    if record then
        if Present[record.definition.id] == false then
            -- PopTracker itemgrids do not expose a per-cell input-disable flag.
            -- Restore absent checks immediately so clicks have no persistent
            -- state, logic, or AP-location effect.
            SuppressCodeWatch = true
            record.item.Active = false
            SuppressCodeWatch = false
            VisualStates[record.definition.id] = nil
            queue_record(record)
            return
        end
        VisualStates[record.definition.id] = nil
    end
    -- A check or unlock can satisfy rules for any number of downstream
    -- locations. Re-evaluate the full graph after PopTracker settles; cached
    -- visual states prevent unchanged icons from being reconstructed.
    FullRefreshDelayFrames = 2
end)

ScriptHost:AddOnFrameHandler("Core Keeper access refresh", function(_elapsed)
    if FullRefreshDelayFrames >= 0 then
        if FullRefreshDelayFrames > 0 then
            FullRefreshDelayFrames = FullRefreshDelayFrames - 1
        else
            CK_REFRESH_ACCESS_LOGIC()
        end
        return
    end
    if RefreshDelayFrames > 0 then
        RefreshDelayFrames = RefreshDelayFrames - 1
        return
    end
    if RefreshCursor > #RefreshQueue then return end
    local last = math.min(#RefreshQueue, RefreshCursor + 31)
    for index = RefreshCursor, last do refresh(RefreshQueue[index]) end
    RefreshCursor = last + 1
end)

CK_REFRESH_ACCESS_LOGIC()
