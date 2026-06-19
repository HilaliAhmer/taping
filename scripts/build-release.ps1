$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$BuildDir = Join-Path $Root "build"
$DistDir = Join-Path $Root "dist"
$ReleaseDir = Join-Path $Root "release"
$PackageRoot = Join-Path $ReleaseDir "taping"
$ZipPath = Join-Path $ReleaseDir "taping-windows-x64.zip"
$SpecPath = Join-Path $Root "taping.spec"

Write-Host "Cleaning old build files..."
Remove-Item $BuildDir -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item $DistDir -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item $ReleaseDir -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item $SpecPath -Force -ErrorAction SilentlyContinue

New-Item -ItemType Directory -Force $PackageRoot | Out-Null

Write-Host "Checking PyInstaller..."
python -m PyInstaller --version *> $null

if ($LASTEXITCODE -ne 0) {
    Write-Host "Installing PyInstaller..."
    python -m pip install --upgrade pyinstaller
}

Write-Host "Building taping.exe..."
python -m PyInstaller --clean --onefile --name taping taping\cli.py

$ExePath = Join-Path $DistDir "taping.exe"

if (-not (Test-Path $ExePath)) {
    throw "Build failed. taping.exe was not created."
}

Write-Host "Preparing release package..."
Copy-Item $ExePath (Join-Path $PackageRoot "taping.exe") -Force

foreach ($file in @("README.md", "LICENSE", "NOTICE")) {
    if (Test-Path $file) {
        Copy-Item $file $PackageRoot -Force
    }
}

@"
TAPING Windows Standalone

Install manually:
1. Extract this ZIP file.
2. Copy the taping folder to C:\taping.
3. Add C:\taping to PATH.
4. Open CMD or PowerShell.
5. Run: taping help

Examples:
taping 8.8.8.8
taping range 192.168.1.1-100
taping 192.168.1.1 -p 443
taping range 192.168.1.1-100 --rdp
"@ | Set-Content (Join-Path $PackageRoot "README.txt") -Encoding UTF8

Write-Host "Creating ZIP..."
Compress-Archive -Path $PackageRoot -DestinationPath $ZipPath -Force

Copy-Item (Join-Path $Root "scripts\install.ps1") (Join-Path $ReleaseDir "install.ps1") -Force

Write-Host ""
Write-Host "Release files created:"
Write-Host $ZipPath
Write-Host (Join-Path $ReleaseDir "install.ps1")
