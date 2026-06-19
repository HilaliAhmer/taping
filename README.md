# TAPING

TAPING is a tiny Windows command-line tool for quick ICMP ping and TCP port checks.

It helps you test a single IP address, an IP range, or a TCP port without memorizing long CMD or PowerShell loops.

## Features

* Single IP ping
* IP range ping
* TCP port check
* TCP port check for IP ranges
* Simple CMD and PowerShell usage
* Service shortcuts like RDP, HTTP, HTTPS, SMB, WinRM and Zebra printer RAW port
* Standalone Windows EXE installation
* Python developer installation

## Recommended Installation

This method installs the standalone Windows EXE. Python, pip and Git are not required.

Open PowerShell and run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -Command "Invoke-RestMethod https://github.com/HilaliAhmer/taping/releases/latest/download/install.ps1 | Invoke-Expression"
```

The installer will:

* download the latest `taping-windows-x64.zip` release
* install TAPING under `C:\taping`
* add `C:\taping` to your user PATH

After installation, close and reopen CMD or PowerShell, then test:

```cmd
taping help
```

## Manual Installation

Download `taping-windows-x64.zip` from the latest GitHub Release.

Extract it so the final folder is:

```text
C:\taping
```

The executable should be here:

```text
C:\taping\taping.exe
```

Add `C:\taping` to your user PATH, then open a new CMD or PowerShell window and run:

```cmd
taping help
```

## Usage

Ping a single IP:

```cmd
taping 192.168.1.1
```

Ping an IP range:

```cmd
taping range 192.168.1.10-20
```

Check a TCP port:

```cmd
taping 192.168.1.1 -p 80
```

Check a TCP port on an IP range:

```cmd
taping range 192.168.1.10-20 -p 443
```

Show only successful results:

```cmd
taping range 192.168.1.10-20 --up
```

Run continuously until CTRL+C:

```cmd
taping 192.168.1.1 -p 443 --loop
```

Show project information:

```cmd
taping about
```

## Examples

```cmd
taping 8.8.8.8
taping 1.1.1.1 -p 443
taping 212.154.103.165
taping range 212.154.103.160-166
taping 10.138.110.117 -p 9100
taping range 10.138.110.100-120 -p 9100
taping range 192.168.1.1-100 --rdp
```

## Service Shortcuts

RDP:

```cmd
taping 192.168.1.10 --rdp
```

HTTP:

```cmd
taping 192.168.1.10 --http
```

HTTPS:

```cmd
taping 192.168.1.10 --https
```

SMB:

```cmd
taping 192.168.1.10 --smb
```

SSH:

```cmd
taping 192.168.1.10 --ssh
```

Zebra printer RAW port:

```cmd
taping 192.168.1.10 --zebra
```

Shortcut mapping:

| Option     | TCP Port |
| ---------- | -------: |
| `--http`   |       80 |
| `--https`  |      443 |
| `--ssh`    |       22 |
| `--rdp`    |     3389 |
| `--smb`    |      445 |
| `--zebra`  |     9100 |
| `--winrm`  |     5985 |
| `--winrms` |     5986 |

## Developer Installation

Use this method only if you want to develop or modify the Python source code.

Requirements:

* Windows
* Python 3.9 or newer
* Git

Clone the repository:

```powershell
git clone https://github.com/HilaliAhmer/taping.git
cd taping
```

Create a virtual environment:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install in editable mode:

```powershell
python -m pip install -e .
```

Test:

```powershell
taping help
taping 8.8.8.8
taping 1.1.1.1 -p 443
```

## Build Standalone Windows Release

Activate your virtual environment first:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install PyInstaller:

```powershell
python -m pip install --upgrade pyinstaller
```

Build the release package:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build-release.ps1
```

The release files will be created under:

```text
release\
```

Upload these files to GitHub Releases:

```text
release\taping-windows-x64.zip
release\install.ps1
```

## Optional Python Package Installation

This method is for users who prefer Python/pip instead of the standalone EXE.

Install directly from GitHub without requiring Git:

```powershell
python -m pip install --user --upgrade --force-reinstall https://github.com/HilaliAhmer/taping/archive/refs/heads/main.zip
```

If your system uses the Python launcher, this also works:

```powershell
py -m pip install --user --upgrade --force-reinstall https://github.com/HilaliAhmer/taping/archive/refs/heads/main.zip
```

If `taping` is not recognized after pip installation, run it directly through Python:

```powershell
python -m taping.cli help
```

## Troubleshooting

### `taping` is not recognized

If the standalone installer completed successfully but Windows says `taping` is not recognized, close and reopen CMD or PowerShell.

If it still does not work, check that this folder exists:

```text
C:\taping
```

Then check that this file exists:

```text
C:\taping\taping.exe
```

Finally, confirm `C:\taping` is in your user PATH.

You can add it manually with PowerShell:

```powershell
$InstallDir = "C:\taping"
$UserPath = [Environment]::GetEnvironmentVariable("Path", "User")

if ($UserPath -notlike "*$InstallDir*") {
    [Environment]::SetEnvironmentVariable("Path", "$UserPath;$InstallDir", "User")
}

$env:Path += ";$InstallDir"
```

Then test:

```powershell
taping help
```

### Cannot create `C:\taping`

If the installer cannot create `C:\taping`, run PowerShell as Administrator and try again.

### PowerShell blocks virtual environment activation

This applies only to developer installation.

If this command fails:

```powershell
.\.venv\Scripts\Activate.ps1
```

Run:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Then try again:

```powershell
.\.venv\Scripts\Activate.ps1
```

## Important Note

Normal ping uses ICMP and does not use ports.

When you use `-p`, TAPING performs a TCP connection test, similar to paping.

Example:

```cmd
taping 192.168.1.1 -p 443
```

This checks whether TCP port 443 is reachable.

SNMP usually uses UDP 161, so this is not a correct SNMP test:

```cmd
taping 192.168.1.1 -p 161
```

That command checks TCP/161, not UDP/161.

## Uninstall

If installed with the standalone installer, remove the folder:

```powershell
Remove-Item C:\taping -Recurse -Force
```

Then remove `C:\taping` from your user PATH.

If installed with pip:

```powershell
python -m pip uninstall taping
```

or:

```powershell
py -m pip uninstall taping
```

## Original Project Notice

TAPING is created and maintained by Selahattin Açıkgöz / HilaliAhmer.

Original project:

```text
https://github.com/HilaliAhmer/taping
```

If you copy, modify, distribute, or use substantial parts of this project, keep the original copyright and license notice.

## License

This project is licensed under the MIT License.

Copyright (c) 2026 Selahattin Açıkgöz
