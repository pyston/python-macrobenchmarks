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


#############################
# benchmarks

def bench_flask_requests(loops=1800):
    """Measure N HTTP requests to a local server.

    Note that the server is freshly started here.

    Only the time for requests is measured here.  The following are not:

    * preparing the site the server will serve
    * starting the server
    * stopping the server

    Hence this should be used with bench_time_func()
    insted of bench_func().
    """
    elapsed = 0
    with netutils.serving(ARGV, DATADIR, "127.0.0.1:8000"):
        requests_get = requests.get
        for _ in range(loops):
            t0 = pyperf.perf_counter()
            requests_get("http://localhost:8000/blog/").text
            elapsed += pyperf.perf_counter() - t0
    return elapsed


if __name__ == "__main__":
    runner = pyperf.Runner()
    runner.metadata['description'] = "Test the performance of flask"
    runner.bench_time_func("flaskblogging", bench_flask_requests)
