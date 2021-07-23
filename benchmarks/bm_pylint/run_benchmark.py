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


def bench_pylint(loops=10):
    """Measure running pylint on a file  N times.

    The target file is a relatively large, complex one copied
    from distutils in the stdlib.

    pylint seems to speed up considerably as it progresses, and this
    benchmark includes that.
    """
    class NullReporter:
        path_strip_prefix = "/"
        def __getattr__(self, attr, _noop=(lambda *a, **k: None)):
            return _noop
    reporter = NullReporter()

    elapsed = 0
    _run = Run
    for _ in range(loops):
        t0 = pyperf.perf_counter()
        _run(TARGETS, exit=False, reporter=reporter)
        elapsed += pyperf.perf_counter() - t0
    return elapsed


if __name__ == "__main__":
    runner = pyperf.Runner()
    runner.metadata['description'] = "Test the performance of pylint"
    runner.bench_time_func("pylint", bench_pylint)
