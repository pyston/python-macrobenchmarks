# Adapted from https://raw.githubusercontent.com/Thriftpy/thriftpy2/master/benchmark/benchmark_apache_thrift_struct.py

import json
import time

from thrift.TSerialization import serialize, deserialize
from thrift.protocol.TBinaryProtocol import (
    TBinaryProtocolFactory,
    TBinaryProtocolAcceleratedFactory
)

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "../data/thrift"))
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


def main():
    # proto_factory = TBinaryProtocolFactory()
    proto_factory = TBinaryProtocolAcceleratedFactory()

    n = 1000
    if len(sys.argv) > 1:
        n = int(sys.argv[1])

    times = []

    for i in range(n):
        times.append(time.time())
        for j in range(100):
            ab = make_addressbook()
            encoded = serialize(ab, proto_factory)
            ab2 = ttypes.AddressBook()
            deserialize(ab2, encoded, proto_factory)
    times.append(time.time())

    if len(sys.argv) > 2:
        json.dump(times, open(sys.argv[2], 'w'))

if __name__ == "__main__":
    main()
