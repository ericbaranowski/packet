#!/usr/bin/python
# -*- coding: UTF-8 -*-

"""
Example 3 - InspectedPacket:
    Use InspectedPacket to send/receive data.
    Since we are working with InspectedPacket, the data to be loaded
    must match the current data, that is, if attribute "a" is of type int,
    only integers are allowed to be loaded on attribute "a". This is the
    reason why you should avoid using None - there is no a different value
    that can be loaded.

    With InspectedPacket is also possible to send instances of classes, as
    you can see in the following example.

    If you want to send an encrypted InspectedPacket use InspectedSafePacket.
"""

from packet import InspectedPacket, InvalidData


class InnerClass:
    def __init__(self):
        self.inner_a = 1
        self.inner_b = 2
        self.inner_c = 3


class DummyPacket(InspectedPacket):
    def __init__(self):
        self.a = 1
        self.b = None  # Avoid using None, as it can´t be changed
        self.c = InnerClass()


def example3():
    # Create packet instances
    packet1 = DummyPacket()
    packet2 = DummyPacket()

    # Change some values so we can see they will be loaded
    packet1.a = 123
    packet1.c.inner_a = 123

    # Send packet1 data to packet2
    packet2.loads(packet1.dumps())

    print("packet2.a: %s, packet2.c.inner_a: %s" % (packet2.a, packet2.c.inner_a))
    print("packet 2 dump: %s" % packet2.dumps())

    # What if we change packet1.b from None to other thing?
    packet1.b = "not None"
    try:
        # Send packet1 data to packet2 again
        packet2.loads(packet1.dumps())
    except InvalidData as e:
        print("\nInvalid data error: %s" % e)


if __name__ == "__main__":
    example3()
