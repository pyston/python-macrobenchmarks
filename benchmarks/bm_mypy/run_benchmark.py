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


def bench_mypy(devnull):
    """Meansure running mypy on a file N times.

    The target file is large (over 2300 lines) with extensive use
    of type hints.

    Note that mypy's main() is called directly, which means
    the measurement includes the time it takes to read the file
    from disk.  Also, all output is discarded (sent to /dev/null).
    """
    try:
        main(None, devnull, devnull, TARGETS)
    except SystemExit:
        pass


if __name__ == "__main__":
    runner = pyperf.Runner()
    runner.metadata['description'] = "Test the performance of mypy types"
    runner.argparser.add_argument("loops", nargs="?", type=int, default=1)
    args = runner.argparser.parse_args()

    with open(os.devnull, "w") as devnull:
        runner.bench_func("mypy", bench_mypy, devnull,
                          inner_loops=args.loops)
