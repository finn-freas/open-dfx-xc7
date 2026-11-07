param(
    [int[]]$Extras = @(0),
    [switch]$Run
)

$CONFIG = @{
    WslProject = "\\wsl.localhost\Ubuntu\home\finnf\open-dfx-xc7"
    WinWork    = "$HOME\open-dfx-xc7-vivado\sim\ddr3_phy"
    VivadoDirs = @("C:\AMDDesignTools\2025.2\Vivado\bin", "C:\Xilinx\Vivado\2025.2\bin", "C:\Xilinx\2025.2\Vivado\bin")
    Sources    = @("phy_top.v", "ddr3_model.v", "tb_phy.v")
    SrcSub     = "designs\ddr3\phy_sim"
    LogDst     = "build\ddr3\sim\phy"
    Top        = "tb_phy"
    Retries    = 3
    DryRun     = $true
}

$bin = $CONFIG.VivadoDirs | Where-Object { Test-Path (Join-Path $_ "xvlog.bat") } | Select-Object -First 1
if (-not $bin) { throw "xvlog.bat not found in: $($CONFIG.VivadoDirs -join ', ')" }
$glbl = Join-Path (Split-Path $bin) "data\verilog\src\glbl.v"

if ($CONFIG.DryRun -and -not $Run) {
    Write-Output "[dry] xvlog -sv $($CONFIG.Sources -join ' ') glbl.v; xelab -L unisims_ver -L secureip $($CONFIG.Top) glbl; xsim -R -testplusarg RD_EXTRA=<n> for n in $($Extras -join ',')  (in $($CONFIG.WinWork))"
    Write-Output "add -Run to simulate"
    exit 0
}
if (Get-Process -Name vivado -ErrorAction SilentlyContinue) { throw "another vivado process is running; not starting" }
New-Item -ItemType Directory -Force $CONFIG.WinWork | Out-Null
Set-Location $CONFIG.WinWork
foreach ($s in $CONFIG.Sources) { Copy-Item -Force "$($CONFIG.WslProject)\$($CONFIG.SrcSub)\$s" . }
Copy-Item -Force $glbl .
& (Join-Path $bin "xvlog.bat") -sv @($CONFIG.Sources) glbl.v *> xvlog.out
if ($LASTEXITCODE) { throw "xvlog failed, see $($CONFIG.WinWork)\xvlog.out" }
& (Join-Path $bin "xelab.bat") -debug off -timescale 1ps/1ps -L unisims_ver -L secureip -s tb_snap "work.$($CONFIG.Top)" work.glbl *> xelab.out
if ($LASTEXITCODE) { throw "xelab failed, see $($CONFIG.WinWork)\xelab.out" }
$dst = "$($CONFIG.WslProject)\$($CONFIG.LogDst)"
New-Item -ItemType Directory -Force $dst | Out-Null
Copy-Item -Force xvlog.out, xelab.out $dst
foreach ($x in $Extras) {
    $log = "xsim_extra$x.out"
    for ($i = 0; $i -lt $CONFIG.Retries; $i++) {
        $t0 = Get-Date
        & (Join-Path $bin "xsim.bat") tb_snap -R -testplusarg "`"RD_EXTRA=$x`"" *> $log
        if (-not (Select-String -Path $log -Pattern "Failed to launch child process" -Quiet)) { break }
        Start-Sleep -Seconds 10
    }
    "seconds $([int]((Get-Date) - $t0).TotalSeconds)" | Add-Content $log
    Copy-Item -Force $log $dst
    $res = Select-String -Path $log -Pattern "\[tb\] (best|PASS|FAIL)" | ForEach-Object { $_.Line }
    Write-Output "RD_EXTRA=$x ps: $($res -join ' | ')"
}
