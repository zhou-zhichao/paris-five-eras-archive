param(
    [string]$ProjectRoot = (Split-Path -Parent $PSScriptRoot),
    [string]$OutputRoot = (Join-Path (Split-Path -Parent $PSScriptRoot) "github-archive"),
    [string]$Repository = "zhou-zhichao/paris-five-eras-archive",
    [string]$ReleaseTag = "archive-2026-08-08",
    [switch]$ReuseManifest
)

$ErrorActionPreference = "Stop"

$youtubeFinal = "https://youtu.be/6st9cc6HeCs"
$youtubeBase = "https://youtu.be/yC6kgCsfEdE"
$releaseBase = "https://github.com/$Repository/releases/download/$ReleaseTag"

New-Item -ItemType Directory -Force -Path $OutputRoot | Out-Null
$thumbnailRoot = Join-Path $OutputRoot "thumbnails"
New-Item -ItemType Directory -Force -Path $thumbnailRoot | Out-Null

$files = Get-ChildItem -LiteralPath $ProjectRoot -Recurse -File |
    Where-Object { $_.Extension.ToLowerInvariant() -in @(".blend", ".blend1", ".mp4") } |
    Sort-Object Name

$duplicateNames = $files | Group-Object Name | Where-Object Count -gt 1
if ($duplicateNames) {
    throw "Release asset basenames must be unique: $($duplicateNames.Name -join ', ')"
}

function Get-VersionLabel {
    param([string]$Name)
    $match = [regex]::Match($Name, "(?:^|[_-])v(?<number>\d+)(?<suffix>[a-z])?(?:[_\.-]|$)", "IgnoreCase")
    if (-not $match.Success) { return "Unversioned" }
    return "v$($match.Groups['number'].Value)$($match.Groups['suffix'].Value.ToLowerInvariant())"
}

function Format-Size {
    param([long]$Bytes)
    if ($Bytes -ge 1GB) { return "{0:N2} GiB" -f ($Bytes / 1GB) }
    if ($Bytes -ge 1MB) { return "{0:N1} MiB" -f ($Bytes / 1MB) }
    return "{0:N1} KiB" -f ($Bytes / 1KB)
}

$manifestPath = Join-Path $OutputRoot "manifest.json"
if ($ReuseManifest -and (Test-Path -LiteralPath $manifestPath)) {
    $manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
} else {
    $manifest = foreach ($file in $files) {
        $relativePath = [System.IO.Path]::GetRelativePath($ProjectRoot, $file.FullName).Replace("\", "/")
        $hash = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
        [pscustomobject]@{
            name = $file.Name
            kind = $file.Extension.TrimStart(".").ToLowerInvariant()
            version = Get-VersionLabel $file.Name
            source_relative_path = $relativePath
            size_bytes = $file.Length
            sha256 = $hash
            release_url = "$releaseBase/$([uri]::EscapeDataString($file.Name))"
        }
    }
}

$manifest | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $manifestPath -Encoding utf8
$manifest | ForEach-Object { "$($_.sha256)  $($_.name)" } |
    Set-Content -LiteralPath (Join-Path $OutputRoot "SHA256SUMS.txt") -Encoding ascii

$mp4Files = $files | Where-Object Extension -eq ".mp4"
foreach ($file in $mp4Files) {
    $thumbnailName = "$([System.IO.Path]::GetFileNameWithoutExtension($file.Name)).png"
    $thumbnailPath = Join-Path $thumbnailRoot $thumbnailName
    & ffmpeg -hide_banner -loglevel error -y -ss 00:00:02 -i $file.FullName -frames:v 1 -vf "scale=480:-2" $thumbnailPath
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $thumbnailPath) -or (Get-Item -LiteralPath $thumbnailPath).Length -eq 0) {
        Write-Warning "Using a placeholder for unreadable video: $($file.Name)"
        & ffmpeg -hide_banner -loglevel error -y -f lavfi -i "color=c=404040:s=480x270" -frames:v 1 $thumbnailPath
        if ($LASTEXITCODE -ne 0) { throw "Placeholder generation failed: $($file.Name)" }
    }
}

$coverRoot = Join-Path $ProjectRoot "qa/youtube_covers"
Copy-Item -LiteralPath (Join-Path $coverRoot "paris_five_eras_v44_cover.jpg") -Destination (Join-Path $thumbnailRoot "youtube-final.jpg") -Force
Copy-Item -LiteralPath (Join-Path $coverRoot "paris_base_cover.jpg") -Destination (Join-Path $thumbnailRoot "youtube-base.jpg") -Force

$totalBytes = ($manifest | Measure-Object size_bytes -Sum).Sum
$blendCount = ($manifest | Where-Object kind -eq "blend").Count
$blendBackupCount = ($manifest | Where-Object kind -eq "blend1").Count
$mp4Count = ($manifest | Where-Object kind -eq "mp4").Count

