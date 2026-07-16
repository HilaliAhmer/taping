"""TAPING command-line interface."""

import argparse
from datetime import datetime
import os
import re
import socket
import subprocess
import sys
import time

try:
    from . import __version__
except ImportError:
    __version__ = "0.3.0"

VERSION = __version__
AUTHOR = "Selahattin Acikgoz / HilaliAhmer"
REPOSITORY = "https://github.com/HilaliAhmer/taping"

DEFAULT_SINGLE_ICMP_TIMEOUT_MS = 4000
DEFAULT_FAST_TIMEOUT_MS = 700
DEFAULT_INTERVAL_MS = 1000

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


def timestamp_now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]


def show_about():
    print(
        f"""
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
""".strip()
    )


def show_help():
    print(
        f"""
taping v{VERSION} - Range ping and TCP port ping helper

TAPING helps you quickly check ICMP reachability and TCP port connectivity
for a single IPv4 address, DNS hostname, or IPv4 range.

Syntax:
  taping [options] <ip-address-or-hostname>
  taping range <start-end> [options]
  taping about

Basic usage:
  taping 192.168.1.1
  taping google.com
  taping range 192.168.1.10-20
  taping 192.168.1.1 -p 443
  taping google.com --https
  taping range 192.168.1.10-20 -p 3389

Options:
  -?, /?, -h, -help, --help
        Display this help screen

  -p, --port PORT
        Set TCP port to check.
        Example: taping google.com -p 443

  -t, --timeout MS
        Set timeout in milliseconds.
        Default for single-target ICMP: {DEFAULT_SINGLE_ICMP_TIMEOUT_MS}
        Default for range and TCP checks: {DEFAULT_FAST_TIMEOUT_MS}

  -c, --count COUNT
        Set number of checks.
        Default: 1
        Example: taping 192.168.1.1 -c 5

  -i, --interval MS
        Delay between check rounds in milliseconds.
        Default: {DEFAULT_INTERVAL_MS}
        Example: taping 192.168.1.1 -c 10 -i 1000

  --loop
        Run continuously until CTRL+C.
        Example: taping google.com --loop

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
  taping google.com
  taping microsoft.com -c 10
  taping 1.1.1.1 -p 443
  taping google.com --https
  taping 192.168.10.36 --rdp
  taping 192.168.110.117 --zebra
  taping range 192.168.70.160-169
  taping range 192.168.70.160-169 -p 3389
  taping range 192.168.70.160-169 -p 3389 -c 3
  taping range 192.168.70.160-169 -p 3389 --loop

Notes:
  ICMP ping does not use ports.
  TCP port mode works similar to paping.
  Hostnames are resolved to IPv4 before the check starts.
  Every result line includes a local timestamp.
  SNMP usually uses UDP 161, so "-p 161" checks TCP/161, not SNMP.
""".strip()
    )


def is_valid_ip(ip):
    parts = ip.split(".")

    if len(parts) != 4:
        return False

    for part in parts:
        if not part.isdigit():
            return False

        if not 0 <= int(part) <= 255:
            return False

    return True


def resolve_target(target):
    target = target.strip()

    if not target:
        raise ValueError("Target cannot be empty.")

    if is_valid_ip(target):
        return target

    if re.fullmatch(r"[0-9.]+", target):
        raise ValueError(f"Invalid IPv4 address: {target}")

    try:
        results = socket.getaddrinfo(
            target,
            None,
            family=socket.AF_INET,
            type=socket.SOCK_STREAM,
        )

    except socket.gaierror as error:
        raise ValueError(
            f"Could not resolve hostname: {target}"
        ) from error

    for result in results:
        resolved_ip = result[4][0]

        if is_valid_ip(resolved_ip):
            return resolved_ip

    raise ValueError(
        f"No IPv4 address found for hostname: {target}"
    )


def format_target_display(target, resolved_ip):
    if target == resolved_ip:
        return target

    return f"{target} [{resolved_ip}]"


def parse_range(range_text):
    match = re.match(
        r"^(\d{1,3}\.\d{1,3}\.\d{1,3})\.(\d{1,3})-(\d{1,3})$",
        range_text,
    )

    if not match:
        raise ValueError(
            "Invalid range format. "
            "Example: taping range 192.168.1.10-20"
        )

    network_part = match.group(1)
    start = int(match.group(2))
    end = int(match.group(3))

    if start > end:
        raise ValueError(
            "Range start cannot be greater than range end."
        )

    if start < 0 or end > 255:
        raise ValueError(
            "Last octet must be between 0 and 255."
        )

    targets = []

    for last_octet in range(start, end + 1):
        ip = f"{network_part}.{last_octet}"

        if not is_valid_ip(ip):
            raise ValueError(
                f"Invalid IP generated: {ip}"
            )

        targets.append(ip)

    return targets


