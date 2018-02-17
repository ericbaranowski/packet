#!/usr/bin/python
# -*- coding: UTF-8 -*-

import ast
import json
from .utils import UnknownPacket, InvalidData, NotSerializable
from .utils import JSON_SERIALIZER, AST_SERIALIZER
from ._compat import get_items


def _check_dict_keys(obj):
    """
    Check if all obj keys are strings, so it can be json serialized.
    If one of the keys is not string, raise TypeError.

    :param obj: dict, Dict to verify
    :return: None
    """

    for k, v in get_items(obj):
        if not isinstance(k, str):
            raise TypeError("Only string keys are allowed in Packet dicts")
        if isinstance(v, dict):
            _check_dict_keys(v)


def set_packet_serializer(serializer):
    """
    Set serializer to be used in all packets.
    Serializer must be either JSON_SERIALIZER or AST_SERIALIZER.

    :param serializer: int, Serializer to use
    :return: None
    """
    if not isinstance(serializer, int) or (
            serializer != JSON_SERIALIZER and serializer != AST_SERIALIZER):
        raise ValueError("Unknown serializer")
    Packet.packet_serializer = serializer


class Packet(object):
    """
    General packet class. This is the main "Packet" class.
    Every packet classes should inherit from this one.
    """

    packet_serializer = JSON_SERIALIZER

    @property
    def __tag__(self):
        """
        Tag of current packet. This must be equal for all instances sharing data.

        :return: str
        """
        return self.__class__.__name__

    @staticmethod
    def _get_attributes(obj):
        """
        Get all the attributes of a given object as a set.

        :param obj: object to check attributes
        :return: set, attributes
        """
        attributes = set()
        for cls in obj.__class__.__mro__:
            for slot in getattr(cls, "__slots__", []):
                if hasattr(obj, slot):
                    attributes.add(slot)

        attributes.update(getattr(obj, "__dict__", {}))
        return attributes

    def _generate_dict(self):
        """
        Return packet as a dictionary

        :return: dict
        """
        _dict = {}
        for attribute in self._get_attributes(self):
            _dict[attribute] = getattr(self, attribute)
        return _dict

    def dumps(self):
        """
        Serialize packet object to string using the packet name as the tag.

        :return: bytes, JSON
        """
        _data = self._generate_dict()
        if self.packet_serializer == AST_SERIALIZER:
            try:
                data = repr({self.__tag__: _data})
                ast.literal_eval(data)
            except ValueError as e:
                raise NotSerializable(e)
        else:
            try:
                _check_dict_keys(_data)
                data = json.dumps({self.__tag__: _data})
            except TypeError as e:
                raise NotSerializable(e)
        return data.encode()

    def _update_dict(self, data):
        """
        Update packet dictionary with the given data.

        :param data: dict, new data
        :return: None
        """
        if not isinstance(data, dict):
            raise InvalidData("Expected dictionary data")
        if set(data) != self._get_attributes(self):
            raise InvalidData("Attributes do not match")
        for k, v in get_items(data):
            self.__setattr__(k, v)

    def loads(self, data):
        """
        Deserialize data and update packet object.
        Raises UnknownPacket or InvalidData if the data is not deserializable.

        :param data: bytes/str, JSON
        :return: None
        """
        tag = self.__tag__
        try:
            if self.packet_serializer == AST_SERIALIZER:
                if isinstance(data, bytes):
                    data = data.decode()
                _data = ast.literal_eval(data)
            else:
                _data = json.loads(data)
        except Exception as e:
            raise UnknownPacket(e)
        if not isinstance(_data, dict):
            raise UnknownPacket("Expected dictionary data")
        if tag not in _data:
            raise InvalidData("Expected data with tag '%s'" % tag)
        self._update_dict(_data[tag])

    def receive_from(self, conn, buffer_size=512):
        """
        Receive data from a connection and load it to the packet.
        If there is an error loading data or no data is obtained, return False.

        :param conn: Socket connection
        :param buffer_size: int, Socket buffer size
        :return: bool, Success
        """
        if conn is None:
            return False
        data = conn.recv(buffer_size)
        if not data:
            return False
        try:
            self.loads(data)
        except (UnknownPacket, InvalidData):
            return False
        return True

    def send_to(self, conn):
        """
        Send data to connection.
        If no connection, return None.

        :param conn: Socket connection
        :return: int, Bytes sent
        """
        if conn is None:
            return None
        return conn.send(self.dumps())
