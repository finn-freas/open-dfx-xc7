param(
    [string[]]$Names = @(),
    [string]$Tag = "qor",
    [string]$Script = "build_gap.tcl",
    [string]$SrcRel = "build\qor\src",
    [switch]$Run
)
$Names = @($Names | ForEach-Object { $_ -split ',' } | ForEach-Object { $_.Trim() } | Where-Object { $_ })

$CONFIG = @{
    WslProject = "\\wsl.localhost\Ubuntu\home\finnf\open-dfx-xc7"
    WinWork    = "$HOME\open-dfx-xc7-vivado"
    VivadoDirs = @("C:\AMDDesignTools\2025.2\Vivado\bin", "C:\Xilinx\Vivado\2025.2\bin", "C:\Xilinx\2025.2\Vivado\bin")
    SrcRel     = $SrcRel
    DryRun     = $true
}

$vivado = $CONFIG.VivadoDirs | ForEach-Object { Join-Path $_ "vivado.bat" } | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $vivado) { throw "vivado.bat not found in: $($CONFIG.VivadoDirs -join ', ')" }
$busy = Get-Process -Name vivado -ErrorAction SilentlyContinue
if ($busy) { throw "another Vivado is running (pid $($busy.Id -join ', '))" }

$wslSrc = Join-Path $CONFIG.WslProject $CONFIG.SrcRel
$srcRoot = Join-Path $CONFIG.WinWork "designs\$Tag"
$outRoot = Join-Path $CONFIG.WinWork "build\$Tag"
$tcl = Join-Path $CONFIG.WinWork "vivado\$Script"
if ($Names.Count -eq 0) {
    $Names = Get-ChildItem -Directory $wslSrc | ForEach-Object { $_.Name } | Sort-Object
}
New-Item -ItemType Directory -Force $srcRoot, (Split-Path $tcl) | Out-Null
foreach ($n in $Names) {
    New-Item -ItemType Directory -Force (Join-Path $srcRoot $n) | Out-Null
    Copy-Item -Force "$wslSrc\$n\*" (Join-Path $srcRoot $n)
}
Copy-Item -Force "$($CONFIG.WslProject)\vivado\$Script" $tcl

$fwd = { param($p) $p -replace '\\', '/' }
$vargs = @("-mode", "batch", "-nojournal", "-log", (& $fwd "$outRoot\vivado_$(Get-Date -Format yyyyMMdd_HHmmss).log"), "-source", (& $fwd $tcl),
          "-tclargs", (& $fwd $srcRoot), (& $fwd $outRoot)) + $Names

if ($CONFIG.DryRun -and -not $Run) {
    Write-Output "[dry] $vivado $($vargs -join ' ')"
    Write-Output "add -Run to build"
    exit 0
}
New-Item -ItemType Directory -Force $outRoot | Out-Null
$t0 = Get-Date
& $vivado @vargs
Write-Output ("done: {0} in {1:N0}s" -f $outRoot, ((Get-Date) - $t0).TotalSeconds)
