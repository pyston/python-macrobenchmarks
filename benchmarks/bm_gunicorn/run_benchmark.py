import os.path
import requests
import sys

import pyperf
import netutils


DATADIR = os.path.join(
    os.path.dirname(__file__),
    "data",
)
GUNICORN = os.path.join(
    os.path.dirname(sys.executable),
    "gunicorn",
)
ADDR = "127.0.0.1:8000"
ARGV = [
    GUNICORN, "serve_aiohttp:main",
    "--bind", ADDR,
    "-w", "1",
    "--worker-class", "aiohttp.GunicornWebWorker",
]


def bench_gunicorn(loops=3000):
    loops = iter(range(loops))
    with netutils.serving(ARGV, DATADIR, ADDR):
        t0 = pyperf.perf_counter()
        for _ in loops:
            requests.get("http://localhost:8000/blog/").text
        return pyperf.perf_counter() - t0


if __name__ == "__main__":
    runner = pyperf.Runner()
    runner.metadata['description'] = "Test the performance of gunicorn"
    #runner.bench_func("gunicorn", bench_gunicorn)
    runner.bench_time_func("gunicorn", bench_gunicorn)
