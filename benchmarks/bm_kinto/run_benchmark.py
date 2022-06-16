from contextlib import ExitStack
import os
import os.path
import requests
import shutil
import subprocess
import sys
import urllib

import pyperf
import netutils


PYTHON = os.path.abspath(sys.executable)
UWSGI = os.path.join(os.path.dirname(PYTHON), "uwsgi")
NGINX = shutil.which("nginx")

SOCK = "/tmp/kinto.sock"
ADDR = "127.0.0.1:8000"

DATADIR = os.path.join(
    os.path.abspath(os.path.dirname(__file__)),
    "data",
)
SETUP_PY = os.path.join(DATADIR, "setup.py")
PRODUCTION_INI = os.path.join(DATADIR, "production.ini")
NGINX_CONF = os.path.join(DATADIR, "nginx.conf")


#############################
# benchmarks

def bench_kinto(loops=5000):
    elapsed, _ = _bench_kinto(loops)
    return elapsed


def _bench_kinto(loops=5000, legacy=False):
    if legacy:
        print(requests.get("http://localhost:8000/v1").text)
        # print(requests.put("http://localhost:8000/v1/accounts/testuser", json={"data": {"password": "password1"}}).text)

    start = pyperf.perf_counter()
    elapsed = 0
    times = []
    for i in range(loops):
        # This is a macro benchmark for a Python implementation
        # so "elapsed" covers more than just how long a request takes.
        t0 = pyperf.perf_counter()
        # requests.get("http://localhost:8000/v1/").text
        urllib.request.urlopen("http://localhost:8000/v1/").read()
        t1 = pyperf.perf_counter()

        elapsed += t1 - t0
        times.append(t0)
        if legacy and (i % 100 == 0):
            print(i, t0 - start)
    times.append(pyperf.perf_counter())
    if legacy:
        total = times[-1] - start
        print("%.2fs (%.3freq/s)" % (total, loops / total))
    return elapsed, times


#############################
# the script

if __name__ == "__main__":
    from legacyutils import maybe_handle_legacy
    maybe_handle_legacy(_bench_kinto, legacyarg='legacy')

    if NGINX is None:
        raise Exception("nginx is not installed")

    with ExitStack() as stack:
        if "--worker" not in sys.argv:
            cmd = [PYTHON, SETUP_PY, "develop"]
            proc = subprocess.run(
                cmd,
                cwd=DATADIR,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.STDOUT,
            )

            if proc.returncode != 0:
                print(f'# running: {" ".join(cmd)} (in {DATADIR})')
                subprocess.run(cmd, cwd=DATADIR, check=True)

            cmd_app = [UWSGI, PRODUCTION_INI]
            stack.enter_context(netutils.serving(cmd_app, DATADIR, SOCK, kill=True))

            cmd_web = [NGINX, "-c", NGINX_CONF, "-p", DATADIR]
            stack.enter_context(netutils.serving(cmd_web, DATADIR, ADDR, pause=0.010, quiet=False))

        runner = pyperf.Runner()
        runner.metadata['description'] = "Test the performance of kinto"
        runner.bench_time_func("kinto", bench_kinto)
