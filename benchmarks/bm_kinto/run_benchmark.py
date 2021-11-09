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
    os.path.dirname(__file__),
    "data",
)
SETUP_PY = os.path.join(DATADIR, "setup.py")
PRODUCTION_INI = os.path.join(DATADIR, "production.ini")
NGINX_CONF = os.path.join(DATADIR, "nginx.conf")


def bench_kinto(loops=5000):
    elapsed = 0

    subprocess.check_call(
        [PYTHON, SETUP_PY, "develop"],
        cwd=DATADIR,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
    )

    cmd_app = [UWSGI, PRODUCTION_INI]
    cmd_web = [NGINX, "-c", NGINX_CONF, "-p", DATADIR]
    with netutils.serving(cmd_app, DATADIR, SOCK, kill=True):
        with netutils.serving(cmd_web, DATADIR, ADDR, pause=0.010, quiet=False):
            print(requests.get("http://localhost:8000/v1").text)
            # print(requests.put("http://localhost:8000/v1/accounts/testuser", json={"data": {"password": "password1"}}).text)

            for _ in range(loops):
                t0 = pyperf.perf_counter()
                # requests.get("http://localhost:8000/v1/").text
                urllib.request.urlopen("http://localhost:8000/v1/").read()
                elapsed += pyperf.perf_counter() - t0

    return elapsed


if __name__ == "__main__":
    if NGINX is None:
        raise Exception("nginx is not installed")
    runner = pyperf.Runner()
    runner.metadata['description'] = "Test the performance of kinto"
    runner.bench_time_func("kinto", bench_kinto)
