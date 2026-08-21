param(
    [Parameter(Mandatory = $true)][string]$GameRoot,
    [Parameter(Mandatory = $true)][string]$IlSpyPath,
    [Parameter(Mandatory = $true)][string]$PythonPath,
    [Parameter(Mandatory = $true)][string]$SourceManifestPath,
    [Parameter(Mandatory = $true)][string]$OutputPath
)

$ErrorActionPreference = 'Stop'
$scratch = Join-Path (Split-Path -Parent $OutputPath) '..\build\enum-source'
New-Item -ItemType Directory -Path $scratch -Force | Out-Null
$assembly = Join-Path $GameRoot 'CoreKeeper_Data\Managed\Pug.Base.dll'
$types = [ordered]@{
    'Biome' = 'Biome'
    'Tileset' = 'PugTilemap.Tileset'
    'TileType' = 'PugTilemap.TileType'
}
$sources = @()
foreach ($entry in $types.GetEnumerator()) {
    $destination = Join-Path $scratch ($entry.Key + '.cs')
    & $IlSpyPath -t $entry.Value $assembly | Set-Content -LiteralPath $destination -Encoding utf8
    if ($LASTEXITCODE -ne 0) { throw "Failed to decompile enum $($entry.Value)." }
    $sources += $destination
}
& $PythonPath (Join-Path $PSScriptRoot 'extract_game_enums.py') `
    $SourceManifestPath $OutputPath @sources
if ($LASTEXITCODE -ne 0) { throw 'Game enum extraction failed.' }
