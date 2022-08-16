import os.path

import pyperf
from mypy.main import main


DATADIR = os.path.join(
    os.path.dirname(__file__),
    "data",
)
"""
I tested it, and it looks like we get the same performance conclusions
when we run on the same file multiple times as if we run on a set of files once.

So for convenience run on a single file multiple times.
"""
TARGETS = [
    os.path.join(DATADIR, "mypy_target.py"),
]


#############################
# benchmarks

def bench_mypy(loops=20):
    elapsed, _ = _bench_mypy(loops)
    return elapsed


def _bench_mypy(loops=20, *, legacy=False):
    """Meansure running mypy on a file N times.

    The target file is large (over 2300 lines) with extensive use
    of type hints.

    Note that mypy's main() is called directly, which means
    the measurement includes the time it takes to read the file
    from disk.  Also, all output is discarded (sent to /dev/null).
    """
    elapsed = 0
    times = []
    with open(os.devnull, "w") as devnull:
        for i in range(loops):
            if legacy:
                print(i)
            # This is a macro benchmark for a Python implementation
            # so "elapsed" covers more than just how long main() takes.
            t0 = pyperf.perf_counter()
            try:
                main(None, devnull, devnull, TARGETS, clean_exit=True)
            except SystemExit:
                pass
            t1 = pyperf.perf_counter()

            elapsed += t1 - t0
            times.append(t0)
        times.append(pyperf.perf_counter())
    return elapsed, times


#############################
# the script

if __name__ == "__main__":
    from legacyutils import maybe_handle_legacy
    maybe_handle_legacy(_bench_mypy, legacyarg='legacy')

    runner = pyperf.Runner()
    runner.metadata['description'] = "Test the performance of mypy types"
    runner.bench_time_func("mypy", bench_mypy)
