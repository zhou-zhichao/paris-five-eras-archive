param(
    [string]$ProjectRoot = (Split-Path -Parent $PSScriptRoot),
    [string]$ManifestPath = (Join-Path (Split-Path -Parent $PSScriptRoot) "github-archive/manifest.json"),
    [string]$Repository = "zhou-zhichao/paris-five-eras-archive",
    [string]$ReleaseTag = "archive-2026-08-08",
    [int]$ThrottleLimit = 4
)

$ErrorActionPreference = "Stop"
$resolvedRoot = (Resolve-Path -LiteralPath $ProjectRoot).Path.TrimEnd("\")
$items = Get-Content -LiteralPath $ManifestPath -Raw | ConvertFrom-Json

foreach ($item in $items) {
    $source = (Resolve-Path -LiteralPath (Join-Path $resolvedRoot $item.source_relative_path)).Path
    if (-not $source.StartsWith("$resolvedRoot\", [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Asset escaped project root: $source"
    }
    if ((Get-Item -LiteralPath $source).Length -ne [long]$item.size_bytes) {
        throw "Asset size changed after manifest generation: $($item.name)"
    }
}

$results = $items | ForEach-Object -Parallel {
    $item = $_
    $source = Join-Path $using:resolvedRoot $item.source_relative_path
    $success = $false
    $lastOutput = ""

    for ($attempt = 1; $attempt -le 3; $attempt++) {
        $output = & gh release upload $using:ReleaseTag $source --repo $using:Repository --clobber 2>&1
        $exitCode = $LASTEXITCODE
        $lastOutput = $output -join "`n"
        if ($exitCode -eq 0) {
            $success = $true
            break
        }
        if ($attempt -lt 3) { Start-Sleep -Seconds (5 * $attempt) }
    }

    [pscustomobject]@{
        name = $item.name
        success = $success
        message = $lastOutput
    }
} -ThrottleLimit $ThrottleLimit

$results | Sort-Object name | ForEach-Object {
    if ($_.success) {
        Write-Output "UPLOADED $($_.name)"
    } else {
        Write-Output "FAILED $($_.name): $($_.message)"
    }
}

$failed = $results | Where-Object { -not $_.success }
if ($failed) {
    throw "$($failed.Count) release assets failed to upload. Re-run the script to retry with --clobber."
}

Write-Output "COMPLETE $($results.Count) assets uploaded."