def parse_ttl(output):
    match = re.search(
        r"ttl[=\s:]+(\d+)",
        output,
        re.IGNORECASE,
    )

    if match:
        return int(match.group(1))

    return None


def parse_time_ms(output):
    patterns = [
        r"time[=<]\s*(\d+(?:\.\d+)?)\s*ms",
        r"süre[=<]\s*(\d+(?:\.\d+)?)\s*ms",
        r"temps[=<]\s*(\d+(?:\.\d+)?)\s*ms",
        r"zeit[=<]\s*(\d+(?:\.\d+)?)\s*ms",
        r"tiempo[=<]\s*(\d+(?:\.\d+)?)\s*ms",
        r"tempo[=<]\s*(\d+(?:\.\d+)?)\s*ms",
    ]

    for pattern in patterns:
        match = re.search(
            pattern,
            output,
            re.IGNORECASE,
        )

        if match:
            return float(match.group(1))

    lower_output = output.lower()

    less_than_one_patterns = (
        "time<1ms",
        "süre<1ms",
        "temps<1ms",
        "zeit<1ms",
        "tiempo<1ms",
        "tempo<1ms",
    )

    if any(
        pattern in lower_output
        for pattern in less_than_one_patterns
    ):
        return 0.0

    return None


def is_icmp_success(output):
    failure_messages = (
        "ttl expired",
        "expired in transit",
        "destination host unreachable",
        "destination net unreachable",
        "request timed out",
        "timed out",
    )

    payload_patterns = (
        "bytes=",
        "bytes<",
        "bayt=",
        "bayt<",
        "octets=",
        "octets<",
    )

    for line in output.splitlines():
        lower_line = line.lower()

        if any(
            message in lower_line
            for message in failure_messages
        ):
            continue

        has_ttl = re.search(
            r"ttl[=\s:]+\d+",
            lower_line,
        ) is not None

        has_payload = any(
            payload in lower_line
            for payload in payload_patterns
        )

        if has_ttl and has_payload:
            return True

    return False


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
            stats["times"].append(
                float(time_ms)
            )

    else:
        stats["failed"] += 1


def print_connection_statistics(stats):
    attempted = stats["attempted"]
    connected = stats["connected"]
    failed = stats["failed"]

    failed_percent = (
        0.00
        if attempted == 0
        else (failed / attempted) * 100
    )

    if stats["times"]:
        minimum = min(stats["times"])
        maximum = max(stats["times"])
        average = (
            sum(stats["times"])
            / len(stats["times"])
        )

    else:
        minimum = 0.00
        maximum = 0.00
        average = 0.00

    print("")
    print("Connection statistics:")
    print(
        f"        Attempted = "
        f"{color(attempted, Colors.CYAN)}, "
        f"Connected = "
        f"{color(connected, Colors.GREEN)}, "
        f"Failed = "
        f"{color(failed, Colors.RED)} "
        f"({failed_percent:.2f}%)"
    )

    print("Approximate connection times:")
    print(
        f"        Minimum = "
        f"{color(format_ms(minimum), Colors.CYAN)}, "
        f"Maximum = "
        f"{color(format_ms(maximum), Colors.CYAN)}, "
        f"Average = "
        f"{color(format_ms(average), Colors.CYAN)}"
    )


def print_result(
    target,
    status,
    message,
    successful=False,
):
    line_color = (
        Colors.GREEN
        if successful
        else Colors.RED
    )

    timestamp_text = color(
        timestamp_now(),
        Colors.GRAY,
    )

    target_text = color(
        f"{target:<42}",
        line_color,
    )

    status_text = color(
        f"{status:<10}",
        line_color,
    )

    print(
        f"{timestamp_text}  "
        f"{target_text} "
        f"{status_text} "
        f"{message}"
    )


