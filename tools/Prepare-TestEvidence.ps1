param(
    [Parameter(Mandatory = $true)]
    [string]$GameRoot,
    [Parameter(Mandatory = $true)]
    [string]$IlSpyPath
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$build = Join-Path $root 'build'

function Export-Assembly([string]$AssemblyName, [string]$OutputName) {
    $assembly = Join-Path $GameRoot "CoreKeeper_Data\Managed\$AssemblyName.dll"
    $output = Join-Path $build $OutputName
    if (-not (Test-Path -LiteralPath $assembly -PathType Leaf)) {
        throw "Required game assembly was not found: $assembly"
    }
    if (Test-Path -LiteralPath $output) {
        Remove-Item -LiteralPath $output -Recurse -Force
    }
    New-Item -ItemType Directory -Path $output -Force | Out-Null
    & $IlSpyPath --disable-updatecheck -p -o $output $assembly
    if ($LASTEXITCODE -ne 0) {
        throw "ILSpy failed while exporting $assembly"
    }
}

Export-Assembly 'Pug.Other' 'decompiled-pug-other'
Export-Assembly 'Pug.Objects' 'decompiled-Pug.Objects'

$pugOther = Join-Path $build 'decompiled-pug-other'
$pugOtherAlias = Join-Path $build 'decompiled-pugother'
if (Test-Path -LiteralPath $pugOtherAlias) {
    Remove-Item -LiteralPath $pugOtherAlias -Recurse -Force
}
Copy-Item -LiteralPath $pugOther -Destination $pugOtherAlias -Recurse