$readme = [System.Collections.Generic.List[string]]::new()
$readme.Add("# Paris Through Five Eras — Project Archive")
$readme.Add("")
$readme.Add("Public archive of the Blender scene history and rendered previews for a stylized animation of Paris across the Roman, medieval, 1700, 1850 and modern eras.")
$readme.Add("")
$readme.Add("> This repository stores the catalog and preview thumbnails. The large Blender and MP4 files are attached to the [$ReleaseTag release](https://github.com/$Repository/releases/tag/$ReleaseTag).")
$readme.Add("")
$readme.Add("## Featured videos")
$readme.Add("")
$readme.Add("| Final 2-minute animation | Early base version |")
$readme.Add("| --- | --- |")
$readme.Add("| [![Final animation](thumbnails/youtube-final.jpg)]($youtubeFinal) | [![Early base](thumbnails/youtube-base.jpg)]($youtubeBase) |")
$readme.Add("| [Watch on YouTube]($youtubeFinal) | [Watch on YouTube]($youtubeBase) |")
$readme.Add("")
$readme.Add("## Archive summary")
$readme.Add("")
$readme.Add("- $blendCount Blender scenes (`.blend`)")
$readme.Add("- $blendBackupCount Blender backups (`.blend1`)")
$readme.Add("- $mp4Count rendered or QA videos (`.mp4`)")
$readme.Add("- $(Format-Size $totalBytes) total release payload")
$readme.Add("- SHA-256 checksums in [`SHA256SUMS.txt`](SHA256SUMS.txt)")
$readme.Add("- Machine-readable metadata in [`manifest.json`](manifest.json)")
$readme.Add("")
$readme.Add("## Rendered videos")
$readme.Add("")
$readme.Add("Each thumbnail opens the downloadable MP4 attached to the release.")
$readme.Add("")
$readme.Add("| Version | Preview | File | Size |")
$readme.Add("| --- | --- | --- | ---: |")
foreach ($item in ($manifest | Where-Object kind -eq "mp4" | Sort-Object @{ Expression = { if ($_.version -eq "Unversioned") { -1 } else { [int]([regex]::Match($_.version, "\d+").Value) } } }, version, name)) {
    $thumb = "thumbnails/$([System.IO.Path]::GetFileNameWithoutExtension($item.name)).png"
    $youtube = if ($item.name -eq "paris_five_eras_v44_temple_enclosure_720p.mp4") { " · [YouTube]($youtubeFinal)" } elseif ($item.name -eq "paris_base.mp4") { " · [YouTube]($youtubeBase)" } else { "" }
    $readme.Add("| $($item.version) | [![$($item.name)]($thumb)]($($item.release_url)) | [$($item.name)]($($item.release_url))$youtube | $(Format-Size $item.size_bytes) |")
}

$readme.Add("")
$readme.Add("## Blender scenes")
$readme.Add("")
$readme.Add("| Version | File | Type | Size | SHA-256 prefix |")
$readme.Add("| --- | --- | --- | ---: | --- |")
foreach ($item in ($manifest | Where-Object kind -in @("blend", "blend1") | Sort-Object @{ Expression = { if ($_.version -eq "Unversioned") { -1 } else { [int]([regex]::Match($_.version, "\d+").Value) } } }, version, name)) {
    $readme.Add("| $($item.version) | [$($item.name)]($($item.release_url)) | `.$($item.kind)` | $(Format-Size $item.size_bytes) | $($item.sha256.Substring(0, 12)) |")
}

$readme.Add("")
$readme.Add("## Notes")
$readme.Add("")
$readme.Add("- Filenames are preserved exactly so earlier references remain traceable.")
$readme.Add("- `.blend1` files are Blender automatic backups, not separate authored branches.")
$readme.Add("- Some MP4 files are short timing, water, encoding or transition tests rather than complete renders.")
$readme.Add("- No third-party license is granted by this archive. Reuse of external models or textures must follow their original license terms.")

$readme | Set-Content -LiteralPath (Join-Path $OutputRoot "README.md") -Encoding utf8

@"
# Release Asset Notice

This public repository is an archival index. Large project files are distributed through GitHub Releases.

Third-party models, textures, geographic data, fonts, and other incorporated assets may remain subject to their original licenses. Their inclusion in an archived Blender scene does not relicense them.
"@ | Set-Content -LiteralPath (Join-Path $OutputRoot "NOTICE.md") -Encoding utf8

@"
# Repository metadata and preview images only
*.blend
*.blend1
*.mp4
"@ | Set-Content -LiteralPath (Join-Path $OutputRoot ".gitignore") -Encoding ascii

[pscustomobject]@{
    output = $OutputRoot
    assets = $manifest.Count
    total_bytes = $totalBytes
    blends = $blendCount
    blend_backups = $blendBackupCount
    videos = $mp4Count
} | ConvertTo-Json
