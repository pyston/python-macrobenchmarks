import os
import os.path

import pyperf
from pycparser import c_parser, c_ast


DATADIR = os.path.join(
    os.path.dirname(__file__),
    "data",
)
TARGET = os.path.join(DATADIR, "pycparser_target")


def _iter_files(rootdir=TARGET, *, _cache={}):
    if not _cache:
        files = _cache['files'] = []
        for name in os.listdir(rootdir):
            if not name.endswith(".ppout"):
                continue
            filename = os.path.join(TARGET, name)
            with open(filename) as f:
                data = (filename, f.read())
                files.append(data)
                yield data
    else:
        yield from _cache['files']


def bench_pycparser(loops=20):
    """Measure running pycparser on several large C files N times.

    The files are all relatively large, from well-known projects.
    Each is already preprocessed.

    Only the CParser.parse() calls are measured.  The following are not:

    * finding the target files
    * reading them from disk
    * creating the CParser object
    """
    elapsed = 0
    parse = c_parser.CParser.parse
    for _ in range(loops):
        for filename, text in _iter_files():
            # We use a new parser each time because CParser objects
            # aren't designed for re-use.
            parser = c_parser.CParser()
            t0 = pyperf.perf_counter()
            ast = parse(parser, text, filename)
            elapsed += pyperf.perf_counter() - t0
            assert isinstance(ast, c_ast.FileAST)
    return elapsed


if __name__ == "__main__":
    runner = pyperf.Runner()
    runner.metadata['description'] = "Test the performance of pycparser"
    runner.bench_time_func("pycparser", bench_pycparser)
