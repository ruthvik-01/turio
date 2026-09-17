# Start the isolated local stack in the foreground so Ubuntu WSL stays alive.
# Data/volumes are retained when Compose is stopped. No distribution is deleted.
param([switch]$SkipBuild)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'use-d-drive.ps1')
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$ubuntu = @(Get-ChildItem 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Lxss' |
    ForEach-Object { Get-ItemProperty $_.PSPath } |
    Where-Object { $_.DistributionName -eq 'Ubuntu' })
if ($ubuntu.Count -ne 1 -or -not $ubuntu[0].BasePath.StartsWith('D:\', [StringComparison]::OrdinalIgnoreCase)) {
    throw 'Ubuntu must be installed on D: before this project stack is started.'
}
$state = Get-Content -LiteralPath (Join-Path $root 'data\stack-verification.json') -Raw | ConvertFrom-Json
if ($state.project -notmatch '^turio-verify-\d{8}-[0-9a-f]{6}$') {
    throw 'Unexpected local stack project name.'
}
$linuxRoot = (wsl -d Ubuntu -u root -- wslpath -u $root).Trim()
$linuxEnv = (wsl -d Ubuntu -u root -- wslpath -u $state.env_file).Trim()
wsl -d Ubuntu -u root -- systemctl start docker
if ($LASTEXITCODE -ne 0) { throw 'Docker could not start.' }
$buildOption = if ($SkipBuild) { '--no-build' } else { '--build' }
wsl -d Ubuntu -u root --cd $linuxRoot -- docker compose --env-file $linuxEnv -p $state.project -f docker-compose.yml -f docker/compose.verify.yml up $buildOption
exit $LASTEXITCODE
