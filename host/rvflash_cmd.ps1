param(
    [string]$Port = "",
    [ValidateSet("J", "R", "S", "C", "A")][string]$Cmd = "J",
    [int]$Slot = 0,
    [string]$Addr = "400000",
    [string[]]$Custom = @("12345678", "0F0F0F0F"),
    [switch]$Run
)

$CONFIG = @{
    Baud      = 1000000
    DryRun    = $true
    TimeoutMs = 5000
    MaxSlots  = 16
}

function ConvertTo-U32([string]$hex) { [Convert]::ToUInt32($hex, 16) }

function Get-Bytes([uint32]$w) {
    $b = [BitConverter]::GetBytes($w)
    [Array]::Reverse($b)
    $b
}

function Read-Exact($sp, [int]$n) {
    $buf = New-Object byte[] $n
    $got = 0
    while ($got -lt $n) { $got += $sp.Read($buf, $got, $n - $got) }
    $buf
}

function Read-Word($sp) {
    $b = Read-Exact $sp 4
    [uint32]([uint64]$b[0] * 16777216 + [uint64]$b[1] * 65536 + [uint64]$b[2] * 256 + [uint64]$b[3])
}

$Custom = @($Custom | ForEach-Object { $_ -split "," } | Where-Object { $_ })
if ($Cmd -in @("C", "A") -and $Custom.Count -ne 2) { throw "-Custom takes two hex words, e.g. -Custom 12345678,0F0F0F0F" }
if ($Cmd -eq "S" -and ($Slot -lt 0 -or $Slot -ge $CONFIG.MaxSlots)) { throw "-Slot must be 0..$($CONFIG.MaxSlots - 1)" }
$frame = New-Object System.Collections.Generic.List[byte]
$frame.Add([byte][char]$Cmd)
switch ($Cmd) {
    "R" { $frame.AddRange([byte[]](Get-Bytes (ConvertTo-U32 $Addr))) }
    "S" { $frame.Add([byte]$Slot) }
    { $_ -in @("C", "A") } { foreach ($w in $Custom) { $frame.AddRange([byte[]](Get-Bytes (ConvertTo-U32 $w))) } }
}

if ($CONFIG.DryRun -and -not $Run) {
    Write-Output ("[dry] {0}: {1}" -f $Cmd, (($frame | ForEach-Object { "{0:X2}" -f $_ }) -join " "))
    Write-Output "add -Run -Port COMx to send (watch board current on a USB power meter; unplug if it jumps)"
    exit 0
}
if (-not $Port) { throw "-Port COMx is required with -Run (the Arty's USB serial port, see Device Manager)" }

$sp = New-Object System.IO.Ports.SerialPort $Port, $CONFIG.Baud, ([IO.Ports.Parity]::None), 8, ([IO.Ports.StopBits]::One)
$sp.ReadTimeout = $CONFIG.TimeoutMs
$sp.Open()
try {
    $sp.DiscardInBuffer()
    $sp.Write($frame.ToArray(), 0, $frame.Count)
    switch ($Cmd) {
        "J" { Write-Output ("JEDEC ID: " + (((Read-Exact $sp 3) | ForEach-Object { "{0:X2}" -f $_ }) -join " ")) }
        "R" { Write-Output ("flash[{0}] = {1:X8}" -f $Addr, (Read-Word $sp)) }
        "S" { Write-Output ("S {0}: status '{1}'" -f $Slot, [char](Read-Exact $sp 1)[0]) }
        "C" { Write-Output ("custom0({0}, {1}) = {2:X8}" -f $Custom[0], $Custom[1], (Read-Word $sp)) }
        "A" {
            $n = 0
            while ($true) {
                $s = [char](Read-Exact $sp 1)[0]
                if ($s -eq ".") { Write-Output "A: end"; break }
                if ($s -eq "K") { Write-Output ("A: slot {0} 'K', custom0 = {1:X8}" -f $n, (Read-Word $sp)) }
                else { Write-Output ("A: slot {0} '{1}'" -f $n, $s) }
                $n++
            }
        }
    }
} finally {
    $sp.Close()
}
