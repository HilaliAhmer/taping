"""TAPING command-line interface."""

import argparse
import os
import re
import socket
import subprocess
import sys
import time

try:
    from . import __version__
except ImportError:
    __version__ = "0.2.2"

VERSION = __version__
AUTHOR = "Selahattin Acikgoz / HilaliAhmer"
REPOSITORY = "https://github.com/HilaliAhmer/taping"

SERVICE_PORTS = {
    "http": 80,
    "https": 443,
    "ssh": 22,
    "rdp": 3389,
    "smb": 445,
    "zebra": 9100,
    "winrm": 5985,
    "winrms": 5986,
}


class Colors:
    RESET = "\033[0m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    GRAY = "\033[90m"


def supports_color():
    if os.environ.get("NO_COLOR"):
        return False

    return os.name == "nt" or sys.stdout.isatty()


def color(text, color_code):
    text = str(text)

    if not supports_color():
        return text

    return f"{color_code}{text}{Colors.RESET}"


def show_about():
    print(f"""
TAPING v{VERSION}
Tiny range ping and TCP port ping helper for Windows.

Author:
  {AUTHOR}

Original project:
  {REPOSITORY}

License:
  MIT

Copyright:
  Copyright (c) 2026 Selahattin Acikgoz
""".strip())


def show_help():
    print(f"""
taping v{VERSION} - Range ping and TCP port ping helper

TAPING helps you quickly check ICMP reachability and TCP port connectivity
for a single IP address or an IP range.

Syntax:
  taping [options] <ip-address>
  taping range <start-end> [options]
  taping about

Basic usage:
  taping 192.168.1.1
  taping range 192.168.1.10-20
  taping 192.168.1.1 -p 443
  taping range 192.168.1.10-20 -p 3389

Options:
  -?, /?, -h, -help, --help
        Display this help screen

  -p, --port PORT
        Set TCP port to check.
        Example: taping 192.168.1.1 -p 443

  -t, --timeout MS
        Set timeout in milliseconds.
        Default: 700

  -c, --count COUNT
        Set number of checks.
        Default: 1
        Example: taping 192.168.1.1 -p 443 -c 5

  --loop
        Run continuously until CTRL+C.
        Example: taping 192.168.1.1 -p 443 --loop

  --up
        Show only successful results.

  --version
        Show TAPING version.

Service shortcuts:
  --http      TCP 80
  --https     TCP 443
  --ssh       TCP 22
  --rdp       TCP 3389
  --smb       TCP 445
  --zebra     TCP 9100
  --winrm     TCP 5985
  --winrms    TCP 5986

Examples:
  taping 8.8.8.8
  taping 1.1.1.1 -p 443
  taping 192.168.10.36 --rdp
  taping 192.168.110.117 --zebra
  taping range 192.168.70.160-169
  taping range 192.168.70.160-169 -p 3389
  taping range 192.168.70.160-169 -p 3389 -c 3
  taping range 192.168.70.160-169 -p 3389 --loop

Notes:
  ICMP ping does not use ports.
  TCP port mode works similar to paping.
  SNMP usually uses UDP 161, so "-p 161" checks TCP/161, not SNMP.
""".strip())


def is_valid_ip(ip):
    parts = ip.split(".")

    if len(parts) != 4:
        return False

    for part in parts:
        if not part.isdigit():
            return False

        number = int(part)

        if number < 0 or number > 255:
            return False

    return True


def parse_range(range_text):
    match = re.match(
        r"^(\d{1,3}\.\d{1,3}\.\d{1,3})\.(\d{1,3})-(\d{1,3})$",
        range_text,
    )

    if not match:
        raise ValueError("Invalid range format. Example: taping range 192.168.1.10-20")

    network_part = match.group(1)
    start = int(match.group(2))
    end = int(match.group(3))

    if start > end:
        raise ValueError("Range start cannot be greater than range end.")

    if start < 0 or end > 255:
        raise ValueError("Last octet must be between 0 and 255.")

    targets = []

    for i in range(start, end + 1):
        ip = f"{network_part}.{i}"

        if not is_valid_ip(ip):
            raise ValueError(f"Invalid IP generated: {ip}")

        targets.append(ip)

    return targets


def parse_ttl(output):
    match = re.search(r"ttl[=\s:]+(\d+)", output, re.IGNORECASE)

    if match:
        return int(match.group(1))

    return None


def parse_time_ms(output):
    patterns = [
        r"time[=<]\s*(\d+(?:\.\d+)?)\s*ms",
        r"sÃ¼re[=<]\s*(\d+(?:\.\d+)?)\s*ms",
        r"temps[=<]\s*(\d+(?:\.\d+)?)\s*ms",
    ]

    for pattern in patterns:
        match = re.search(pattern, output, re.IGNORECASE)

        if match:
            return float(match.group(1))

    lower_output = output.lower()

    if "time<1ms" in lower_output or "sÃ¼re<1ms" in lower_output:
        return 0.0

    return None


def format_ms(value):
    if value is None:
        return "0.00ms"

    return f"{value:.2f}ms"


def new_stats():
    return {
        "attempted": 0,
        "connected": 0,
        "failed": 0,
        "times": [],
    }


def add_stats(stats, success, time_ms):
    stats["attempted"] += 1

    if success:
        stats["connected"] += 1

        if time_ms is not None:
            stats["times"].append(float(time_ms))
    else:
        stats["failed"] += 1


def print_connection_statistics(stats):
    attempted = stats["attempted"]
    connected = stats["connected"]
    failed = stats["failed"]

    failed_percent = 0.00 if attempted == 0 else (failed / attempted) * 100

    if stats["times"]:
        minimum = min(stats["times"])
        maximum = max(stats["times"])
        average = sum(stats["times"]) / len(stats["times"])
    else:
        minimum = 0.00
        maximum = 0.00
        average = 0.00

    print("")
    print("Connection statistics:")
    print(
        f"        Attempted = {color(attempted, Colors.CYAN)}, "
        f"Connected = {color(connected, Colors.GREEN)}, "
        f"Failed = {color(failed, Colors.RED)} "
        f"({failed_percent:.2f}%)"
    )
    print("Approximate connection times:")
    print(
        f"        Minimum = {color(format_ms(minimum), Colors.CYAN)}, "
        f"Maximum = {color(format_ms(maximum), Colors.CYAN)}, "
        f"Average = {color(format_ms(average), Colors.CYAN)}"
    )


def icmp_ping(ip, timeout_ms, show_success_only=False):
    cmd = ["ping", "-n", "1", "-w", str(timeout_ms), ip]
    start_time = time.perf_counter()

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=(timeout_ms / 1000) + 2,
        )

        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
        output = (result.stdout or "") + "\n" + (result.stderr or "")

        ttl = parse_ttl(output)
        ping_time = parse_time_ms(output)

        if ping_time is None:
            ping_time = elapsed_ms

        if result.returncode == 0:
            ip_text = color(f"{ip:<18}", Colors.GREEN)
            status_text = color("UP", Colors.GREEN)
            time_text = color(format_ms(ping_time), Colors.CYAN)

            if ttl is not None:
                print(f"{ip_text} {status_text:<12} {time_text} TTL={ttl}")
            else:
                print(f"{ip_text} {status_text:<12} {time_text}")

            return True, ping_time

        if not show_success_only:
            ip_text = color(f"{ip:<18}", Colors.RED)
            status_text = color("DOWN", Colors.RED)
            print(f"{ip_text} {status_text:<12} No reply")

        return False, None

    except subprocess.TimeoutExpired:
        if not show_success_only:
            ip_text = color(f"{ip:<18}", Colors.RED)
            status_text = color("TIMEOUT", Colors.RED)
            print(f"{ip_text} {status_text:<12} Ping timeout")

        return False, None

    except Exception as error:
        if not show_success_only:
            ip_text = color(f"{ip:<18}", Colors.RED)
            status_text = color("ERROR", Colors.RED)
            print(f"{ip_text} {status_text:<12} {error}")

        return False, None


