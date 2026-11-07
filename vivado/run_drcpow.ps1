param(
    [string[]]$Names = @(),
    [string]$Tag = "drcpow",
    [switch]$Run
)
$Names = @($Names | ForEach-Object { $_ -split ',' } | ForEach-Object { $_.Trim() } | Where-Object { $_ })

$CONFIG = @{
    WslProject = "\\wsl.localhost\Ubuntu\home\finnf\open-dfx-xc7"
    WinWork    = "$HOME\open-dfx-xc7-vivado"
    VivadoDirs = @("C:\AMDDesignTools\2025.2\Vivado\bin", "C:\Xilinx\Vivado\2025.2\bin", "C:\Xilinx\2025.2\Vivado\bin")
    Script     = "build_drcpow.tcl"
    SrcSub     = "designs\drcpow"
    DryRun     = $true
}

$vivado = $CONFIG.VivadoDirs | ForEach-Object { Join-Path $_ "vivado.bat" } | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $vivado) { throw "vivado.bat not found in: $($CONFIG.VivadoDirs -join ', ')" }
if ($Names.Count -eq 0) { throw "give -Names as WSL-relative source directories, e.g. designs/drc/drc_ok,build/qor/src/fir_p10" }

$srcRoot = Join-Path $CONFIG.WinWork $CONFIG.SrcSub
$outRoot = Join-Path $CONFIG.WinWork "build\$Tag"
$tcl = Join-Path $CONFIG.WinWork "vivado\$($CONFIG.Script)"
New-Item -ItemType Directory -Force $srcRoot, (Split-Path $tcl) | Out-Null
$leaves = @()
foreach ($n in $Names) {
    $leaf = Split-Path $n -Leaf
    $d = Join-Path $srcRoot $leaf
    New-Item -ItemType Directory -Force $d | Out-Null
    Get-ChildItem -File (Join-Path $CONFIG.WslProject ($n -replace '/', '\')) | Copy-Item -Force -Destination $d
    $leaves += $leaf
}
Copy-Item -Force "$($CONFIG.WslProject)\vivado\$($CONFIG.Script)" $tcl

$fwd = { param($p) $p -replace '\\', '/' }
$vargs = @("-mode", "batch", "-nojournal", "-log", (& $fwd "$outRoot\vivado.log"), "-source", (& $fwd $tcl),
          "-tclargs", (& $fwd $srcRoot), (& $fwd $outRoot)) + $leaves

if ($CONFIG.DryRun -and -not $Run) {
    Write-Output "[dry] $vivado $($vargs -join ' ')"
    Write-Output "add -Run to build"
    exit 0
}
if (Get-Process -Name vivado -ErrorAction SilentlyContinue) { throw "another vivado process is running; not starting" }
New-Item -ItemType Directory -Force $outRoot | Out-Null
$t0 = Get-Date
& $vivado @vargs
Write-Output ("done: {0} in {1:N0}s" -f $outRoot, ((Get-Date) - $t0).TotalSeconds)
