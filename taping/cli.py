"""TAPING command-line interface: ICMP, TCP port checks and traceroute.

Based on the public HilaliAhmer/taping main branch (v0.3.1).
Copyright (c) 2026 Selahattin Açıkgöz. MIT License.
"""

import argparse
import ctypes
from ctypes import wintypes
from functools import lru_cache
import ipaddress
from concurrent.futures import ThreadPoolExecutor
import errno
from datetime import datetime
import os
import re
import select
import socket
import struct
import subprocess
import sys
import time

from taping import __version__


VERSION = __version__
AUTHOR = "Selahattin Acikgoz / HilaliAhmer"
REPOSITORY = "https://github.com/HilaliAhmer/taping"
DEFAULT_TIMEOUT_MS = 4000
DEFAULT_INTERVAL_MS = 1000
MAX_TRACE_HOPS = 30
MAX_TCP_PORT = 65535
MIN_TIMEOUT_MS = 100

# Range scans: retry only hosts that did not answer. Fast hosts never wait.
# First probes are short; the final probe gets the full -w timeout.
RANGE_PROBE_TIMEOUTS_MS = (800, 1200, 2000, None)
RANGE_RETRY_DELAYS_MS = (250, 350, 500)
RANGE_MAX_WORKERS = 8


class Colors:
    RESET = "\033[0m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    GRAY = "\033[90m"


_WINDOWS_ANSI_ENABLED = False


def enable_console_colors():
    """Enable ANSI on Windows terminals without launching a shell."""
    global _WINDOWS_ANSI_ENABLED
    if os.name != "nt" or not sys.stdout.isatty():
        return
    try:
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.GetStdHandle.argtypes = [wintypes.DWORD]
        kernel.GetStdHandle.restype = wintypes.HANDLE
        kernel.GetConsoleMode.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
        kernel.GetConsoleMode.restype = wintypes.BOOL
        kernel.SetConsoleMode.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        kernel.SetConsoleMode.restype = wintypes.BOOL
        handle = kernel.GetStdHandle(0xFFFFFFF5)  # STD_OUTPUT_HANDLE (-11)
        mode = wintypes.DWORD()
        if kernel.GetConsoleMode(handle, ctypes.byref(mode)):
            _WINDOWS_ANSI_ENABLED = bool(
                kernel.SetConsoleMode(handle, mode.value | 0x0004)
            )
    except (OSError, AttributeError):
        _WINDOWS_ANSI_ENABLED = False


def supports_color():
    if "NO_COLOR" in os.environ or not sys.stdout.isatty():
        return False
    return os.name != "nt" or _WINDOWS_ANSI_ENABLED


def color(text, code):
    if not supports_color():
        return str(text)
    return f"{code}{text}{Colors.RESET}"


def timestamp_now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]


def show_about():
    print(
        f"TAPING v{VERSION}\n"
        "ICMP ping, TCP port test and traceroute.\n\n"
        f"Author: {AUTHOR}\n"
        f"Project: {REPOSITORY}\n"
        "License: MIT\n"
        "Copyright (c) 2026 Selahattin Acikgoz"
    )


def show_help():
    print(f"""taping v{VERSION} - Ping, TCP port test and traceroute

Usage:
  taping <ip-or-hostname> [options]
  taping range <start-end> [options]
  taping trace <ip-or-hostname> [-p PORT] [-w MS]
  taping about

Options:
  -p, --port PORT     Test a TCP port instead of ICMP (1-65535)
  -t, --loop          Repeat until CTRL+C
  -w, --timeout MS    Timeout in milliseconds (default: {DEFAULT_TIMEOUT_MS})
  -c, --count COUNT   Number of checks (default: 1)
  -?, -h, --help      Show this help

Examples:
  taping 8.8.8.8
  taping google.com -t
  taping 8.8.8.8 -c 5 -w 2000
  taping google.com -p 443
  taping range 192.168.1.10-20
  taping range 192.168.1.10-20 -p 3389
  taping trace 8.8.8.8
  taping trace 10.6.106.50 -p 443

Notes:
  -p checks TCP (not UDP). Without -p, ping uses ICMP.
  Range ICMP automatically retries missed replies (up to 4 attempts per IP).
  TCP traceroute requires Administrator on Windows (root/CAP_NET_RAW on Linux).
  IPv4 only. CTRL+C stops continuous ping.
""".rstrip())