def tcp_ping(ip, port, timeout_ms, show_success_only=False):
    start_time = time.perf_counter()
    target_text = f"{ip}:{port}"

    try:
        with socket.create_connection((ip, port), timeout=timeout_ms / 1000):
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

            print(
                f"{color(f'{target_text:<24}', Colors.GREEN)} "
                f"{color('OPEN', Colors.GREEN):<12} "
                f"time={color(format_ms(elapsed_ms), Colors.CYAN)} "
                f"protocol={color('TCP', Colors.GREEN)} "
                f"port={color(port, Colors.GREEN)}"
            )

            return True, elapsed_ms

    except socket.timeout:
        if not show_success_only:
            print(
                f"{color(f'{target_text:<24}', Colors.RED)} "
                f"{color('TIMEOUT', Colors.RED):<12} "
                f"Connection timed out"
            )

        return False, None

    except ConnectionRefusedError:
        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

        if not show_success_only:
            print(
                f"{color(f'{target_text:<24}', Colors.RED)} "
                f"{color('CLOSED', Colors.RED):<12} "
                f"Connection refused "
                f"time={color(format_ms(elapsed_ms), Colors.CYAN)}"
            )

        return False, elapsed_ms

    except Exception as error:
        if not show_success_only:
            print(
                f"{color(f'{target_text:<24}', Colors.RED)} "
                f"{color('ERROR', Colors.RED):<12} "
                f"{error}"
            )

        return False, None


