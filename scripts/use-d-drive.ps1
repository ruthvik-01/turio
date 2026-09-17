# Dot-source before project commands: . .\scripts\use-d-drive.ps1
# Process-scoped only; does not change caches for other projects/users.
$projectRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
if ([IO.Path]::GetPathRoot($projectRoot) -ne 'D:\') {
    throw 'This project is configured to keep generated data on D:.'
}
$runtimeRoot = Join-Path $projectRoot '.runtime'
$paths = @{
    TEMP = Join-Path $runtimeRoot 'tmp'
    TMP = Join-Path $runtimeRoot 'tmp'
    PIP_CACHE_DIR = Join-Path $runtimeRoot 'pip-cache'
    npm_config_cache = Join-Path $runtimeRoot 'npm-cache'
    PLAYWRIGHT_BROWSERS_PATH = Join-Path $runtimeRoot 'playwright'
    HF_HOME = Join-Path $runtimeRoot 'huggingface'
    XDG_CACHE_HOME = Join-Path $runtimeRoot 'cache'
}
foreach ($entry in $paths.GetEnumerator()) {
    $resolved = [IO.Path]::GetFullPath($entry.Value)
    if (-not $resolved.StartsWith($runtimeRoot + '\', [StringComparison]::OrdinalIgnoreCase)) {
        throw 'Generated path escaped the project runtime directory.'
    }
    New-Item -ItemType Directory -Path $resolved -Force | Out-Null
    [Environment]::SetEnvironmentVariable($entry.Key, $resolved, 'Process')
}
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:NEXT_TELEMETRY_DISABLED = '1'
$browser = Join-Path $paths.PLAYWRIGHT_BROWSERS_PATH 'chromium-1234\chrome-win64\chrome.exe'
if (Test-Path -LiteralPath $browser -PathType Leaf) {
    $env:BROWSER_EXECUTABLE_PATH = $browser
}
