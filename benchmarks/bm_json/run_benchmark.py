import json
import os.path

import pyperf


DATADIR = os.path.join(
    os.path.dirname(__file__),
    "data",
)
TARGET = os.path.join(DATADIR, "reddit_comments.json")


#############################
# benchmarks

def bench_json_loads(loops=400):
    elapsed, _ = _bench_json_loads(loops)
    return elapsed


def _bench_json_loads(loops=400):
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
    lines = s.splitlines()

    elapsed = 0
    times = []
    for _ in range(loops):
        # This is a macro benchmark for a Python implementation
        # so "elapsed" covers more than just how long json.loads() takes.
        t0 = pyperf.perf_counter()
        for text in lines:
            if not text:
                continue
            json.loads(text)
        t1 = pyperf.perf_counter()

        elapsed += t1 - t0
        times.append(t0)
    times.append(pyperf.perf_counter())
    return elapsed, times


#############################
# the script

if __name__ == "__main__":
    from legacyutils import maybe_handle_legacy
    maybe_handle_legacy(_bench_json_loads)

    runner = pyperf.Runner()
    runner.metadata['description'] = "Test the performance of json"
    runner.bench_time_func("json", bench_json_loads)
