param(
    [string]$ProjectRoot = (Split-Path -Parent $PSScriptRoot),
    [string]$BuildRoot = (Join-Path (Split-Path -Parent $PSScriptRoot) "source-assets-package")
)

$ErrorActionPreference = "Stop"
$projectPath = (Resolve-Path -LiteralPath $ProjectRoot).Path.TrimEnd("\")
$buildPath = [IO.Path]::GetFullPath($BuildRoot).TrimEnd("\")

if ([IO.Path]::GetFileName($buildPath) -ne "source-assets-package") {
    throw "Unexpected build directory: $buildPath"
}
if (-not $buildPath.StartsWith("$projectPath\", [StringComparison]::OrdinalIgnoreCase)) {
    throw "Build directory must stay inside the project root."
}

if (Test-Path -LiteralPath $buildPath) {
    Remove-Item -LiteralPath $buildPath -Recurse -Force
}

$payloadRoot = Join-Path $buildPath "payload"
New-Item -ItemType Directory -Force -Path $payloadRoot | Out-Null

$sourceExtensions = @(
    ".py", ".ps1", ".sbatch", ".md", ".html", ".json", ".js", ".mjs",
    ".ts", ".css", ".csv", ".npz", ".npy", ".pkl", ".ass", ".txt",
    ".toml", ".yaml", ".yml", ".ini", ".cfg"
)
$assetExtensions = @(".glb", ".png", ".jpg", ".jpeg", ".webp")
$assetRoots = @("assets\", "outputs\", "threejs_house_kit\", "threejs_vicvs_kit\")
$excludedRoots = @(
    ".git\", "github-archive\", "node_modules\", "previews\", "stills\",
    "snapshots\", "reports\", "qa\", "renders\", ".thumbnails\",
    "source-assets-package\"
)

$selected = [System.Collections.Generic.List[object]]::new()
foreach ($file in (Get-ChildItem -LiteralPath $projectPath -Recurse -File)) {
    $relative = [IO.Path]::GetRelativePath($projectPath, $file.FullName)
    $lower = $relative.ToLowerInvariant()
    $extension = $file.Extension.ToLowerInvariant()

    if ($excludedRoots | Where-Object { $lower.StartsWith($_) }) { continue }
    if ($lower.Contains("\tools\python_vendor\") -or $lower.StartsWith("tools\python_vendor\")) { continue }
    if ($lower.Contains("\logs\") -or $lower.EndsWith(".log")) { continue }

    $isAsset = $assetExtensions -contains $extension -and ($assetRoots | Where-Object { $lower.StartsWith($_) })
    $isSource = $sourceExtensions -contains $extension
    if (-not $isAsset -and -not $isSource) { continue }

    $destination = Join-Path $payloadRoot $relative
    $destinationDirectory = Split-Path -Parent $destination
    New-Item -ItemType Directory -Force -Path $destinationDirectory | Out-Null
    Copy-Item -LiteralPath $file.FullName -Destination $destination -Force
    $selected.Add([pscustomobject]@{
        relative_path = $relative.Replace("\", "/")
        size_bytes = $file.Length
        sha256 = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
    })
}

$manifestPath = Join-Path $buildPath "source-manifest.json"
$checksumPath = Join-Path $buildPath "SOURCE_SHA256SUMS.txt"
$readmePath = Join-Path $buildPath "SOURCE_ASSETS_README.txt"
$selected | Sort-Object relative_path | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $manifestPath -Encoding utf8
$selected | Sort-Object relative_path | ForEach-Object { "$($_.sha256)  $($_.relative_path)" } |
    Set-Content -LiteralPath $checksumPath -Encoding utf8

@"
Paris Through Five Eras — Source Assets Archive

Contents:
- Landmark and house-kit GLB models
- Reference images used for 3D generation and placement
- Blender scene-building, audit, QA and rendering scripts
- Minerva Slurm rendering and encoding scripts
- Paris geographic and medieval block data
- Project configuration and documentation

Excluded:
- node_modules and vendored Python packages
- Render frames, stills, snapshots, QA images and reports
- Logs and temporary output
- Blender scenes and MP4 files already stored in the complete project archive release

Third-party assets remain subject to their original licenses. Inclusion in this archive does not relicense them.
"@ | Set-Content -LiteralPath $readmePath -Encoding utf8

Copy-Item -LiteralPath $manifestPath -Destination (Join-Path $payloadRoot "source-manifest.json") -Force
Copy-Item -LiteralPath $checksumPath -Destination (Join-Path $payloadRoot "SOURCE_SHA256SUMS.txt") -Force
Copy-Item -LiteralPath $readmePath -Destination (Join-Path $payloadRoot "SOURCE_ASSETS_README.txt") -Force

$zipPath = Join-Path $buildPath "paris-source-assets-2026-08-08.zip"
Compress-Archive -Path (Join-Path $payloadRoot "*") -DestinationPath $zipPath -CompressionLevel Optimal -Force
$zipHash = (Get-FileHash -LiteralPath $zipPath -Algorithm SHA256).Hash.ToLowerInvariant()
"$zipHash  $([IO.Path]::GetFileName($zipPath))" | Set-Content -LiteralPath (Join-Path $buildPath "ARCHIVE_SHA256.txt") -Encoding ascii

[pscustomobject]@{
    files = $selected.Count
    source_bytes = ($selected | Measure-Object size_bytes -Sum).Sum
    zip_path = $zipPath
    zip_bytes = (Get-Item -LiteralPath $zipPath).Length
    zip_sha256 = $zipHash
} | ConvertTo-Json
