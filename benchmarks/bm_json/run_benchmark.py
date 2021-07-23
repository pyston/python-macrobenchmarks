import json
import os.path

import pyperf


DATADIR = os.path.join(
    os.path.dirname(__file__),
    "data",
)
TARGET = os.path.join(DATADIR, "reddit_comments.json")


def bench_json_loads(loops=400):
    """Measure running json.loads() N times.

    The target data is nearly 1100 JSON objects, each on a single line,
    from a file.  The objects:
    
    * are all flat (no compound values)
    * vary a little in number of properties, though none are big
    * have a mix of values, both of type and size

    Only the json.loads() calls are measured.  The following are not:

    * reading the text from the file
    * looping through the lines
    """
    with open(TARGET) as f:
        s = f.read()
#    data = s.split('\n')
    data = s.splitlines()

    elapsed = 0
    json_loads = json.loads
    for _ in range(loops):
        for s in data:
            if not s:
                continue
            t0 = pyperf.perf_counter()
            json_loads(s)
            elapsed += pyperf.perf_counter() - t0
    return elapsed


if __name__ == "__main__":
    runner = pyperf.Runner()
    runner.metadata['description'] = "Test the performance of json"
    runner.bench_time_func("json", bench_json_loads)
