# TAPING Development Guide

This document describes the **v0.3.2 source code**. The latest public GitHub Release can still be an earlier version until v0.3.2 is published.

## Setup

Use Python 3.11 or later for new development environments (the package retains 3.9+ metadata compatibility). On Windows (PowerShell):

```powershell
git clone https://github.com/HilaliAhmer/taping.git
cd taping
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
python -m pip install -e '.[dev]'
```

Run the source checkout with `python -m taping.cli ...`. All ping, TCP and traceroute application logic lives in `taping/cli.py`. `scripts/entrypoint.py` is only a tiny PyInstaller launcher.

## Quick checks

```powershell
python -m taping.cli about
python -m taping.cli help
python -m taping.cli 8.8.8.8 -c 3
python -m taping.cli google.com -p 443
python -m taping.cli range 192.168.1.1-10
python -m taping.cli range 192.168.1.1-10 -p 3389
python -m taping.cli trace 8.8.8.8
python -m taping.cli trace google.com -p 443
```

`-t` runs continuously until Ctrl+C; `-c` sets rounds; `-w` sets the per-attempt timeout. TCP traceroute requires elevated privileges on Windows or root/CAP_NET_RAW on Linux. On Linux, install `ping` and `traceroute` if not present.

Invalid input should return 1, unreachable/no successful checks 2, success 0. Example validation:

```powershell
python -m taping.cli 8.8.8.8 -c 0
python -m taping.cli 8.8.8.8 -w 50
python -m taping.cli 8.8.8.8 -p 70000
python -m taping.cli range 192.168.1.20-10
```

## Automated tests and style

```powershell
python -m pytest -q
python -m ruff check taping tests scripts/entrypoint.py
python -m compileall -q taping scripts/entrypoint.py
```

CI runs these on Windows and Ubuntu. Synthetic tests cover range retries, argument/exit codes, route reply parsing, Unicode IPv4 validation, and stdout color behavior. Network and raw-socket tests still need manual validation on real Windows machines.

## Build a standalone Windows executable

```powershell
python -m pip install -r .\requirements-build.txt
powershell -ExecutionPolicy Bypass -File .\scripts\build-release.ps1
```

The script builds **onefile without UPX**, tests `taping.exe about`, creates a ZIP using `/` separators, and writes a SHA-256 checksum. Release assets:

```text
release/
  taping/
    taping.exe
    README.md
    README.txt
    LICENSE
    NOTICE
  taping-windows-x64.zip
  SHA256SUMS
  install.ps1
```

To test the packaged application:

```powershell
.\release\taping\taping.exe about
.\release\taping\taping.exe help
.\release\taping\taping.exe 8.8.8.8 -c 3
.\release\taping\taping.exe trace 8.8.8.8
```

Test TCP traceroute separately using an Administrator terminal. Windows EXE build and installer cannot be fully verified on Linux; test both before publishing.

## Publishing

Update `taping/__init__.py` to change the version; setuptools reads it dynamically. Update `CHANGELOG.md` and README's version note. Only after testing and building should you commit, tag and publish a GitHub Release.

Upload **all three** files from `release/`: `taping-windows-x64.zip`, `SHA256SUMS`, and `install.ps1`. The installer verifies the downloaded ZIP against `SHA256SUMS`. Since both are published from the same release, this protects against accidental corruption but is not an independent signature.

Do not publish or push untested changes to `main`. Check `git status` and use a separate branch if desired.
