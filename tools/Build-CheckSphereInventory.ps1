param(
    [string]$Root = (Split-Path -Parent $PSScriptRoot),
    [string]$Output = (Join-Path (Split-Path -Parent $PSScriptRoot) 'CHECK_SPHERE_INVENTORY.md')
)

$catalog = Get-Content -LiteralPath (Join-Path $Root 'data\canonical_catalog.json') -Raw |
    ConvertFrom-Json

$tiers = [ordered]@{
    '1' = @{ title = 'Sphere 1 - The Great Wall'; rank = 0 }
    '2A' = @{ title = 'Sphere 2A - Great Wall lowered'; rank = 1 }
    '2B' = @{ title = 'Sphere 2B - After Azeos'; rank = 2 }
    '2C' = @{ title = 'Sphere 2C - After Omoroth'; rank = 3 }
    '3A' = @{ title = 'Sphere 3A - First Titans complete'; rank = 4 }
    '3B' = @{ title = 'Sphere 3B - After Druidra'; rank = 5 }
    '3C' = @{ title = 'Sphere 3C - After Crydra'; rank = 6 }
    '3D' = @{ title = 'Sphere 3D - After Pyrdra / Second Titans complete'; rank = 7 }
    '4A' = @{ title = 'Sphere 4A - After Core Commander'; rank = 8 }
    '4B' = @{ title = 'Sphere 4B - After Nimruza'; rank = 9 }
}

$requirementTier = @{
    defeat_glurch = '1'; defeat_ghorm = '1'; defeat_malugaz = '1'
    defeat_hive_mother = '1'; defeat_king_slime = '1'
    lower_wall = '2A'
    defeat_ivy = '2A'; defeat_azeos = '2B'; defeat_morpha = '2B'
    defeat_igneous = '2C'
    defeat_omoroth = '2C'
    defeat_ra_akar = '3A'; defeat_first_titans = '3A'
    defeat_druidra = '3B'; defeat_atlantean_worm = '3B'
    defeat_crydra = '3C'
    defeat_pyrdra = '3D'; defeat_second_titans = '3D'
    defeat_core_commander = '4A'
    defeat_urschleim = '4B'; defeat_nimruza = '4B'
    defeat_oblidra = '4B'; defeat_sahabar = '4B'
}

function Get-Tier([object[]]$requirements) {
    $selected = '1'
    foreach ($requirement in $requirements) {
        $key = [string]$requirement
        if ($requirementTier.ContainsKey($key)) {
            $candidate = $requirementTier[$key]
            if ($tiers[$candidate].rank -gt $tiers[$selected].rank) { $selected = $candidate }
        }
    }
    return $selected
}

function Format-Logic($logic) {
    if ($null -eq $logic) { return 'N/A' }
    $parts = @()
    if (@($logic.all_of).Count) { $parts += 'all: ' + (@($logic.all_of) -join ', ') }
    if (@($logic.any_of).Count) { $parts += 'any: ' + (@($logic.any_of) -join ', ') }
    if (-not $parts.Count) { return 'none' }
    return ($parts -join '; ')
}

$rows = foreach ($check in $catalog.checks) {
    [pscustomobject]@{
        Tier = Get-Tier @($check.normal.all_of)
        Group = [string]$check.group
        Id = [long]$check.stable_id
        Name = [string]$check.display_name
        Scope = if ($check.goal_scope) { [string]$check.goal_scope } else { 'all enabled goals' }
        Normal = Format-Logic $check.normal
        BreakTier = if ($check.sequence_break) { Get-Tier @($check.sequence_break.all_of) } else { 'N/A' }
        Sequence = Format-Logic $check.sequence_break
    }
}

$lines = [System.Collections.Generic.List[string]]::new()
$lines.Add('# Core Keeper check sphere inventory')
$lines.Add('')
$lines.Add('Generated from `data/canonical_catalog.json`. This is the static design tier from each check''s boss requirements, not a generated seed''s Archipelago item-placement sphere. Randomized licenses and other required items can push a check later. Sequence-break logic is shown separately.')
$lines.Add('')
$lines.Add("Total possible checks: **$($rows.Count)**")
$lines.Add('')
$lines.Add('## Counts')
$lines.Add('')
$lines.Add('| Tier | Checks |')
$lines.Add('|---|---:|')
foreach ($tierKey in $tiers.Keys) {
    $lines.Add("| $($tiers[$tierKey].title) | $(@($rows | Where-Object Tier -eq $tierKey).Count) |")
}
$lines.Add('')

foreach ($tierKey in $tiers.Keys) {
    $tierRows = @($rows | Where-Object Tier -eq $tierKey | Sort-Object Group, Id)
    $lines.Add("## $($tiers[$tierKey].title)")
    $lines.Add('')
    foreach ($group in @($tierRows.Group | Sort-Object -Unique)) {
        $groupRows = @($tierRows | Where-Object Group -eq $group)
        $lines.Add("### $group ($($groupRows.Count))")
        $lines.Add('')
        $lines.Add('| ID | Check | Goal scope | Normal requirements | Sequence-break tier | Sequence-break requirements |')
        $lines.Add('|---:|---|---|---|---|---|')
        foreach ($row in $groupRows) {
            $name = $row.Name.Replace('|', '\|')
            $normal = $row.Normal.Replace('|', '\|')
            $sequence = $row.Sequence.Replace('|', '\|')
            $lines.Add("| $($row.Id) | $name | $($row.Scope) | $normal | $($row.BreakTier) | $sequence |")
        }
        $lines.Add('')
    }
}

[System.IO.File]::WriteAllLines($Output, $lines, [System.Text.UTF8Encoding]::new($false))
Write-Output "Wrote $($rows.Count) checks to $Output"
