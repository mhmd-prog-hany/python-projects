#!/usr/bin/env python3
# ============================================================
#   MHScan - Advanced Port Scanner
#   Built by Mohammed Hany
#   Version 2.0 | For Bug Bounty & Security Research
# ============================================================

import socket
import threading
import argparse
import json
import csv
import os
import sys
import time
import ipaddress
import random
import struct
import select
import signal
import re
import ssl
import hashlib
import datetime
from queue import Queue, Empty
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Tuple
from enum import Enum
from pathlib import Path
from contextlib import suppress


# ─────────────────────────────────────────────
#  ANSI COLORS & TERMINAL STYLES
# ─────────────────────────────────────────────

class Color:
    RED      = "\033[91m"
    GREEN    = "\033[92m"
    YELLOW   = "\033[93m"
    BLUE     = "\033[94m"
    MAGENTA  = "\033[95m"
    CYAN     = "\033[96m"
    WHITE    = "\033[97m"
    BOLD     = "\033[1m"
    DIM      = "\033[2m"
    ITALIC   = "\033[3m"
    UNDER    = "\033[4m"
    RESET    = "\033[0m"

    @staticmethod
    def strip(text: str) -> str:
        import re
        return re.sub(r'\033\[[0-9;]*m', '', text)


def c(color: str, text: str) -> str:
    return f"{color}{text}{Color.RESET}"


# ─────────────────────────────────────────────
#  BANNER
# ─────────────────────────────────────────────

BANNER = f"""
{Color.CYAN}{Color.BOLD}
  ███╗   ███╗██╗  ██╗███████╗ ██████╗ █████╗ ███╗   ██╗
  ████╗ ████║██║  ██║██╔════╝██╔════╝██╔══██╗████╗  ██║
  ██╔████╔██║███████║███████╗██║     ███████║██╔██╗ ██║
  ██║╚██╔╝██║██╔══██║╚════██║██║     ██╔══██║██║╚██╗██║
  ██║ ╚═╝ ██║██║  ██║███████║╚██████╗██║  ██║██║ ╚████║
  ╚═╝     ╚═╝╚═╝  ╚═╝╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═══╝
{Color.RESET}{Color.DIM}
         Advanced Port Scanner  |  Built by Mohammed Hany
         Version 2.0  |  Bug Bounty & Security Research
{Color.RESET}"""


# ─────────────────────────────────────────────
#  ENUMS
# ─────────────────────────────────────────────

class PortState(Enum):
    OPEN      = "open"
    CLOSED    = "closed"
    FILTERED  = "filtered"
    OPEN_FILTERED = "open|filtered"
    UNKNOWN   = "unknown"


class ScanMode(Enum):
    TCP_CONNECT  = "tcp"
    SYN_STEALTH  = "syn"
    UDP          = "udp"
    FULL         = "full"


class OutputFormat(Enum):
    TERMINAL = "terminal"
    JSON     = "json"
    CSV      = "csv"
    HTML     = "html"
    ALL      = "all"


# ─────────────────────────────────────────────
#  DATA MODELS
# ─────────────────────────────────────────────

@dataclass
class ServiceInfo:
    name: str = "unknown"
    version: str = ""
    banner: str = ""
    extra: str = ""

    def __str__(self):
        parts = [self.name]
        if self.version:
            parts.append(self.version)
        if self.extra:
            parts.append(self.extra)
        return " | ".join(parts)


@dataclass
class PortResult:
    port: int
    protocol: str
    state: PortState
    service: ServiceInfo = field(default_factory=ServiceInfo)
    response_time: float = 0.0
    ssl_info: Optional[Dict] = None
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.datetime.now().isoformat()


@dataclass
class ScanResult:
    target: str
    ip: str
    hostname: str
    scan_mode: str
    start_time: str
    end_time: str = ""
    duration: float = 0.0
    ports: List[PortResult] = field(default_factory=list)
    os_guess: str = ""
    host_status: str = "up"

    def open_ports(self) -> List[PortResult]:
        return [p for p in self.ports if p.state == PortState.OPEN]

    def filtered_ports(self) -> List[PortResult]:
        return [p for p in self.ports if p.state == PortState.FILTERED]

    def summary(self) -> Dict:
        return {
            "target": self.target,
            "ip": self.ip,
            "hostname": self.hostname,
            "open": len(self.open_ports()),
            "filtered": len(self.filtered_ports()),
            "total_scanned": len(self.ports),
            "duration": round(self.duration, 2),
            "os_guess": self.os_guess,
        }


# ─────────────────────────────────────────────
#  SERVICE DATABASE
# ─────────────────────────────────────────────

