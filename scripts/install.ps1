$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host " TAPING installer started" -ForegroundColor Green
Write-Host " Please wait, installation is running..." -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

$InstallDir = "C:\taping"
$ZipUrl = "https://github.com/HilaliAhmer/taping/releases/latest/download/taping-windows-x64.zip"
$TempRoot = Join-Path $env:TEMP ("taping-install-" + [guid]::NewGuid().ToString())
$TempZip = Join-Path $TempRoot "taping-windows-x64.zip"
$TempExtract = Join-Path $TempRoot "extract"

Write-Host "Installing TAPING..." -ForegroundColor Green
Write-Host "Install directory: $InstallDir" -ForegroundColor Cyan

try {
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

    New-Item -ItemType Directory -Force $TempRoot | Out-Null
    New-Item -ItemType Directory -Force $TempExtract | Out-Null

    try {
        New-Item -ItemType Directory -Force $InstallDir | Out-Null
    }
    catch {
        Write-Host "Cannot create $InstallDir"
        Write-Host "Please run PowerShell as Administrator and try again."
        throw
    }

    Write-Host "Downloading latest TAPING release. This may take a few seconds..." -ForegroundColor Yellow
    Invoke-WebRequest -Uri $ZipUrl -OutFile $TempZip -UseBasicParsing

    Write-Host "Extracting package..." -ForegroundColor Yellow
    Expand-Archive -Path $TempZip -DestinationPath $TempExtract -Force

    $PackageDir = Join-Path $TempExtract "taping"

    if (Test-Path $PackageDir) {
        Copy-Item "$PackageDir\*" $InstallDir -Recurse -Force
    }
    else {
        Copy-Item "$TempExtract\*" $InstallDir -Recurse -Force
    }

    $ExePath = Join-Path $InstallDir "taping.exe"

    if (-not (Test-Path $ExePath)) {
        throw "taping.exe was not found after installation."
    }

    Write-Host "Adding $InstallDir to User PATH..."

    $UserPath = [Environment]::GetEnvironmentVariable("Path", "User")

    if ([string]::IsNullOrWhiteSpace($UserPath)) {
        $PathItems = @()
    }
    else {
        $PathItems = $UserPath -split ";" | Where-Object { $_ -ne "" }
    }

    if ($PathItems -notcontains $InstallDir) {
        $NewPath = (($PathItems + $InstallDir) -join ";")
        [Environment]::SetEnvironmentVariable("Path", $NewPath, "User")
    }

    if (($env:Path -split ";") -notcontains $InstallDir) {
        $env:Path += ";$InstallDir"
    }

    Write-Host ""
    Write-Host "TAPING installed successfully."
    Write-Host "Open a new CMD or PowerShell window and run: taping help"
    Write-Host ""

    & $ExePath help
}
finally {
    Remove-Item $TempRoot -Recurse -Force -ErrorAction SilentlyContinue
}