def get_service_port(args):
    selected_services = []

    for service_name, port in SERVICE_PORTS.items():
        if getattr(args, service_name):
            selected_services.append((service_name, port))

    if len(selected_services) > 1:
        raise ValueError("Only one service shortcut can be used at a time.")

    if selected_services and args.port:
        raise ValueError("Do not use -p together with a service shortcut.")

    if selected_services:
        return selected_services[0][1]

    return args.port


def print_header(target_text, port):
    if port is not None:
        print(
            f"Connecting to {color(target_text, Colors.YELLOW)} "
            f"on {color('TCP', Colors.YELLOW)} {color(port, Colors.YELLOW)}:"
        )
    else:
        print(
            f"Pinging {color(target_text, Colors.YELLOW)} "
            f"using {color('ICMP', Colors.YELLOW)}:"
        )

    print("")


def build_parser():
    parser = argparse.ArgumentParser(add_help=False)

    parser.add_argument("target", nargs="?")
    parser.add_argument("value", nargs="?")

    parser.add_argument("-?", "-h", "-help", "--help", action="store_true", dest="help_flag")

    parser.add_argument("-p", "--port", type=int)
    parser.add_argument("-t", "--timeout", type=int, default=700)
    parser.add_argument("-c", "--count", type=int, default=1)
    parser.add_argument("--loop", action="store_true")
    parser.add_argument("--up", action="store_true")
    parser.add_argument("--version", action="store_true")

    parser.add_argument("--http", action="store_true")
    parser.add_argument("--https", action="store_true")
    parser.add_argument("--ssh", action="store_true")
    parser.add_argument("--rdp", action="store_true")
    parser.add_argument("--smb", action="store_true")
    parser.add_argument("--zebra", action="store_true")
    parser.add_argument("--winrm", action="store_true")
    parser.add_argument("--winrms", action="store_true")

    return parser


def main():
    os.system("")

    parser = build_parser()
    args = parser.parse_args()

    if args.version:
        print(f"taping {VERSION}")
        return 0

    if args.help_flag or not args.target or args.target.lower() in ["help", "/?"]:
        show_help()
        return 0

    if args.target.lower() == "about":
        show_about()
        return 0

    if args.timeout < 100:
        print("Timeout must be at least 100 ms.")
        return 1

    if args.count < 1:
        print("Count must be at least 1.")
        return 1

    try:
        port = get_service_port(args)
    except ValueError as error:
        print(error)
        return 1

    if port is not None and (port < 1 or port > 65535):
        print("Port must be between 1 and 65535.")
        return 1

    try:
        if args.target.lower() == "range":
            if not args.value:
                print("Range value is missing.")
                print("Example: taping range 192.168.1.10-20")
                return 1

            targets = parse_range(args.value)
            target_text = args.value

        else:
            if args.value:
                print(f"Unexpected value: {args.value}")
                return 1

            targets = [args.target]
            target_text = args.target

            if not is_valid_ip(args.target):
                print("Invalid IP address.")
                return 1

    except ValueError as error:
        print(error)
        return 1

    stats = new_stats()
    print_header(target_text, port)

    try:
        if args.loop:
            while True:
                for ip in targets:
                    if port is not None:
                        success, time_ms = tcp_ping(ip, port, args.timeout, args.up)
                    else:
                        success, time_ms = icmp_ping(ip, args.timeout, args.up)

                    add_stats(stats, success, time_ms)

                time.sleep(1)

        else:
            for _ in range(args.count):
                for ip in targets:
                    if port is not None:
                        success, time_ms = tcp_ping(ip, port, args.timeout, args.up)
                    else:
                        success, time_ms = icmp_ping(ip, args.timeout, args.up)

                    add_stats(stats, success, time_ms)

    except KeyboardInterrupt:
        print("")
        print(color("Break received. Stopping...", Colors.YELLOW))

    finally:
        print_connection_statistics(stats)

    if stats["connected"] > 0:
        return 0

    return 2


if __name__ == "__main__":
    sys.exit(main())

