param(
    [int]$Port = 38406,
    [string]$Slot = "Player",
    [string]$ArchipelagoRoot = $env:ARCHIPELAGO_ROOT,
    [string]$PythonPath = "python"
)

$ErrorActionPreference = "Stop"
$MainlineRoot = Split-Path -Parent $PSScriptRoot
$RoomArchive = Join-Path $MainlineRoot "dist\playtest-room\AP_90428350886166383246.zip"
$ServerRoot = Join-Path $MainlineRoot "build\transport-server"
$Multidata = Join-Path $ServerRoot "AP_90428350886166383246.archipelago"
# MultiServer 0.7 derives its save name from the multidata filename; its
# parsed --savefile value is currently not forwarded into Context.init_save.
$SaveFile = Join-Path $ServerRoot "AP_90428350886166383246.apsave"
$Dependencies = Join-Path $MainlineRoot ".deps"
$Catalog = Join-Path $MainlineRoot "data\canonical_catalog.json"

if (-not (Test-Path -LiteralPath $RoomArchive)) {
    throw "Missing deterministic playtest room: $RoomArchive"
}
if (-not (Test-Path -LiteralPath $PythonPath)) {
    throw "Missing supported Python runtime: $PythonPath"
}

New-Item -ItemType Directory -Force -Path $ServerRoot | Out-Null
Expand-Archive -LiteralPath $RoomArchive -DestinationPath $ServerRoot -Force
if (Test-Path -LiteralPath $SaveFile) {
    Remove-Item -LiteralPath $SaveFile -Force
}

$ServerArguments = '"{0}" --archipelago "{1}" --dependencies "{2}" --catalog "{3}" --multidata "{4}" --savefile "{5}" --host 127.0.0.1 --port {6}' -f `
    (Join-Path $PSScriptRoot "run_isolated_server.py"), $ArchipelagoRoot, $Dependencies, $Catalog, `
    $Multidata, $SaveFile, $Port
$StartInfo = New-Object System.Diagnostics.ProcessStartInfo
$StartInfo.FileName = $PythonPath
$StartInfo.Arguments = $ServerArguments
$StartInfo.UseShellExecute = $false
$StartInfo.CreateNoWindow = $true
$StartInfo.RedirectStandardOutput = $true
$StartInfo.RedirectStandardError = $true
$Server = New-Object System.Diagnostics.Process
$Server.StartInfo = $StartInfo
if (-not $Server.Start()) {
    throw "Failed to launch the official Archipelago server."
}
$ServerOutputTask = $Server.StandardOutput.ReadToEndAsync()
$ServerErrorTask = $Server.StandardError.ReadToEndAsync()

try {
    $Deadline = [DateTime]::UtcNow.AddSeconds(30)
    do {
        Start-Sleep -Milliseconds 100
        $Probe = New-Object System.Net.Sockets.TcpClient
        try {
            $Probe.Connect("127.0.0.1", $Port)
            $Listening = $Probe.Connected
        }
        catch {
            $Listening = $false
        }
        finally {
            $Probe.Dispose()
        }
    } while (-not $Listening -and [DateTime]::UtcNow -lt $Deadline -and -not $Server.HasExited)

    if (-not $Listening) {
        if (-not $Server.HasExited) {
            $Server.Kill()
            $Server.WaitForExit()
        }
        $Details = $ServerOutputTask.GetAwaiter().GetResult() + [Environment]::NewLine `
            + $ServerErrorTask.GetAwaiter().GetResult()
        throw "Archipelago server did not listen on port $Port. $Details"
    }

    dotnet run --configuration Release --project (Join-Path $PSScriptRoot "transport\CoreKeeperArchipelago.Transport.Tests.csproj") `
        -- "ws://127.0.0.1:$Port" $Slot
    if ($LASTEXITCODE -ne 0) {
        throw "Transport integration test failed with exit code $LASTEXITCODE."
    }
}
finally {
    if (-not $Server.HasExited) {
        $Server.Kill()
        $Server.WaitForExit()
    }
}
