# TAPING

[![Latest Release](https://img.shields.io/github/v/release/HilaliAhmer/taping)](https://github.com/HilaliAhmer/taping/releases/latest)
[![License](https://img.shields.io/github/license/HilaliAhmer/taping)](LICENSE)

**TAPING** is a small command-line network diagnostic tool for Windows and Linux. It checks IPv4 reachability, TCP ports, IPv4 ranges, and network routes — without a long list of special-purpose switches.

> **Version note:** This README describes the **v0.3.2 source code**. Until v0.3.2 is built and published as a GitHub Release, the **latest release installer may still install v0.3.1**. Do not expect the new `trace` command in an older executable.

## Quick start

| Task | Command |
| --- | --- |
| Ping an IP | `taping 8.8.8.8` |
| Ping a hostname | `taping google.com` |
| Ping continuously | `taping 8.8.8.8 -t` |
| Ping 5 times | `taping 8.8.8.8 -c 5` |
| Custom timeout | `taping 8.8.8.8 -w 2000` |
| Test TCP port 443 | `taping google.com -p 443` |
| Scan an IPv4 range | `taping range 192.168.1.10-20` |
| Check TCP 3389 across a range | `taping range 192.168.1.10-20 -p 3389` |
| Trace ICMP route | `taping trace 8.8.8.8` |
| Trace route using TCP/443 | `taping trace google.com -p 443` |

Run `taping help` for the short built-in help screen, or `taping about` to see the version. Stop continuous mode with `Ctrl+C`.

## Options

| Option | Purpose |
| --- | --- |
| `-p PORT`, `--port PORT` | TCP port check, or TCP traceroute when used with `trace` |
| `-t`, `--loop` | Run ping/port checks continuously until `Ctrl+C` |
| `-w MS`, `--timeout MS` | Per-attempt timeout in milliseconds (default **4000**) |
| `-c COUNT`, `--count COUNT` | Number of ping/port check rounds (default **1**) |
| `-?`, `-h`, `--help` | Show help |

The interval between check **rounds** is fixed at approximately **1000 ms** (measured from the start of each round). `-t` and `-c` do **not** apply to `trace`.

**Removed in v0.3.2:** `--up`, `-i`/`--interval`, `--version`, and service shortcuts such as `--https`, `--rdp`, and `--ssh`. Use `-p` with a port number instead (for example `-p 3389`). Use `taping about` instead of `--version`.

## Smart IPv4 range scans

A range changes only the final octet:

```powershell
taping range 192.168.1.10-20
```

The full-address form `192.168.1.10-192.168.1.20` is **not** supported.

Range ICMP checks are fast when a device answers immediately, but cautious about reporting `DOWN`:

1. First echo: up to **800 ms**.
2. If unanswered, retry after 250 ms with up to **1200 ms**.
3. If still unanswered, retry after 350 ms with up to **2000 ms**.
4. If still unanswered, retry after 500 ms with the full timeout (**4000 ms** by default).

The first successful response marks the host `UP`; no more attempts are sent to it. An initially missed reply that later succeeds appears as `recovered on attempt 2/4`, for example. To avoid large delays, at most **8** range IPs are checked concurrently; output remains in IP order.

A custom `-w` limits **each** retry's timeout. When `-c` or `-t` is used with a range, every round repeats the range checks. Each IP counts **once per round** in the final connection statistics, regardless of retries.

A `DOWN` result means there was no ICMP reply to the attempted checks; it does **not** prove that the device is powered off. Firewalls may block ICMP.

## ICMP, TCP and traceroute

Without `-p`, TAPING checks **ICMP Echo**. The `-p` option checks **TCP**, not UDP or SNMP:

```powershell
taping example.com
taping example.com -p 443
```

An ICMP-blocked website can still have an open TCP port.

Route tracing:

```powershell
taping trace 10.6.106.50
taping trace 10.6.106.50 -p 443
```

- **ICMP trace** runs the system's `tracert` (Windows) or `traceroute -I` (Linux). On Linux, install `traceroute` separately if needed (`sudo apt install traceroute`).
- **TCP trace** uses TTL-limited TCP connections and captures ICMP replies. It generally requires an **Administrator** terminal on Windows or **root/CAP_NET_RAW** on Linux. Some routers do not return their hop information, so `*`/`TIMEOUT` is not necessarily a broken route.
- TAPING uses **IPv4 only**.

On Windows, TAPING uses the native `IcmpSendEcho` API for ICMP ping, avoiding language-dependent parsing of `ping.exe` output. On Linux, it uses the system `ping` command.

## Installation

### Windows standalone (no Python needed)

Download `taping-windows-x64.zip` and `install.ps1` from the [GitHub Releases page](https://github.com/HilaliAhmer/taping/releases/latest). When using the **v0.3.2 installer**, it also downloads `SHA256SUMS` and checks the archive's SHA-256 hash before extraction.

To run the installer after inspecting its contents:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\install.ps1
```

The updated installer installs for the current user under `%LOCALAPPDATA%\Programs\taping` and adds that directory to your **User PATH**. Close and reopen the terminal, then run:

```powershell
taping about
taping help
```

For **manual installation**, extract the ZIP file to a directory such as `%LOCALAPPDATA%\Programs\taping` and add that directory to PATH. If an old copy remains under `C:\taping`, use `where.exe taping` to check which one takes priority.

**Existing v0.3.1 installs:** A new v0.3.2 release must be published before the latest-release installer can install the commands described here. The installer cannot update a release that has not been published.

### Python development install

Python **3.11+ is recommended** (the package still permits Python 3.9+, but older Python versions are no longer security-supported). Clone the repository, create a virtual environment and install the editable project:

```powershell
git clone https://github.com/HilaliAhmer/taping.git
cd taping
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
python -m taping.cli about
```

On Linux, create the environment with `python3 -m venv .venv`, activate with `source .venv/bin/activate` and run the same pip command. In source checkout, `python -m taping.cli ...` runs the modified `cli.py` directly.

## Updating and troubleshooting

- **Update standalone:** download and run the installer for the newly published release, or replace your standalone files manually.
- **Command not found:** reopen the terminal, then run `where.exe taping` (Windows) or `command -v taping` (Linux).
- **Old version runs:** check `taping about` and the executable locations on PATH. A standalone executable is independent of the Python source files you just edited.
- **TCP trace reports permission denied:** run an elevated Windows terminal or use root/CAP_NET_RAW on Linux. Network policy may still block raw socket capture.
- **ICMP says DOWN but TCP works:** try `taping example.com -p 443`; some destinations block ICMP.
- **Security software blocks the installer:** do not disable endpoint protections. Download the official release manually and request your security team's review.

## Exit codes

| Exit code | Meaning |
| ---: | --- |
| `0` | At least one check succeeded, or traced destination was confirmed |
| `1` | Invalid command, DNS/configuration issue, or execution failure |
| `2` | No checks succeeded, or trace could not confirm the destination |

## Uninstall

For the updated standalone installer, remove `%LOCALAPPDATA%\Programs\taping` and remove its entry from your User PATH. Older installations might be under `C:\taping`. For pip installs:

```powershell
python -m pip uninstall taping
```

## Project

- [Development Guide](DEVELOPMENT.md)
- [Contributing](CONTRIBUTING.md)
- [Changelog](CHANGELOG.md)
- [License](LICENSE)

TAPING is developed by Selahattin Açıkgöz / HilaliAhmer. Copyright © 2026 Selahattin Açıkgöz. MIT License.
