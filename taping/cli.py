import argparse
import re
import socket
import subprocess
import sys
import time


VERSION = "0.1.0"

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


def show_help():
    print(f"""
TAPING v{VERSION} - Range ping and TCP port ping helper

Usage:
  taping 192.168.1.1
  taping range 192.168.1.10-20
  taping 192.168.1.1 -p 80
  taping range 192.168.1.10-20 -p 443

Examples:
  taping 212.154.103.165
  taping range 212.154.103.160-166
  taping 10.138.110.117 -p 9100
  taping range 10.138.110.100-120 -p 9100
  taping 192.168.1.10 --rdp
  taping 192.168.1.10 --zebra

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
        return match.group(1)

    return None


def parse_time_ms(output):
    patterns = [
        r"time[=<]\s*(\d+)\s*ms",
        r"süre[=<]\s*(\d+)\s*ms",
        r"temps[=<]\s*(\d+)\s*ms",
    ]

    for pattern in patterns:
        match = re.search(pattern, output, re.IGNORECASE)

        if match:
            return match.group(1)

    lower_output = output.lower()

    if "time<1ms" in lower_output or "süre<1ms" in lower_output:
        return "<1"

    return None


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

        elapsed_ms = round((time.perf_counter() - start_time) * 1000)
        output = (result.stdout or "") + "\n" + (result.stderr or "")

        ttl = parse_ttl(output)
        ping_time = parse_time_ms(output)

        if result.returncode == 0:
            time_text = f"{ping_time} ms" if ping_time else f"{elapsed_ms} ms"

            if ttl:
                print(f"{ip:<18} UP       {time_text} TTL={ttl}")
            else:
                print(f"{ip:<18} UP       {time_text}")

            return True

        print(f"{ip:<18} DOWN     No reply")
        return False

    except subprocess.TimeoutExpired:
        print(f"{ip:<18} TIMEOUT  Ping timeout")
        return False

    except Exception as error:
        print(f"{ip:<18} ERROR    {error}")
        return False


def tcp_ping(ip, port, timeout_ms):
    start_time = time.perf_counter()

    try:
        with socket.create_connection((ip, port), timeout=timeout_ms / 1000):
            elapsed_ms = round((time.perf_counter() - start_time) * 1000)
            print(f"{ip:<18}:{port:<5} OPEN     {elapsed_ms} ms")
            return True

    except socket.timeout:
        print(f"{ip:<18}:{port:<5} TIMEOUT  Connection timed out")
        return False

    except ConnectionRefusedError:
        print(f"{ip:<18}:{port:<5} CLOSED   Connection refused")
        return False

    except Exception as error:
        print(f"{ip:<18}:{port:<5} ERROR    {error}")
        return False


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


def main():
    parser = argparse.ArgumentParser(add_help=False)

    parser.add_argument("target", nargs="?")
    parser.add_argument("value", nargs="?")
    parser.add_argument("-p", "--port", type=int)
    parser.add_argument("-t", "--timeout", type=int, default=700)
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

        else:
            targets = [args.target]

            if not is_valid_ip(args.target):
                print("Hatalı IP adresi.")
                return 1

    except ValueError as error:
        print(error)
        return 1

    success_count = 0

    for ip in targets:
        if port:
            success = tcp_ping(ip, port, args.timeout)
        else:
            success = icmp_ping(ip, args.timeout)

        if success:
            success_count += 1

    if success_count > 0:
        return 0

    return 2


if __name__ == "__main__":
    sys.exit(main())