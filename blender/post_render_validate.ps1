param(
    [Parameter(Mandatory = $true)]
    [int]$RenderPid,

    [Parameter(Mandatory = $true)]
    [string]$VideoPath,

    [Parameter(Mandatory = $true)]
    [string]$ReportPath,

    [Parameter(Mandatory = $true)]
    [string]$QaDirectory
)

$ErrorActionPreference = "Stop"
$startedAt = Get-Date

try {
    Wait-Process -Id $RenderPid -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 3

    if (-not (Test-Path -LiteralPath $VideoPath)) {
        throw "Rendered video does not exist: $VideoPath"
    }

    $ffprobe = (Get-Command ffprobe -ErrorAction Stop).Source
    $ffmpeg = (Get-Command ffmpeg -ErrorAction Stop).Source
    $probeText = & $ffprobe -v error -select_streams v:0 `
        -show_entries stream=codec_name,width,height,r_frame_rate,avg_frame_rate,nb_frames,duration `
        -show_entries format=duration,size -of json $VideoPath
    if ($LASTEXITCODE -ne 0) {
        throw "ffprobe failed with exit code $LASTEXITCODE"
    }

    $probe = $probeText | ConvertFrom-Json
    $stream = $probe.streams[0]
    $format = $probe.format

    & $ffmpeg -v error -i $VideoPath -map 0:v:0 -f null -
    $decodeExitCode = $LASTEXITCODE
    if ($decodeExitCode -ne 0) {
        throw "Full decode failed with exit code $decodeExitCode"
    }

    New-Item -ItemType Directory -Force -Path $QaDirectory | Out-Null
    $timestamps = @(4, 6, 10, 28, 32, 35, 97, 103, 115)
    foreach ($timestamp in $timestamps) {
        $output = Join-Path $QaDirectory ("final_{0:D3}s.png" -f $timestamp)
        & $ffmpeg -y -v error -ss $timestamp -i $VideoPath -frames:v 1 $output
        if ($LASTEXITCODE -ne 0) {
            throw "Frame extraction failed at ${timestamp}s"
        }
    }

    $result = [ordered]@{
        status = "passed"
        validation_started_at = $startedAt.ToString("o")
        validation_finished_at = (Get-Date).ToString("o")
        video_path = $VideoPath
        codec = $stream.codec_name
        width = [int]$stream.width
        height = [int]$stream.height
        frame_rate = $stream.avg_frame_rate
        duration_seconds = [double]$format.duration
        frame_count = [int]$stream.nb_frames
        size_bytes = [long]$format.size
        decode_exit_code = $decodeExitCode
        qa_directory = $QaDirectory
        extracted_timestamps_seconds = $timestamps
    }
}
catch {
    $result = [ordered]@{
        status = "failed"
        validation_started_at = $startedAt.ToString("o")
        validation_finished_at = (Get-Date).ToString("o")
        video_path = $VideoPath
        error = $_.Exception.Message
    }
}

$reportDirectory = Split-Path -Parent $ReportPath
New-Item -ItemType Directory -Force -Path $reportDirectory | Out-Null
$result | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $ReportPath -Encoding UTF8

if ($result.status -ne "passed") {
    exit 1
}
