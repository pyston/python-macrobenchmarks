import contextlib
import ipaddress
import re
import socket
import subprocess
import time
import urllib.parse


# See: https://validators.readthedocs.io/en/latest/_modules/validators/domain.html
DOMAIN_RE = re.compile(
    r'^(([a-zA-Z]{1})|([a-zA-Z]{1}[a-zA-Z]{1})|'
    r'([a-zA-Z]{1}[0-9]{1})|([0-9]{1}[a-zA-Z]{1})|'
    r'([a-zA-Z0-9][-_.a-zA-Z0-9]{0,61}[a-zA-Z0-9]))\.'
    r'([a-zA-Z]{2,13}|[a-zA-Z0-9-]{2,30}.[a-zA-Z]{2,3})$'
)

LOCALHOST = '127.0.0.1'
HTTP_PORT = 8080


@contextlib.contextmanager
def serving(argv, sitedir, addr='127.0.0.1'):
    p = subprocess.Popen(
        argv,
        cwd=sitedir,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
    )
    try:
        waitUntilUp(addr)
        yield
        assert p.poll() is None, p.poll()
    finally:
        p.terminate()
        p.wait()


def waitUntilUp(addr, timeout=10.0):
    end = time.time() + timeout
    addr = parse_socket_addr(addr)
    while True:
        try:
            with socket.create_connection(addr) as sock:
                return
        except ConnectionRefusedError:
            if time.time() > end:
                raise Exception("Timeout reached when trying to connect")
            time.sleep(0.001)


def parse_socket_addr(addr, *, resolve=True):
    orig = addr
    if not isinstance(addr, str):
        addr = _render_attr(addr)
    scheme, domain, ipaddr, port = _parse_addr(addr)

    domain, ipaddr = _resolve_hostname(domain, ipaddr, dns=resolve)
    hostname = ipaddr or domain or LOCALHOST
    port = _resolve_port(port, scheme, names=resolve)

    return hostname, port


def _resolve_port(port, scheme, *, names=False):
    if port is None:
        if not scheme or scheme in ('http', 'https'):
            return HTTP_PORT
        else:
            raise ValueError(f'missing port in {addr!r}')

    try:
        port = int(port)
    except (TypeError, ValueError):
        if not isinstance(port, str):
            raise  # re-raise
        if names:
            raise NotImplementedError
    # else check bounds?
    return port


def _parse_addr(addr):
    parsed = urllib.parse.urlparse(addr)
    scheme = parsed.scheme
    if not scheme:
        parsed = urllib.parse.urlparse(f'spam://{addr}')

    hostname = parsed.hostname
    try:
        port = parsed.port
    except ValueError:
        if hostname:
            raise NotImplementedError(addr)
        port = None

    if not hostname and not port:
        if not parsed.netloc:
            raise NotImplementedError(addr)
        hostname, _, port = parsed.netloc.partition(':')
        if port:
            if port.isdigit():
                port = int(port)
            elif port.isalpha():
                port = port.upper()
            else:
                raise NotImplementedError(addr)
        else:
            port = None

    domain = addr = None
    if hostname:
        try:
            ipaddress.ip_address(hostname)
        except ValueError:
            domain, err = _normalize_domainname(hostname)
            if err:
                raise ValueError(f'bad hostname in addr {addr!r}')
        else:
            addr = hostname

    return scheme, domain, addr, port


def _resolve_hostname(domain, addr=None, *, dns=False):
    if addr:
        # XXX Resolve other addresses?
        domain = 'localhost' if addr == LOCALHOST else None
    elif not domain:
        domain = 'localhost'
        addr = LOCALHOST
    elif domain.lower() == 'localhost':
        domain = 'localhost'
        addr = LOCALHOST
    elif dns:
        raise NotImplementedError
    else:
        raise ValueError(f'could not resolve hostname {domain!r}')
    return domain, addr


def _normalize_domainname(name):
    # See:
    #   * https://datatracker.ietf.org/doc/html/rfc3696#section-2
    if not name:
        raise ValueError('missing hostname')

    if name[-1] == '.':
        name = name[:-1]

    if len(name) > 253:
        err = f'domain name too long {name!r}'
    elif not DOMAIN_RE.match(name):
        err = f'invalid domain name {name!r}'
    else:
        err = None
    return name, err
