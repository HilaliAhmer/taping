# TAPING

TAPING is a lightweight Windows command-line tool for ICMP ping, IPv4 range scanning, DNS hostname checks, and TCP port connectivity tests.

It provides a simpler and more readable alternative to long CMD or PowerShell network-testing commands.

## Features

- Ping a single IPv4 address
- Ping a DNS hostname such as `google.com`
- Display the resolved IPv4 address for hostnames
- Ping an IPv4 address range
- Check TCP port connectivity
- Check TCP ports across an IPv4 range
- Use shortcuts for common services such as HTTP, HTTPS, SSH, RDP, SMB, Zebra, and WinRM
- Add a timestamp to every ICMP and TCP result
- Run continuously with `-t` or `--loop`
- Set a custom timeout with `-w` or `--timeout`
- Set the number of checks with `-c` or `--count`
- Set the interval between checks with `-i` or `--interval`
- Show only successful results with `--up`
- Display connection statistics
- Install as a standalone Windows executable
- Install optionally through Python and pip
- Build standalone Windows release packages with PyInstaller

## Installation Methods

| Method | Recommended for | Python required | Git required |
| --- | --- | ---: | ---: |
| Standalone EXE | Regular users | No | No |
| Python/pip | Technical users | Yes | No |
| Developer installation | Contributors and developers | Yes | Yes |

## Standalone EXE Installation

This is the recommended installation method.

TAPING is installed under:

```text
C:\taping
```

Python, pip, and Git are not required.

Open PowerShell and run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -Command "Write-Host 'Starting TAPING installer... Please wait.' -ForegroundColor Green; iex ((New-Object Net.WebClient).DownloadString('https://github.com/HilaliAhmer/taping/releases/latest/download/install.ps1'))"
```

The installer will:

- Download the latest `taping-windows-x64.zip` release
- Extract TAPING under `C:\taping`
- Add `C:\taping` to the beginning of the user PATH
- Prioritize the standalone installation over older pip installations
- Run a quick TAPING test

Wait until you see:

```text
TAPING installed successfully.
```

After installation, close and reopen CMD or PowerShell.

Check the installed version:

```cmd
taping --version
```

Show the help screen:

```cmd
taping help
```

## Quick Usage

Ping an IPv4 address:

```cmd
taping 8.8.8.8
```

Ping a DNS hostname:

```cmd
taping google.com
```

Ping a target continuously until `CTRL+C`:

```cmd
taping google.com -t
```

The long option is also supported:

```cmd
taping google.com --loop
```

Ping a target five times:

```cmd
taping google.com -c 5
```

Use a custom timeout:

```cmd
taping google.com -w 2000
```

Ping continuously with a custom timeout:

```cmd
taping google.com -t -w 2000
```

Ping an IPv4 range:

```cmd
taping range 192.168.1.1-100
```

Check a TCP port:

```cmd
taping google.com -p 443
```

Check a TCP port across an IPv4 range:

```cmd
taping range 192.168.1.1-100 -p 3389
```

Show only successful results:

```cmd
taping range 192.168.1.1-100 --up
```

## Command-Line Options

| Option | Description |
| --- | --- |
| `-p PORT`, `--port PORT` | Check a TCP port instead of ICMP |
| `-t`, `--loop` | Run continuously until `CTRL+C`, similar to Windows `ping -t` |
| `-w MS`, `--timeout MS` | Set the timeout in milliseconds |
| `-c COUNT`, `--count COUNT` | Set the number of checks |
| `-i MS`, `--interval MS` | Set the delay between check rounds in milliseconds |
| `--up` | Show only successful results |
| `--version` | Show the installed TAPING version |
| `-?`, `-h`, `-help`, `--help` | Display the help screen |

### Default Timing Values

| Check type | Default timeout |
| --- | ---: |
| Single-target ICMP | 4000 ms |
| IPv4 range ICMP | 4000 ms |
| TCP port check | 4000 ms |

The default timeout is `4000 ms` for all ICMP and TCP checks.

A custom timeout can be selected with `-w` or `--timeout`:

```cmd
taping range 192.168.1.1-100 -w 1000
```

The default interval between check rounds is:

```text
1000 ms
```

### Timing Examples

Run ten checks with the default one-second interval:

```cmd
taping 8.8.8.8 -c 10
```

Run ten checks with a 500 ms interval:

```cmd
taping 8.8.8.8 -c 10 -i 500
```

Use a 2000 ms timeout:

```cmd
taping google.com -c 5 -w 2000
```

Run continuously with a 2000 ms timeout:

```cmd
taping google.com -t -w 2000
```

## Examples

```cmd
taping 8.8.8.8
taping google.com
taping google.com -c 5
taping google.com -t
taping google.com --loop
taping google.com -t -w 2000
taping google.com -c 5 -w 3000
taping google.com --https
taping microsoft.com --https
taping 1.1.1.1 -p 443
taping 8.8.8.8 -c 10 -i 1000
taping 192.168.10.36 --rdp
taping 192.168.10.3 --zebra
taping range 192.168.1.1-100
taping range 192.168.1.1-100 --up
taping range 192.168.1.1-100 --rdp
taping range 10.10.110.100-120 -p 9100
taping range 192.168.1.1-100 -p 3389 -c 3
taping range 192.168.1.1-100 -p 3389 --loop
```

## Output Example

```text
Pinging google.com [142.251.110.100] using ICMP:

