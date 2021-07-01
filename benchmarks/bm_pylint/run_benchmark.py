import json
import os
import subprocess
import sys
import time

from pylint import epylint as lint
from pylint.lint import Run

"""
pylint benchmark

pylint seems to speed up considerably as it progresses, and this
benchmark includes that
"""

if __name__ == "__main__":
    def noop(*args, **kw):
        pass
    class NullReporter:
        path_strip_prefix = "/"
        def __getattr__(self, attr):
            return noop

    n = 10
    if len(sys.argv) > 1:
        n = int(sys.argv[1])

    times = []
    for i in range(n):
        times.append(time.time())
        print(i)
        Run([os.path.join(os.path.dirname(__file__), "../data/pylint_target/dist.py")], exit=False, reporter=NullReporter())
    times.append(time.time())

    if len(sys.argv) > 2:
        json.dump(times, open(sys.argv[2], 'w'))
