# -*- coding: utf-8 -*-
"""
Benchmarks for hub primitive operations.

Taken from https://github.com/gevent/gevent/blob/master/benchmarks/bench_hub.py
Modified to remove perf and not need any command line arguments
"""
import contextlib

import pyperf
import gevent
import gevent.hub
from greenlet import greenlet
from greenlet import getcurrent


@contextlib.contextmanager
def active_hub(hub=None):
    if hub is None:
        hub = gevent.get_hub()
    try:
        yield hub
    finally:
        # Destroy the loop so we don't keep building up state (e.g. callbacks).
        hub.destroy(True)


class SwitchingParent(gevent.hub.Hub):
    """A gevent hub greenlet that switches back and forth with its child."""

    def __init__(self, nswitches):
        super().__init__(None, None)
        self.nswitches = nswitches
        self.child = greenlet(self._run_child, self)

    def _run_child(self):
        # Back to the hub, which in turn goes
        # back to the main greenlet
        switch = getcurrent().parent.switch
        for _ in range(self.nswitches):
            switch()

    def run(self):
        # Return to the main greenlet.
        switch = self.parent.switch
        for _ in range(self.nswitches):
            switch()


class NoopWatcher:
    def start(self, cb, obj):
        # Immediately switch back to the waiter, mark as ready
        cb(obj)

    def stop(self):
        pass


class ActiveWatcher:
    active = True
    callback = object()

    def close(self):
        pass


class NoopWatchTarget(object):
    def rawlink(self, cb):
        cb(self)


#############################
# benchmarks

def bench_switch(loops=1000):
    """Measure switching between a greenlet and the gevent hub N^2 times."""
    hub = SwitchingParent(loops)
    child = hub.child

    with active_hub(hub):
        elapsed = 0
        child_switch = child.switch
        for _ in range(loops):
            t0 = pyperf.perf_counter()
            child_switch()
            elapsed += pyperf.perf_counter() - t0
        return elapsed


def bench_wait_ready(loops=1000):
    """Measure waiting for a "noop" watcher to become ready N times."""
    watcher = NoopWatcher()

    with active_hub() as hub:
        elapsed = 0
        hub_wait = hub.wait
        for _ in range(loops):
            t0 = pyperf.perf_counter()
            hub_wait(watcher)
            elapsed += pyperf.perf_counter() - t0
        return elapsed


def bench_cancel_wait(loops=1000):
    """Measure canceling N watchers.
    
    Note that it is the same watcher N times and that it is a fake
    that pretends to already be started.
    """
    watcher = ActiveWatcher()

    with active_hub() as hub:
        t0 = pyperf.perf_counter()

        # Cancel the fake wait requests.
        for _ in range(loops):
            # Schedule all the callbacks.
            hub.cancel_wait(watcher, None, True)

        # Wait for all the watchers to be closed.
        # TODO Start timing here?
        for cb in hub.loop._callbacks:
            if cb.callback:
                cb.callback(*cb.args)
                cb.stop()  # so the real loop won't do it

        return pyperf.perf_counter() - t0


def bench_wait_func_ready(loops=1000):
    """Measure waiting for N noop watch targets to become ready."""
    watched_objects = [NoopWatchTarget() for _ in range(loops)]

    t0 = pyperf.perf_counter()
    gevent.hub.wait(watched_objects)
    return pyperf.perf_counter() - t0


BENCHMARKS = {
    "gevent_hub": bench_switch,
    "gevent_wait_func_ready": bench_wait_func_ready,
    "gevent_wait_ready": bench_wait_ready,
    "gevent_cancel_wait": bench_cancel_wait,
    "gevent_switch": bench_switch,
}


if __name__ == "__main__":
    runner = pyperf.Runner()
    runner.metadata['description'] = "Test the performance of gevent"
    runner.argparser.add_argument("benchmark", nargs="?",
                                  choices=sorted(BENCHMARKS),
                                  default="gevent_hub")

    args = runner.parse_args()
    name = args.benchmark
    bench = BENCHMARKS[name]
    assert(bench.__code__.co_varnames[0] == 'loops')
    inner_loops = bench.__defaults__[0]

    runner.bench_time_func(name, bench, inner_loops=inner_loops)