def is_valid_ip(ip):
    try:
        ipaddress.IPv4Address(ip)
    except (ipaddress.AddressValueError, ValueError, TypeError):
        return False
    return True


def resolve_target(target):
    target = target.strip()
    if not target:
        raise ValueError("Target cannot be empty.")
    if is_valid_ip(target):
        return target
    if all(char.isdigit() or char == "." for char in target):
        raise ValueError(f"Invalid IPv4 address: {target}")
    try:
        results = socket.getaddrinfo(target, None, family=socket.AF_INET,
                                      type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise ValueError(f"Could not resolve hostname: {target}") from exc
    for result in results:
        ip = result[4][0]
        if is_valid_ip(ip):
            return ip
    raise ValueError(f"No IPv4 address found for hostname: {target}")


def format_target_display(target, ip):
    return target if target == ip else f"{target} [{ip}]"


def parse_range(value):
    match = re.fullmatch(r"([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})\.([0-9]{1,3})-([0-9]{1,3})", value)
    if not match:
        raise ValueError("Invalid range format. Example: taping range 192.168.1.10-20")
    prefix, start_text, end_text = match.groups()
    start, end = int(start_text), int(end_text)
    if start > end:
        raise ValueError("Range start cannot be greater than range end.")
    if start < 0 or end > 255:
        raise ValueError("Last octet must be between 0 and 255.")
    result = [f"{prefix}.{last}" for last in range(start, end + 1)]
    if not all(is_valid_ip(ip) for ip in result):
        raise ValueError("Invalid IP address in range.")
    return result


def parse_ttl(output):
    match = re.search(r"ttl[=\s:]+(\d+)", output, re.IGNORECASE)
    return int(match.group(1)) if match else None


def parse_time_ms(output):
    for pattern in (
        r"time[=<]\s*(\d+(?:\.\d+)?)\s*ms",
        r"süre[=<]\s*(\d+(?:\.\d+)?)\s*ms",
        r"temps[=<]\s*(\d+(?:\.\d+)?)\s*ms",
        r"zeit[=<]\s*(\d+(?:\.\d+)?)\s*ms",
        r"tiempo[=<]\s*(\d+(?:\.\d+)?)\s*ms",
        r"tempo[=<]\s*(\d+(?:\.\d+)?)\s*ms",
    ):
        match = re.search(pattern, output, re.IGNORECASE)
        if match:
            return float(match.group(1))
    if re.search(r"(?:time|süre|temps|zeit|tiempo|tempo)\s*<\s*1\s*ms", output, re.IGNORECASE):
        return 0.0
    return None


def format_ms(value):
    return "0.00ms" if value is None else f"{value:.2f}ms"


def new_stats():
    return {"attempted": 0, "connected": 0, "failed": 0, "times": []}


def add_stats(stats, success, duration_ms):
    stats["attempted"] += 1
    if success:
        stats["connected"] += 1
        if duration_ms is not None:
            stats["times"].append(float(duration_ms))
    else:
        stats["failed"] += 1


def print_connection_statistics(stats):
    attempted, connected, failed = (stats[k] for k in ("attempted", "connected", "failed"))
    fail_percent = failed / attempted * 100 if attempted else 0
    times = stats["times"]
    low, high, mean = (min(times), max(times), sum(times) / len(times)) if times else (0, 0, 0)
    print("\nConnection statistics:")
    print(f"        Attempted = {color(attempted, Colors.CYAN)}, "
          f"Connected = {color(connected, Colors.GREEN)}, "
          f"Failed = {color(failed, Colors.RED)} ({fail_percent:.2f}%)")
    print("Approximate connection times:")
    print(f"        Minimum = {color(format_ms(low), Colors.CYAN)}, "
          f"Maximum = {color(format_ms(high), Colors.CYAN)}, "
          f"Average = {color(format_ms(mean), Colors.CYAN)}")


def print_result(target, status, message, successful=False):
    display_color = Colors.GREEN if successful else Colors.RED
    print(f"{color(timestamp_now(), Colors.GRAY)}  "
          f"{color(f'{target:<42}', display_color)} "
          f"{color(f'{status:<10}', display_color)} {message}")


class _IpOptionInformation(ctypes.Structure):
    _fields_ = [
        ("Ttl", ctypes.c_ubyte),
        ("Tos", ctypes.c_ubyte),
        ("Flags", ctypes.c_ubyte),
        ("OptionsSize", ctypes.c_ubyte),
        ("OptionsData", ctypes.c_void_p),
    ]


class _IcmpEchoReply(ctypes.Structure):
    _fields_ = [
        ("Address", wintypes.ULONG),
        ("Status", wintypes.ULONG),
        ("RoundTripTime", wintypes.ULONG),
        ("DataSize", wintypes.USHORT),
        ("Reserved", wintypes.USHORT),
        ("Data", ctypes.c_void_p),
        ("Options", _IpOptionInformation),
    ]


@lru_cache(maxsize=1)
def _windows_icmp_api():
    """Load built-in Windows ICMP API (no external Python packages)."""
    library = ctypes.WinDLL("iphlpapi.dll", use_last_error=True)
    create = library.IcmpCreateFile
    create.restype = wintypes.HANDLE
    send = library.IcmpSendEcho
    send.argtypes = [
        wintypes.HANDLE, wintypes.ULONG, ctypes.c_void_p, wintypes.WORD,
        ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD,
    ]
    send.restype = wintypes.DWORD
    close = library.IcmpCloseHandle
    close.argtypes = [wintypes.HANDLE]
    close.restype = wintypes.BOOL
    return create, send, close


def _probe_icmp_windows(ip, timeout_ms):
    """ICMP via IcmpSendEcho: independent of Windows UI language/code page."""
    create, send, close = _windows_icmp_api()
    handle = create()
    if handle in (None, ctypes.c_void_p(-1).value):
        return "ERROR", None, None, "IcmpCreateFile failed"
    payload = ctypes.create_string_buffer(b"taping-ping")
    buffer = ctypes.create_string_buffer(
        ctypes.sizeof(_IcmpEchoReply) + len(payload) + 32
    )
    destination = int.from_bytes(socket.inet_aton(ip), sys.byteorder)
    try:
        count = send(
            handle, destination, ctypes.cast(payload, ctypes.c_void_p),
            len(payload) - 1, None, ctypes.cast(buffer, ctypes.c_void_p),
            len(buffer), timeout_ms,
        )
        if count:
            reply = ctypes.cast(buffer, ctypes.POINTER(_IcmpEchoReply)).contents
            if reply.Status == 0:  # IP_SUCCESS
                return "UP", float(reply.RoundTripTime), int(reply.Options.Ttl), ""
            return "DOWN", None, None, f"ICMP status {reply.Status}"
        error = ctypes.get_last_error()
        if error in (0, 11010):  # IP_REQ_TIMED_OUT
            return "DOWN", None, None, "No reply"
        if error in (11002, 11003, 11004, 11005, 11012, 11013):
            return "DOWN", None, None, f"ICMP status {error}"
        return "ERROR", None, None, f"IcmpSendEcho failed (error {error})"
    finally:
        close(handle)


def probe_icmp(ip, timeout_ms):
    """Return (status, latency_ms, ttl, message), without printing."""
    if os.name == "nt":
        try:
            return _probe_icmp_windows(ip, timeout_ms)
        except (OSError, AttributeError) as exc:
            return "ERROR", None, None, f"Windows ICMP API error: {exc}"

    # Linux/other: rely on ping's exit status, not translated output strings.
    command = [
        "ping", "-4", "-n", "-c", "1", "-W",
        f"{timeout_ms / 1000:g}", ip,
    ]
    started = time.perf_counter()
    try:
        result = subprocess.run(
            command, capture_output=True, text=True, errors="replace",
            timeout=(timeout_ms / 1000) + 3,
        )
    except subprocess.TimeoutExpired:
        return "TIMEOUT", None, None, "Ping process timeout"
    except OSError as exc:
        return "ERROR", None, None, str(exc)
    if result.returncode == 0:
        output = result.stdout or ""
        latency = parse_time_ms(output)
        if latency is None:
            latency = round((time.perf_counter() - started) * 1000, 2)
        return "UP", latency, parse_ttl(output), ""
    return "DOWN", None, None, "No reply"


def show_icmp_probe_result(display_target, status, duration, ttl, message, attempts=1):
    if status == "UP":
        detail = color(format_ms(duration), Colors.CYAN)
        if ttl is not None:
            detail += f" TTL={ttl}"
        if attempts > 1:
            detail += f" (recovered on attempt {attempts}/{len(RANGE_PROBE_TIMEOUTS_MS)})"
        print_result(display_target, "UP", detail, successful=True)
    else:
        if attempts > 1:
            message += f" (after {attempts} attempts)"
        print_result(display_target, status, message)


def icmp_ping(ip, display_target, timeout_ms):
    """Unchanged single-host semantics: one echo per requested ping."""
    status, duration, ttl, message = probe_icmp(ip, timeout_ms)
    show_icmp_probe_result(display_target, status, duration, ttl, message)
    return status == "UP", duration


def probe_icmp_range_host(ip, timeout_ms):
    """Probe a range IP up to four times, stopping at the first Echo Reply.

    Probe 1 uses up to 800ms, then up to 1200ms and 2000ms. The last
    attempt honors the full requested timeout. Only unsuccessful attempts
    incur the small delay; an answering host is returned immediately.
    """
    for index, short_timeout in enumerate(RANGE_PROBE_TIMEOUTS_MS):
        if index:
            time.sleep(RANGE_RETRY_DELAYS_MS[index - 1] / 1000)
        effective_timeout = min(timeout_ms, short_timeout) if short_timeout else timeout_ms
        status, duration, ttl, message = probe_icmp(ip, effective_timeout)
        if status in ("UP", "ERROR"):
            return status, duration, ttl, message, index + 1
    return status, duration, ttl, message, len(RANGE_PROBE_TIMEOUTS_MS)


def tcp_ping(ip, display_target, port, timeout_ms):
    started = time.perf_counter()
    target = f"{display_target}:{port}"
    try:
        with socket.create_connection((ip, port), timeout=timeout_ms / 1000):
            duration = round((time.perf_counter() - started) * 1000, 2)
            message = (f"time={color(format_ms(duration), Colors.CYAN)} "
                       f"protocol={color('TCP', Colors.GREEN)} "
                       f"port={color(port, Colors.GREEN)}")
            print_result(target, "OPEN", message, successful=True)
            return True, duration
    except socket.timeout:
        print_result(target, "TIMEOUT", "Connection timed out")
    except ConnectionRefusedError:
        elapsed = round((time.perf_counter() - started) * 1000, 2)
        print_result(target, "CLOSED", f"Connection refused time={color(format_ms(elapsed), Colors.CYAN)}")
        return False, elapsed
    except OSError as exc:
        print_result(target, "ERROR", str(exc))
    return False, None


def print_header(target_text, port):
    if port is None:
        print(f"Pinging {color(target_text, Colors.YELLOW)} using "
              f"{color('ICMP', Colors.YELLOW)}:\n")
    else:
        print(f"Connecting to {color(target_text, Colors.YELLOW)} on "
              f"{color('TCP', Colors.YELLOW)} {color(port, Colors.YELLOW)}:\n")



def trace_route(ip, display_target, port, timeout_ms):
    """Run native ICMP trace or TCP trace, returning a command success flag."""
    if port is None:
        return icmp_trace(ip, display_target, timeout_ms)
    return tcp_trace(ip, display_target, port, timeout_ms)


def icmp_trace(ip, display_target, timeout_ms):
    """Stream native traceroute; confirm the destination appears in a hop line."""
    if os.name == "nt":
        command = ["tracert", "-4", "-d", "-h", str(MAX_TRACE_HOPS),
                   "-w", str(timeout_ms), ip]
    else:
        command = ["traceroute", "-4", "-n", "-I", "-m", str(MAX_TRACE_HOPS),
                   "-w", str(timeout_ms / 1000), ip]
    try:
        found_destination = False
        with subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, errors="replace",
        ) as process:
            for line in process.stdout:
                print(line, end="")
                # Do not count the command's heading (which contains the target).
                if re.match(r"^\s*\d+\s+", line) and re.search(
                    r"(?<![\d.])" + re.escape(ip) + r"(?![\d.])", line
                ):
                    found_destination = True
            return_code = process.wait()
        if return_code != 0:
            return 1  # traceroute executable reported an execution error
        return 0 if found_destination else 2
    except FileNotFoundError:
        print("Traceroute command not found. Install the system traceroute utility.", file=sys.stderr)
    except KeyboardInterrupt:
        print("\nTrace interrupted.", file=sys.stderr)
    except OSError as exc:
        print(f"Traceroute error: {exc}", file=sys.stderr)
    return 1


