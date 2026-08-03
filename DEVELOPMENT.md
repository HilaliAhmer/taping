# TAPING Development Guide

This document explains how to set up the TAPING development environment, test changes, build the Windows executable, and publish a release.

## Requirements

* Windows 10 or Windows 11
* Python 3.9 or newer
* pip
* Git
* PowerShell

Check the installed versions:

```powershell
python --version
python -m pip --version
git --version
```

## Clone the Repository

```powershell
git clone https://github.com/HilaliAhmer/taping.git
cd taping
```

## Create a Virtual Environment

```powershell
py -m venv .venv
```

Activate the environment:

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, run the following command for the current PowerShell session:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Then activate the environment again:

```powershell
.\.venv\Scripts\Activate.ps1
```

## Install TAPING in Editable Mode

```powershell
python -m pip install --upgrade pip
python -m pip install -e .
```

Editable mode allows changes in the local source code to be used immediately without reinstalling TAPING after each edit.

Confirm the development installation:

```powershell
python -m taping.cli --version
python -m taping.cli help
```

## Project Structure

```text
taping/
├── taping/
│   ├── __init__.py
│   └── cli.py
├── scripts/
│   ├── build-release.ps1
│   └── install.ps1
├── README.md
├── DEVELOPMENT.md
├── CONTRIBUTING.md
├── CHANGELOG.md
├── LICENSE
├── NOTICE
└── pyproject.toml
```

The main application code is located in:

```text
taping/cli.py
```

The package version is stored in:

```text
pyproject.toml
taping/__init__.py
```

`cli.py` also contains a fallback version for direct execution. All version values must match before publishing a release.

## Basic Validation

Check the Python syntax:

```powershell
python -m py_compile .\taping\cli.py
```

Test the version and help commands:

```powershell
python -m taping.cli --version
python -m taping.cli help
python -m taping.cli about
```

## Functional Tests

### ICMP Tests

```powershell
python -m taping.cli 8.8.8.8
python -m taping.cli 8.8.8.8 -c 5
python -m taping.cli google.com -c 3
python -m taping.cli google.com -w 2000
```

### Continuous Mode

```powershell
python -m taping.cli google.com -t
```

Stop continuous mode with `CTRL+C`.

### TCP Tests

```powershell
python -m taping.cli google.com -p 443
python -m taping.cli google.com --https
python -m taping.cli 192.168.1.10 --rdp
```

### Range Tests

```powershell
python -m taping.cli range 192.168.1.1-10
python -m taping.cli range 192.168.1.1-10 --up
python -m taping.cli range 192.168.1.1-10 -p 3389
```

### Parameter Validation

Confirm that TAPING rejects invalid values:

```powershell
python -m taping.cli 8.8.8.8 -c 0
python -m taping.cli 8.8.8.8 -w 50
python -m taping.cli 8.8.8.8 -p 70000
python -m taping.cli range 192.168.1.20-10
python -m taping.cli 8.8.8.8 -p 443 --https
```

## Building the Windows Release

Activate the virtual environment:

```powershell
.\.venv\Scripts\Activate.ps1
```

Run the build script:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build-release.ps1
```

The script will:

1. Remove old `build`, `dist`, and `release` directories.
2. Install or verify PyInstaller.
3. Build `taping.exe`.
4. Create the standalone package.
5. Copy the installer into the release directory.

The generated release files are:

```text
release/
├── taping/
│   ├── taping.exe
│   ├── README.md
│   ├── README.txt
│   ├── LICENSE
│   └── NOTICE
├── taping-windows-x64.zip
└── install.ps1
```

## Testing the Generated Executable

Check the generated version:

```powershell
.\release\taping\taping.exe --version
```

Show the help screen:

```powershell
.\release\taping\taping.exe help
```

Test ICMP:

```powershell
.\release\taping\taping.exe 8.8.8.8 -c 3
```

Test DNS hostname resolution:

```powershell
.\release\taping\taping.exe google.com -c 3
```

Test TCP:

```powershell
.\release\taping\taping.exe google.com --https
```

Test an IPv4 range:

```powershell
.\release\taping\taping.exe range 192.168.1.1-10 --up
```

Test continuous mode:

```powershell
.\release\taping\taping.exe google.com -t
```

Stop the test with `CTRL+C`.

## Preparing a New Version

Update the version number in all of the following files:

```text
pyproject.toml
taping/__init__.py
taping/cli.py
```

Example:

```toml
version = "0.4.0"
```

```python
__version__ = "0.4.0"
```

Update `CHANGELOG.md` with the changes included in the new release.

Then verify the version:

```powershell
python -m taping.cli --version
```

Build the release again:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build-release.ps1
```

Confirm that the generated executable reports the same version:

```powershell
.\release\taping\taping.exe --version
```

## Release Checklist

Before publishing a release, confirm that:

* Python syntax validation succeeds.
* The Python module reports the correct version.
* The standalone executable reports the correct version.
* ICMP checks work.
* DNS hostname checks work.
* TCP checks work.
* IPv4 range checks work.
* Service shortcuts work.
* `-t` continuous mode works.
* `-c` count works.
* `-w` timeout works.
* `-i` interval works.
* `--up` filtering works.
* Invalid parameters return readable errors.
* The release ZIP contains the expected files.
* The PowerShell installer downloads the correct release.
* `CHANGELOG.md` is updated.
* The Git working tree is clean.

Check the working tree:

```powershell
git status
```

## Publishing a GitHub Release

Commit the release changes:

```powershell
git add .
git commit -m "Prepare TAPING v0.4.0"
git push origin main
```

Create an annotated tag:

```powershell
git tag -a v0.4.0 -m "TAPING v0.4.0"
git push origin v0.4.0
```

Create a GitHub Release using the same tag.

Upload these files:

```text
release/taping-windows-x64.zip
release/install.ps1
```

Mark the release as the latest release.

The GitHub release notes should summarize the relevant sections from `CHANGELOG.md`.

## Cleaning the Development Environment

Remove generated build files:

```powershell
Remove-Item .\build -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item .\dist -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item .\release -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item .\taping.spec -Force -ErrorAction SilentlyContinue
```

Deactivate the Python virtual environment:

```powershell
deactivate
```
