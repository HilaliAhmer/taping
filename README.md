# TAPING

TAPING is a small Windows command-line tool for quick ICMP ping and TCP port checks.

It helps you test a single IP address, an IP range, or a TCP port without memorizing long CMD or PowerShell loops.

## Features

* Single IP ping
* IP range ping
* TCP port check
* TCP port check for IP ranges
* Service shortcuts for common ports
* `--up` mode to show only successful results
* `--loop` mode for continuous checks
* Standalone Windows EXE installation
* Optional Python/pip installation for technical users
* Developer workflow for modifying the source code

## Installation

TAPING can be installed in two ways.

| Method         | Best for                      | Requires Python? | Requires Git? |
| -------------- | ----------------------------- | ---------------: | ------------: |
| Standalone EXE | Regular usage                 |               No |            No |
| Python/pip     | Technical users or developers |              Yes |            No |

## Standalone EXE Installation

This is the recommended method for most users.

It installs TAPING under:

```text
C:\taping
```

Python, pip and Git are not required.

Open PowerShell and run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -Command "Write-Host 'Starting TAPING installer... Please wait.' -ForegroundColor Green; iex ((New-Object Net.WebClient).DownloadString('https://github.com/HilaliAhmer/taping/releases/latest/download/install.ps1'))"
```

The installer will:

* download the latest `taping-windows-x64.zip` release
* install TAPING under `C:\taping`
* add `C:\taping` to the user PATH
* run a quick TAPING test at the end

> The installation may take a few seconds depending on the internet connection.
> Wait until you see `TAPING installed successfully.`
> Do not close PowerShell or press `CTRL+C` during installation.

After installation, close and reopen CMD or PowerShell, then test:

```cmd
taping help
```

## Quick Usage

Ping a single IP:

```cmd
taping 192.168.1.1
```

Ping an IP range:

```cmd
taping range 192.168.1.1-100
```

Check a TCP port:

```cmd
taping 192.168.1.1 -p 443
```

Check a TCP port on an IP range:

```cmd
taping range 192.168.1.1-100 -p 3389
```

Show only successful results:

```cmd
taping range 192.168.1.1-100 --up
```

Run continuously until `CTRL+C`:

```cmd
taping 192.168.1.1 -p 443 --loop
```

Show version:

```cmd
taping --version
```

Show project information:

```cmd
taping about
```

## Examples

```cmd
taping 8.8.8.8
taping 1.1.1.1 -p 443
taping range 192.168.1.1-100
taping range 192.168.1.1-100 --up
taping range 192.168.1.1-100 --rdp
taping 10.138.110.117 --zebra
taping range 10.138.110.100-120 -p 9100
```

## Service Shortcuts

| Option     | TCP Port | Usage                          |
| ---------- | -------: | ------------------------------ |
| `--http`   |       80 | `taping 192.168.1.10 --http`   |
| `--https`  |      443 | `taping 192.168.1.10 --https`  |
| `--ssh`    |       22 | `taping 192.168.1.10 --ssh`    |
| `--rdp`    |     3389 | `taping 192.168.1.10 --rdp`    |
| `--smb`    |      445 | `taping 192.168.1.10 --smb`    |
| `--zebra`  |     9100 | `taping 192.168.1.10 --zebra`  |
| `--winrm`  |     5985 | `taping 192.168.1.10 --winrm`  |
| `--winrms` |     5986 | `taping 192.168.1.10 --winrms` |

Only one service shortcut can be used at a time.

Do not use `-p` together with a service shortcut.

Correct:

```cmd
taping 192.168.1.10 --rdp
```

Correct:

```cmd
taping 192.168.1.10 -p 3389
```

Incorrect:

```cmd
taping 192.168.1.10 -p 3389 --rdp
```

## Manual Standalone Installation

Download `taping-windows-x64.zip` from the latest GitHub Release.

Extract it so the final folder is:

```text
C:\taping
```

The executable should be here:

```text
C:\taping\taping.exe
```

Add `C:\taping` to the user PATH.

Then open a new CMD or PowerShell window and run:

```cmd
taping help
```

## Optional Python/pip Installation

Use this method if you want to install TAPING with Python and pip instead of the standalone EXE.

Python and pip are required. Git is not required.

Install or upgrade directly from GitHub:

```powershell
python -m pip install --no-cache-dir --user --upgrade --force-reinstall https://github.com/HilaliAhmer/taping/archive/refs/heads/main.zip
```

If your system uses the Python launcher, this also works:

```powershell
py -m pip install --no-cache-dir --user --upgrade --force-reinstall https://github.com/HilaliAhmer/taping/archive/refs/heads/main.zip
```

Test:

```powershell
python -m taping.cli help
```

If the `taping` command is not recognized after pip installation, add the Python user Scripts folder to PATH:

```powershell
$ScriptsPath = python -c "import sysconfig; print(sysconfig.get_path('scripts', scheme='nt_user'))"
$UserPath = [Environment]::GetEnvironmentVariable("Path", "User")

if ($UserPath -notlike "*$ScriptsPath*") {
    [Environment]::SetEnvironmentVariable("Path", "$UserPath;$ScriptsPath", "User")
}

$env:Path += ";$ScriptsPath"
```

Then test again:

```powershell
taping help
```

## Developer Installation

Use this method if you want to develop, modify or test the Python source code.

Requirements:

* Windows
* Python 3.9 or newer
* pip
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

Install TAPING in editable mode:

```powershell
python -m pip install -e .
```

Test:

```powershell
taping help
taping about
taping 8.8.8.8
taping 1.1.1.1 -p 443
```

When you edit the source code, the `taping` command will use your local development version.

## Build Standalone Windows Release

Use this method only when preparing a new Windows release package.

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

The release package will be created under:

```text
release\
```

Test the generated executable:

```powershell
.\release\taping\taping.exe help
.\release\taping\taping.exe 8.8.8.8
.\release\taping\taping.exe 1.1.1.1 -p 443
.\release\taping\taping.exe range 192.168.1.1-10 --up
```

Upload these files to GitHub Releases:

```text
release\taping-windows-x64.zip
scripts\install.ps1
```

## Troubleshooting

### `taping` is not recognized after standalone installation

Close and reopen CMD or PowerShell.

If it still does not work, check that this folder exists:

```text
C:\taping
```

Then check that this file exists:

```text
C:\taping\taping.exe
```

Finally, confirm that `C:\taping` is in the user PATH.

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

Run PowerShell as Administrator and try the installer again.

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

## Important Notes

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

### Standalone EXE installation

Remove the installation folder:

```powershell
Remove-Item C:\taping -Recurse -Force
```

Then remove `C:\taping` from the user PATH.

### Python/pip installation

Uninstall with pip:

```powershell
python -m pip uninstall taping
```

or:

```powershell
py -m pip uninstall taping
```

If a stale `taping.exe` launcher remains, remove it from the Python Scripts folder.

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
