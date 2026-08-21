param(
    [string]$PythonPath = 'python'
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$version = (Get-Content -LiteralPath (Join-Path $root 'poptracker\manifest.json') -Raw | ConvertFrom-Json).package_version
$payload = Join-Path $root 'build\tracker-local-distribution'
$pyinstallerWork = Join-Path $root 'build\pyinstaller-work'
$binaryDirectory = Join-Path $root 'dist\tracker-local-setup-bin'
$releaseDirectory = Join-Path $root 'dist\CoreKeeperArchipelago-Tracker-Setup'
$releaseArchive = Join-Path $root "dist\CoreKeeperArchipelago-Tracker-Setup-$version.zip"

& (Join-Path $PSScriptRoot 'Package-Extractor.ps1') -Configuration Release
if ($LASTEXITCODE -ne 0) { throw 'Extractor packaging failed.' }
& $PythonPath (Join-Path $PSScriptRoot 'build_tracker_local_distribution.py') $root $payload
if ($LASTEXITCODE -ne 0) { throw 'Texture-free payload build failed.' }

if (Test-Path -LiteralPath $binaryDirectory) { Remove-Item -LiteralPath $binaryDirectory -Recurse -Force }
& $PythonPath -m PyInstaller --noconfirm --clean --onefile --console --uac-admin `
    --name 'Install-Core-Keeper-Archipelago-Tracker' `
    --distpath $binaryDirectory --workpath $pyinstallerWork `
    --specpath (Join-Path $root 'build') --collect-all PIL `
    --add-data "$payload\template;template" `
    --add-data "$payload\tools;tools" `
    --add-data "$payload\extractor;extractor" `
    --add-data "$payload\TEXTURE_FREE_REPORT.json;." `
    (Join-Path $PSScriptRoot 'tracker_local_setup.py')
if ($LASTEXITCODE -ne 0) { throw 'Self-contained setup build failed.' }

if (Test-Path -LiteralPath $releaseDirectory) { Remove-Item -LiteralPath $releaseDirectory -Recurse -Force }
New-Item -ItemType Directory -Force -Path (Join-Path $releaseDirectory 'licenses') | Out-Null
$executable = Join-Path $binaryDirectory 'Install-Core-Keeper-Archipelago-Tracker.exe'
Copy-Item -LiteralPath $executable -Destination $releaseDirectory
Copy-Item -LiteralPath (Join-Path $root 'TRACKER_LOCAL_SETUP.md') -Destination (Join-Path $releaseDirectory 'README.md')
Copy-Item -LiteralPath (Join-Path $payload 'TEXTURE_FREE_REPORT.json') -Destination $releaseDirectory
Copy-Item -LiteralPath (Join-Path $root 'LICENSE') -Destination (Join-Path $releaseDirectory 'licenses\CoreKeeperArchipelago-LICENSE.txt')

$pythonRoot = Split-Path -Parent $PythonPath
Copy-Item -LiteralPath (Join-Path $pythonRoot 'LICENSE.txt') -Destination (Join-Path $releaseDirectory 'licenses\Python-LICENSE.txt')
$sitePackages = Join-Path $pythonRoot 'Lib\site-packages'
Copy-Item -LiteralPath (Get-ChildItem $sitePackages -Recurse -File -Filter LICENSE | Where-Object FullName -like '*pillow-*.dist-info*' | Select-Object -First 1).FullName -Destination (Join-Path $releaseDirectory 'licenses\Pillow-LICENSE.txt')
Copy-Item -LiteralPath (Get-ChildItem $sitePackages -Recurse -File -Filter COPYING.txt | Where-Object FullName -like '*pyinstaller-*.dist-info*' | Select-Object -First 1).FullName -Destination (Join-Path $releaseDirectory 'licenses\PyInstaller-COPYING.txt')
Copy-Item -LiteralPath (Get-ChildItem $sitePackages -Recurse -File -Filter LICENSE | Where-Object FullName -like '*pyinstaller_hooks_contrib-*.dist-info*' | Select-Object -First 1).FullName -Destination (Join-Path $releaseDirectory 'licenses\PyInstaller-hooks-contrib-LICENSE.txt')

$hash = (Get-FileHash -LiteralPath (Join-Path $releaseDirectory 'Install-Core-Keeper-Archipelago-Tracker.exe') -Algorithm SHA256).Hash.ToLowerInvariant()
Set-Content -LiteralPath (Join-Path $releaseDirectory 'SHA256SUMS.txt') -Value "$hash  Install-Core-Keeper-Archipelago-Tracker.exe" -Encoding ascii
& $PythonPath (Join-Path $PSScriptRoot 'package_poptracker.py') $releaseDirectory $releaseArchive
if ($LASTEXITCODE -ne 0) { throw 'Setup release archive failed.' }
Write-Output "Built texture-free tracker setup: $releaseArchive"