def local_ipv4_for_destination(ip, port):
    """Find the local IPv4 chosen by the routing table (UDP connect sends no data)."""
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.connect((ip, port))
        return sock.getsockname()[0]


def open_icmp_receiver(local_ip):
    """Start capturing ICMP on Windows and Linux; caller must close receiver."""
    receiver = None
    try:
        if os.name == "nt":
            # A plain IPPROTO_ICMP receiver can miss Windows TTL-exceeded replies.
            # RCVALL captures the reply's IPv4 packet for strict probe matching.
            receiver = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_IP)
            receiver.bind((local_ip, 0))
            receiver.ioctl(socket.SIO_RCVALL, socket.RCVALL_ON)
        else:
            receiver = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
            receiver.bind((local_ip, 0))
        receiver.setblocking(False)
        return receiver
    except OSError:
        if receiver is not None:
            receiver.close()
        raise


def close_icmp_receiver(receiver):
    if receiver is None:
        return
    try:
        if os.name == "nt":
            receiver.ioctl(socket.SIO_RCVALL, socket.RCVALL_OFF)
    except OSError:
        pass
    finally:
        receiver.close()


def decode_icmp_reply(packet, destination_ip, source_port, destination_port):
    """Parse only ICMP errors containing *this exact TCP probe*.

    Returns (kind, code) or None. Verify IPv4 headers, protocol, destination,
    and embedded TCP ports to reject unrelated network traffic.
    """
    if len(packet) < 20 or packet[0] >> 4 != 4:
        return None
    outer_len = (packet[0] & 0x0F) * 4
    if outer_len < 20 or len(packet) < outer_len + 8 + 20 + 8:
        return None
    if packet[9] != socket.IPPROTO_ICMP:
        return None
    icmp_type, icmp_code = packet[outer_len], packet[outer_len + 1]
    if icmp_type not in (3, 11):
        return None
    embedded_start = outer_len + 8
    if packet[embedded_start] >> 4 != 4:
        return None
    embedded_len = (packet[embedded_start] & 0x0F) * 4
    if embedded_len < 20 or len(packet) < embedded_start + embedded_len + 4:
        return None
    if packet[embedded_start + 9] != socket.IPPROTO_TCP:
        return None
    if socket.inet_ntoa(packet[embedded_start + 16: embedded_start + 20]) != destination_ip:
        return None
    offset = embedded_start + embedded_len
    probe_source_port, probe_dest_port = struct.unpack_from("!HH", packet, offset)
    if probe_source_port != source_port or probe_dest_port != destination_port:
        return None
    if icmp_type == 11 and icmp_code == 0:
        return "TTL_EXCEEDED", icmp_code
    if icmp_type == 3:
        return "UNREACHABLE", icmp_code
    return None


