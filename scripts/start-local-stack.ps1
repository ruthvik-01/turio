# Start/reuse the provisioned native Windows development runtime. No Docker/WSL.
param([switch]$SkipBuild, [switch]$Check, [switch]$Wait)
$ErrorActionPreference = 'Stop'
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$native = Join-Path $root '.runtime/native'
$python = Join-Path $root 'backend/.venv/Scripts/python.exe'
$pg = Join-Path $native 'pgsql/bin/pg_ctl.exe'
$s3 = Join-Path $native 's3/node_modules/s3rver/bin/s3rver.js'
$next = Join-Path $root 'frontend/node_modules/next/dist/bin/next'
foreach ($path in @((Join-Path $native 'env.json'), (Join-Path $native 'pgdata/PG_VERSION'), $pg, $s3, $python, $next)) {
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        throw "Native runtime is not provisioned. Missing: $path. See docs/DEPLOYMENT.md."
    }
}
$node = (Get-Command node.exe -ErrorAction Stop).Source
$build = Join-Path $root 'frontend/.next/BUILD_ID'
if ($Check) {
    if (-not (Test-Path -LiteralPath $build -PathType Leaf)) { throw 'Build the frontend with npm run build before startup.' }
    Write-Output 'Native runtime prerequisites are present. No services started.'
    exit 0
}
Set-Location -LiteralPath $root
. (Join-Path $PSScriptRoot 'use-d-drive.ps1')
$settings = Get-Content -LiteralPath (Join-Path $native 'env.json') -Raw | ConvertFrom-Json
foreach ($entry in $settings.PSObject.Properties) { [Environment]::SetEnvironmentVariable($entry.Name, [string]$entry.Value, 'Process') }
if (-not (Test-Path -LiteralPath $build -PathType Leaf)) {
    if ($SkipBuild) { throw 'The frontend build is missing; run npm run build in frontend/.' }
    Push-Location (Join-Path $root 'frontend')
    try {
        & npm.cmd run build
        if ($LASTEXITCODE -ne 0) { throw 'Frontend build failed.' }
    } finally { Pop-Location }
}
$pidFile = Join-Path $native 'pgdata/postmaster.pid'
if (-not (Get-NetTCPConnection -LocalPort 18543 -State Listen -ErrorAction SilentlyContinue)) {
    if (Test-Path -LiteralPath $pidFile) {
        $stalePid = (Get-Content -LiteralPath $pidFile -TotalCount 1).Trim()
        if (-not (Get-Process -Id $stalePid -ErrorAction SilentlyContinue)) {
            Remove-Item -LiteralPath $pidFile -Force -ErrorAction SilentlyContinue
        }
    }
    & $pg -D (Join-Path $native 'pgdata') -l (Join-Path $native 'postgres.log') -o '-h 127.0.0.1 -p 18543' -w start
    if ($LASTEXITCODE -ne 0) { throw 'Native PostgreSQL could not start.' }
}
New-Item -ItemType Directory (Join-Path $native 'objects') -Force | Out-Null
$services = @(
    @{Name='storage'; Port=19000; File=$node; Args="`"$s3`" -d `"$native\objects`" -a 127.0.0.1 -p 19000 --no-vhost-buckets"; WorkDir=$root},
    @{Name='api'; Port=18080; File=$python; Args="-m uvicorn app.main:app --host 127.0.0.1 --port 18080 --loop asyncio:SelectorEventLoop"; WorkDir=(Join-Path $root 'backend')},
    @{Name='frontend'; Port=13000; File=$node; Args="`"$next`" start -p 13000 -H 127.0.0.1"; WorkDir=(Join-Path $root 'frontend')}
)
$manifest = Join-Path $native 'processes.json'
$started = @()
if (Test-Path -LiteralPath $manifest) {
    $previous = Get-Content -LiteralPath $manifest -Raw | ConvertFrom-Json
    foreach ($record in $previous) {
        if (Get-Process -Id $record.pid -ErrorAction SilentlyContinue) { $started += $record }
    }
}
foreach ($service in $services) {
    if (Get-NetTCPConnection -LocalPort $service.Port -State Listen -ErrorAction SilentlyContinue) { Write-Output "$($service.Name): already listening"; continue }
    $workdir = if ($service.WorkDir) { $service.WorkDir } else { $root }
    $proc = Start-Process -FilePath $service.File -ArgumentList $service.Args -WorkingDirectory $workdir -WindowStyle Hidden -RedirectStandardOutput (Join-Path $native "$($service.Name).out.log") -RedirectStandardError (Join-Path $native "$($service.Name).err.log") -PassThru
    $started += @{name=$service.Name;pid=$proc.Id}
    Write-Output "$($service.Name) PID $($proc.Id)"
}
if (-not ($started | Where-Object { $_.name -eq 'worker' })) {
    $worker = Start-Process -FilePath $python -ArgumentList "-m app.workers.main" -WorkingDirectory (Join-Path $root 'backend') -WindowStyle Hidden -RedirectStandardOutput (Join-Path $native 'worker.out.log') -RedirectStandardError (Join-Path $native 'worker.err.log') -PassThru
    $started += @{name='worker';pid=$worker.Id}
    Write-Output "worker PID $($worker.Id)"
}
ConvertTo-Json -InputObject $started -Depth 3 | Set-Content -LiteralPath $manifest

if ($Wait) {
    Write-Output "Stack running in supervisor mode. Waiting on processes..."
    $pids = @($started | ForEach-Object { $_.pid } | Where-Object { $_ -gt 0 })
    if ($pids.Count -gt 0) {
        Wait-Process -Id $pids
    }
}
