param(
    [Parameter(Mandatory = $true)]
    [string]$ManifestPath
)

$ErrorActionPreference = 'Stop'
$manifest = Get-Content -LiteralPath $ManifestPath -Raw | ConvertFrom-Json

if ($manifest.schema_version -ne 1) { throw 'Unsupported source manifest schema.' }
if (-not $manifest.source_timestamp) { throw 'Source manifest has no pinned timestamp.' }
if ($manifest.core_keeper.steam_build_id -le 0) { throw 'Missing Core Keeper build ID.' }
if ($manifest.core_keeper.configuration_manifest.Count -eq 0) { throw 'No configuration files were recorded.' }
if ($manifest.core_keeper.assembly_manifest.Count -eq 0) { throw 'No shipped assemblies were recorded.' }

$duplicates = @($manifest.core_keeper.configuration_manifest |
    Group-Object path |
    Where-Object Count -gt 1)
if ($duplicates.Count -gt 0) { throw 'Duplicate configuration paths in source manifest.' }

$badHashes = @($manifest.core_keeper.configuration_manifest + $manifest.core_keeper.assembly_manifest |
    Where-Object { $_.sha256 -notmatch '^[0-9a-f]{64}$' })
if ($badHashes.Count -gt 0) { throw 'Invalid SHA-256 value in source manifest.' }

Write-Output "Verified source manifest for Core Keeper build $($manifest.core_keeper.steam_build_id)."