WELL_KNOWN_PORTS: Dict[int, str] = {
    7: "echo", 9: "discard", 11: "systat", 13: "daytime", 17: "qotd",
    19: "chargen", 20: "ftp-data", 21: "ftp", 22: "ssh", 23: "telnet",
    25: "smtp", 37: "time", 42: "nameserver", 43: "whois", 49: "tacacs",
    53: "dns", 67: "dhcp", 68: "dhcp-client", 69: "tftp", 70: "gopher",
    79: "finger", 80: "http", 81: "http-alt", 82: "http-alt2",
    88: "kerberos", 102: "iso-tsap", 110: "pop3", 111: "rpcbind",
    113: "ident", 119: "nntp", 123: "ntp", 135: "msrpc",
    137: "netbios-ns", 138: "netbios-dgm", 139: "netbios-ssn",
    143: "imap", 161: "snmp", 162: "snmp-trap", 179: "bgp",
    194: "irc", 389: "ldap", 443: "https", 445: "smb",
    464: "kerberos-change", 465: "smtps", 500: "isakmp",
    502: "modbus", 512: "rexec", 513: "rlogin", 514: "syslog",
    515: "printer", 520: "rip", 521: "ripng", 522: "ulp",
    523: "ibm-db2", 524: "ncp", 525: "timed", 530: "courier",
    531: "conference", 532: "netnews", 533: "netwall", 540: "uucp",
    543: "klogin", 544: "kshell", 546: "dhcpv6", 547: "dhcpv6-server",
    548: "afp", 554: "rtsp", 563: "snews", 587: "smtp-submission",
    593: "http-rpc", 601: "syslog", 623: "ipmi", 631: "ipp",
    636: "ldaps", 646: "ldp", 666: "doom", 674: "acap",
    706: "silc", 749: "kerberos-admin", 750: "kerberos-iv",
    873: "rsync", 902: "vmware-auth", 989: "ftps-data",
    990: "ftps", 992: "telnets", 993: "imaps", 994: "ircs",
    995: "pop3s", 1080: "socks", 1099: "rmiregistry",
    1194: "openvpn", 1214: "kazaa", 1241: "nessus", 1311: "dell-openmanage",
    1337: "waste", 1433: "mssql", 1434: "mssql-monitor",
    1521: "oracle", 1604: "citrix-ica", 1723: "pptp",
    1755: "wms", 1812: "radius", 1813: "radius-acct",
    1883: "mqtt", 1900: "upnp", 2000: "cisco-sccp",
    2049: "nfs", 2082: "cpanel", 2083: "cpanel-ssl",
    2086: "whm", 2087: "whm-ssl", 2095: "cPanel-webmail",
    2096: "cpanel-webmail-ssl", 2100: "amiganetfs", 2181: "zookeeper",
    2222: "ssh-alt", 2375: "docker", 2376: "docker-ssl",
    2379: "etcd", 2380: "etcd-peer", 2404: "iec-104",
    2483: "oracle-tns", 2484: "oracle-tns-ssl", 2638: "sybase",
    3000: "dev-server", 3001: "dev-server-alt", 3128: "squid",
    3260: "iscsi", 3268: "ldap-global", 3269: "ldaps-global",
    3306: "mysql", 3389: "rdp", 3690: "svn", 3784: "bfd",
    4000: "remoteanything", 4040: "spark-ui", 4200: "angular-dev",
    4369: "epmd", 4443: "https-alt", 4444: "metasploit",
    4500: "ipsec-nat", 4505: "salt-master", 4506: "salt-worker",
    4567: "sinatra", 4848: "glassfish", 4900: "hfcs",
    5000: "flask-dev", 5001: "commplex-link", 5002: "rfe",
    5004: "rtp", 5005: "rtp-alt", 5060: "sip", 5061: "sips",
    5432: "postgresql", 5672: "amqp", 5900: "vnc",
    5901: "vnc-2", 5902: "vnc-3", 6000: "x11",
    6001: "x11-2", 6379: "redis", 6443: "kubernetes-api",
    6660: "irc-alt", 6667: "irc", 6881: "bittorrent",
    7001: "weblogic", 7002: "weblogic-ssl", 7077: "spark-master",
    7474: "neo4j", 7546: "dhcpv6-alt", 8000: "http-alt",
    8001: "http-alt2", 8008: "http-alt3", 8009: "ajp",
    8080: "http-proxy", 8081: "http-alt4", 8082: "blackice",
    8083: "us-srv", 8086: "influxdb", 8088: "radan-http",
    8089: "splunkd", 8090: "http-alt5", 8161: "activemq",
    8181: "intermapper", 8443: "https-alt", 8500: "consul",
    8888: "jupyter", 8983: "solr", 9000: "php-fpm",
    9001: "tor-orport", 9042: "cassandra", 9090: "prometheus",
    9091: "xmltec", 9092: "kafka", 9100: "jetdirect",
    9200: "elasticsearch", 9300: "elasticsearch-cluster",
    9418: "git", 9999: "abyss", 10000: "webmin",
    10001: "scp-config", 10250: "kubelet", 10255: "kubelet-ro",
    11211: "memcached", 15672: "rabbitmq-mgmt", 16010: "hbase-master",
    16030: "hbase-regionserver", 17500: "dropbox-lan",
    20000: "usermin", 27017: "mongodb", 27018: "mongodb-shard",
    27019: "mongodb-arbiter", 28017: "mongodb-web",
    32768: "filenet-tms", 50000: "db2", 50070: "hadoop-namenode",
    50075: "hadoop-datanode", 61616: "activemq-broker",
}

# Common service banners / probes
SERVICE_PROBES: Dict[str, bytes] = {
    "http": b"HEAD / HTTP/1.0\r\nHost: {host}\r\nUser-Agent: MHScan/2.0\r\n\r\n",
    "ftp":  b"",          # Just read banner
    "smtp": b"",          # Just read banner
    "ssh":  b"",          # Just read banner
    "pop3": b"",          # Just read banner
    "imap": b"",          # Just read banner
    "rdp":  b"\x03\x00\x00\x13\x0e\xe0\x00\x00\x00\x00\x00\x01\x00\x08\x00\x03\x00\x00\x00",
    "mysql": b"\x00",
    "redis": b"*1\r\n$4\r\nPING\r\n",
    "telnet": b"",
}

# CVE hints per service (simplified)
CVE_HINTS: Dict[str, List[str]] = {
    "ssh":   ["Check for CVE-2023-38408 (OpenSSH agent hijack)", "CVE-2016-0777 (openssh roaming)"],
    "ftp":   ["Anonymous FTP login? Check CVE-2010-4221", "CVE-2011-0762 (vsftpd backdoor)"],
    "http":  ["Check for CVE-2021-41773 (Apache path traversal)", "Heartbleed CVE-2014-0160 if old TLS"],
    "https": ["Check TLS version - SSLv3/TLS1.0 deprecated", "BEAST, POODLE, Heartbleed checks recommended"],
    "smb":   ["EternalBlue CVE-2017-0144 (MS17-010)", "PrintNightmare CVE-2021-1675"],
    "rdp":   ["BlueKeep CVE-2019-0708", "DejaBlue CVE-2019-1181/1182"],
    "mysql": ["CVE-2012-2122 authentication bypass", "Check for default root with no password"],
    "mssql": ["CVE-2020-0618 RCE via SSRS", "Default SA account check"],
    "redis": ["Unauthenticated access? CVE-2022-0543", "SSRF via redis SLAVEOF command"],
    "mongodb": ["No auth by default in old versions", "CVE-2013-4650 injection"],
    "telnet": ["Plaintext protocol - credentials sniffable", "Should be replaced with SSH"],
    "snmp":  ["Default community string 'public'", "CVE-2002-0013 SNMPv1 buffer overflow"],
    "vnc":   ["Brute-force attack surface", "CVE-2015-5239 null auth bypass"],
    "elasticsearch": ["CVE-2015-1427 Groovy sandbox escape", "No-auth by default in old versions"],
}


