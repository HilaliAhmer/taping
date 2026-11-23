"""Offline regression tests for TAPING v0.3.2."""

import contextlib
import ctypes
import io
import socket
import struct
import sys

import pytest

from taping import cli


def invoke(*args):
    stdout, stderr = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        code = cli.main(list(args))
    return code, stdout.getvalue(), stderr.getvalue()


@pytest.mark.parametrize("address", ["127.0.0.1", "8.8.8.8", "192.168.100.254"])
def test_valid_ipv4(address):
    assert cli.is_valid_ip(address)


@pytest.mark.parametrize("address", [
    "1.2.3.²", "١.٢.٣.٤", "01.002.3.4", "256.1.1.1", "1.2.3", "a.b.c.d", "",
])
def test_invalid_ipv4(address):
    assert not cli.is_valid_ip(address)


def test_unicode_numeric_target_returns_input_error():
    code, output, error = invoke("1.2.3.²")
    assert code == 1
    assert output == ""
    assert "Invalid IPv4 address" in error


@pytest.mark.parametrize("value, expected", [
    ("192.168.1.10-12", ["192.168.1.10", "192.168.1.11", "192.168.1.12"]),
    ("10.138.70.151-151", ["10.138.70.151"]),
])
def test_range(value, expected):
    assert cli.parse_range(value) == expected


@pytest.mark.parametrize("value", [
    "192.168.1.20-10", "192.168.1.254-256", "192.168.333.1-3", "01.002.3.4-9",
    "192.168.1.10-192.168.1.20", "1.2.3.²-5",
])
def test_bad_range(value):
    with pytest.raises(ValueError):
        cli.parse_range(value)


@pytest.mark.parametrize("args", [
    ("127.0.0.1", "--https"), ("127.0.0.1", "--up"),
    ("127.0.0.1", "-i", "100"), ("--version",),
    ("127.0.0.1", "-c", "0"), ("127.0.0.1", "-p", "65536"),
    ("127.0.0.1", "-w", "50"),
])
def test_invalid_args_are_stderr_and_exit_one(args):
    code, out, err = invoke(*args)
    assert code == 1
    assert out == ""
    assert err.strip()


def test_help_has_only_supported_flags():
    code, out, _ = invoke("help")
    assert code == 0
    for option in ("--loop", "--timeout", "--count", "--port"):
        assert option in out
    for removed in ("--rdp", "--up", "--interval", "--version"):
        assert removed not in out


def test_colors_not_written_when_redirected():
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        cli.print_result("127.0.0.1", "UP", cli.color("1.00ms", cli.Colors.CYAN), True)
    assert "\x1b[" not in output.getvalue()
    assert cli.supports_color() is False


def test_native_icmp_reply_parsed_without_locale(monkeypatch):
    def fake_create():
        return 1

    def fake_send(handle, dst, payload, payload_len, opts, buffer, buffer_len, timeout):
        assert timeout == 4000
        reply = ctypes.cast(buffer, ctypes.POINTER(cli._IcmpEchoReply)).contents
        reply.Status = 0
        reply.RoundTripTime = 16
        reply.Options.Ttl = 116
        return 1

    closed = []
    monkeypatch.setattr(cli, "_windows_icmp_api", lambda: (fake_create, fake_send, closed.append))
    assert cli._probe_icmp_windows("8.8.8.8", 4000) == ("UP", 16.0, 116, "")
    assert closed == [1]


def test_native_icmp_host_unreachable_is_down_not_runtime_error(monkeypatch):
    def fake_send(*args):
        return 0
    monkeypatch.setattr(cli, "_windows_icmp_api", lambda: (lambda: 1, fake_send, lambda handle: None))
    monkeypatch.setattr(cli.ctypes, "get_last_error", lambda: 11003, raising=False)
    assert cli._probe_icmp_windows("8.8.8.8", 800)[0] == "DOWN"


def test_range_recovers_and_stops_after_success(monkeypatch):
    tries = []
    answers = [
        ("DOWN", None, None, "No reply"),
        ("DOWN", None, None, "No reply"),
        ("UP", 1.0, 126, ""),
    ]

    def fake_probe(ip, timeout):
        tries.append(timeout)
        return answers[len(tries) - 1]

    monkeypatch.setattr(cli, "probe_icmp", fake_probe)
    monkeypatch.setattr(cli.time, "sleep", lambda _: None)
    assert cli.probe_icmp_range_host("10.138.70.151", 4000) == (*answers[-1], 3)
    assert tries == [800, 1200, 2000]


