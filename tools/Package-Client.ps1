param(
    [string]$Configuration = 'Release'
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$project = Join-Path $root 'client\CoreKeeperArchipelago.Mainline.csproj'
$packageRoot = Join-Path $root 'dist\CoreKeeperArchipelago'
$libraries = Join-Path $packageRoot 'Libraries'
$officialClient = Join-Path $root 'build\vendor-client\Archipelago.MultiClient.Net.dll'

& (Join-Path $root 'tools\Prepare-OfficialClientSource.ps1')
if ($LASTEXITCODE -ne 0) { throw 'Official Archipelago client compatibility build failed.' }

& dotnet build $project --configuration $Configuration --no-restore "-p:RestorePackagesPath=$(Join-Path $root '.nuget')"
if ($LASTEXITCODE -ne 0) { throw 'Client compilation failed.' }

if (Test-Path -LiteralPath $packageRoot) {
    Remove-Item -LiteralPath $packageRoot -Recurse -Force
}
New-Item -ItemType Directory -Path $libraries -Force | Out-Null

Copy-Item -LiteralPath (Join-Path $root 'client\ModManifest.json') -Destination $packageRoot
Copy-Item -LiteralPath (Join-Path $root "client\bin\$Configuration\netstandard2.1\CoreKeeperArchipelago.Mainline.dll") `
    -Destination (Join-Path $packageRoot 'CoreKeeperArchipelago.dll')
Copy-Item -LiteralPath $officialClient -Destination $libraries
$assetDirectory = Join-Path $packageRoot 'Assets'
New-Item -ItemType Directory -Path $assetDirectory -Force | Out-Null
Copy-Item -LiteralPath (Join-Path $root 'client\Assets\ArchipelagoLogo.png') -Destination $assetDirectory

$files = Get-ChildItem -LiteralPath $packageRoot -File -Recurse
$size = ($files | Measure-Object -Property Length -Sum).Sum
Write-Output "Packaged $($files.Count) client files ($size bytes) at $packageRoot"
