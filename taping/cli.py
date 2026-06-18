import argparse
import os
import re
import socket
import subprocess
import sys
import time


VERSION = "0.2.1"

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
    WHITE = "\033[97m"
    GRAY = "\033[90m"


def supports_color():
    return os.name == "nt" or sys.stdout.isatty()


def color(text, color_code):
    if not supports_color():
        return str(text)

    return f"{color_code}{text}{Colors.RESET}"


def show_help():
    print(f"""
TAPING v{VERSION} - Range ping and TCP port ping helper

Usage:
  taping 192.168.1.1
  taping range 192.168.1.10-20
  taping 192.168.1.1 -p 80
  taping range 192.168.1.10-20 -p 443

Paping-like loop mode:
  taping 192.168.1.1 -p 443 --loop
  taping 192.168.1.1 -p 443 -c 8

Examples:
  taping 8.8.8.8
  taping 1.1.1.1 -p 443
  taping 212.154.103.165
  taping range 212.154.103.160-166
  taping 10.138.110.117 -p 9100
  taping range 10.138.110.100-120 -p 9100
  taping 192.168.1.10 --rdp
  taping 192.168.1.10 --zebra

Options:
  -p, --port <port>      TCP port check
  -t, --timeout <ms>     Timeout in milliseconds. Default: 700
  -c, --count <count>    Repeat count. Default: 1
  --loop                 Run continuously until CTRL+C
  --up                   Show only successful results
  --version              Show version

Notes:
  Normal ping uses ICMP and has no port concept.
  -p mode tests TCP ports, similar to paping.
  SNMP 161 usually uses UDP, so -p 161 is not a correct SNMP test.
""")


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
        range_text
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
        r"süre[=<]\s*(\d+(?:\.\d+)?)\s*ms",
        r"temps[=<]\s*(\d+(?:\.\d+)?)\s*ms",
    ]

    for pattern in patterns:
        match = re.search(pattern, output, re.IGNORECASE)

        if match:
            return float(match.group(1))

    lower_output = output.lower()

    if "time<1ms" in lower_output or "süre<1ms" in lower_output:
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
        "times": []
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

    if attempted == 0:
        failed_percent = 0.00
    else:
        failed_percent = (failed / attempted) * 100

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


def icmp_ping(ip, timeout_ms):
    cmd = ["ping", "-n", "1", "-w", str(timeout_ms), ip]
    start_time = time.perf_counter()

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=(timeout_ms / 1000) + 2
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

        ip_text = color(f"{ip:<18}", Colors.RED)
        status_text = color("DOWN", Colors.RED)
        print(f"{ip_text} {status_text:<12} No reply")
        return False, None

    except subprocess.TimeoutExpired:
        ip_text = color(f"{ip:<18}", Colors.RED)
        status_text = color("TIMEOUT", Colors.RED)
        print(f"{ip_text} {status_text:<12} Ping timeout")
        return False, None

    except Exception as error:
        ip_text = color(f"{ip:<18}", Colors.RED)
        status_text = color("ERROR", Colors.RED)
        print(f"{ip_text} {status_text:<12} {error}")
        return False, None


def tcp_ping(ip, port, timeout_ms):
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
        print(
            f"{color(f'{target_text:<24}', Colors.RED)} "
            f"{color('TIMEOUT', Colors.RED):<12} "
            f"Connection timed out"
        )
        return False, None

    except ConnectionRefusedError:
        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

        print(
            f"{color(f'{target_text:<24}', Colors.RED)} "
            f"{color('CLOSED', Colors.RED):<12} "
            f"Connection refused "
            f"time={color(format_ms(elapsed_ms), Colors.CYAN)}"
        )
        return False, elapsed_ms

    except Exception as error:
        print(
            f"{color(f'{target_text:<24}', Colors.RED)} "
            f"{color('ERROR', Colors.RED):<12} "
            f"{error}"
        )
        return False, None
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
        print(
            f"{color(f'{target_text:<24}', Colors.RED)} "
            f"{color('TIMEOUT', Colors.RED):<12} "
            f"Connection timed out"
        )
        return False, None

    except ConnectionRefusedError:
        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

        print(
            f"{color(f'{target_text:<24}', Colors.RED)} "
            f"{color('CLOSED', Colors.RED):<12} "
            f"Connection refused "
            f"time={color(format_ms(elapsed_ms), Colors.CYAN)}"
        )
        return False, elapsed_ms

    except Exception as error:
        print(
            f"{color(f'{target_text:<24}', Colors.RED)} "
            f"{color('ERROR', Colors.RED):<12} "
            f"{error}"
        )
        return False, None
    start_time = time.perf_counter()

    try:
        with socket.create_connection((ip, port), timeout=timeout_ms / 1000):
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

            print(
                f"Connected to {color(ip, Colors.GREEN)}: "
                f"time={color(format_ms(elapsed_ms), Colors.CYAN)} "
                f"protocol={color('TCP', Colors.GREEN)} "
                f"port={color(port, Colors.GREEN)}"
            )

            return True, elapsed_ms

    except socket.timeout:
        print(color("Connection timed out", Colors.RED))
        return False, None

    except ConnectionRefusedError:
        print(color("Connection refused", Colors.RED))
        return False, None

    except Exception as error:
        print(color(str(error), Colors.RED))
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
    if port:
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


def main():
    os.system("")

    parser = argparse.ArgumentParser(add_help=False)

    parser.add_argument("target", nargs="?")
    parser.add_argument("value", nargs="?")
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

    args = parser.parse_args()

    if args.version:
        print(f"taping {VERSION}")
        return 0

    if not args.target or args.target.lower() in ["help", "/?", "-h", "--help"]:
        show_help()
        return 0

    if args.timeout < 100:
        print("Timeout minimum 100 ms olmalı.")
        return 1

    if args.count < 1:
        print("Count minimum 1 olmalı.")
        return 1

    try:
        port = get_service_port(args)
    except ValueError as error:
        print(error)
        return 1

    if port is not None:
        if port < 1 or port > 65535:
            print("Port 1-65535 arasında olmalı.")
            return 1

    try:
        if args.target.lower() == "range":
            if not args.value:
                print("Range değeri eksik.")
                print("Örnek: taping range 192.168.1.10-20")
                return 1

            targets = parse_range(args.value)
            target_text = args.value

        else:
            targets = [args.target]
            target_text = args.target

            if not is_valid_ip(args.target):
                print("Hatalı IP adresi.")
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
                    if port:
                        success, time_ms = tcp_ping(ip, port, args.timeout)
                    else:
                        success, time_ms = icmp_ping(ip, args.timeout)

                    add_stats(stats, success, time_ms)

                time.sleep(1)

        else:
            for _ in range(args.count):
                for ip in targets:
                    if port:
                        success, time_ms = tcp_ping(ip, port, args.timeout)
                    else:
                        success, time_ms = icmp_ping(ip, args.timeout)

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