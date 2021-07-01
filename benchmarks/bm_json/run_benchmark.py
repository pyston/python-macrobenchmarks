import json
import os
import sys
import time

if __name__ == "__main__":
    exe = sys.executable

    times = []

    with open(os.path.join(os.path.dirname(__file__), "../data/reddit_comments.json")) as f:
        s = f.read()

    data = s.split('\n')

    n = 400
    if len(sys.argv) > 1:
        n = int(sys.argv[1])

    times = []

    for i in range(n):
        times.append(time.time())
        for s in data:
            if not s:
                continue
            json.loads(s)
    times.append(time.time())

    if len(sys.argv) > 2:
        json.dump(times, open(sys.argv[2], 'w'))
