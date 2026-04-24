from __future__ import annotations

from unittest.mock import MagicMock, Mock, patch

from roku_tui.ecp.discovery import discover_rokus, probe_roku

# ── probe_roku ────────────────────────────────────────────────────────────────


def test_probe_roku_reachable() -> None:
    with patch("roku_tui.ecp.discovery.socket.create_connection") as mock_conn:
        mock_conn.return_value.__enter__ = Mock(return_value=Mock())
        mock_conn.return_value.__exit__ = Mock(return_value=False)
        assert probe_roku("192.168.1.50") is True


def test_probe_roku_unreachable() -> None:
    with patch("roku_tui.ecp.discovery.socket.create_connection") as mock_conn:
        mock_conn.side_effect = OSError("Connection refused")
        assert probe_roku("192.168.1.50") is False


# ── discover_rokus ────────────────────────────────────────────────────────────


def test_discover_rokus_returns_empty_on_timeout() -> None:
    with patch("roku_tui.ecp.discovery.socket.socket") as MockSocket:
        mock_sock = MagicMock()
        MockSocket.return_value = mock_sock
        mock_sock.recvfrom.side_effect = TimeoutError
        results = discover_rokus(timeout=0.01)
    assert results == []


def test_discover_rokus_parses_location_header() -> None:
    location = "http://192.168.1.50:8060/"
    ssdp_response = (
        f"HTTP/1.1 200 OK\r\nLOCATION: {location}\r\nST: roku:ecp\r\n\r\n"
    ).encode()

    with patch("roku_tui.ecp.discovery.socket.socket") as MockSocket:
        mock_sock = MagicMock()
        MockSocket.return_value = mock_sock
        mock_sock.recvfrom.side_effect = [
            (ssdp_response, ("192.168.1.50", 1900)),
            TimeoutError(),
        ]
        results = discover_rokus(timeout=0.01)

    assert location in results


def test_discover_rokus_deduplicates() -> None:
    location = "http://192.168.1.50:8060/"
    ssdp_response = (f"HTTP/1.1 200 OK\r\nLOCATION: {location}\r\n\r\n").encode()

    with patch("roku_tui.ecp.discovery.socket.socket") as MockSocket:
        mock_sock = MagicMock()
        MockSocket.return_value = mock_sock
        mock_sock.recvfrom.side_effect = [
            (ssdp_response, ("192.168.1.50", 1900)),
            (ssdp_response, ("192.168.1.50", 1900)),
            TimeoutError(),
        ]
        results = discover_rokus(timeout=0.01)

    assert results.count(location) == 1


def test_discover_rokus_ignores_non_location_data() -> None:
    ssdp_response = b"HTTP/1.1 200 OK\r\nST: roku:ecp\r\n\r\n"

    with patch("roku_tui.ecp.discovery.socket.socket") as MockSocket:
        mock_sock = MagicMock()
        MockSocket.return_value = mock_sock
        mock_sock.recvfrom.side_effect = [
            (ssdp_response, ("192.168.1.50", 1900)),
            TimeoutError(),
        ]
        results = discover_rokus(timeout=0.01)

    assert results == []
