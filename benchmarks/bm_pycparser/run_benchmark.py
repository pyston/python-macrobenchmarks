import os
import os.path

import pyperf
from pycparser import c_parser, c_ast


DATADIR = os.path.join(
    os.path.dirname(__file__),
    "data",
)
TARGET = os.path.join(DATADIR, "pycparser_target")


def parse_files(files):
    for code in files:
        parser = c_parser.CParser()
        ast = parser.parse(code, '')
        assert isinstance(ast, c_ast.FileAST)


def bench_pycparser(loops=20):
    files = []
    for filename in os.listdir(TARGET):
        filename = os.path.join(TARGET, filename)
        if not filename.endswith(".ppout"):
            continue
        with open(filename) as f:
            files.append(f.read())

    _parse = parse_files
    loops = iter(range(loops))
    t0 = pyperf.perf_counter()
    for _ in loops:
        _parse(files)
    return pyperf.perf_counter() - t0


if __name__ == "__main__":
    runner = pyperf.Runner()
    runner.metadata['description'] = "Test the performance of pycparser"
    runner.bench_time_func("pycparser", bench_pycparser)
