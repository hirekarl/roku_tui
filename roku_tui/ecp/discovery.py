import re
import socket

SSDP_ADDR = "239.255.255.250"
SSDP_PORT = 1900
MSEARCH = (
    "M-SEARCH * HTTP/1.1\r\n"
    f"HOST: {SSDP_ADDR}:{SSDP_PORT}\r\n"
    'MAN: "ssdp:discover"\r\n'
    "MX: 3\r\n"
    "ST: roku:ecp\r\n"
    "\r\n"
)


def probe_roku(ip: str, timeout: float = 1.5) -> bool:
    """Return True if port 8060 is reachable on the given IP. Blocking."""
    try:
        with socket.create_connection((ip, 8060), timeout=timeout):
            return True
    except OSError:
        return False


def discover_rokus(timeout: float = 3.0) -> list[str]:
    """Return Roku base URLs found via SSDP. Blocking — run in a thread worker."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(timeout)
    results: list[str] = []
    try:
        sock.sendto(MSEARCH.encode(), (SSDP_ADDR, SSDP_PORT))
        while True:
            data, _ = sock.recvfrom(1024)
            text = data.decode(errors="ignore")
            if m := re.search(r"LOCATION:\s*(.+)", text, re.IGNORECASE):
                url = m.group(1).strip()
                if url not in results:
                    results.append(url)
    except (TimeoutError, OSError):
        pass
    finally:
        sock.close()
    return results
