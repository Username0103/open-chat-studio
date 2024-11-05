# Copied from CommCare HQ: https://github.com/dimagi/commcare-hq/blob/master/corehq/util/urlvalidate/ip_resolver.py
import ipaddress
import socket


def resolve_to_ips(hostname, port=80):
    if len(hostname) > 255:
        raise CannotResolveHost("hostname too long")

    try:
        socket.setdefaulttimeout(10)
        address_tuples = socket.getaddrinfo(
            hostname,
            port,
            proto=socket.IPPROTO_TCP,  # Restrict to TCP
        )
    except socket.gaierror as e:
        raise CannotResolveHost(f"{hostname}: {str(e)}")
    except TimeoutError:
        raise CannotResolveHost(f"{hostname}: DNS resolution timed out")
    finally:
        socket.setdefaulttimeout(None)  # Reset timeout

    return [extract_ip(addr_info) for addr_info in address_tuples]


INDEX_SOCKADDR = 4
INDEX_ADDRESS = 0


def extract_ip(addr_info):
    return ipaddress.ip_address(addr_info[INDEX_SOCKADDR][INDEX_ADDRESS])


class CannotResolveHost(Exception):
    pass