def icmp_ping(
    ip,
    display_target,
    timeout_ms,
    show_success_only=False,
):
    cmd = [
        "ping",
        "-4",
        "-n",
        "1",
        "-w",
        str(timeout_ms),
        ip,
    ]

    start_time = time.perf_counter()

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            errors="replace",
            timeout=(timeout_ms / 1000) + 3,
        )

        elapsed_ms = round(
            (
                time.perf_counter()
                - start_time
            ) * 1000,
            2,
        )

        output = (
            (result.stdout or "")
            + "\n"
            + (result.stderr or "")
        )

        success = (
            result.returncode == 0
            and is_icmp_success(output)
        )

        if success:
            ttl = parse_ttl(output)
            ping_time = parse_time_ms(output)

            if ping_time is None:
                ping_time = elapsed_ms

            message = color(
                format_ms(ping_time),
                Colors.CYAN,
            )

            if ttl is not None:
                message += f" TTL={ttl}"

            print_result(
                display_target,
                "UP",
                message,
                successful=True,
            )

            return True, ping_time

        if not show_success_only:
            print_result(
                display_target,
                "DOWN",
                "No reply",
            )

        return False, None

    except subprocess.TimeoutExpired:
        if not show_success_only:
            print_result(
                display_target,
                "TIMEOUT",
                "Ping process timeout",
            )

        return False, None

    except Exception as error:
        if not show_success_only:
            print_result(
                display_target,
                "ERROR",
                str(error),
            )

        return False, None


def tcp_ping(
    ip,
    display_target,
    port,
    timeout_ms,
    show_success_only=False,
):
    start_time = time.perf_counter()
    target_text = f"{display_target}:{port}"

    try:
        with socket.create_connection(
            (ip, port),
            timeout=timeout_ms / 1000,
        ):
            elapsed_ms = round(
                (
                    time.perf_counter()
                    - start_time
                ) * 1000,
                2,
            )

            message = (
                f"time="
                f"{color(format_ms(elapsed_ms), Colors.CYAN)} "
                f"protocol="
                f"{color('TCP', Colors.GREEN)} "
                f"port="
                f"{color(port, Colors.GREEN)}"
            )

            print_result(
                target_text,
                "OPEN",
                message,
                successful=True,
            )

            return True, elapsed_ms

    except socket.timeout:
        if not show_success_only:
            print_result(
                target_text,
                "TIMEOUT",
                "Connection timed out",
            )

        return False, None

    except ConnectionRefusedError:
        elapsed_ms = round(
            (
                time.perf_counter()
                - start_time
            ) * 1000,
            2,
        )

        if not show_success_only:
            message = (
                f"Connection refused "
                f"time="
                f"{color(format_ms(elapsed_ms), Colors.CYAN)}"
            )

            print_result(
                target_text,
                "CLOSED",
                message,
            )

        return False, elapsed_ms

    except Exception as error:
        if not show_success_only:
            print_result(
                target_text,
                "ERROR",
                str(error),
            )

        return False, None


def get_service_port(args):
    selected_services = []

    for service_name, port in SERVICE_PORTS.items():
        if getattr(args, service_name):
            selected_services.append(
                (service_name, port)
            )

    if len(selected_services) > 1:
        raise ValueError(
            "Only one service shortcut "
            "can be used at a time."
        )

    if selected_services and args.port:
        raise ValueError(
            "Do not use -p together "
            "with a service shortcut."
        )

    if selected_services:
        return selected_services[0][1]

    return args.port


def print_header(target_text, port):
    if port is not None:
        print(
            f"Connecting to "
            f"{color(target_text, Colors.YELLOW)} "
            f"on "
            f"{color('TCP', Colors.YELLOW)} "
            f"{color(port, Colors.YELLOW)}:"
        )

    else:
        print(
            f"Pinging "
            f"{color(target_text, Colors.YELLOW)} "
            f"using "
            f"{color('ICMP', Colors.YELLOW)}:"
        )

    print("")


def build_parser():
    parser = argparse.ArgumentParser(
        add_help=False
    )

    parser.add_argument(
        "target",
        nargs="?",
    )

    parser.add_argument(
        "value",
        nargs="?",
    )

    parser.add_argument(
        "-?",
        "-h",
        "-help",
        "--help",
        action="store_true",
        dest="help_flag",
    )

    parser.add_argument(
        "-p",
        "--port",
        type=int,
    )

    parser.add_argument(
        "-t",
        "--timeout",
        type=int,
    )

    parser.add_argument(
        "-c",
        "--count",
        type=int,
        default=1,
    )

    parser.add_argument(
        "-i",
        "--interval",
        type=int,
        default=DEFAULT_INTERVAL_MS,
    )

    parser.add_argument(
        "--loop",
        action="store_true",
    )

    parser.add_argument(
        "--up",
        action="store_true",
    )

    parser.add_argument(
        "--version",
        action="store_true",
    )

    parser.add_argument(
        "--http",
        action="store_true",
    )

    parser.add_argument(
        "--https",
        action="store_true",
    )

    parser.add_argument(
        "--ssh",
        action="store_true",
    )

    parser.add_argument(
        "--rdp",
        action="store_true",
    )

    parser.add_argument(
        "--smb",
        action="store_true",
    )

    parser.add_argument(
        "--zebra",
        action="store_true",
    )

    parser.add_argument(
        "--winrm",
        action="store_true",
    )

    parser.add_argument(
        "--winrms",
        action="store_true",
    )

    return parser


