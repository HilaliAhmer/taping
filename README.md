# TAPING

[![Latest Release](https://img.shields.io/github/v/release/HilaliAhmer/taping)](https://github.com/HilaliAhmer/taping/releases/latest)
[![License](https://img.shields.io/github/license/HilaliAhmer/taping)](LICENSE)
[![Windows](https://img.shields.io/badge/platform-Windows-blue)](https://github.com/HilaliAhmer/taping)

**TAPING** is a lightweight Windows command-line tool for checking ICMP ping, TCP ports, DNS hostnames, and IPv4 ranges.

It provides a simple and readable alternative to long CMD and PowerShell network-testing commands.

## Features

* Ping IPv4 addresses and DNS hostnames
* Scan an IPv4 address range
* Test TCP port connectivity
* Use shortcuts for common services
* Run continuously
* Display timestamps and connection statistics
* Show only reachable hosts
* Use without installing Python

## Installation

### Recommended: PowerShell Installer

Open PowerShell and run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -Command "Write-Host 'Starting TAPING installer... Please wait.' -ForegroundColor Green; iex ((New-Object Net.WebClient).DownloadString('https://github.com/HilaliAhmer/taping/releases/latest/download/install.ps1'))"
```

The installer downloads TAPING, installs it under `C:\taping`, and adds it to your user PATH.

After installation, close and reopen PowerShell or CMD.

Confirm the installation:

```powershell
taping --version
```

Show the help screen:

```powershell
taping help
```

### Manual Installation

Download `taping-windows-x64.zip` from the [latest release](https://github.com/HilaliAhmer/taping/releases/latest).

Do not download GitHub's automatically generated **Source code** ZIP.

Extract the package and run `taping.exe`, or copy its contents into:

```text
C:\taping
```

## Quick Start

| What you want to do       | Command                              |
| ------------------------- | ------------------------------------ |
| Ping an IP address        | `taping 8.8.8.8`                     |
| Ping a hostname           | `taping google.com`                  |
| Run continuously          | `taping google.com -t`               |
| Run five checks           | `taping google.com -c 5`             |
| Scan an IPv4 range        | `taping range 192.168.1.1-100`       |
| Show only reachable hosts | `taping range 192.168.1.1-100 --up`  |
| Test TCP port 443         | `taping google.com -p 443`           |
| Test RDP across a range   | `taping range 192.168.1.1-100 --rdp` |

Stop continuous mode with `CTRL+C`.

## Service Shortcuts

Instead of remembering common TCP port numbers, use a service shortcut:

| Shortcut   | Service        | TCP port |
| ---------- | -------------- | -------: |
| `--http`   | HTTP           |       80 |
| `--https`  | HTTPS          |      443 |
| `--ssh`    | SSH            |       22 |
| `--rdp`    | Remote Desktop |     3389 |
| `--smb`    | SMB            |      445 |
| `--zebra`  | Zebra printing |     9100 |
| `--winrm`  | WinRM          |     5985 |
| `--winrms` | Secure WinRM   |     5986 |

Example:

```powershell
taping server01 --rdp
```

The following commands perform the same TCP test:

```powershell
taping server01 --rdp
taping server01 -p 3389
```

Do not combine `-p` with a service shortcut.

## Options

| Option                      | Description                     |
| --------------------------- | ------------------------------- |
| `-p PORT`, `--port PORT`    | Test a TCP port instead of ICMP |
| `-t`, `--loop`              | Run continuously until `CTRL+C` |
| `-c COUNT`, `--count COUNT` | Set the number of checks        |
| `-w MS`, `--timeout MS`     | Set the timeout in milliseconds |
| `-i MS`, `--interval MS`    | Set the delay between checks    |
| `--up`                      | Show only successful results    |
| `--version`                 | Show the installed version      |
| `-h`, `--help`              | Show the help screen            |

The default timeout is `4000 ms`, and the default interval is `1000 ms`.

Example with custom values:

```powershell
taping google.com -c 10 -w 2000 -i 500
```

## IPv4 Range Format

TAPING changes only the final part of an IPv4 address.

Correct:

```powershell
taping range 192.168.1.10-20
```

This checks addresses from `192.168.1.10` through `192.168.1.20`.

The following full-address format is not supported:

```text
192.168.1.10-192.168.1.20
```

## ICMP and TCP Tests

A device or website may block ICMP ping while still accepting TCP connections.

For example, a website may appear as `DOWN` with:

```powershell
taping example.com
```

Test its HTTPS service separately:

```powershell
taping example.com --https
```

The `-p` option always performs a **TCP** connection test. It does not test UDP services.

IPv6 is not currently supported.

## Updating

Run the PowerShell installer again:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -Command "Write-Host 'Starting TAPING installer... Please wait.' -ForegroundColor Green; iex ((New-Object Net.WebClient).DownloadString('https://github.com/HilaliAhmer/taping/releases/latest/download/install.ps1'))"
```

Close and reopen PowerShell or CMD, then verify the version:

```powershell
taping --version
```

## Troubleshooting

### `taping` is not recognized

Close and reopen PowerShell or CMD.

Test the executable directly:

```powershell
C:\taping\taping.exe --version
```

### An older version opens

Check which executable Windows is using:

```powershell
where.exe taping
```

For the standalone installation, the first result should be:

```text
C:\taping\taping.exe
```

### A website opens but TAPING reports DOWN

The website may be blocking ICMP ping. Test its HTTPS port:

```powershell
taping example.com --https
```

### The installer is blocked by security software

Do not bypass endpoint-security controls.

Download `taping-windows-x64.zip` manually from the [latest release](https://github.com/HilaliAhmer/taping/releases/latest), or contact your security team for review.

## Optional Python Installation

Python 3.9 or newer is required.

```powershell
python -m pip install --no-cache-dir --user --upgrade --force-reinstall https://github.com/HilaliAhmer/taping/archive/refs/heads/main.zip
```

Run TAPING through Python:

```powershell
python -m taping.cli google.com
```

## Uninstall

Delete the standalone installation:

```powershell
Remove-Item C:\taping -Recurse -Force
```

Then remove `C:\taping` from your user PATH.

For the Python installation:

```powershell
python -m pip uninstall taping
```

## Project Documentation

- [Development Guide](DEVELOPMENT.md)
- [Contributing](CONTRIBUTING.md)
- [Changelog](CHANGELOG.md)

## License

TAPING is licensed under the [MIT License](LICENSE).

Copyright © 2026 Selahattin Açıkgöz.