def probe_tcp_hop(receiver, local_ip, destination_ip, destination_port, ttl, timeout_seconds):
    """One TCP connection attempt with a low TTL.

    Returns (hop_ip or None, rtt_ms or None, status).
    A TCP connection or refusal from the target means the target was reached.
    """
    start = time.perf_counter()
    deadline = start + timeout_seconds
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP) as probe:
        probe.setsockopt(socket.IPPROTO_IP, socket.IP_TTL, ttl)
        probe.bind((local_ip, 0))
        source_port = probe.getsockname()[1]
        probe.setblocking(False)
        result = probe.connect_ex((destination_ip, destination_port))
        if result == 0:
            return destination_ip, (time.perf_counter() - start) * 1000, "OPEN"
        if result in (errno.ECONNREFUSED, 10061):
            return destination_ip, (time.perf_counter() - start) * 1000, "CLOSED"
        in_progress = {errno.EINPROGRESS, errno.EWOULDBLOCK, errno.EALREADY, 10035, 10036, 10037}
        if result not in in_progress:
            return None, None, f"SOCKET_ERROR:{result}"

        watch_write = True
        while True:
            remaining = deadline - time.perf_counter()
            if remaining <= 0:
                return None, None, "TIMEOUT"
            # The TCP socket may be writable before a router's ICMP reply arrives.
            # For non-terminal SO_ERROR values, keep listening until timeout.
            readable, writable, _ = select.select(
                [receiver], [probe] if watch_write else [], [], remaining
            )
            if readable:
                try:
                    payload, sender = receiver.recvfrom(65535)
                except BlockingIOError:
                    continue
                decoded = decode_icmp_reply(payload, destination_ip, source_port, destination_port)
                if decoded is not None:
                    elapsed = round((time.perf_counter() - start) * 1000, 2)
                    kind, code = decoded
                    return sender[0], elapsed, kind if kind == "TTL_EXCEEDED" else f"UNREACHABLE:{code}"
            if writable:
                err = probe.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)
                if err == 0:
                    elapsed = round((time.perf_counter() - start) * 1000, 2)
                    return destination_ip, elapsed, "OPEN"
                if err in (errno.ECONNREFUSED, 10061):
                    elapsed = round((time.perf_counter() - start) * 1000, 2)
                    return destination_ip, elapsed, "CLOSED"
                watch_write = False


