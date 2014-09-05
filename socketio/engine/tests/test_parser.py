# coding=utf-8
from unittest import TestCase

from socketio.engine.parser import Parser


class TestParser(TestCase):
    def test_encode_payload_as_binary(self):
        buffer = Parser.encode_payload_as_binary([
            {
                'type': 'open',
                'data': 'what'
            },
            {
                'type': 'message',
                'data': 'hello'
            }
        ])

        self.assertEqual(len(buffer), 3 + 1 + 4 + 3 + 1 + 5)

    def test_encode_payload(self):
        b = bytearray([0, 1, 2, 3, 4])

        encoded = Parser.encode_payload([
            {
                "type": "message",
                "data": b
            },
            {
                "type": "message",
                "data": "hello"
            }
        ])

        for packet, index, total in Parser.decode_payload(encoded):
            is_last = index + 1 == total
            self.assertEqual(packet["type"], "message")
            if is_last:
                self.assertEqual(packet["data"], "hello")
            else:
                self.assertEqual(len(packet["data"]), 5)

    def test_encode_binary_message(self):
        buffer = bytearray([0, 1, 2, 3, 4])
        encoded_buffer = Parser.encode_packet({
            'type': 'message',
            'data': buffer
        })
        packet = Parser.decode_packet(encoded_buffer)
        self.assertEqual(packet['type'], 'message')
        self.assertEqual(packet['data'], buffer)

    def test_encode_decode_base64(self):
        encoded = Parser.encode_base64_packet({
            "type": "message",
            "data": "hello"
        })

        decoded = Parser.decode_base64_packet(encoded)

        self.assertEqual(decoded['type'], 'message')
        self.assertEqual(decoded['data'], 'hello')

    def test_encode_binary_as_binary(self):
        first_buf = bytearray([0, 1, 2, 3, 4])
        second_buf = bytearray([5, 6, 7, 8])

        encoded = Parser.encode_payload_as_binary([
            {
                "type": "message",
                "data": first_buf
            },
            {
                "type": "message",
                "data": second_buf
            }
        ])

        for packet, index, total in Parser.decode_payload_as_binary(encoded):
            is_last = index + 1 == total

            if is_last:
                self.assertEqual(packet["data"], second_buf)
            else:
                self.assertEqual(packet["data"], first_buf)

    def test_encode_mixed_binary_string_as_binary(self):
        buf = bytearray([0, 1, 2, 3, 4])

        encoded = Parser.encode_payload_as_binary([
            {
                "type": "message",
                "data": buf
            },
            {
                "type": "message",
                "data": "hello"
            },
            {
                "type": "close"
            }
        ])

        for packet, index, total in Parser.decode_payload_as_binary(encoded):
            if index == 0:
                self.assertEqual(packet["data"], buf)
            elif index == 1:
                self.assertEqual(packet["data"], "hello")
            elif index == 2:
                self.assertFalse("data" in packet)