def test_range_down_after_four_attempts(monkeypatch):
    tries = []
    monkeypatch.setattr(cli, "probe_icmp", lambda ip, timeout: (
        tries.append(timeout) or "DOWN", None, None, "No reply"
    ))
    monkeypatch.setattr(cli.time, "sleep", lambda _: None)
    result = cli.probe_icmp_range_host("10.138.70.151", 4000)
    assert result == ("DOWN", None, None, "No reply", 4)
    assert tries == [800, 1200, 2000, 4000]


def test_timeout_override_is_cap(monkeypatch):
    tries = []
    monkeypatch.setattr(cli, "probe_icmp", lambda ip, timeout: (
        tries.append(timeout) or "DOWN", None, None, "No reply"
    ))
    monkeypatch.setattr(cli.time, "sleep", lambda _: None)
    cli.probe_icmp_range_host("127.0.0.1", 500)
    assert tries == [500, 500, 500, 500]


def test_range_concurrency_preserves_output_order(monkeypatch):
    observed = []

    def fake_probe(ip, timeout):
        observed.append(ip)
        return "UP", 2.0, 64, "", 1

    monkeypatch.setattr(cli, "probe_icmp_range_host", fake_probe)
    code, out, _ = invoke("range", "192.168.1.10-13")
    assert code == 0
    assert out.index("192.168.1.10") < out.index("192.168.1.11")
    assert "Attempted = 4" in out
    assert len(observed) == 4


def test_dns_failure_exit_one(monkeypatch):
    monkeypatch.setattr(cli.socket, "getaddrinfo", lambda *a, **k: (
        (_ for _ in ()).throw(socket.gaierror("not found"))
    ))
    code, out, err = invoke("invalidhost.example.invalid")
    assert code == 1
    assert out == ""
    assert "DNS_FAILED" in err


def test_trace_uses_status_from_handler(monkeypatch):
    args = []

    def fake_trace(*values):
        args.extend(values)
        return 2

    monkeypatch.setattr(cli, "trace_route", fake_trace)
    assert invoke("trace", "127.0.0.1", "-p", "443")[0] == 2
    assert args == ["127.0.0.1", "127.0.0.1", 443, 4000]


def _ipv4_header(proto, dest="127.0.0.1"):
    return (
        bytes([0x45, 0, 0, 0, 0, 0, 0, 0, 64, proto, 0, 0])
        + socket.inet_aton("192.168.1.1") + socket.inet_aton(dest)
    )


def test_tcp_icmp_reply_matches_ports_and_address():
    data = (
        _ipv4_header(socket.IPPROTO_ICMP)
        + struct.pack("!BBHI", 11, 0, 0, 0)
        + _ipv4_header(socket.IPPROTO_TCP, "10.6.106.50")
        + struct.pack("!HHI", 55555, 443, 0)
    )
    assert cli.decode_icmp_reply(data, "10.6.106.50", 55555, 443) == ("TTL_EXCEEDED", 0)
    assert cli.decode_icmp_reply(data, "10.6.106.51", 55555, 443) is None
    assert cli.decode_icmp_reply(data, "10.6.106.50", 55556, 443) is None
    assert cli.decode_icmp_reply(data[:30], "10.6.106.50", 55555, 443) is None


def test_icmp_trace_does_not_trust_zero_return_code_alone(monkeypatch):
    class FakeProcess:
        stdout = [
            "Tracing route to 10.6.106.50 using ICMP\n",
            " 1  10.138.100.254  1ms\n",
            "Trace complete\n",
        ]

        def __enter__(self):
            return self

        def __exit__(self, *_):
            pass

        def wait(self):
            return 0

    monkeypatch.setattr(cli.subprocess, "Popen", lambda *a, **kw: FakeProcess())
    assert cli.icmp_trace("10.6.106.50", "10.6.106.50", 4000) == 2


@pytest.mark.skipif(sys.platform != "linux", reason="Linux only smoke test")
def test_linux_ping_subprocess_error_is_clean(monkeypatch):
    def broken(*args, **kwargs):
        raise FileNotFoundError("ping not available")
    monkeypatch.setattr(cli.subprocess, "run", broken)
    assert cli.probe_icmp("127.0.0.1", 500)[0] == "ERROR"
