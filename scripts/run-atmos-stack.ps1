# Start native services (PG 18543, Storage 19000, API 18080, Next 13002) for Atmos preview
param([switch]$Wait, [switch]$Stop)
$ErrorActionPreference = 'Stop'
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$native = Join-Path $root '.runtime/native'
$python = Join-Path $root 'backend/.venv/Scripts/python.exe'
$pg = Join-Path $native 'pgsql/bin/pg_ctl.exe'
$s3 = Join-Path $native 's3/node_modules/s3rver/bin/s3rver.js'
$next = Join-Path $root 'frontend/node_modules/next/dist/bin/next'
$node = (Get-Command node.exe -ErrorAction Stop).Source

if ($Stop) {
    foreach ($port in @(13002, 18080, 19000)) {
        $conns = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
        foreach ($conn in $conns) {
            Stop-Process -Id $conn.OwningProcess -Force -ErrorAction SilentlyContinue
        }
    }
    Get-CimInstance Win32_Process -Filter "Name = 'python.exe'" -ErrorAction SilentlyContinue |
        Where-Object { $_.CommandLine -like '*app.workers.main*' } |
        ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
    if (Get-NetTCPConnection -LocalPort 18543 -State Listen -ErrorAction SilentlyContinue) {
        & $pg -D (Join-Path $native 'pgdata') -m fast stop
    }
    Write-Output "Native Atmos stack stopped."
    exit 0
}

. (Join-Path $PSScriptRoot 'use-d-drive.ps1')

# Environment
$settings = Get-Content -LiteralPath (Join-Path $native 'env.json') -Raw | ConvertFrom-Json
foreach ($entry in $settings.PSObject.Properties) {
    [Environment]::SetEnvironmentVariable($entry.Name, [string]$entry.Value, 'Process')
}
[Environment]::SetEnvironmentVariable('TURIO_UI_VERIFY', '1', 'Process')
[Environment]::SetEnvironmentVariable('INTERNAL_API_BASE_URL', 'http://127.0.0.1:18080/api/v1', 'Process')
[Environment]::SetEnvironmentVariable('NODE_ENV', 'production', 'Process')

# 1. Clean stale PID and start PostgreSQL
$pidFile = Join-Path $native 'pgdata/postmaster.pid'
if (Test-Path -LiteralPath $pidFile) {
    $stalePid = (Get-Content -LiteralPath $pidFile -TotalCount 1).Trim()
    $existing = Get-Process -Id $stalePid -ErrorAction SilentlyContinue
    if (-not $existing -or $existing.ProcessName -ne 'postgres') {
        Remove-Item -LiteralPath $pidFile -Force -ErrorAction SilentlyContinue
    }
}
if (-not (Get-NetTCPConnection -LocalPort 18543 -State Listen -ErrorAction SilentlyContinue)) {
    & $pg -D (Join-Path $native 'pgdata') -l (Join-Path $native 'postgres.log') -o '-h 127.0.0.1 -p 18543' -w start
    if ($LASTEXITCODE -ne 0) { throw 'PostgreSQL failed to start.' }
    Write-Output "PostgreSQL started on 18543"
} else {
    Write-Output "PostgreSQL already listening on 18543"
}

# 2. Start Storage (19000)
New-Item -ItemType Directory (Join-Path $native 'objects') -Force | Out-Null
$storageProc = $null
if (-not (Get-NetTCPConnection -LocalPort 19000 -State Listen -ErrorAction SilentlyContinue)) {
    $storageProc = Start-Process -FilePath $node -ArgumentList "`"$s3`" -d `"$native\objects`" -a 127.0.0.1 -p 19000 --no-vhost-buckets" -WorkingDirectory $root -WindowStyle Hidden -PassThru
    Write-Output "Storage started (PID $($storageProc.Id)) on 19000"
} else {
    Write-Output "Storage already listening on 19000"
}

# 3. Start API (18080)
$apiProc = $null
if (-not (Get-NetTCPConnection -LocalPort 18080 -State Listen -ErrorAction SilentlyContinue)) {
    $apiProc = Start-Process -FilePath $python -ArgumentList "-m uvicorn app.main:app --host 127.0.0.1 --port 18080 --loop asyncio:SelectorEventLoop" -WorkingDirectory (Join-Path $root 'backend') -WindowStyle Hidden -PassThru
    Write-Output "API started (PID $($apiProc.Id)) on 18080"
} else {
    Write-Output "API already listening on 18080"
}

# 4. Start Next.js (13002)
$frontendProc = $null
if (-not (Get-NetTCPConnection -LocalPort 13002 -State Listen -ErrorAction SilentlyContinue)) {
    $frontendProc = Start-Process -FilePath $node -ArgumentList "`"$next`" start -p 13002 -H 127.0.0.1" -WorkingDirectory (Join-Path $root 'frontend') -WindowStyle Hidden -PassThru
    Write-Output "Frontend Atmos started (PID $($frontendProc.Id)) on 13002"
} else {
    Write-Output "Frontend Atmos already listening on 13002"
}

# 5. Start Worker
$workerProc = $null
$existingWorker = Get-CimInstance Win32_Process -Filter "Name = 'python.exe'" -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -like '*app.workers.main*' } |
    Select-Object -First 1
if (-not $existingWorker) {
    $workerProc = Start-Process -FilePath $python -ArgumentList "-m app.workers.main" -WorkingDirectory (Join-Path $root 'backend') -WindowStyle Hidden -PassThru
    Write-Output "Worker started (PID $($workerProc.Id))"
} else {
    Write-Output "Worker already running (PID $($existingWorker.ProcessId))"
}

Write-Output "Stack ready. API on 18080, DB on 18543, Storage on 19000, Worker on $(if ($workerProc) { $workerProc.Id } else { $existingWorker.ProcessId }), Preview on 13002."

if ($Wait) {
    try {
        while ($true) {
            Start-Sleep -Seconds 3
        }
    } finally {
        Write-Output "Shutting down services..."
        if ($workerProc) { Stop-Process -Id $workerProc.Id -ErrorAction SilentlyContinue }
        if ($frontendProc) { Stop-Process -Id $frontendProc.Id -ErrorAction SilentlyContinue }
        if ($apiProc) { Stop-Process -Id $apiProc.Id -ErrorAction SilentlyContinue }
        if ($storageProc) { Stop-Process -Id $storageProc.Id -ErrorAction SilentlyContinue }
        & $pg -D (Join-Path $native 'pgdata') -m fast stop
    }
}