# ─────────────────────────────────────────────
#  OS FINGERPRINTING (TTL-BASED)
# ─────────────────────────────────────────────

TTL_OS_MAP: Dict[range, str] = {
    range(0, 65):   "Network Device / Custom",
    range(65, 69):  "Linux / Android",
    range(64, 65):  "Linux / macOS",
    range(128, 129): "Windows",
    range(255, 256): "Cisco / Solaris / HP-UX",
}

def guess_os_from_ttl(ttl: int) -> str:
    if ttl <= 64:
        return "Linux / macOS / Android"
    elif ttl <= 128:
        return "Windows"
    elif ttl <= 255:
        return "Cisco IOS / Solaris / Network Device"
    return "Unknown"


def get_ttl(host: str) -> Optional[int]:
    """Try to get TTL via ICMP ping (requires raw sockets or ping command)."""
    try:
        import subprocess
        result = subprocess.run(
            ["ping", "-c", "1", "-W", "2", host],
            capture_output=True, text=True, timeout=5
        )
        output = result.stdout
        match = re.search(r'ttl=(\d+)', output, re.IGNORECASE)
        if match:
            return int(match.group(1))
    except Exception:
        pass
    return None


# ─────────────────────────────────────────────
#  SSL / TLS INSPECTOR
# ─────────────────────────────────────────────

def get_ssl_info(host: str, port: int, timeout: float = 3.0) -> Optional[Dict]:
    """Attempt TLS handshake and extract certificate metadata."""
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        with socket.create_connection((host, port), timeout=timeout) as raw:
            with ctx.wrap_socket(raw, server_hostname=host) as s:
                cert = s.getpeercert()
                cipher = s.cipher()
                version = s.version()
                info = {
                    "tls_version": version,
                    "cipher_suite": cipher[0] if cipher else "unknown",
                    "subject": dict(x[0] for x in cert.get("subject", [])) if cert else {},
                    "issuer": dict(x[0] for x in cert.get("issuer", [])) if cert else {},
                    "expires": cert.get("notAfter", "") if cert else "",
                    "sans": [],
                }
                if cert:
                    for san_type, san_val in cert.get("subjectAltName", []):
                        info["sans"].append(san_val)
                return info
    except Exception:
        return None


# ─────────────────────────────────────────────
#  BANNER GRABBER
# ─────────────────────────────────────────────

class BannerGrabber:
    def __init__(self, timeout: float = 2.5):
        self.timeout = timeout

    def grab(self, host: str, port: int, service_hint: str = "") -> str:
        """Attempt to grab a service banner."""
        banner = ""
        try:
            with socket.create_connection((host, port), timeout=self.timeout) as s:
                s.settimeout(self.timeout)

                # Send appropriate probe
                probe_key = service_hint.lower()
                if probe_key in SERVICE_PROBES and SERVICE_PROBES[probe_key]:
                    probe = SERVICE_PROBES[probe_key]
                    if b"{host}" in probe:
                        probe = probe.replace(b"{host}", host.encode())
                    s.send(probe)

                # Read response
                try:
                    data = s.recv(4096)
                    banner = self._clean_banner(data)
                except socket.timeout:
                    pass

                # For HTTP, try to extract server header
                if probe_key == "http" and banner:
                    banner = self._parse_http_banner(banner)

        except (socket.timeout, ConnectionRefusedError, OSError):
            pass
        except Exception:
            pass

        return banner[:512]  # Max 512 chars

    def _clean_banner(self, data: bytes) -> str:
        try:
            text = data.decode("utf-8", errors="replace")
        except Exception:
            text = data.decode("latin-1", errors="replace")
        return " ".join(text.split())

    def _parse_http_banner(self, response: str) -> str:
        server = ""
        powered = ""
        for line in response.split(" "):
            if "server:" in line.lower():
                server = line.strip()
            if "x-powered-by:" in line.lower():
                powered = line.strip()
        if server or powered:
            return f"{server} {powered}".strip()
        return response[:200]


# ─────────────────────────────────────────────
#  SERVICE DETECTOR
# ─────────────────────────────────────────────

class ServiceDetector:
    def __init__(self, banner_grabber: BannerGrabber):
        self.grabber = banner_grabber

    def detect(self, host: str, port: int) -> ServiceInfo:
        name = WELL_KNOWN_PORTS.get(port, "unknown")
        info = ServiceInfo(name=name)

        # Grab banner
        banner = self.grabber.grab(host, port, name)
        info.banner = banner

        # Version extraction heuristics
        if banner:
            info.version = self._extract_version(banner, name)

        return info

    def _extract_version(self, banner: str, service: str) -> str:
        """Heuristic version extraction from banner strings."""
        patterns = [
            r'([\w\-]+)[/ ]([\d.]+(?:-[\w.]+)?)',
            r'v([\d.]+)',
            r'version ([\d.]+)',
        ]
        for pat in patterns:
            m = re.search(pat, banner, re.IGNORECASE)
            if m:
                return m.group(0)[:80]
        return ""


# ─────────────────────────────────────────────
#  PORT RANGE PARSER
# ─────────────────────────────────────────────