def get_timeout_ms(
    args,
    is_range,
    port,
):
    if args.timeout is not None:
        return args.timeout

    if not is_range and port is None:
        return DEFAULT_SINGLE_ICMP_TIMEOUT_MS

    return DEFAULT_FAST_TIMEOUT_MS


def sleep_between_rounds(interval_ms):
    if interval_ms > 0:
        time.sleep(interval_ms / 1000)


def main():
    os.system("")

    parser = build_parser()
    args = parser.parse_args()

    if args.version:
        print(f"taping {VERSION}")
        return 0

    if (
        args.help_flag
        or not args.target
        or args.target.lower()
        in ["help", "/?"]
    ):
        show_help()
        return 0

    if args.target.lower() == "about":
        show_about()
        return 0

    if (
        args.timeout is not None
        and args.timeout < 100
    ):
        print(
            "Timeout must be at least 100 ms."
        )

        return 1

    if args.count < 1:
        print(
            "Count must be at least 1."
        )

        return 1

    if args.interval < 0:
        print(
            "Interval cannot be negative."
        )

        return 1

    try:
        port = get_service_port(args)

    except ValueError as error:
        print(error)
        return 1

    if (
        port is not None
        and not 1 <= port <= 65535
    ):
        print(
            "Port must be between 1 and 65535."
        )

        return 1

    is_range = (
        args.target.lower() == "range"
    )

    if is_range:
        if not args.value:
            print(
                "Range value is missing."
            )

            print(
                "Example: "
                "taping range 192.168.1.10-20"
            )

            return 1

        target_text = args.value

        try:
            raw_targets = parse_range(
                args.value
            )

        except ValueError as error:
            print(error)
            return 1

    else:
        if args.value:
            print(
                f"Unexpected value: "
                f"{args.value}"
            )

            return 1

        raw_targets = [args.target]
        target_text = args.target

    stats = new_stats()
    resolved_targets = []

    try:
        for target in raw_targets:
            resolved_ip = resolve_target(
                target
            )

            display_target = (
                format_target_display(
                    target,
                    resolved_ip,
                )
            )

            resolved_targets.append(
                (
                    resolved_ip,
                    display_target,
                )
            )

    except ValueError as error:
        print_header(
            target_text,
            port,
        )

        if not args.up:
            print_result(
                target_text,
                "DNS_FAILED",
                str(error),
            )

        add_stats(
            stats,
            False,
            None,
        )

        if args.up:
            print(
                "No successful results found."
            )

        print_connection_statistics(
            stats
        )

        return 2

    if not is_range:
        target_text = (
            resolved_targets[0][1]
        )

    timeout_ms = get_timeout_ms(
        args,
        is_range,
        port,
    )

    print_header(
        target_text,
        port,
    )

    def run_check_round():
        for ip, display_target in resolved_targets:
            if port is not None:
                success, time_ms = tcp_ping(
                    ip,
                    display_target,
                    port,
                    timeout_ms,
                    args.up,
                )

            else:
                success, time_ms = icmp_ping(
                    ip,
                    display_target,
                    timeout_ms,
                    args.up,
                )

            add_stats(
                stats,
                success,
                time_ms,
            )

    try:
        if args.loop:
            while True:
                run_check_round()

                sleep_between_rounds(
                    args.interval
                )

        else:
            for round_number in range(
                args.count
            ):
                run_check_round()

                if (
                    round_number
                    < args.count - 1
                ):
                    sleep_between_rounds(
                        args.interval
                    )

    except KeyboardInterrupt:
        print("")

        print(
            color(
                "Break received. Stopping...",
                Colors.YELLOW,
            )
        )

    finally:
        if (
            args.up
            and stats["connected"] == 0
        ):
            print(
                "No successful results found."
            )

        print_connection_statistics(
            stats
        )

    if stats["connected"] > 0:
        return 0

    return 2


if __name__ == "__main__":
    sys.exit(main())