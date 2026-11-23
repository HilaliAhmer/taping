$ErrorActionPreference = 'Stop'

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$BuildDir = Join-Path $Root 'build'
$DistDir = Join-Path $Root 'dist'
$ReleaseDir = Join-Path $Root 'release'
$PackageDir = Join-Path $ReleaseDir 'taping'
$ZipPath = Join-Path $ReleaseDir 'taping-windows-x64.zip'

foreach ($path in @($BuildDir, $DistDir, $ReleaseDir, (Join-Path $Root 'taping.spec'))) {
    Remove-Item $path -Force -Recurse -ErrorAction SilentlyContinue
}

# Install pinned dependencies in your virtual environment before starting:
#   python -m pip install -r requirements-build.txt
$PyInstallerVersion = & python -m PyInstaller --version 2>$null
if ($LASTEXITCODE -ne 0) {
    throw 'PyInstaller is missing. Run: python -m pip install -r requirements-build.txt'
}
$PinnedVersion = '6.21.0'
if (($PyInstallerVersion | Select-Object -Last 1).Trim() -ne $PinnedVersion) {
    throw "Expected PyInstaller $PinnedVersion. Install: python -m pip install -r requirements-build.txt"
}

Write-Host 'Building Windows taping.exe (onefile, no UPX)...'
& python -m PyInstaller --clean --onefile --noupx --name taping --paths $Root scripts\entrypoint.py
if ($LASTEXITCODE -ne 0) { throw 'PyInstaller build failed.' }

$ExePath = Join-Path $DistDir 'taping.exe'
if (-not (Test-Path $ExePath)) { throw 'taping.exe was not created.' }

Write-Host 'Smoke-testing the executable...'
& $ExePath about
if ($LASTEXITCODE -ne 0) { throw 'Executable smoke test failed.' }

New-Item -ItemType Directory -Path $PackageDir -Force | Out-Null
Copy-Item $ExePath (Join-Path $PackageDir 'taping.exe') -Force
foreach ($name in @('README.md', 'LICENSE', 'NOTICE')) {
    if (Test-Path $name) { Copy-Item $name $PackageDir -Force }
}

@'
TAPING Windows Standalone

1. Extract the archive into a folder.
2. Add that folder to PATH (or use the included verified install.ps1).
3. Open a new CMD or PowerShell.
4. Run: taping help

Examples:
taping 8.8.8.8
taping range 192.168.1.1-100
taping 192.168.1.1 -p 443
taping trace 8.8.8.8
taping trace 192.168.1.1 -p 443

Version: taping about
'@ | Set-Content (Join-Path $PackageDir 'README.txt') -Encoding UTF8

# Write ZIP entry names with forward slashes for cross-platform extraction.
Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem
$archive = [System.IO.Compression.ZipFile]::Open($ZipPath, [System.IO.Compression.ZipArchiveMode]::Create)
try {
    Get-ChildItem $PackageDir -File | ForEach-Object {
        $entry = 'taping/' + $_.Name
        [System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile(
            $archive, $_.FullName, $entry,
            [System.IO.Compression.CompressionLevel]::Optimal
        ) | Out-Null
    }
}
finally {
    $archive.Dispose()
}

$Hash = (Get-FileHash -Path $ZipPath -Algorithm SHA256).Hash.ToLowerInvariant()
("$Hash  taping-windows-x64.zip" + [Environment]::NewLine) |
    Set-Content -Path (Join-Path $ReleaseDir 'SHA256SUMS') -Encoding Ascii -NoNewline

Copy-Item (Join-Path $Root 'scripts\install.ps1') $ReleaseDir -Force

Write-Host 'Release files created:'
Write-Host $ZipPath
Write-Host (Join-Path $ReleaseDir 'SHA256SUMS')
Write-Host (Join-Path $ReleaseDir 'install.ps1')