def parse_port_range(port_str: str) -> List[int]:
    """
    Parse port specifications like:
      80,443,8080
      1-1024
      22,80,443,8000-8100
      top100  (shortcut)
    """
    if port_str.lower() == "top100":
        return TOP_100_PORTS
    if port_str.lower() == "top1000":
        return TOP_1000_PORTS
    if port_str.lower() == "all":
        return list(range(1, 65536))
    if port_str.lower() == "common":
        return list(WELL_KNOWN_PORTS.keys())

    ports = []
    for part in port_str.split(","):
        part = part.strip()
        if "-" in part:
            start, end = part.split("-", 1)
            ports.extend(range(int(start), int(end) + 1))
        else:
            ports.append(int(part))
    return sorted(set(ports))


TOP_100_PORTS = [
    21, 22, 23, 25, 53, 80, 81, 88, 110, 111,
    119, 123, 135, 137, 138, 139, 143, 161, 179, 194,
    389, 443, 445, 465, 500, 512, 513, 514, 515, 548,
    554, 587, 593, 631, 636, 646, 873, 902, 993, 995,
    1080, 1194, 1433, 1434, 1521, 1723, 1883, 1900, 2049, 2082,
    2083, 2086, 2087, 2222, 2375, 2376, 3000, 3128, 3260, 3306,
    3389, 3690, 4000, 4443, 4444, 4500, 4848, 5000, 5432, 5672,
    5900, 6000, 6379, 6443, 6667, 7001, 7474, 8000, 8080, 8081,
    8086, 8088, 8089, 8161, 8443, 8888, 8983, 9000, 9042, 9090,
    9092, 9200, 10000, 10250, 11211, 15672, 27017, 27018, 50000, 61616,
]

TOP_1000_PORTS = sorted(list(WELL_KNOWN_PORTS.keys()) + list(range(1, 1025)))


# ─────────────────────────────────────────────
#  PROGRESS BAR
# ─────────────────────────────────────────────

class ProgressBar:
    def __init__(self, total: int, label: str = "Scanning"):
        self.total = total
        self.current = 0
        self.label = label
        self.lock = threading.Lock()
        self.start = time.time()
        self._last_print = 0

    def update(self, n: int = 1):
        with self.lock:
            self.current += n
            now = time.time()
            if now - self._last_print >= 0.15 or self.current >= self.total:
                self._draw()
                self._last_print = now

    def _draw(self):
        pct = self.current / self.total if self.total else 1
        filled = int(pct * 40)
        bar = "█" * filled + "░" * (40 - filled)
        elapsed = time.time() - self.start
        rate = self.current / elapsed if elapsed > 0 else 0
        eta = (self.total - self.current) / rate if rate > 0 else 0

        line = (
            f"\r{Color.CYAN}{self.label}{Color.RESET} "
            f"[{Color.GREEN}{bar}{Color.RESET}] "
            f"{Color.BOLD}{pct*100:5.1f}%{Color.RESET} "
            f"{Color.DIM}({self.current}/{self.total}) "
            f"rate={rate:.0f}/s eta={eta:.1f}s{Color.RESET}"
        )
        sys.stdout.write(line)
        sys.stdout.flush()
        if self.current >= self.total:
            print()


# ─────────────────────────────────────────────
#  LIVE RESULTS PRINTER
# ─────────────────────────────────────────────

class LivePrinter:
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.lock = threading.Lock()

    def port_open(self, result: PortResult):
        with self.lock:
            svc = str(result.service)
            state_color = {
                PortState.OPEN: Color.GREEN,
                PortState.FILTERED: Color.YELLOW,
                PortState.CLOSED: Color.DIM,
            }.get(result.state, Color.WHITE)

            port_str = f"{Color.BOLD}{result.port:5d}{Color.RESET}/{result.protocol}"
            state_str = f"{state_color}{result.state.value:<12}{Color.RESET}"
            svc_str = f"{Color.CYAN}{svc}{Color.RESET}"
            rt_str = f"{Color.DIM}{result.response_time*1000:.1f}ms{Color.RESET}"

            print(f"\r  {port_str}  {state_str}  {svc_str:<35}  {rt_str}")

    def port_filtered(self, result: PortResult):
        if self.verbose:
            with self.lock:
                print(f"\r  {result.port:5d}/{result.protocol}  "
                      f"{Color.YELLOW}filtered{Color.RESET}")

    def info(self, msg: str):
        with self.lock:
            print(f"\r{Color.BLUE}[*]{Color.RESET} {msg}")

    def success(self, msg: str):
        with self.lock:
            print(f"\r{Color.GREEN}[+]{Color.RESET} {msg}")

    def warn(self, msg: str):
        with self.lock:
            print(f"\r{Color.YELLOW}[!]{Color.RESET} {msg}")

    def error(self, msg: str):
        with self.lock:
            print(f"\r{Color.RED}[-]{Color.RESET} {msg}")


# ─────────────────────────────────────────────
#  HOST RESOLVER
# ─────────────────────────────────────────────

class HostResolver:
    @staticmethod
    def resolve(target: str) -> Tuple[str, str]:
        """Returns (ip, hostname)."""
        try:
            ip = socket.gethostbyname(target)
            try:
                hostname = socket.gethostbyaddr(ip)[0]
            except socket.herror:
                hostname = target if target != ip else ""
            return ip, hostname
        except socket.gaierror as e:
            raise ValueError(f"Cannot resolve host '{target}': {e}")

    @staticmethod
    def is_alive(ip: str, timeout: float = 2.0) -> bool:
        """Quick liveness check via TCP to port 80 or ICMP."""
        for port in [80, 443, 22]:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(timeout)
                result = s.connect_ex((ip, port))
                s.close()
                if result == 0:
                    return True
            except Exception:
                pass

        # ICMP ping fallback
        try:
            import subprocess
            r = subprocess.run(
                ["ping", "-c", "1", "-W", "1", ip],
                capture_output=True, timeout=3
            )
            return r.returncode == 0
        except Exception:
            pass
        return True  # Assume up if can't determine


