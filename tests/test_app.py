from app import parse_ping


def test_parse_ping_success():
    line = "64 bytes from 8.8.8.8: icmp_seq=1 ttl=117 time=14.5 ms"
    assert parse_ping(line) == 14.5


def test_parse_ping_failure():
    line = "Request timeout"
    assert parse_ping(line) is None


def test_parse_ping_integer():
    line = "64 bytes from 8.8.8.8: icmp_seq=1 ttl=117 time=15 ms"
    assert parse_ping(line) == 15.0
