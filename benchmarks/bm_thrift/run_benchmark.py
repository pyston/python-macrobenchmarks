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
TARGET = os.path.join(DATADIR, "thrift")

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


def bench_thrift(loops=1000):
    # proto_factory = TBinaryProtocolFactory()
    proto_factory = TBinaryProtocolAcceleratedFactory()
    _serialize = serialize
    _deserialize = deserialize
    _AddressBook = ttypes.AddressBook
    _mkaddr = make_addressbook
    loops = iter(range(loops))

    t0 = pyperf.perf_counter()
    for _ in loops:
        for j in range(100):
            ab = _mkaddr()
            encoded = _serialize(ab, proto_factory)
            ab2 = _AddressBook()
            _deserialize(ab2, encoded, proto_factory)
    return pyperf.perf_counter() - t0


if __name__ == "__main__":
    runner = pyperf.Runner()
    runner.metadata['description'] = "Test the performance of thrift"
    runner.bench_time_func("thrift", bench_thrift)