# ─────────────────────────────────────────────
#  TCP CONNECT SCANNER
# ─────────────────────────────────────────────

class TCPConnectScanner:
    def __init__(self, timeout: float = 1.5, threads: int = 200,
                 grab_banners: bool = True, verbose: bool = False):
        self.timeout = timeout
        self.threads = threads
        self.grab_banners = grab_banners
        self.verbose = verbose
        self.grabber = BannerGrabber(timeout=timeout)
        self.detector = ServiceDetector(self.grabber)
        self.printer = LivePrinter(verbose)
        self._stop_event = threading.Event()

    def scan_port(self, host: str, port: int) -> PortResult:
        start = time.time()
        try:
            with socket.create_connection((host, port), timeout=self.timeout):
                elapsed = time.time() - start
                state = PortState.OPEN
        except ConnectionRefusedError:
            elapsed = time.time() - start
            return PortResult(
                port=port, protocol="tcp",
                state=PortState.CLOSED,
                response_time=elapsed
            )
        except (socket.timeout, OSError):
            elapsed = time.time() - start
            return PortResult(
                port=port, protocol="tcp",
                state=PortState.FILTERED,
                response_time=elapsed
            )
        except Exception:
            elapsed = time.time() - start
            return PortResult(
                port=port, protocol="tcp",
                state=PortState.UNKNOWN,
                response_time=elapsed
            )

        # Port is open - gather service info
        service = self.detector.detect(host, port) if self.grab_banners else ServiceInfo(
            name=WELL_KNOWN_PORTS.get(port, "unknown")
        )

        ssl_info = None
        if port in (443, 8443, 993, 995, 465, 636, 8083, 8084):
            ssl_info = get_ssl_info(host, port, self.timeout)

        return PortResult(
            port=port,
            protocol="tcp",
            state=PortState.OPEN,
            service=service,
            response_time=elapsed,
            ssl_info=ssl_info
        )

    def scan(self, host: str, ports: List[int],
             progress: Optional[ProgressBar] = None) -> List[PortResult]:
        results = []
        lock = threading.Lock()

        def worker(port):
            if self._stop_event.is_set():
                return
            res = self.scan_port(host, port)
            with lock:
                results.append(res)
            if res.state == PortState.OPEN:
                self.printer.port_open(res)
            elif res.state == PortState.FILTERED:
                self.printer.port_filtered(res)
            if progress:
                progress.update()

        with ThreadPoolExecutor(max_workers=self.threads) as ex:
            futures = [ex.submit(worker, p) for p in ports]
            try:
                for f in as_completed(futures):
                    f.result()
            except KeyboardInterrupt:
                self._stop_event.set()
                ex.shutdown(wait=False)

        return sorted(results, key=lambda r: r.port)

    def stop(self):
        self._stop_event.set()


# ─────────────────────────────────────────────
#  UDP SCANNER
# ─────────────────────────────────────────────

class UDPScanner:
    COMMON_UDP_PORTS = [53, 67, 68, 69, 123, 137, 138, 161, 162,
                        500, 514, 520, 1194, 1812, 1813, 4500, 5353]

    UDP_PAYLOADS: Dict[int, bytes] = {
        53:  b"\x12\x34\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00"
             b"\x07version\x04bind\x00\x00\x10\x00\x03",  # DNS version query
        123: (b"\x1b" + b"\x00" * 47),   # NTP client request
        161: b"\x30\x26\x02\x01\x00\x04\x06public\xa0\x19"
             b"\x02\x01\x01\x02\x01\x00\x02\x01\x00\x30\x0e"
             b"\x30\x0c\x06\x08\x2b\x06\x01\x02\x01\x01\x01\x00\x05\x00",  # SNMPv1 get
    }

    def __init__(self, timeout: float = 2.0):
        self.timeout = timeout
        self.printer = LivePrinter()

    def scan_port(self, host: str, port: int) -> PortResult:
        payload = self.UDP_PAYLOADS.get(port, b"\x00" * 8)
        start = time.time()
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.settimeout(self.timeout)
            s.sendto(payload, (host, port))
            data, _ = s.recvfrom(1024)
            elapsed = time.time() - start
            s.close()
            service_name = WELL_KNOWN_PORTS.get(port, "unknown")
            return PortResult(
                port=port, protocol="udp",
                state=PortState.OPEN,
                service=ServiceInfo(name=service_name, banner=data[:64].hex()),
                response_time=elapsed
            )
        except socket.timeout:
            elapsed = time.time() - start
            return PortResult(
                port=port, protocol="udp",
                state=PortState.OPEN_FILTERED,
                response_time=elapsed,
                service=ServiceInfo(name=WELL_KNOWN_PORTS.get(port, "unknown"))
            )
        except ConnectionRefusedError:
            elapsed = time.time() - start
            return PortResult(port=port, protocol="udp",
                              state=PortState.CLOSED, response_time=elapsed)
        except Exception:
            elapsed = time.time() - start
            return PortResult(port=port, protocol="udp",
                              state=PortState.UNKNOWN, response_time=elapsed)
        finally:
            with suppress(Exception):
                s.close()

    def scan(self, host: str, ports: List[int],
             progress: Optional[ProgressBar] = None) -> List[PortResult]:
        results = []
        for port in ports:
            res = self.scan_port(host, port)
            results.append(res)
            if res.state in (PortState.OPEN, PortState.OPEN_FILTERED):
                self.printer.port_open(res)
            if progress:
                progress.update()
        return sorted(results, key=lambda r: r.port)


# ─────────────────────────────────────────────
#  REPORT GENERATOR
# ─────────────────────────────────────────────

