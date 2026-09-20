"""
URL security, validation, and SSRF prevention utility.
Protects against server-side request forgery, localhost access, and invalid schemes.
"""

import ipaddress
import socket
import urllib.parse
from typing import Tuple, Optional


PRIVATE_NETWORKS = [
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
]


def is_safe_url(url: str) -> Tuple[bool, Optional[str]]:
    """
    Validates URL safety against SSRF and invalid formats.
    Returns (is_safe, error_reason).
    """
    if not url or not isinstance(url, str):
        return False, "URL cannot be empty"

    try:
        parsed = urllib.parse.urlparse(url.strip())
    except Exception as e:
        return False, f"Malformed URL: {str(e)}"

    # Scheme check
    if parsed.scheme.lower() not in ("http", "https"):
        return False, f"Invalid URL scheme '{parsed.scheme}'. Only http and https are allowed."

    hostname = parsed.hostname
    if not hostname:
        return False, "URL is missing a valid hostname"

    # Reject localhost directly
    if hostname.lower() in ("localhost", "127.0.0.1", "0.0.0.0", "::1"):
        return False, "Access to localhost or loopback addresses is forbidden"

    # Resolve IP and verify not private / local
    try:
        # Check if hostname is an IP string
        try:
            ip_obj = ipaddress.ip_address(hostname)
            for net in PRIVATE_NETWORKS:
                if ip_obj in net:
                    return False, "Access to private IP networks is forbidden"
            if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_reserved:
                return False, "Access to private or reserved IP address is forbidden"
        except ValueError:
            # Hostname is a domain name, resolve DNS
            resolved_ips = socket.getaddrinfo(hostname, None)
            for item in resolved_ips:
                ip_str = item[4][0]
                ip_obj = ipaddress.ip_address(ip_str)
                for net in PRIVATE_NETWORKS:
                    if ip_obj in net:
                        return False, f"Resolved IP {ip_str} belongs to a private network"
                if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_reserved:
                    return False, f"Resolved IP {ip_str} is private or reserved"
    except socket.gaierror:
        # Domain cannot be resolved; will fail upon request
        pass
    except Exception:
        # Pass resolution exceptions gracefully
        pass

    return True, None


def normalize_url(url: str) -> str:
    """Standardizes URL by trimming, converting scheme/host to lowercase, and stripping fragments."""
    if not url:
        return ""
    try:
        parsed = urllib.parse.urlparse(url.strip())
        scheme = parsed.scheme.lower()
        netloc = parsed.netloc.lower()
        # Remove standard tracking query params like utm_*
        query_params = urllib.parse.parse_qsl(parsed.query)
        clean_params = [
            (k, v) for k, v in query_params 
            if not k.lower().startswith("utm_") and k.lower() not in ("fbclid", "gclid", "ref")
        ]
        new_query = urllib.parse.urlencode(clean_params)
        normalized = urllib.parse.urlunparse((
            scheme,
            netloc,
            parsed.path,
            parsed.params,
            new_query,
            "" # strip fragment
        ))
        return normalized
    except Exception:
        return url.strip()
