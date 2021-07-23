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


def bench_thrift(loops=1000):
    """Measure using a thrift-generated library N times.

    The target is a simple addressbook.  We measure the following:

    * create an addressbook with 1 person in it
    * serialize it
    * deserialize it into a new addressbook

    For each iteration we repeat this 100 times.
    """
    sys.path.insert(0, TARGET)
    from addressbook import ttypes

    elapsed = 0
    # proto_factory = TBinaryProtocolFactory()
    proto_factory = TBinaryProtocolAcceleratedFactory()
    _serialize = serialize
    _deserialize = deserialize
    _AddressBook = ttypes.AddressBook
    _Person = ttypes.Person
    _PhoneNumber = ttypes.PhoneNumber
    MOBILE = ttypes.PhoneType.MOBILE
    HOME = ttypes.PhoneType.HOME
    for _ in range(loops):
        t0 = pyperf.perf_counter()
        for _ in range(100):
            # First, create the addressbook.
            ab = _AddressBook()
            phone1 = _PhoneNumber()
            phone1.type = MOBILE
            phone1.number = '555-1212'
            phone2 = _PhoneNumber()
            phone2.type = HOME
            phone2.number = '555-1234'
            person = _Person()
            person.name = "Alice"
            person.phones = [phone1, phone2]
            person.created_at = 1400000000
            ab.people = {person.name: person}
            # Then, round-trip through serialization.
            encoded = _serialize(ab, proto_factory)
            ab2 = _AddressBook()
            _deserialize(ab2, encoded, proto_factory)
        elapsed += pyperf.perf_counter() - t0
    return elapsed


if __name__ == "__main__":
    runner = pyperf.Runner()
    runner.metadata['description'] = "Test the performance of thrift"
    runner.bench_time_func("thrift", bench_thrift)
