param(
    [Parameter(Mandatory = $true)]
    [string]$GameRoot,
    [Parameter(Mandatory = $true)]
    [string]$OutputPath
)

$ErrorActionPreference = 'Stop'

function Get-RelativeManifest([string]$Root, [string]$Path) {
    $rootUri = [System.Uri]::new(($Root.TrimEnd('\') + '\'))
    $pathUri = [System.Uri]::new($Path)
    return [System.Uri]::UnescapeDataString($rootUri.MakeRelativeUri($pathUri).ToString())
}

function Get-ManifestEntries([string]$Root, [string]$Filter) {
    return @(Get-ChildItem -LiteralPath $Root -File -Recurse -Filter $Filter |
        Sort-Object FullName |
        ForEach-Object {
            $hash = Get-FileHash -Algorithm SHA256 -LiteralPath $_.FullName
            [ordered]@{
                path = Get-RelativeManifest -Root $GameRoot -Path $_.FullName
                length = $_.Length
                sha256 = $hash.Hash.ToLowerInvariant()
            }
        })
}

$acfPath = Join-Path (Split-Path $GameRoot -Parent) '..\appmanifest_1621690.acf'
$acfPath = [System.IO.Path]::GetFullPath($acfPath)
$acf = Get-Content -LiteralPath $acfPath -Raw
$buildMatch = [regex]::Match($acf, '"buildid"\s+"(?<value>\d+)"')
$updatedMatch = [regex]::Match($acf, '"LastUpdated"\s+"(?<value>\d+)"')
if (-not $buildMatch.Success -or -not $updatedMatch.Success) {
    throw "Could not parse Core Keeper Steam manifest at $acfPath"
}

$confRoot = Join-Path $GameRoot 'CoreKeeper_Data\StreamingAssets\Conf'
$managedRoot = Join-Path $GameRoot 'CoreKeeper_Data\Managed'
$objectCatalog = Join-Path $confRoot 'ID\ObjectID.json'
$criticalAssemblyNames = @(
    '0Harmony.dll',
    'Assembly-CSharp.dll',
    'Interaction.CoreKeeper.dll',
    'Interaction.CoreKeeper.Components.dll',
    'Newtonsoft.Json.dll',
    'ObjectLookup.dll',
    'ObjectLookup.Components.dll',
    'Pug.Automation.dll',
    'Pug.Base.dll',
    'Pug.ECS.Components.dll',
    'Pug.ECS.Conversion.dll',
    'Pug.Objects.dll',
    'Pug.Other.dll',
    'PugMod.Integration.dll',
    'PugMod.Loader.dll',
    'PugMod.SDK.dll',
    'PugMod.SDK.Runtime.dll',
    'Unity.Collections.dll',
    'Unity.Entities.dll',
    'Unity.Mathematics.dll',
    'Unity.NetCode.dll',
    'Unity.Transforms.dll',
    'UnityEngine.CoreModule.dll'
)

$assemblies = @($criticalAssemblyNames | ForEach-Object {
    $path = Join-Path $managedRoot $_
    if (-not (Test-Path -LiteralPath $path)) {
        throw "Required shipped assembly is missing: $path"
    }
    $item = Get-Item -LiteralPath $path
    $hash = Get-FileHash -Algorithm SHA256 -LiteralPath $path
    [ordered]@{
        path = Get-RelativeManifest -Root $GameRoot -Path $path
        length = $item.Length
        sha256 = $hash.Hash.ToLowerInvariant()
    }
})

$objectHash = Get-FileHash -Algorithm SHA256 -LiteralPath $objectCatalog
$sourceTimestamp = [DateTimeOffset]::FromUnixTimeSeconds(
    [int64]$updatedMatch.Groups['value'].Value
).UtcDateTime.ToString('o')
$manifest = [ordered]@{
    schema_version = 1
    source_timestamp = $sourceTimestamp
    core_keeper = [ordered]@{
        steam_app_id = 1621690
        steam_build_id = [int64]$buildMatch.Groups['value'].Value
        last_updated_unix = [int64]$updatedMatch.Groups['value'].Value
        object_id_catalog = [ordered]@{
            path = Get-RelativeManifest -Root $GameRoot -Path $objectCatalog
            sha256 = $objectHash.Hash.ToLowerInvariant()
        }
        configuration_manifest = Get-ManifestEntries -Root $confRoot -Filter '*'
        assembly_manifest = $assemblies
    }
    archipelago = [ordered]@{
        version = '0.6.8'
        source_path = 'Archipelago-main'
        revision = $null
    }
    poptracker = [ordered]@{
        installed_version = '0.35.3'
        reference_version = '0.35.4-rc2'
        reference_revision = '407506c72ebf08f419f85b2f844ec8ca6c452ed7'
    }
}

$parent = Split-Path $OutputPath -Parent
if ($parent) {
    New-Item -ItemType Directory -Path $parent -Force | Out-Null
}
$manifest | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $OutputPath -Encoding utf8