def tcp_trace(ip, display_target, port, timeout_ms):
    print(f"Tracing route to {display_target} using TCP/{port} (max {MAX_TRACE_HOPS} hops):\n")
    print("Hop  IP address          Time       Status")
    receiver = None
    try:
        local_ip = local_ipv4_for_destination(ip, port)
        receiver = open_icmp_receiver(local_ip)
        for hop in range(1, MAX_TRACE_HOPS + 1):
            address, rtt_ms, status = probe_tcp_hop(
                receiver, local_ip, ip, port, hop, timeout_ms / 1000
            )
            if status.startswith("SOCKET_ERROR:"):
                print(f"{hop:<4} {'*':<19} {'-':<10} {status}")
                return 1
            latency = f"{rtt_ms:.2f}ms" if rtt_ms is not None else "*"
            print(f"{hop:<4} {(address or '*'):<19} {latency:<10} {status}", flush=True)
            if status in ("OPEN", "CLOSED"):
                print(f"\nDestination reached (TCP/{port}: {status}).")
                return 0
            if status.startswith("UNREACHABLE:"):
                print("\nNetwork reported destination unreachable.")
                return 2
        print(f"\nDestination not confirmed within {MAX_TRACE_HOPS} hops.")
        return 2
    except PermissionError:
        if os.name == "nt":
            print("TCP traceroute requires an Administrator terminal on Windows.", file=sys.stderr)
        else:
            print("TCP traceroute requires root or CAP_NET_RAW on Linux.", file=sys.stderr)
    except KeyboardInterrupt:
        print("Trace interrupted.", file=sys.stderr)
    except OSError as exc:
        print(f"TCP traceroute error: {exc}", file=sys.stderr)
        if os.name == "nt":
            print("Raw socket capture may be blocked by Windows or security policy.", file=sys.stderr)
    finally:
        close_icmp_receiver(receiver)
    return 1


