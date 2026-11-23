$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'

$InstallDir = Join-Path $env:LOCALAPPDATA 'Programs\taping'
$ReleaseUrl = 'https://github.com/HilaliAhmer/taping/releases/latest/download/'
$ZipUrl = $ReleaseUrl + 'taping-windows-x64.zip'
$HashUrl = $ReleaseUrl + 'SHA256SUMS'
$TempDir = Join-Path $env:TEMP ('taping-install-' + [guid]::NewGuid().ToString('N'))
$TempZip = Join-Path $TempDir 'taping-windows-x64.zip'
$TempHashes = Join-Path $TempDir 'SHA256SUMS'
$ExtractDir = Join-Path $TempDir 'extract'

Write-Host 'TAPING installer - verifying release files before installation...'

try {
    # Keep other already enabled security protocols; add TLS 1.2.
    [Net.ServicePointManager]::SecurityProtocol = (
        [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12
    )
    New-Item -ItemType Directory $TempDir -Force | Out-Null
    New-Item -ItemType Directory $ExtractDir -Force | Out-Null

    Invoke-WebRequest -Uri $ZipUrl -OutFile $TempZip -UseBasicParsing
    Invoke-WebRequest -Uri $HashUrl -OutFile $TempHashes -UseBasicParsing

    $Expected = $null
    foreach ($line in (Get-Content $TempHashes)) {
        if ($line -match '^([A-Fa-f0-9]{64})\s+\*?taping-windows-x64\.zip\s*$') {
            $Expected = $Matches[1].ToLowerInvariant()
            break
        }
    }
    if (-not $Expected) { throw 'SHA256SUMS is missing the expected ZIP checksum.' }

    $Actual = (Get-FileHash -Path $TempZip -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($Actual -ne $Expected) { throw 'SHA-256 checksum mismatch. Installation cancelled.' }
    Write-Host 'Archive SHA-256 verified.' -ForegroundColor Green

    Expand-Archive -Path $TempZip -DestinationPath $ExtractDir -Force
    $SourceDir = Join-Path $ExtractDir 'taping'
    if (-not (Test-Path $SourceDir)) { throw 'Invalid ZIP: taping folder missing.' }
    if (-not (Test-Path (Join-Path $SourceDir 'taping.exe'))) {
        throw 'Invalid ZIP: taping.exe missing.'
    }

    New-Item -ItemType Directory $InstallDir -Force | Out-Null
    Copy-Item (Join-Path $SourceDir '*') $InstallDir -Recurse -Force

    $AppPath = (Resolve-Path $InstallDir).Path.TrimEnd('\')
    $LegacyPath = 'C:\taping'
    $UserPath = [Environment]::GetEnvironmentVariable('Path', 'User')
    $Existing = @($UserPath -split ';' | Where-Object {
        $_ -and $_.Trim().TrimEnd('\') -ne $AppPath -and
        $_.Trim().TrimEnd('\') -ne $LegacyPath
    })
    [Environment]::SetEnvironmentVariable('Path', ((@($AppPath) + $Existing) -join ';'), 'User')

    Write-Host "Installed to $AppPath" -ForegroundColor Green
    Write-Host 'Open a new CMD/PowerShell and run: taping about'
    Write-Host 'If an old install exists, use: where.exe taping'
    & (Join-Path $InstallDir 'taping.exe') about
    if ($LASTEXITCODE -ne 0) { throw 'Installed executable failed smoke test.' }
}
finally {
    Remove-Item $TempDir -Recurse -Force -ErrorAction SilentlyContinue
}
