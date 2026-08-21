param([string]$Configuration = 'Release')

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$project = Join-Path $root 'extractor\CoreKeeperArchipelago.Extractor.csproj'
$output = Join-Path $root 'extractor-output\CoreKeeperArchipelagoExtractor'

& dotnet build $project -c $Configuration --nologo
if ($LASTEXITCODE -ne 0) { throw 'Extractor build failed.' }

New-Item -ItemType Directory -Force -Path $output | Out-Null
Copy-Item -LiteralPath (Join-Path $root "extractor\bin\$Configuration\netstandard2.1\CoreKeeperArchipelago.Extractor.dll") `
    -Destination (Join-Path $output 'CoreKeeperArchipelagoExtractor.dll') -Force
Copy-Item -LiteralPath (Join-Path $root 'extractor\ModManifest.json') `
    -Destination (Join-Path $output 'ModManifest.json') -Force
Write-Output "Packaged developer extractor at $output"
