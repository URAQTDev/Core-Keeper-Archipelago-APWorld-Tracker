local function as_set(values)
    local result = {}
    if values then
        for _, value in ipairs(values) do result[value] = true end
    end
    return result
end

local pending_sync = nil
local pending_index = 1
local sync_batch_size = 32
local poll_elapsed = 0
local poll_interval = 0.25
local last_server_signature = nil

local function clear_handler(slot_data)
    CK_CONFIGURE_RANDOMIZER_REVEALS(slot_data)
    pending_sync = { ready = false }
    pending_index = 1
    last_server_signature = nil
end

local function location_handler(location_id, _location_name)
    CK_SET_CHECK_STATE(location_id, true, true)
end

local function server_signature(missing, checked)
    if not missing or not checked or (#missing + #checked) == 0 then
        return nil
    end
    local hash = 0
    for _, location_id in ipairs(checked) do
        hash = (hash + location_id * 31) % 2147483647
    end
    return tostring(Archipelago.PlayerNumber) .. ":" .. tostring(#missing)
        .. ":" .. tostring(#checked) .. ":" .. tostring(hash)
end

local function begin_live_sync(missing, checked)
    pending_sync = {
        ready = true,
        missing = as_set(missing),
        checked = as_set(checked),
    }
    pending_index = 1
end

local function sync_frame(elapsed)
    poll_elapsed = poll_elapsed + elapsed
    if poll_elapsed >= poll_interval then
        poll_elapsed = 0
        local missing = Archipelago.MissingLocations
        local checked = Archipelago.CheckedLocations
        local signature = server_signature(missing, checked)
        if signature and signature ~= last_server_signature then
            last_server_signature = signature
            begin_live_sync(missing, checked)
        end
    end
    if not pending_sync then return end
    if not pending_sync.ready then
        local missing = Archipelago.MissingLocations
        local checked = Archipelago.CheckedLocations
        if (not missing or not checked or (#missing + #checked) == 0) then
            return
        end
        pending_sync.missing = as_set(missing)
        pending_sync.checked = as_set(checked)
        pending_sync.ready = true
    end
    local last = math.min(
        #CK_CHECK_DEFINITIONS,
        pending_index + sync_batch_size - 1
    )
    for index = pending_index, last do
        local definition = CK_CHECK_DEFINITIONS[index]
        local present = pending_sync.missing[definition.id] == true
            or pending_sync.checked[definition.id] == true
        CK_SET_CHECK_STATE(
            definition.id,
            present,
            pending_sync.checked[definition.id] == true
        )
    end
    pending_index = last + 1
    if pending_index > #CK_CHECK_DEFINITIONS then
        pending_sync = nil
        CK_REFRESH_ACCESS_LOGIC()
    end
end

Archipelago:AddClearHandler("Core Keeper clear", clear_handler)
Archipelago:AddLocationHandler("Core Keeper locations", location_handler)
ScriptHost:AddOnFrameHandler("Core Keeper initial location sync", sync_frame)