class ReportGenerator:
    def __init__(self, result: ScanResult):
        self.result = result

    # ── Terminal ──────────────────────────────

    def print_terminal(self):
        r = self.result
        open_ports = r.open_ports()
        filtered = r.filtered_ports()

        print(f"\n{'═'*65}")
        print(f"  {Color.BOLD}SCAN REPORT  —  {r.target}{Color.RESET}")
        print(f"{'═'*65}")
        print(f"  {Color.DIM}IP       :{Color.RESET}  {r.ip}")
        if r.hostname and r.hostname != r.target:
            print(f"  {Color.DIM}Hostname :{Color.RESET}  {r.hostname}")
        print(f"  {Color.DIM}Status   :{Color.RESET}  {Color.GREEN}Host is UP{Color.RESET}")
        if r.os_guess:
            print(f"  {Color.DIM}OS Guess :{Color.RESET}  {Color.YELLOW}{r.os_guess}{Color.RESET}")
        print(f"  {Color.DIM}Duration :{Color.RESET}  {r.duration:.2f}s")
        print(f"  {Color.DIM}Mode     :{Color.RESET}  {r.scan_mode}")
        print(f"{'─'*65}")

        if not open_ports:
            print(f"\n  {Color.YELLOW}No open ports found.{Color.RESET}\n")
        else:
            print(f"\n  {Color.BOLD}{'PORT':<10} {'STATE':<12} {'SERVICE':<20} {'VERSION/BANNER'}{Color.RESET}")
            print(f"  {'─'*62}")
            for p in open_ports:
                svc_name = p.service.name
                version = p.service.version or p.service.banner[:40] or ""
                port_str = f"{p.port}/{p.protocol}"
                print(
                    f"  {Color.CYAN}{port_str:<10}{Color.RESET}"
                    f"  {Color.GREEN}{'open':<12}{Color.RESET}"
                    f"  {svc_name:<20}"
                    f"  {Color.DIM}{version}{Color.RESET}"
                )
                if p.ssl_info:
                    tls = p.ssl_info
                    print(f"  {'':10}  {Color.MAGENTA}TLS:{Color.RESET} "
                          f"{tls.get('tls_version','?')} | "
                          f"Cipher: {tls.get('cipher_suite','?')[:40]}")
                    if tls.get("expires"):
                        print(f"  {'':10}  {Color.MAGENTA}Cert expires:{Color.RESET} {tls['expires']}")

        # CVE hints
        cve_shown = set()
        for p in open_ports:
            svc = p.service.name.lower()
            hints = CVE_HINTS.get(svc, [])
            for h in hints:
                if h not in cve_shown:
                    cve_shown.add(h)

        if cve_shown:
            print(f"\n  {Color.BOLD}{'─'*62}{Color.RESET}")
            print(f"  {Color.YELLOW}{Color.BOLD}⚑  SECURITY NOTES{Color.RESET}")
            for note in cve_shown:
                print(f"  {Color.YELLOW}•{Color.RESET}  {note}")

        if filtered:
            print(f"\n  {Color.DIM}{len(filtered)} filtered port(s) not shown{Color.RESET}")

        print(f"\n{'═'*65}")
        print(f"  Summary: {Color.GREEN}{len(open_ports)} open{Color.RESET}  |  "
              f"{Color.YELLOW}{len(filtered)} filtered{Color.RESET}  |  "
              f"Total scanned: {len(r.ports)}")
        print(f"{'═'*65}\n")

    # ── JSON ──────────────────────────────────

    def to_json(self, path: str):
        r = self.result

        def serialize(obj):
            if isinstance(obj, PortState):
                return obj.value
            if isinstance(obj, (datetime.datetime, datetime.date)):
                return obj.isoformat()
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

        data = {
            "meta": {
                "tool": "MHScan v2.0",
                "author": "Mohammed Hany",
                "scan_date": r.start_time,
            },
            "target": {
                "input": r.target,
                "ip": r.ip,
                "hostname": r.hostname,
                "os_guess": r.os_guess,
                "host_status": r.host_status,
            },
            "scan": {
                "mode": r.scan_mode,
                "start": r.start_time,
                "end": r.end_time,
                "duration_sec": round(r.duration, 3),
            },
            "results": {
                "open_count": len(r.open_ports()),
                "filtered_count": len(r.filtered_ports()),
                "total_scanned": len(r.ports),
                "ports": [
                    {
                        "port": p.port,
                        "protocol": p.protocol,
                        "state": p.state.value,
                        "service": p.service.name,
                        "version": p.service.version,
                        "banner": p.service.banner,
                        "response_ms": round(p.response_time * 1000, 2),
                        "ssl": p.ssl_info,
                    }
                    for p in r.open_ports()
                ]
            }
        }

        with open(path, "w") as f:
            json.dump(data, f, indent=2, default=serialize)
        return path

    # ── CSV ───────────────────────────────────

    def to_csv(self, path: str):
        with open(path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "target", "ip", "port", "protocol", "state",
                "service", "version", "banner", "response_ms", "tls_version"
            ])
            for p in self.result.open_ports():
                tls_ver = p.ssl_info.get("tls_version", "") if p.ssl_info else ""
                writer.writerow([
                    self.result.target,
                    self.result.ip,
                    p.port,
                    p.protocol,
                    p.state.value,
                    p.service.name,
                    p.service.version,
                    p.service.banner[:100],
                    round(p.response_time * 1000, 2),
                    tls_ver,
                ])
        return path

    # ── HTML ──────────────────────────────────

    def to_html(self, path: str):
        r = self.result
        open_ports = r.open_ports()
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        rows = ""
        for p in open_ports:
            tls_badge = ""
            if p.ssl_info:
                tls_badge = f'<span class="badge tls">{p.ssl_info.get("tls_version","TLS")}</span>'
            banner_text = (p.service.version or p.service.banner or "")[:80]
            rows += f"""
            <tr>
              <td><span class="port">{p.port}</span><span class="proto">/{p.protocol}</span></td>
              <td><span class="badge open">open</span></td>
              <td>{p.service.name}</td>
              <td class="banner">{banner_text} {tls_badge}</td>
              <td>{p.response_time*1000:.1f} ms</td>
            </tr>"""

        cve_items = ""
        shown = set()
        for p in open_ports:
            for note in CVE_HINTS.get(p.service.name.lower(), []):
                if note not in shown:
                    cve_items += f"<li>{note}</li>"
                    shown.add(note)

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>MHScan Report — {r.target}</title>
<style>
  :root {{
    --bg: #0d1117; --card: #161b22; --border: #30363d;
    --text: #c9d1d9; --green: #3fb950; --yellow: #d29922;
    --cyan: #58a6ff; --red: #f85149; --purple: #bc8cff;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ background: var(--bg); color: var(--text); font-family: 'Courier New', monospace; padding: 2rem; }}
  h1 {{ color: var(--cyan); font-size: 1.8rem; margin-bottom: 0.3rem; }}
  .sub {{ color: #8b949e; font-size: 0.85rem; margin-bottom: 2rem; }}
  .meta {{ display: flex; gap: 2rem; background: var(--card);
           border: 1px solid var(--border); border-radius: 8px;
           padding: 1.2rem 1.5rem; margin-bottom: 1.5rem; flex-wrap: wrap; }}
  .meta-item label {{ display: block; color: #8b949e; font-size: 0.75rem; text-transform: uppercase; }}
  .meta-item span {{ font-size: 1rem; color: var(--text); }}
  table {{ width: 100%; border-collapse: collapse; background: var(--card);
           border: 1px solid var(--border); border-radius: 8px; overflow: hidden; }}
  th {{ background: #21262d; color: #8b949e; padding: 0.7rem 1rem;
        text-align: left; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; }}
  td {{ padding: 0.6rem 1rem; border-top: 1px solid var(--border); font-size: 0.88rem; }}
  tr:hover td {{ background: #1c2128; }}
  .port {{ color: var(--cyan); font-weight: bold; }}
  .proto {{ color: #8b949e; }}
  .badge {{ border-radius: 4px; padding: 2px 8px; font-size: 0.75rem; font-weight: bold; }}
  .open {{ background: rgba(63,185,80,0.15); color: var(--green); border: 1px solid rgba(63,185,80,0.3); }}
  .tls  {{ background: rgba(188,140,255,0.15); color: var(--purple); border: 1px solid rgba(188,140,255,0.3); }}
  .banner {{ color: #8b949e; font-size: 0.82rem; }}
  .cve-section {{ margin-top: 1.5rem; background: var(--card);
                  border: 1px solid var(--border); border-radius: 8px; padding: 1.2rem 1.5rem; }}
  .cve-section h3 {{ color: var(--yellow); margin-bottom: 0.8rem; }}
  .cve-section li {{ margin: 0.4rem 0 0 1.2rem; color: #8b949e; font-size: 0.88rem; }}
  footer {{ text-align: center; margin-top: 2rem; color: #30363d; font-size: 0.8rem; }}
</style>
</head>
<body>
  <h1>⚡ MHScan Report</h1>
  <div class="sub">Generated {now} by Mohammed Hany</div>

  <div class="meta">
    <div class="meta-item"><label>Target</label><span>{r.target}</span></div>
    <div class="meta-item"><label>IP</label><span>{r.ip}</span></div>
    <div class="meta-item"><label>Hostname</label><span>{r.hostname or "—"}</span></div>
    <div class="meta-item"><label>OS Guess</label><span>{r.os_guess or "Unknown"}</span></div>
    <div class="meta-item"><label>Scan Mode</label><span>{r.scan_mode}</span></div>
    <div class="meta-item"><label>Duration</label><span>{r.duration:.2f}s</span></div>
    <div class="meta-item"><label>Open Ports</label><span style="color:var(--green)">{len(open_ports)}</span></div>
    <div class="meta-item"><label>Total Scanned</label><span>{len(r.ports)}</span></div>
  </div>

  <table>
    <thead><tr>
      <th>Port</th><th>State</th><th>Service</th><th>Version / Banner</th><th>Response</th>
    </tr></thead>
    <tbody>{rows if rows else '<tr><td colspan="5" style="text-align:center;color:#8b949e;">No open ports found</td></tr>'}</tbody>
  </table>

  {"<div class='cve-section'><h3>⚑ Security Notes</h3><ul>" + cve_items + "</ul></div>" if cve_items else ""}

  <footer>MHScan v2.0 — Built by Mohammed Hany for Bug Bounty &amp; Security Research</footer>
</body>
</html>"""

        with open(path, "w") as f:
            f.write(html)
        return path


# ─────────────────────────────────────────────
#  MAIN SCANNER ORCHESTRATOR
# ─────────────────────────────────────────────

class MHScan:
    def __init__(self, args):
        self.args = args
        self.printer = LivePrinter(verbose=args.verbose)

    def run(self):
        print(BANNER)

        target = self.args.target
        ports = parse_port_range(self.args.ports)
        threads = self.args.threads
        timeout = self.args.timeout
        mode = self.args.mode
        output_format = self.args.output
        output_dir = Path(self.args.output_dir)
        grab_banners = not self.args.no_banners
        skip_host_check = self.args.skip_host_check

        output_dir.mkdir(parents=True, exist_ok=True)

        # ── Resolve host ──────────────────────
        self.printer.info(f"Resolving target: {Color.CYAN}{target}{Color.RESET}")
        try:
            ip, hostname = HostResolver.resolve(target)
        except ValueError as e:
            self.printer.error(str(e))
            sys.exit(1)

        self.printer.success(f"Target: {Color.CYAN}{target}{Color.RESET}  →  IP: {Color.GREEN}{ip}{Color.RESET}"
                             + (f"  |  Hostname: {hostname}" if hostname and hostname != target else ""))

        # ── Host liveness ─────────────────────
        if not skip_host_check:
            self.printer.info("Checking host liveness...")
            alive = HostResolver.is_alive(ip)
            if not alive:
                self.printer.warn(f"Host {ip} appears to be DOWN or blocking probes. Use --skip-host-check to force scan.")
                if not self.args.force:
                    sys.exit(0)

        # ── OS fingerprint via TTL ────────────
        os_guess = ""
        ttl = get_ttl(ip)
        if ttl:
            os_guess = guess_os_from_ttl(ttl)
            self.printer.info(f"TTL={ttl}  →  OS guess: {Color.YELLOW}{os_guess}{Color.RESET}")

        # ── Prepare result object ─────────────
        start_time = datetime.datetime.now().isoformat()
        result = ScanResult(
            target=target, ip=ip, hostname=hostname,
            scan_mode=mode, start_time=start_time, os_guess=os_guess
        )

        self.printer.info(f"Scanning {Color.CYAN}{len(ports)}{Color.RESET} ports  |  "
                          f"threads={threads}  timeout={timeout}s  mode={mode}")

        if self.args.randomize:
            random.shuffle(ports)
            self.printer.info("Port order: randomized (stealth)")

        print(f"\n  {Color.BOLD}{'PORT':<10} {'STATE':<12} {'SERVICE':<20} {'VERSION/BANNER'}{Color.RESET}")
        print(f"  {'─'*62}")

        t_start = time.time()
        progress = ProgressBar(total=len(ports), label="Scanning")

        # ── TCP Scan ──────────────────────────
        if mode in ("tcp", "full"):
            scanner = TCPConnectScanner(
                timeout=timeout, threads=threads,
                grab_banners=grab_banners, verbose=self.args.verbose
            )

            def handle_sigint(sig, frame):
                print(f"\n\n{Color.YELLOW}[!] Scan interrupted by user.{Color.RESET}")
                scanner.stop()

            signal.signal(signal.SIGINT, handle_sigint)

            tcp_results = scanner.scan(ip, ports, progress=progress)
            result.ports.extend(tcp_results)

        # ── UDP Scan ──────────────────────────
        if mode in ("udp", "full"):
            udp_ports = UDPScanner.COMMON_UDP_PORTS
            self.printer.info(f"Running UDP scan on {len(udp_ports)} common UDP ports...")
            udp_progress = ProgressBar(len(udp_ports), "UDP Scan")
            udp_scanner = UDPScanner(timeout=timeout)
            udp_results = udp_scanner.scan(ip, udp_ports, udp_progress)
            result.ports.extend(udp_results)

        t_end = time.time()
        result.end_time = datetime.datetime.now().isoformat()
        result.duration = t_end - t_start

        # ── Reports ───────────────────────────
        reporter = ReportGenerator(result)
        reporter.print_terminal()

        base_name = f"mhscan_{target.replace('.', '_').replace(':', '_')}_{int(time.time())}"

        if output_format in ("json", "all"):
            path = str(output_dir / f"{base_name}.json")
            reporter.to_json(path)
            self.printer.success(f"JSON saved → {path}")

        if output_format in ("csv", "all"):
            path = str(output_dir / f"{base_name}.csv")
            reporter.to_csv(path)
            self.printer.success(f"CSV  saved → {path}")

        if output_format in ("html", "all"):
            path = str(output_dir / f"{base_name}.html")
            reporter.to_html(path)
            self.printer.success(f"HTML saved → {path}")

        return result


# ─────────────────────────────────────────────
#  CLI ARGUMENT PARSER
# ─────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mhscan",
        description=f"{Color.BOLD}MHScan v2.0{Color.RESET} — Advanced Port Scanner by Mohammed Hany",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=f"""
{Color.CYAN}Examples:{Color.RESET}
  python mhscan.py scanme.nmap.org
  python mhscan.py 192.168.1.1 -p 1-1024 -t 300
  python mhscan.py target.com -p top100 --mode full -o all
  python mhscan.py 10.0.0.1 -p 22,80,443,8080-8090 --no-banners
  python mhscan.py example.com -p all --threads 500 --timeout 0.8
        """
    )

    parser.add_argument("target", help="Target hostname or IP address")
    parser.add_argument("-p", "--ports",
                        default="top100",
                        help="Ports to scan. Examples:\n"
                             "  top100  (default)\n"
                             "  top1000\n"
                             "  all (1-65535)\n"
                             "  common (well-known only)\n"
                             "  1-1024\n"
                             "  22,80,443,8080")
    parser.add_argument("--mode", "-m",
                        choices=["tcp", "udp", "full"],
                        default="tcp",
                        help="Scan mode (default: tcp)")
    parser.add_argument("--threads", "-t",
                        type=int, default=200,
                        help="Number of concurrent threads (default: 200)")
    parser.add_argument("--timeout",
                        type=float, default=1.5,
                        help="Socket timeout in seconds (default: 1.5)")
    parser.add_argument("--output", "-o",
                        choices=["terminal", "json", "csv", "html", "all"],
                        default="terminal",
                        help="Output format (default: terminal)")
    parser.add_argument("--output-dir",
                        default="./mhscan_results",
                        help="Directory for output files (default: ./mhscan_results)")
    parser.add_argument("--no-banners",
                        action="store_true",
                        help="Skip banner grabbing (faster)")
    parser.add_argument("--randomize", "-r",
                        action="store_true",
                        help="Randomize port scan order (stealth)")
    parser.add_argument("--skip-host-check",
                        action="store_true",
                        help="Skip host liveness check")
    parser.add_argument("--force", "-f",
                        action="store_true",
                        help="Force scan even if host appears down")
    parser.add_argument("--verbose", "-v",
                        action="store_true",
                        help="Verbose output (show filtered ports)")

    return parser


# ─────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────

def main():
    parser = build_parser()
    if len(sys.argv) == 1:
        print(BANNER)
        parser.print_help()
        sys.exit(0)

    args = parser.parse_args()
    scanner = MHScan(args)
    scanner.run()


if __name__ == "__main__":
    main()
