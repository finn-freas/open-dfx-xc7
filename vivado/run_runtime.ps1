param(
    [string[]]$Names = @("blinky", "rv_soc", "litex_ddr3", "mc12_a100"),
    [int]$Rep = 1,
    [switch]$Run
)
$Names = @($Names | ForEach-Object { $_ -split ',' } | ForEach-Object { $_.Trim() } | Where-Object { $_ })
$CONFIG = @{
    WslProject = "\wsl.localhost\Ubuntu\home\finnf\open-dfx-xc7"
    WinWork    = "$HOME\open-dfx-xc7-vivado"
    Vivado     = "C:\AMDDesignTools\2025.2\Vivado\bin\vivado.bat"
}
$srcRoot = Join-Path $CONFIG.WinWork "designs\runtime"
$outRoot = Join-Path $CONFIG.WinWork "build\runtime"
$tcl = Join-Path $CONFIG.WinWork "vivado\build_runtime.tcl"
New-Item -ItemType Directory -Force $srcRoot, $outRoot, (Split-Path $tcl) | Out-Null
Copy-Item -Force "$($CONFIG.WslProject)\vivado\build_runtime.tcl" $tcl
$fwd = { param($p) $p -replace '\', '/' }
foreach ($n in $Names) {
    $s = Join-Path $srcRoot $n
    if (Test-Path $s) { Remove-Item -Recurse -Force $s }
    Copy-Item -Recurse -Force "$($CONFIG.WslProject)\build\runtime\vsrc\$n" $s
    $o = Join-Path $outRoot "$n\r$Rep"
    New-Item -ItemType Directory -Force $o | Out-Null
    $vargs = @("-mode", "batch", "-nojournal", "-log", (& $fwd "$o\vivado.log"), "-source", (& $fwd $tcl), "-tclargs", (& $fwd $s), (& $fwd $o), $n)
    if (-not $Run) { Write-Output "[dry] $($CONFIG.Vivado) $($vargs -join ' ')"; continue }
    $t0 = Get-Date
    & $CONFIG.Vivado @vargs | Out-Null
    $w = ((Get-Date) - $t0).TotalSeconds
    "process_wall {0:N2}" -f $w | Out-File -Encoding ascii -Append (Join-Path $o "times.txt")
    Write-Output ("{0} r{1}: {2:N1}s" -f $n, $Rep, $w)
}
