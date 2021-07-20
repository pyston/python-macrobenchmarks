# -*- coding: utf-8 -*-
"""
Benchmarks for hub primitive operations.

Taken from https://github.com/gevent/gevent/blob/master/benchmarks/bench_hub.py
Modified to remove perf and not need any command line arguments
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import pyperf
import gevent
import gevent.hub
from greenlet import greenlet
from greenlet import getcurrent


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


def get_switching_greenlets(nswitches=1000):
    class Parent(type(gevent.get_hub())):
        def run(self, *, _loops=nswitches):
            switch = self.parent.switch
            for _ in range(_loops):
                switch()

    def child(*, _loops=nswitches):
        switch = getcurrent().parent.switch
        # Back to the hub, which in turn goes
        # back to the main greenlet
        for _ in range(_loops):
            switch()

    hub = Parent(None, None)
    child_greenlet = greenlet(child, hub)
    return hub, child_greenlet


def bench_switch(loops=1000):
    _, child = get_switching_greenlets(loops)
    child_switch = child.switch
    loops = iter(range(loops))

    t0 = pyperf.perf_counter()
    for _ in loops:
        child_switch()
    return pyperf.perf_counter() - t0


def bench_wait_ready(loops=1000):
    watcher = NoopWatcher()
    hub = gevent.get_hub()
    hub_wait = hub.wait
    loops = iter(range(loops))

    t0 = pyperf.perf_counter()
    for _ in loops:
        hub_wait(watcher)
    return pyperf.perf_counter() - t0


def bench_cancel_wait(loops=1000):
    watcher = ActiveWatcher()
    hub = gevent.get_hub()
    hub_cancel_wait = hub.cancel_wait
    hub_loop = hub.loop
    loops = iter(range(loops))

    t0 = pyperf.perf_counter()
    for _ in loops:
        # Schedule all the callbacks.
        hub_cancel_wait(watcher, None, True)
    # Run them!
    # XXX Start timing here?
    for cb in hub_loop._callbacks:
        if cb.callback:
            cb.callback(*cb.args)
            cb.stop()  # so the real loop won't do it
    elapsed = pyperf.perf_counter() - t0

    # Destroy the loop so we don't keep building these functions up.
    hub.destroy(True)

    return elapsed


def bench_wait_func_ready(loops=1000):
    watched_objects = [NoopWatchTarget() for _ in range(loops)]
    wait = gevent.hub.wait

    t0 = pyperf.perf_counter()
    wait(watched_objects)
    return pyperf.perf_counter() - t0


BENCHMARKS = {
    "gevent_hub": bench_switch,  # XXX Release 10,000 times?
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
