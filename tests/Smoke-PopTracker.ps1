param(
    [string]$PopTrackerPath = 'poptracker',
    [string]$PackPath = (Join-Path (Split-Path -Parent $PSScriptRoot) 'dist\core_keeper_poptracker.zip'),
    [string]$Variant = 'medium',
    [int]$ObservationSeconds = 5
)

$ErrorActionPreference = 'Stop'
if (-not (Test-Path -LiteralPath $PopTrackerPath)) {
    Write-Warning "PopTracker runtime smoke test skipped: $PopTrackerPath was not found."
    return
}
if (-not (Test-Path -LiteralPath $PackPath)) {
    throw "PopTracker pack was not found: $PackPath"
}

# PopTracker 0.35.3 accepts a pack path as its positional action and uses
# --pack-variant for the variant. --pack and --variant are not valid flags.
$process = Start-Process `
    -FilePath $PopTrackerPath `
    -ArgumentList @('--no-console', '--pack-variant', $Variant, $PackPath) `
    -WindowStyle Hidden `
    -PassThru
try {
    Start-Sleep -Seconds $ObservationSeconds
    if ($process.HasExited) {
        throw "PopTracker exited during pack load with code $($process.ExitCode)."
    }
    Write-Output "PopTracker $Variant pack runtime smoke test passed."
}
finally {
    if (-not $process.HasExited) {
        Stop-Process -Id $process.Id -Force
    }
}
