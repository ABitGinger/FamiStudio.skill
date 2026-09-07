# render.ps1 - FamiStudio text project -> WAV with built-in verification.
# Usage (from Git Bash):
#   powershell -NoProfile -File render.ps1 -InputFile song.txt -OutputFile song.wav [-ExpectedSeconds 12.8] [-Play] [-Rate 44100] [-Loop 1]
# Exit code 0 = rendered + verified; 1 = failed (error details printed).
# Note: FamiStudio.exe is a GUI-subsystem app, so we must Start-Process -Wait
# (plain `&` returns immediately and $LASTEXITCODE stays empty).
param(
    [Parameter(Mandatory=$true)][string]$InputFile,
    [Parameter(Mandatory=$true)][string]$OutputFile,
    [string]$FamiStudio = "C:\Program Files\FamiStudio\FamiStudio.exe",
    [double]$ExpectedSeconds = 0,   # if > 0, fail when |actual-expected| > Tolerance
    [double]$Tolerance = 0.02,
    [switch]$Play,
    [int]$Rate = 0,                 # 44100/48000/... (0 = FamiStudio default 44100)
    [int]$Loop = 0,                 # >0 = play the song N times
    [string[]]$Extra = @()
)
$ErrorActionPreference = "Stop"

if (-not (Test-Path $FamiStudio)) { Write-Error "FamiStudio not found: $FamiStudio"; exit 1 }
if (-not (Test-Path $InputFile))  { Write-Error "Input not found: $InputFile"; exit 1 }

$in  = (Resolve-Path $InputFile).Path
# Resolve output to an absolute path (bare filenames resolve against CWD;
# Split-Path -Parent returns "" for them and Join-Path would throw).
$out = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($OutputFile)
if (Test-Path $out) { Remove-Item $out -Force }   # never trust a stale file

$cli = @($in, "wav-export", $out)
if ($Rate -gt 0) { $cli += "-wav-export-rate:$Rate" }
if ($Loop -gt 0) { $cli += "-wav-export-loop:$Loop" }
$cli += $Extra
# Start-Process joins ArgumentList with spaces and does not quote, so quote here.
$cliQ = ($cli | ForEach-Object { if ($_ -match ' ') { '"' + $_ + '"' } else { $_ } }) -join ' '

$tmpOut = [IO.Path]::GetTempFileName()
$tmpErr = [IO.Path]::GetTempFileName()
try {
    $p = Start-Process -FilePath $FamiStudio -ArgumentList $cliQ -NoNewWindow -Wait -PassThru `
            -RedirectStandardOutput $tmpOut -RedirectStandardError $tmpErr
    Get-Content $tmpOut | ForEach-Object { Write-Output $_ }
    if ($p.ExitCode -ne 0) {
        Get-Content $tmpErr | ForEach-Object { Write-Output $_ }
        Write-Error "FamiStudio CLI failed with exit code $($p.ExitCode) (parse error? see output above)"
        exit 1
    }
} finally {
    Remove-Item $tmpOut, $tmpErr -Force -ErrorAction SilentlyContinue
}

if (-not (Test-Path $out)) { Write-Error "CLI reported success but no WAV was created"; exit 1 }

$b = [IO.File]::ReadAllBytes($out)
$channels = [BitConverter]::ToUInt16($b, 22)
$rate     = [BitConverter]::ToUInt32($b, 24)
$bits     = [BitConverter]::ToUInt16($b, 34)
$seconds  = ($b.Length - 44) / ($rate * $channels * ($bits / 8))

$verdict = "OK: $([math]::Round($seconds,2))s, $rate Hz, $($channels)ch, $($bits)-bit, $out"
if ($ExpectedSeconds -gt 0) {
    if ([math]::Abs($seconds - $ExpectedSeconds) -gt $ExpectedSeconds * $Tolerance) {
        Write-Error ("DURATION MISMATCH: expected ~{0}s, got {1}s. Check Time/Duration units (frames) and note math." -f $ExpectedSeconds, [math]::Round($seconds,3))
        exit 1
    }
    $verdict += " (matches expected ~$([math]::Round($ExpectedSeconds,2))s)"
}
Write-Output $verdict

if ($Play) { (New-Object Media.SoundPlayer $out).PlaySync() }
exit 0
