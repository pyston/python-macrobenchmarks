import os
import os.path

import pyperf
from pycparser import c_parser, c_ast


DATADIR = os.path.join(
    os.path.dirname(__file__),
    "data",
)
TARGET = os.path.join(DATADIR, "pycparser_target")


def _iter_files(rootdir=TARGET):
    for name in os.listdir(rootdir):
        if not name.endswith(".ppout"):
            continue
        filename = os.path.join(TARGET, name)
        with open(filename) as f:
            yield (filename, f.read())


def parse_files(files):
    for _, text in files:
        # We use a new parser each time because CParser objects
        # aren't designed for re-use.
        parser = c_parser.CParser()
        ast = parser.parse(text, '')
        assert isinstance(ast, c_ast.FileAST)


#############################
# benchmarks

def bench_pycparser(loops=20):
    elapsed, _ = _bench_pycparser(loops)
    return elapsed


def _bench_pycparser(loops=20):
    """Measure running pycparser on several large C files N times.

    The files are all relatively large, from well-known projects.
    Each is already preprocessed.

    Only the CParser.parse() calls are measured.  The following are not:

    * finding the target files
    * reading them from disk
    * creating the CParser object
    """
    files = list(_iter_files())

    elapsed = 0
    times = []
    for _ in range(loops):
        times.append(pyperf.perf_counter())
        # This is a macro benchmark for a Python implementation
        # so "elapsed" covers more than just how long parser.parse() takes.
        t0 = pyperf.perf_counter()
        parse_files(files)
        t1 = pyperf.perf_counter()

        elapsed += t1 - t0
    times.append(pyperf.perf_counter())
    return elapsed, times


#############################
# the script

if __name__ == "__main__":
    from legacyutils import maybe_handle_legacy
    maybe_handle_legacy(_bench_pycparser)

    runner = pyperf.Runner()
    runner.metadata['description'] = "Test the performance of pycparser"
    runner.bench_time_func("pycparser", bench_pycparser)
