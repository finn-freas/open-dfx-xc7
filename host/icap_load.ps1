param(
    [string]$Port = "",
    [string]$Partial = "",
    [switch]$ReadIdcode,
    [ValidateSet("bridge", "rvsoc")][string]$Target = "bridge",
    [string[]]$Custom = @(),
    [switch]$Run
)

$CONFIG = @{
    Baud        = 1000000
    DryRun      = $true
    ReadWords   = 16
    TimeoutMs   = 3000
    IdcodeWrite = @("FFFFFFFF", "AA995566", "20000000", "28018001", "20000000", "20000000")
    DesyncWrite = @("30008001", "0000000D", "20000000", "20000000")
    Idcode      = "0362D093"
}

function ConvertTo-U32([string[]]$hex) {
    [uint32[]]($hex | ForEach-Object { [Convert]::ToUInt32($_, 16) })
}

function Get-Words([byte[]]$b) {
    if ($b.Length % 4) { throw "length $($b.Length) is not a multiple of 4" }
    $w = New-Object 'uint32[]' ($b.Length / 4)
    for ($i = 0; $i -lt $w.Length; $i++) {
        $w[$i] = [uint32]([uint64]$b[4*$i] * 16777216 + [uint64]$b[4*$i+1] * 65536 + [uint64]$b[4*$i+2] * 256 + [uint64]$b[4*$i+3])
    }
    ,$w
}

function Get-Bytes([uint32]$w) {
    $b = [BitConverter]::GetBytes($w)
    [Array]::Reverse($b)
    $b
}

function Get-Frame([string]$cmd, [uint32[]]$words, [uint32]$count) {
    $out = New-Object System.Collections.Generic.List[byte]
    $out.Add([byte][char]$cmd)
    $out.AddRange([byte[]](Get-Bytes $count))
    foreach ($w in $words) { $out.AddRange([byte[]](Get-Bytes $w)) }
    $out.ToArray()
}

function Assert-Checked([string]$bin) {
    $rec = [IO.Path]::ChangeExtension($bin, ".check.json")
    if (-not (Test-Path $rec)) { throw "REFUSED: no safety record $rec (write partials with flow/partial.py)" }
    $r = Get-Content $rec -Raw | ConvertFrom-Json
    $sha = (Get-FileHash -Algorithm SHA256 $bin).Hash.ToLower()
    if ($sha -ne $r.sha256) { throw "REFUSED: $bin sha256 $sha does not match its safety record" }
    if (-not $r.outside_are_static_pads) { throw "REFUSED: safety record says frames outside the region" }
    if ($null -eq $r.simulated -or $r.simulated.frames_differ -ne 0 -or -not $r.simulated.crc_ok) { throw "REFUSED: partial was not simulated clean" }
    Write-Output "safety record OK: region $($r.region), $($r.region_frames) frames, outside only static pads $($r.outside_frames -join ', ')"
}

function Read-Exact($sp, [int]$n) {
    $buf = New-Object byte[] $n
    $got = 0
    while ($got -lt $n) { $got += $sp.Read($buf, $got, $n - $got) }
    $buf
}

$jobs = @()
if ($Partial) {
    Assert-Checked $Partial
    $words = Get-Words ([IO.File]::ReadAllBytes($Partial))
    $jobs += ,@("W", $words, "partial $Partial ($($words.Length) words)")
}
if ($ReadIdcode -and $Target -eq "rvsoc") { throw "-ReadIdcode needs the bridge design (designs/pr_uart); the rvsoc firmware has no read command" }
$Custom = @($Custom | ForEach-Object { $_ -split "," } | Where-Object { $_ })
if ($Custom.Count) {
    if ($Target -ne "rvsoc") { throw "-Custom needs -Target rvsoc" }
    if ($Custom.Count -ne 2) { throw "-Custom takes two hex words, e.g. -Custom 12345678,0F0F0F0F" }
    $jobs += ,@("C", (ConvertTo-U32 $Custom), "custom0($($Custom[0]), $($Custom[1]))")
}
if ($ReadIdcode) {
    $jobs += ,@("W", (ConvertTo-U32 $CONFIG.IdcodeWrite), "IDCODE read packet")
    $jobs += ,@("R", [uint32[]]@(), "read $($CONFIG.ReadWords) words")
    $jobs += ,@("W", (ConvertTo-U32 $CONFIG.DesyncWrite), "DESYNC")
}
if (-not $jobs) { throw "nothing to do: give -Partial <file.bin> and/or -ReadIdcode" }

if ($CONFIG.DryRun -and -not $Run) {
    foreach ($j in $jobs) {
        if ($j[0] -eq "C") { Write-Output "[dry] C $($j[2])"; continue }
        $f = Get-Frame $j[0] $j[1] ([uint32]$(if ($j[0] -eq "W") { $j[1].Length } else { $CONFIG.ReadWords }))
        $head = ($f[0..([Math]::Min(12, $f.Length - 1))] | ForEach-Object { "{0:X2}" -f $_ }) -join " "
        Write-Output "[dry] $($j[0]) $($j[2]): $($f.Length) bytes, starts $head"
    }
    Write-Output "add -Run -Port COMx to send (watch board current on a USB power meter; unplug if it jumps)"
    exit 0
}
if (-not $Port) { throw "-Port COMx is required with -Run (the Arty's USB serial port, see Device Manager)" }

$sp = New-Object System.IO.Ports.SerialPort $Port, $CONFIG.Baud, ([IO.Ports.Parity]::None), 8, ([IO.Ports.StopBits]::One)
$sp.ReadTimeout = $CONFIG.TimeoutMs
$sp.Open()
try {
    $sp.DiscardInBuffer()
    foreach ($j in $jobs) {
        if ($j[0] -eq "W") {
            $f = Get-Frame "W" $j[1] ([uint32]$j[1].Length)
            $sp.Write($f, 0, $f.Length)
            if ($Target -eq "rvsoc") {
                $ack = Read-Exact $sp 1
                if ($ack[0] -ne [byte][char]"K") { throw "bad ack for $($j[2]): $([BitConverter]::ToString($ack))" }
                Write-Output "sent $($j[2]), acked by the CPU"
                continue
            }
            $ack = Read-Exact $sp 5
            $n = (Get-Words $ack[1..4])[0]
            if ($ack[0] -ne [byte][char]"K" -or $n -ne $j[1].Length) { throw "bad ack for $($j[2]): $([BitConverter]::ToString($ack))" }
            Write-Output "sent $($j[2]), acked $n words"
        } elseif ($j[0] -eq "C") {
            $f = New-Object System.Collections.Generic.List[byte]
            $f.Add([byte][char]"C")
            foreach ($w in $j[1]) { $f.AddRange([byte[]](Get-Bytes $w)) }
            $sp.Write($f.ToArray(), 0, $f.Count)
            $r = (Get-Words (Read-Exact $sp 4))[0]
            Write-Output ("{0} = {1:X8} (LEDs show the low 4 bits)" -f $j[2], $r)
        } else {
            $f = Get-Frame "R" @() ([uint32]$CONFIG.ReadWords)
            $sp.Write($f, 0, $f.Length)
            $words = Get-Words (Read-Exact $sp (4 * $CONFIG.ReadWords))
            Write-Output ("read: " + (($words | ForEach-Object { "{0:X8}" -f $_ }) -join " "))
            if ($words -contains (ConvertTo-U32 $CONFIG.Idcode)[0]) { Write-Output "IDCODE 0x0362D093 seen: ICAP read path works" }
            else { Write-Output "IDCODE not seen" }
        }
    }
} finally {
    $sp.Close()
}
