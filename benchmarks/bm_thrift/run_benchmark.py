# Adapted from https://raw.githubusercontent.com/Thriftpy/thriftpy2/master/benchmark/benchmark_apache_thrift_struct.py

import os.path
import sys

import pyperf
from thrift.TSerialization import serialize, deserialize
from thrift.protocol.TBinaryProtocol import (
    TBinaryProtocolFactory,
    TBinaryProtocolAcceleratedFactory
)


DATADIR = os.path.join(
    os.path.dirname(__file__),
    "data",
)
# The target files were generated using the make file in the data dir.
TARGET = os.path.join(DATADIR, "thrift")


if TARGET not in sys.path:
    sys.path.insert(0, TARGET)
from addressbook import ttypes


def make_addressbook():
    phone1 = ttypes.PhoneNumber()
    phone1.type = ttypes.PhoneType.MOBILE
    phone1.number = '555-1212'
    phone2 = ttypes.PhoneNumber()
    phone2.type = ttypes.PhoneType.HOME
    phone2.number = '555-1234'
    person = ttypes.Person()
    person.name = "Alice"
    person.phones = [phone1, phone2]
    person.created_at = 1400000000

    ab = ttypes.AddressBook()
    ab.people = {person.name: person}
    return ab


#############################
# benchmarks

def bench_thrift(loops=1000):
    elapsed, _ = _bench_thrift(loops)
    return elapsed


def _bench_thrift(loops=1000):
    """Measure using a thrift-generated library N times.

    The target is a simple addressbook.  We measure the following:

    * create an addressbook with 1 person in it
    * serialize it
    * deserialize it into a new addressbook

    For each iteration we repeat this 100 times.
    """
    # proto_factory = TBinaryProtocolFactory()
    proto_factory = TBinaryProtocolAcceleratedFactory()

    elapsed = 0
    times = []
    for _ in range(loops):
        # This is a macro benchmark for a Python implementation
        # so "elapsed" covers more than just how long the Addressbook ops take.
        t0 = pyperf.perf_counter()
        for _ in range(100):
            # First, create the addressbook.
            ab = make_addressbook()
            # Then, round-trip through serialization.
            encoded = serialize(ab, proto_factory)
            ab2 = ttypes.AddressBook()
            deserialize(ab2, encoded, proto_factory)
        t1 = pyperf.perf_counter()

        elapsed += t1 - t0
        times.append(t0)
    times.append(pyperf.perf_counter())
    return elapsed, times


#############################
# the script

if __name__ == "__main__":
    from legacyutils import maybe_handle_legacy
    maybe_handle_legacy(_bench_thrift)

    runner = pyperf.Runner()
    runner.metadata['description'] = "Test the performance of thrift"
    runner.bench_time_func("thrift", bench_thrift)
