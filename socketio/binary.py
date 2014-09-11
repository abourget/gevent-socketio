# coding=utf-8
"""
Binary class deconstruct, reconstruct packet
"""
import copy
import datetime


class Binary(object):

    @staticmethod
    def deconstruct_packet(packet):
        """
        Replaces every bytearray in packet with a numbered placeholder.
        :param packet:
        :return: dict with packet and list of buffers
        """
        buffers = []
        packet_data = packet.get('data', None)

        def _deconstruct_packet(data):
            if data is None:
                return {
                    'packet': packet,
                    'buffers': buffers
                }

            if type(data) is bytearray:
                place_holder = {
                    '_placeholder': True,
                    'num': len(buffers)
                }

                buffers.append(data)
                return place_holder

            if type(data) is list:
                new_data = []
                for d in data:
                    new_data.append(_deconstruct_packet(d))

                return new_data

            if type(data) is dict:
                new_data = {}

                for k, v in data.items():
                    new_data[k] = _deconstruct_packet(v)

                return new_data

            return data

        pack = copy.copy(packet)
        pack['data'] = _deconstruct_packet(packet_data)
        pack['attachments'] = len(buffers)

        return {
            'packet': pack,
            'buffers': buffers
        }


    @staticmethod
    def reconstruct_packet(packet, buffers):
        def _reconstruct_packet(data):
            if data and '_placeholder' in data:
                buf = buffers[data['num']]
                return buf

            if type(data) is list:
                for i in xrange(len(data)):
                    data[i] = _reconstruct_packet(data[i])

                return data

            if data and type(data) is dict:
                for k, v in data.items():
                    data[k] = _reconstruct_packet(v)

                return data

            return data

        packet['data'] = _reconstruct_packet(packet['data'])
        del packet['attachments']
        return packet

    # TODO Add the remove blob function which removes FileObject async
    # In gevent, file object reading should be async by default, so we should just read file and convert it as
    # bytearray and return
    @staticmethod
    def remove_blobs(data):
        def _remove_blobs(obj, cur_key=None, containing_obj=None):
            if not obj:
                return obj

            try:
                # Try to read it as a file
                buf = bytearray(obj.read())

                if containing_obj is not None and cur_key is not None:
                    containing_obj[cur_key] = buf
                else:
                    return buf

            except AttributeError:
                pass

            if type(obj) is list:
                for index, item in enumerate(obj):
                    _remove_blobs(item, index, obj)

            if type(obj) is dict:
                for k, v in obj.items():
                    _remove_blobs(v, k, obj)

            return obj

        blobless_data = _remove_blobs(data)
        return blobless_data