2026-07-16 10:02:20.903  google.com [142.251.110.100]               UP         44.00ms TTL=109
2026-07-16 10:02:21.969  google.com [142.251.110.100]               UP         44.00ms TTL=109
2026-07-16 10:02:23.031  google.com [142.251.110.100]               UP         44.00ms TTL=109

Connection statistics:
        Attempted = 3, Connected = 3, Failed = 0 (0.00%)
Approximate connection times:
        Minimum = 44.00ms, Maximum = 44.00ms, Average = 44.00ms
```

## DNS Hostname Support

TAPING accepts DNS hostnames in addition to IPv4 addresses.

Example:

```cmd
taping google.com
```

TAPING resolves the hostname before starting the check:

```text
Pinging google.com [142.251.110.100] using ICMP:
```

Internal DNS names are also supported when they can be resolved by the client:

```cmd
taping server01.contoso.local
```

If a hostname cannot be resolved, TAPING reports a DNS failure instead of treating it as an unreachable IPv4 address.

## ICMP and TCP Are Different

A website can be reachable over HTTPS even when it does not respond to ICMP ping.

For example:

```cmd
taping microsoft.com
```

may display:

```text
DOWN No reply
```

This does not necessarily mean that the website is unavailable.

Test HTTPS separately:

```cmd
taping microsoft.com --https
```

A successful result may look like:

```text
OPEN time=45.00ms protocol=TCP port=443
```

## Service Shortcuts

| Option | TCP port | Example |
| --- | ---: | --- |
| `--http` | 80 | `taping 192.168.1.10 --http` |
| `--https` | 443 | `taping google.com --https` |
| `--ssh` | 22 | `taping 192.168.1.10 --ssh` |
| `--rdp` | 3389 | `taping 192.168.1.10 --rdp` |
| `--smb` | 445 | `taping 192.168.1.10 --smb` |
| `--zebra` | 9100 | `taping 192.168.1.10 --zebra` |
| `--winrm` | 5985 | `taping 192.168.1.10 --winrm` |
| `--winrms` | 5986 | `taping 192.168.1.10 --winrms` |

Only one service shortcut can be used at a time.

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

Do not combine `-p` with a service shortcut.

## IPv4 Range Format

The supported range format changes only the last octet.

Correct:

```cmd
taping range 192.168.1.10-20
```

This checks:

```text
192.168.1.10
192.168.1.11
192.168.1.12
...
192.168.1.20
```

Invalid examples:

```text
192.168.1.20-10
192.168.1-10
192.168.1.1-192.168.1.10
```

## Manual Standalone Installation

Download this file from the latest GitHub Release:

```text
taping-windows-x64.zip
```

Do not download GitHub's automatically generated `Source code (zip)` package for client installation.

Extract the release ZIP.

The package should contain a `taping` folder with files similar to:

```text
taping\
├── taping.exe
├── README.md
├── README.txt
├── LICENSE
└── NOTICE
```

Copy the contents into:

```text
C:\taping
```

The executable should be located at:

```text
C:\taping\taping.exe
```

Add `C:\taping` to the beginning of the user PATH.

Open a new CMD or PowerShell window and run:

```cmd
taping --version
```

## Updating TAPING

Run the standalone installer again:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -Command "Write-Host 'Starting TAPING installer... Please wait.' -ForegroundColor Green; iex ((New-Object Net.WebClient).DownloadString('https://github.com/HilaliAhmer/taping/releases/latest/download/install.ps1'))"
```

