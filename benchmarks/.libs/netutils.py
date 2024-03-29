import contextlib
import ipaddress
import os.path
import socket
import subprocess
import time


@contextlib.contextmanager
def serving(argv, sitedir, addr, *,
            pause=None,
            kill=False,
            quiet=True,
            ):
    if os.path.exists(addr):
        sock = addr
        addr = None
        try:
            os.remove(sock)
        except FileNotFoundError:
            pass
    else:
        sock = None

    p = subprocess.Popen(
        argv,
        cwd=sitedir,
        stdout=subprocess.DEVNULL if quiet else None,
        stderr=subprocess.STDOUT if quiet else None,
    )
    try:
        if pause:
            time.sleep(pause)
        if not sock:
            try:
                waitUntilUp(addr)
            except NotImplementedError:
                sock = addr
                addr = None
        if sock:
            while not os.path.exists(sock):
                time.sleep(0.001)
        assert p.poll() is None, p.poll()
        yield
        assert p.poll() is None, p.poll()
    finally:
        p.terminate()
        if kill:
            p.kill()
        p.wait()


def waitUntilUp(addr, timeout=10.0):
    end = time.time() + timeout
    addr = parse_socket_addr(addr)
    started = False
    current = time.time()
    while not started or current <= end:
        try:
            with socket.create_connection(addr) as sock:
                return
        except ConnectionRefusedError:
            time.sleep(0.001)
        started = True
        current = time.time()
    raise Exception('Timeout reached when trying to connect')


def parse_socket_addr(addr, *, resolve=True):
    if not isinstance(addr, str):
        raise NotImplementedError(addr)
    host, _, port = addr.partition(':')

    if not host:
        raise NotImplementedError(addr)
    try:
        host = ipaddress.ip_address(host)
    except ValueError:
        raise NotImplementedError(addr)
    host = str(host)

    if not port:
        raise NotImplementedError(addr)
    if not port.isdigit():
        raise NotImplementedError(addr)
    port = int(port)

    return (host, port)
