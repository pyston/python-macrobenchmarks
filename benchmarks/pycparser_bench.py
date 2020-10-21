import json
import os
import sys
import time

from pycparser import c_parser, c_ast

def parse_files(files):
    for code in files:
        parser = c_parser.CParser()
        ast = parser.parse(code, '')
        assert isinstance(ast, c_ast.FileAST)

if __name__ == "__main__":
    n = 20
    if len(sys.argv) > 1:
        n = int(sys.argv[1])

    files = []
    directory = os.path.abspath(__file__ + "/../../data/pycparser_target")
    for filename in os.listdir(directory):
        filename = os.path.join(directory, filename)
        if not filename.endswith(".ppout"):
            continue
        with open(filename) as f:
            files.append(f.read())

    times = []
    for i in range(n):
        times.append(time.time())
        
        parse_files(files)

    times.append(time.time())

    if len(sys.argv) > 2:
        json.dump(times, open(sys.argv[2], 'w'))
