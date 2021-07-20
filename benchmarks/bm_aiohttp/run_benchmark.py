import os.path
import requests
import sys

import pyperf
import netutils


DATADIR = os.path.join(
    os.path.dirname(__file__),
    "data",
)
ARGV = [sys.executable, "serve.py"]


def bench_aiohttp(loops=3000):
    loops = iter(range(loops))
    with netutils.serving(ARGV, DATADIR, "127.0.0.1:8080"):
        t0 = pyperf.perf_counter()
        for _ in loops:
            requests.get("http://localhost:8080/blog/").text
        return pyperf.perf_counter() - t0


if __name__ == "__main__":
    runner = pyperf.Runner()
    runner.metadata['description'] = "Test the performance of aiohttp"
    #runner.bench_func("aiohttp", bench_aiohttp)
    runner.bench_time_func("aiohttp", bench_aiohttp)
