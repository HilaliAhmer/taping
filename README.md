# TAPING

TAPING is a tiny command-line tool for quick ICMP ping and TCP port checks.

It helps you test a single IP address, an IP range, or a TCP port without memorizing long CMD or PowerShell loops.

## Features

* Single IP ping
* IP range ping
* TCP port check
* TCP port check for IP ranges
* Simple CMD and PowerShell usage
* Service shortcuts like RDP, HTTP, HTTPS, SMB and Zebra printer port

## Requirements

* Windows
* Python 3.9 or newer
* Git, only required when installing directly from GitHub

Check Python:

```powershell
py --version
```

or:

```powershell
python --version
```

## Installation

### Quick install from GitHub

Install TAPING directly from GitHub:

```powershell
py -m pip install --user git+https://github.com/HilaliAhmer/taping.git
```

Close and reopen CMD or PowerShell, then test:

```powershell
taping help
```

### If `taping` is not recognized

If installation succeeds but Windows says `taping` is not recognized, the Python user Scripts folder is probably not in your PATH.

Run this in PowerShell:

```powershell
$ScriptsPath = py -c "import site, pathlib; print(pathlib.Path(site.USER_BASE) / 'Scripts')"
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

If it still does not work, close and reopen CMD or PowerShell.

## Developer Installation

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

## Upgrade

To upgrade TAPING to the latest version from GitHub:

```powershell
py -m pip install --user --upgrade --force-reinstall git+https://github.com/HilaliAhmer/taping.git

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

## Examples

```cmd
taping 8.8.8.8
taping 1.1.1.1 -p 443
taping 212.154.103.165
taping range 212.154.103.160-166
taping 10.138.110.117 -p 9100
taping range 10.138.110.100-120 -p 9100
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

## Troubleshooting

### `taping` is not recognized

If Windows says `taping` is not recognized after installation, the Python Scripts folder may not be in your PATH.

Find your Python user base path:

```powershell
py -m site --user-base
```

The Scripts folder is usually similar to:

```text
C:\Users\<YourUser>\AppData\Roaming\Python\Python312\Scripts
```

Add that `Scripts` folder to your user PATH, then close and reopen CMD or PowerShell.

### PowerShell blocks virtual environment activation

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

If installed from GitHub with pip:

```powershell
py -m pip uninstall taping
```

## License

This project is licensed under the MIT License.
