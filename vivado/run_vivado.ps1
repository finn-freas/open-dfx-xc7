param(
    [Parameter(Mandatory=$true)][string]$Design,
    [string]$Top = $Design,
    [string]$Xdc = "arty_a7_35t.xdc",
    [string]$Script = "build_full.tcl",
    [string]$Rms = "",
    [switch]$Run
)

$CONFIG = @{
    WslProject = "\\wsl.localhost\Ubuntu\home\finnf\open-dfx-xc7"
    WinWork    = "$HOME\open-dfx-xc7-vivado"
    VivadoDirs = @("C:\AMDDesignTools\2025.2\Vivado\bin", "C:\Xilinx\Vivado\2025.2\bin", "C:\Xilinx\2025.2\Vivado\bin")
    DryRun     = $true
}

$vivado = $CONFIG.VivadoDirs | ForEach-Object { Join-Path $_ "vivado.bat" } | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $vivado) { throw "vivado.bat not found in: $($CONFIG.VivadoDirs -join ', ')" }

$src = Join-Path $CONFIG.WinWork "designs\$Design"
$out = Join-Path $CONFIG.WinWork "build\$Design"
$tcl = Join-Path $CONFIG.WinWork "vivado\$Script"
New-Item -ItemType Directory -Force $src, (Split-Path $tcl) | Out-Null
Copy-Item -Force "$($CONFIG.WslProject)\designs\$Design\*" $src
Copy-Item -Force "$($CONFIG.WslProject)\vivado\$Script" $tcl

$fwd = { param($p) $p -replace '\\', '/' }
$vargs = @("-mode", "batch", "-nojournal", "-log", (& $fwd "$out\vivado.log"), "-source", (& $fwd $tcl),
          "-tclargs", $Design, $Top, (& $fwd $src), (& $fwd "$src\$Xdc"), (& $fwd $out))
if ($Rms) { $vargs += $Rms }

if ($CONFIG.DryRun -and -not $Run) {
    Write-Output "[dry] $vivado $($vargs -join ' ')"
    Write-Output "add -Run to build"
    exit 0
}
New-Item -ItemType Directory -Force $out | Out-Null
& $vivado @vargs
Write-Output "done: $out"
