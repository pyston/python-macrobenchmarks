import os.path

import pyperf
from mypy.main import main


DATADIR = os.path.join(
    os.path.dirname(__file__),
    "data",
)
TARGET = os.path.join(DATADIR, "mypy_target.py")


def bench_mypy(devnull):
    try:
        main(None, devnull, devnull, [TARGET])
    except SystemExit:
        pass


#def bench_mypy(loops, devnull):
#    range_it = range(loops)
#    t0 = pyperf.perf_counter()
#    for _ in range_it:
#        try:
#            main(None, devnull, devnull, [TARGET])
#        except SystemExit:
#            pass
#    return pyperf.perf_counter() - t0


"""
I tested it, and it looks like we get the same performance conclusions
when we run on the same file multiple times as if we run on a set of files once.

So for convenience run on a single file multiple times.
"""


if __name__ == "__main__":
    runner = pyperf.Runner()
    runner.metadata['description'] = "Test the performance of mypy types"
    with open(os.devnull, "w") as devnull:
        # XXX 20 loops (by default)?
        runner.bench_func("mypy", bench_mypy, devnull)
#        runner.bench_time_func("mypy", bench_mypy, devnull)
