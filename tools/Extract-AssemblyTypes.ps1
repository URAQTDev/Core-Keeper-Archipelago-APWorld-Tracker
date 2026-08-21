param(
    [Parameter(Mandatory = $true)]
    [string]$GameRoot,
    [Parameter(Mandatory = $true)]
    [string]$IlSpyPath,
    [Parameter(Mandatory = $true)]
    [string]$SourceManifestPath,
    [Parameter(Mandatory = $true)]
    [string]$OutputPath
)

$ErrorActionPreference = 'Stop'
$sourceManifest = Get-Content -LiteralPath $SourceManifestPath -Raw | ConvertFrom-Json
$records = @()

foreach ($assembly in $sourceManifest.core_keeper.assembly_manifest) {
    $assemblyPath = Join-Path $GameRoot ($assembly.path -replace '/', '\')
    $entities = @()
    foreach ($kind in @('c', 's', 'e', 'i', 'd')) {
        $lines = @(& $IlSpyPath --disable-updatecheck -l $kind $assemblyPath)
        if ($LASTEXITCODE -ne 0) {
            throw "ILSpy failed while inspecting $assemblyPath"
        }
        foreach ($line in $lines) {
            if ($line -match '^(Class|Struct|Enum|Interface|Delegate)\s+(.+)$') {
                $entities += [ordered]@{
                    kind = $Matches[1].ToLowerInvariant()
                    full_name = $Matches[2]
                }
            }
        }
    }
    $records += [ordered]@{
        assembly = [System.IO.Path]::GetFileName($assemblyPath)
        sha256 = $assembly.sha256
        entities = @($entities | Sort-Object kind, full_name)
    }
}

$payload = [ordered]@{
    schema_version = 1
    core_keeper_steam_build_id = $sourceManifest.core_keeper.steam_build_id
    ilspy_version = (& $IlSpyPath --version | Select-Object -First 1)
    assemblies = $records
}

$parent = Split-Path $OutputPath -Parent
if ($parent) {
    New-Item -ItemType Directory -Path $parent -Force | Out-Null
}
$payload | ConvertTo-Json -Depth 6 -Compress | Set-Content -LiteralPath $OutputPath -Encoding utf8
