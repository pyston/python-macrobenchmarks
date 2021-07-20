import os.path

import pyperf
#from pylint import epylint as lint
from pylint.lint import Run


DATADIR = os.path.join(
    os.path.dirname(__file__),
    "data",
)
TARGET = os.path.join(DATADIR, "pylint_target", "dist.py")


"""
pylint benchmark

pylint seems to speed up considerably as it progresses, and this
benchmark includes that
"""

def bench_pylint(loops=10):
    class NullReporter:
        path_strip_prefix = "/"
        def __getattr__(self, attr, _noop=(lambda *a, **k: None)):
            return _noop
    reporter = NullReporter()
    _run = Run
    loops = iter(range(loops))

    t0 = pyperf.perf_counter()
    for _ in loops:
        _run([TARGET], exit=False, reporter=reporter)
    return pyperf.perf_counter() - t0


if __name__ == "__main__":
    runner = pyperf.Runner()
    runner.metadata['description'] = "Test the performance of pylint"
    runner.bench_time_func("pylint", bench_pylint)
