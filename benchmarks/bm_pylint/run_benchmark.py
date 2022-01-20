import os.path

import pyperf
#from pylint import epylint as lint
from pylint.lint import Run


DATADIR = os.path.join(
    os.path.dirname(__file__),
    "data",
)
TARGETS = [
    os.path.join(DATADIR, "pylint_target", "dist.py"),
]


def noop(*args, **kw):
    pass


class NullReporter:
    path_strip_prefix = "/"
    def __getattr__(self, attr):
        return noop


#############################
# benchmarks

def bench_pylint(loops=10):
    elapsed, _ = _bench_pylint(loops)
    return elapsed


def _bench_pylint(loops=10):
    """Measure running pylint on a file  N times.

    The target file is a relatively large, complex one copied
    from distutils in the stdlib.

    pylint seems to speed up considerably as it progresses, and this
    benchmark includes that.
    """
    elapsed = 0
    times = []
    for i in range(loops):
        print(i)
        # This is a macro benchmark for a Python implementation
        # so "elapsed" covers more than just how long Run() takes.
        t0 = pyperf.perf_counter()
        reporter = NullReporter()
        Run(TARGETS, exit=False, reporter=reporter)
        t1 = pyperf.perf_counter()

        elapsed += t1 - t0
        times.append(t0)
    times.append(pyperf.perf_counter())
    return elapsed, times


#############################
# the script

if __name__ == "__main__":
    from legacyutils import maybe_handle_legacy
    maybe_handle_legacy(_bench_pylint)

    runner = pyperf.Runner()
    runner.metadata['description'] = "Test the performance of pylint"
    runner.bench_time_func("pylint", bench_pylint)