class _TapingArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        self.print_usage(sys.stderr)
        self.exit(1, f"taping: error: {message}\n")


def build_parser():
    parser = _TapingArgumentParser(prog="taping", add_help=False, allow_abbrev=False)
    parser.add_argument("target", nargs="?")
    parser.add_argument("value", nargs="?")
    parser.add_argument("-?", "-h", "-help", "--help", action="store_true", dest="help_flag")
    parser.add_argument("-p", "--port", type=int)
    parser.add_argument("-w", "--timeout", type=int)
    parser.add_argument("-c", "--count", type=int, default=1)
    parser.add_argument("-t", "--loop", action="store_true")
    return parser


def wait_for_next_round(started_at):
    remaining = DEFAULT_INTERVAL_MS / 1000 - (time.perf_counter() - started_at)
    if remaining > 0:
        time.sleep(remaining)


def main(argv=None):
    enable_console_colors()
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return int(exc.code)

    if args.help_flag or args.target is None or args.target.lower() in ("help", "/?"):
        show_help()
        return 0
    if args.target.lower() == "about":
        if args.value:
            print(f"Unexpected value: {args.value}", file=sys.stderr)
            return 1
        show_about()
        return 0
    if args.timeout is not None and args.timeout < MIN_TIMEOUT_MS:
        print("Timeout must be at least 100 ms.", file=sys.stderr)
        return 1
    if args.count < 1:
        print("Count must be at least 1.", file=sys.stderr)
        return 1
    if args.port is not None and not (1 <= args.port <= MAX_TCP_PORT):
        print("Port must be between 1 and 65535.", file=sys.stderr)
        return 1
    timeout_ms = args.timeout if args.timeout is not None else DEFAULT_TIMEOUT_MS

    if args.target.lower() == "trace":
        if not args.value:
            print("Trace target is missing. Example: taping trace google.com -p 443", file=sys.stderr)
            return 1
        if args.loop or args.count != 1:
            print("-t/--loop and -c are not supported in trace mode.", file=sys.stderr)
            return 1
        try:
            ip = resolve_target(args.value)
        except ValueError as exc:
            print(f"DNS_FAILED: {exc}", file=sys.stderr)
            return 1
        label = format_target_display(args.value, ip)
        return trace_route(ip, label, args.port, timeout_ms)

    is_range = args.target.lower() == "range"
    if is_range:
        if not args.value:
            print("Range is missing. Example: taping range 192.168.1.10-20", file=sys.stderr)
            return 1
        try:
            raw_targets = parse_range(args.value)
        except ValueError as exc:
            print(exc, file=sys.stderr)
            return 1
        header = args.value
    else:
        if args.value:
            print(f"Unexpected value: {args.value}", file=sys.stderr)
            return 1
        raw_targets = [args.target]
        header = args.target

    stats = new_stats()
    resolved_targets = []
    try:
        for target in raw_targets:
            ip = resolve_target(target)
            resolved_targets.append((ip, format_target_display(target, ip)))
    except ValueError as exc:
        print(f"DNS_FAILED: {exc}", file=sys.stderr)
        return 1

    if not is_range:
        header = resolved_targets[0][1]
    print_header(header, args.port)

    def run_round():
        if is_range and args.port is None:
            # Cap concurrency to avoid flooding the network with echo probes.
            # executor.map preserves the original numeric IP order in output.
            workers = min(RANGE_MAX_WORKERS, len(resolved_targets))
            with ThreadPoolExecutor(max_workers=workers) as pool:
                results = pool.map(
                    lambda target: probe_icmp_range_host(target[0], timeout_ms),
                    resolved_targets,
                )
                for (ip, label), result in zip(resolved_targets, results):
                    status, duration, ttl, message, attempts = result
                    show_icmp_probe_result(label, status, duration, ttl, message, attempts)
                    add_stats(stats, status == "UP", duration)
            return

        for ip, label in resolved_targets:
            if args.port is None:
                success, duration = icmp_ping(ip, label, timeout_ms)
            else:
                success, duration = tcp_ping(ip, label, args.port, timeout_ms)
            add_stats(stats, success, duration)

    try:
        if args.loop:
            while True:
                round_started = time.perf_counter()
                run_round()
                wait_for_next_round(round_started)
        else:
            for index in range(args.count):
                round_started = time.perf_counter()
                run_round()
                if index < args.count - 1:
                    wait_for_next_round(round_started)
    except KeyboardInterrupt:
        print(f"\n{color('Break received. Stopping...', Colors.YELLOW)}")
    finally:
        print_connection_statistics(stats)
    return 0 if stats["connected"] else 2


if __name__ == "__main__":
    sys.exit(main())
