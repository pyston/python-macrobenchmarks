import json
import os
import sys
import time

"""
I tested it, and it looks like we get the same performance conclusions
when we run on the same file multiple times as if we run on a set of files once.

So for convenience run on a single file multiple times.
"""

if __name__ == "__main__":
    from mypy.main import main

    n = 20
    if len(sys.argv) > 1:
        n = int(sys.argv[1])
    target = os.path.join(os.path.dirname(__file__), "../data/mypy_target.py")

    times = []
    devnull = open("/dev/null", "w")
    for i in range(n):
        times.append(time.time())
        print(i)
        try:
            main(None, devnull, devnull, [target])
        except SystemExit:
            pass
    times.append(time.time())

    if len(sys.argv) > 2:
        json.dump(times, open(sys.argv[2], 'w'))