The installer downloads and installs the latest GitHub Release.

After the update, close and reopen CMD or PowerShell.

Check the version:

```cmd
taping --version
```

## Optional Python/pip Installation

Use this method only when you specifically want a Python-based installation.

Python and pip are required.

Install or upgrade from GitHub:

```powershell
python -m pip install --no-cache-dir --user --upgrade --force-reinstall https://github.com/HilaliAhmer/taping/archive/refs/heads/main.zip
```

The Python launcher can also be used:

```powershell
py -m pip install --no-cache-dir --user --upgrade --force-reinstall https://github.com/HilaliAhmer/taping/archive/refs/heads/main.zip
```

Test the module:

```powershell
python -m taping.cli --version
python -m taping.cli help
```

### Standalone and pip PATH Conflict

An older pip installation may create a launcher under a path similar to:

```text
C:\Users\USERNAME\AppData\Roaming\Python\Python312\Scripts\taping.exe
```

Check all detected TAPING commands:

```powershell
where.exe taping
```

Or:

```powershell
Get-Command taping -All |
    Format-Table CommandType, Name, Source, Definition -AutoSize
```

For the standalone installation, the first result should be:

```text
C:\taping\taping.exe
```

An old pip installation can be removed with:

```powershell
python -m pip uninstall taping
```

## Developer Installation

Use this method to modify or test the Python source code.

### Requirements

- Windows
- Python 3.9 or newer
- pip
- Git

Clone the repository:

```powershell
git clone https://github.com/HilaliAhmer/taping.git
cd taping
```

Create a virtual environment:

```powershell
py -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install TAPING in editable mode:

```powershell
python -m pip install -e .
```

Run developer tests:

```powershell
python -m py_compile .\taping\cli.py
python -m taping.cli --version
python -m taping.cli help
python -m taping.cli about
python -m taping.cli 8.8.8.8
python -m taping.cli google.com -c 3
python -m taping.cli google.com -c 3 -w 2000
python -m taping.cli google.com --https -c 2
python -m taping.cli range 192.168.1.1-10 --up
```

Continuous mode test:

```powershell
python -m taping.cli google.com -t
```

Stop it with `CTRL+C`.

When the source code is edited, the editable installation uses the local development version.

## Building a Standalone Windows Release

Activate the virtual environment:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install or upgrade PyInstaller:

```powershell
python -m pip install --upgrade pyinstaller
```

Build the release:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build-release.ps1
```

The release files are created under:

```text
release\
```

Expected release assets:

```text
release\taping-windows-x64.zip
release\install.ps1
```

## Testing the Generated EXE

Check the version:

```powershell
.\release\taping\taping.exe --version
```

Show help:

```powershell
.\release\taping\taping.exe help
```

Test ICMP:

```powershell
.\release\taping\taping.exe 8.8.8.8 -c 5
```

Test a DNS hostname:

```powershell
.\release\taping\taping.exe google.com -c 3
```

Test custom timeout:

```powershell
.\release\taping\taping.exe google.com -c 3 -w 2000
```

Test continuous mode:

```powershell
.\release\taping\taping.exe google.com -t
```

Stop it with `CTRL+C`.

Test TCP:

```powershell
.\release\taping\taping.exe google.com --https -c 2
```

Test an IPv4 range:

```powershell
.\release\taping\taping.exe range 192.168.1.1-10 --up
```

## Publishing a GitHub Release

Before publishing, confirm that:

- The Python version is correct
- The standalone EXE version is correct
- DNS hostname checks work
- ICMP checks work
- TCP checks work
- Range checks work
- `-t` continuous mode works
- `-w` timeout works
- The installer prioritizes `C:\taping` in PATH
- The Git working tree is clean

Create and push a version tag:

```powershell
git tag -a v0.3.1 -m "TAPING v0.3.1"
git push origin v0.3.1
```

Create a GitHub Release using the same tag.

