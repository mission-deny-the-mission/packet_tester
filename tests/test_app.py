from app import parse_ping, calculate_mos, get_ip_info, ip_info_cache
import pytest
from unittest.mock import patch, MagicMock


def test_parse_ping_success():
    line = "64 bytes from 8.8.8.8: icmp_seq=1 ttl=117 time=14.5 ms"
    assert parse_ping(line) == 14.5


def test_parse_ping_failure():
    line = "Request timeout"
    assert parse_ping(line) is None


def test_parse_ping_integer():
    line = "64 bytes from 8.8.8.8: icmp_seq=1 ttl=117 time=15 ms"
    assert parse_ping(line) == 15.0


def test_calculate_mos_perfect():
    # Low latency, zero loss, zero jitter should be close to 4.4 - 4.5
    mos = calculate_mos(20, 0, 2)
    assert 4.0 <= mos <= 4.5


def test_calculate_mos_high_latency():
    # High latency should drop MOS
    mos_low = calculate_mos(20, 0, 0)
    mos_high = calculate_mos(300, 0, 0)
    assert mos_high < mos_low


def test_calculate_mos_high_loss():
    # 10% loss should significantly drop MOS
    mos_no_loss = calculate_mos(50, 0, 5)
    mos_loss = calculate_mos(50, 10, 5)
    assert mos_loss < mos_no_loss


def test_calculate_mos_timeout():
    # Timeout (None latency) should return 1.0
    assert calculate_mos(None, 100, 0) == 1.0


def test_get_ip_info_private():
    # Reset cache for test
    ip_info_cache.clear()
    info = get_ip_info("192.168.1.1")
    assert info["isp"] == "Local Network"
    assert info["location"] == "Private IP"


@patch("requests.get")
def test_get_ip_info_public_success(mock_get):
    ip_info_cache.clear()
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "status": "success",
        "isp": "Google LLC",
        "city": "Mountain View",
        "countryCode": "US",
    }
    mock_get.return_value = mock_response

    info = get_ip_info("8.8.8.8")
    assert info["isp"] == "Google LLC"
    assert "Mountain View" in info["location"]
    assert "US" in info["location"]


@patch("requests.get")
def test_get_ip_info_public_failure(mock_get):
    ip_info_cache.clear()
    mock_response = MagicMock()
    mock_response.json.return_value = {"status": "fail"}
    mock_get.return_value = mock_response

    info = get_ip_info("1.2.3.4")
    assert info["isp"] == "Unknown ISP"


@patch("requests.get")
def test_get_ip_info_exception(mock_get):
    ip_info_cache.clear()
    mock_get.side_effect = Exception("Network error")

    info = get_ip_info("1.2.3.4")
    assert info["isp"] == "Unknown ISP"


def test_get_ip_info_cache_hit():
    ip_info_cache.clear()
    ip_info_cache["1.1.1.1"] = {"isp": "Cached ISP", "location": "Cached Loc"}
    info = get_ip_info("1.1.1.1")
    assert info["isp"] == "Cached ISP"
