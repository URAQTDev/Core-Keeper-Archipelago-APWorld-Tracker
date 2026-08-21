param(
    [string]$GameRoot = 'C:\Program Files (x86)\Steam\steamapps\common\Core Keeper'
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$repository = Join-Path $root '.deps\Archipelago.MultiClient.Net'
$commit = '0c57591db30f2497b0b4fef87164aa2bbe2e51b2'
$project = Join-Path $repository 'Archipelago.MultiClient.Net\Archipelago.MultiClient.Net.csproj'
$socketHelper = Join-Path $repository 'Archipelago.MultiClient.Net\Helpers\ArchipelagoSocketHelper_system.net.websockets.cs'
$socketBase = Join-Path $repository 'Archipelago.MultiClient.Net\Helpers\BaseArchipelagoSocketHelper_system.net.websockets.cs'
$sharpHelper = Join-Path $repository 'Archipelago.MultiClient.Net\Helpers\ArchipelagoSocketHelper_websocket-sharp.cs'
$compressedSocket = Join-Path $root 'vendor\CompressedWebSocketClient.cs'
$newtonsoft = Join-Path $GameRoot 'CoreKeeper_Data\Managed\Newtonsoft.Json.dll'
$output = Join-Path $root 'build\vendor-client'

if (-not (Test-Path -LiteralPath $repository)) {
    & git clone https://github.com/ArchipelagoMW/Archipelago.MultiClient.Net.git $repository
    if ($LASTEXITCODE -ne 0) { throw 'Could not clone the official Archipelago client.' }
}

& git -c "safe.directory=$repository" -C $repository checkout --detach $commit
if ($LASTEXITCODE -ne 0) { throw 'Could not select the pinned official Archipelago client commit.' }

$contents = (& git -c "safe.directory=$repository" -C $repository show "$commit`:Archipelago.MultiClient.Net/Archipelago.MultiClient.Net.csproj") -join "`n"
if ($LASTEXITCODE -ne 0) { throw 'Could not read the pinned official client project.' }
$contents = $contents.Replace(
    '<TargetFrameworks>net35;net40;net45;netstandard2.0;net6.0</TargetFrameworks>',
    '<TargetFrameworks>netstandard2.0</TargetFrameworks>')
$contents = $contents.Replace(
    '..\DLLs\netstandard2.0\Newtonsoft.Json.dll',
    $newtonsoft)
$contents = $contents.Replace(
    "<HintPath>$newtonsoft</HintPath>",
    "<HintPath>$newtonsoft</HintPath>`r`n`t`t`t<Private>false</Private>")
$contents = $contents.Replace(
    '</Project>',
    ('`t<ItemGroup>`r`n`t`t<Compile Include="{0}" Link="Helpers\CompressedWebSocketClient.cs" />`r`n`t</ItemGroup>`r`n</Project>' -f $compressedSocket).Replace('`t', "`t").Replace('`r`n', "`r`n"))
Set-Content -LiteralPath $project -Value $contents -Encoding UTF8

# Core Keeper's Mono ClientWebSocket lacks the compression API used by the
# official client's net6 target. Keep the official packet/session stack but
# substitute the audited RFC 6455/permessage-deflate adapter for its socket.
$socketContents = (& git -c "safe.directory=$repository" -C $repository show "$commit`:Archipelago.MultiClient.Net/Helpers/ArchipelagoSocketHelper_system.net.websockets.cs") -join "`n"
if ($LASTEXITCODE -ne 0) { throw 'Could not read the pinned official socket helper.' }
$directDeflate = @'
#if NET6_0
			clientWebSocket.Options.DangerousDeflateOptions = new WebSocketDeflateOptions();
#endif
'@
if (-not $socketContents.Contains($directDeflate)) { throw 'Pinned official deflate block changed.' }
$socketContents = $socketContents.Replace('ClientWebSocket', 'CompressedWebSocketClient')
$socketContents = $socketContents.Replace($directDeflate, '')
Set-Content -LiteralPath $socketHelper -Value $socketContents -Encoding UTF8

foreach ($source in @(
    @{ Path = $socketBase; GitPath = 'Archipelago.MultiClient.Net/Helpers/BaseArchipelagoSocketHelper_system.net.websockets.cs' },
    @{ Path = $sharpHelper; GitPath = 'Archipelago.MultiClient.Net/Helpers/ArchipelagoSocketHelper_websocket-sharp.cs' }
)) {
    $sourceContents = (& git -c "safe.directory=$repository" -C $repository show "$commit`:$($source.GitPath)") -join "`n"
    if ($LASTEXITCODE -ne 0) { throw "Could not restore pinned transport source $($source.GitPath)." }
    Set-Content -LiteralPath $source.Path -Value $sourceContents -Encoding UTF8
}

& dotnet build $project `
    --configuration Release `
    --framework netstandard2.0 `
    "-p:OutputPath=$output\" `
    -p:GenerateDocumentationFile=false
if ($LASTEXITCODE -ne 0) { throw 'Official Archipelago client compatibility build failed.' }

$assembly = Join-Path $output 'Archipelago.MultiClient.Net.dll'
if (-not (Test-Path -LiteralPath $assembly)) { throw 'Official client output is missing.' }
$reference = [Reflection.Assembly]::LoadFrom($assembly).GetReferencedAssemblies() |
    Where-Object Name -eq 'Newtonsoft.Json'
if ($reference.Version.Major -ne 13 -or $reference.GetPublicKeyToken().Length -eq 0) {
    throw "Official client did not bind to Core Keeper's signed Newtonsoft 13 assembly."
}