Upload:

```text
release\taping-windows-x64.zip
release\install.ps1
```

Mark the new release as:

```text
Latest
```

Do not upload GitHub's automatically generated source ZIP as the Windows installer package.

## Troubleshooting

### `taping` is not recognized

Close and reopen CMD or PowerShell.

Confirm the installation folder exists:

```text
C:\taping
```

Confirm the executable exists:

```text
C:\taping\taping.exe
```

Test the executable directly:

```powershell
C:\taping\taping.exe --version
```

### An older TAPING version is executed

Check the command resolution order:

```powershell
where.exe taping
```

The first result should be:

```text
C:\taping\taping.exe
```

Check all detected commands:

```powershell
Get-Command taping -All |
    Format-Table CommandType, Name, Source, Definition -AutoSize
```

Place `C:\taping` at the beginning of the user PATH:

```powershell
$InstallDir = "C:\taping"
$NormalizedInstallDir = $InstallDir.TrimEnd("\")
$UserPath = [Environment]::GetEnvironmentVariable("Path", "User")

$ExistingItems = @(
    $UserPath -split ";" |
        Where-Object {
            $_ -and
            $_.Trim().TrimEnd("\") -ne $NormalizedInstallDir
        }
)

$NewUserPath = (@($InstallDir) + $ExistingItems) -join ";"

[Environment]::SetEnvironmentVariable(
    "Path",
    $NewUserPath,
    "User"
)

$CurrentItems = @(
    $env:Path -split ";" |
        Where-Object {
            $_ -and
            $_.Trim().TrimEnd("\") -ne $NormalizedInstallDir
        }
)

$env:Path = (@($InstallDir) + $CurrentItems) -join ";"
```

Test again:

```powershell
where.exe taping
taping --version
```

### CrowdStrike or another security product blocks the installer

Do not bypass endpoint security controls.

Download the following asset manually from the latest GitHub Release:

```text
taping-windows-x64.zip
```

Extract it and copy the packaged files into:

```text
C:\taping
```

If `taping.exe` itself is blocked, contact the security team and request an appropriate review or allowlisting decision.

### Cannot create `C:\taping`

Open PowerShell as Administrator and run the installer again.

### PowerShell blocks virtual environment activation

This applies only to developer installation.

Run:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Then activate the environment:

```powershell
.\.venv\Scripts\Activate.ps1
```

### A hostname is DOWN but the website opens

The target may block ICMP while allowing TCP connections.

Test its HTTPS port:

```cmd
taping hostname.example --https
```

### DNS resolution fails

Confirm that Windows can resolve the hostname:

```powershell
Resolve-DnsName google.com
```

For internal hostnames, verify that the client is using the correct corporate DNS servers.

## Important Notes

ICMP ping does not use TCP or UDP ports.

When `-p` or a service shortcut is used, TAPING performs a TCP connection test similar to paping.

Example:

```cmd
taping 192.168.1.1 -p 443
```

This checks whether TCP port 443 is reachable.

SNMP normally uses UDP port 161.

This command:

```cmd
taping 192.168.1.1 -p 161
```

checks TCP port 161, not SNMP over UDP.

IPv6 is not currently supported. TAPING resolves and checks IPv4 addresses.

## Exit Codes

| Exit code | Meaning |
| ---: | --- |
| `0` | At least one check succeeded |
| `1` | Invalid argument, configuration, or input |
| `2` | No checks succeeded |

## Uninstall

### Standalone EXE Installation

Remove the TAPING folder:

```powershell
Remove-Item C:\taping -Recurse -Force
```

Remove `C:\taping` from the user PATH afterward.

### Python/pip Installation

Uninstall with:

```powershell
python -m pip uninstall taping
```

Or:

```powershell
py -m pip uninstall taping
```

If a stale `taping.exe` launcher remains, remove it from the corresponding Python Scripts folder.

## Original Project Notice

TAPING is created and maintained by:

```text
Selahattin Açıkgöz / HilaliAhmer
```

Original project:

```text
https://github.com/HilaliAhmer/taping
```

If you copy, modify, distribute, or use substantial parts of this project, retain the original copyright and license notices.

## License

This project is licensed under the MIT License.

```text
Copyright (c) 2026 Selahattin Açıkgöz
```
