import json
import os.path

import pyperf


DATADIR = os.path.join(
    os.path.dirname(__file__),
    "data",
)
TARGET = os.path.join(DATADIR, "reddit_comments.json")


def bench_json(loops=400):
    with open(TARGET) as f:
        s = f.read()
    data = s.split('\n')

    json_loads = json.loads
    loops = iter(range(loops))
    t0 = pyperf.perf_counter()
    for _ in loops:
        for s in data:
            if not s:
                continue
            json_loads(s)
    return pyperf.perf_counter() - t0


if __name__ == "__main__":
    runner = pyperf.Runner()
    runner.metadata['description'] = "Test the performance of json"
    runner.bench_time_func("json", bench_json)
