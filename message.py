"""Handles the messaging with EV3 and contains several functions for dealing
with message variable types.

"""


import struct

import system_command
import direct_command


class MessageError(Exception):
    """Subclass for reporting errors."""
    pass


def send_message_for_reply(port, msg, message_counter=0x1234):
    """Sends the message and waits for a reply. The msg is expected to be a
    sequence of bytes and it should not contain the length/message_counter
    header. Returns an sequence of bytes without the length/message_counter
    header.

    """
    if (not msg_expects_reply(msg)):
        raise MessageError('The message is not a type that expects a reply.')

    # Message length includes the two message_counter bytes.
    msg_len = (2 + len(msg))

    msg_counter_lsb = (message_counter & 0xFF)
    msg_counter_msb = ((message_counter >> 8) & 0xFF)

    buf = [(msg_len & 0xFF),
                ((msg_len >> 8) & 0xFF),
                msg_counter_lsb,
                msg_counter_msb]

    _write_bytes(port, buf)
    _write_bytes(port, msg)

    expected_len = _read_bytes(port, 2)
    expected_len = (expected_len[0] | (expected_len[1] << 8))

    reply = _read_bytes(port, expected_len)

    if (reply[0] != msg_counter_lsb or reply[1] != msg_counter_msb):
        raise MessageError('Reply message counter does not match.')

    return reply[2:]


def send_message_no_reply(port, msg, message_counter=0x1234):
    """Sends the message without waiting for a reply."""
    if (msg_expects_reply(msg)):
        raise MessageError('The message is a type that expects a reply.')

    # Message length includes the two message_counter bytes.
    msg_len = (2 + len(msg))

    msg_counter_lsb = (message_counter & 0xFF)
    msg_counter_msb = ((message_counter >> 8) & 0xFF)

    buf = [(msg_len & 0xFF),
                ((msg_len >> 8) & 0xFF),
                msg_counter_lsb,
                msg_counter_msb]

    _write_bytes(port, buf)
    _write_bytes(port, msg)


def msg_expects_reply(msg):
    """Returns True if the given message is a type that expects a reply. The
    given message should not include the length/message_counter header.

    """
    if (system_command.CommandType.SYSTEM_COMMAND_REPLY == msg[0]):
        return True

    if (direct_command.CommandType.DIRECT_COMMAND_REPLY == msg[0]):
        return True

    return False


def parse_u16(byte_seq, index):
    """Parses a u32 value at the given index from the byte_seq."""
    return (byte_seq[index] | (byte_seq[index + 1] << 8))


def parse_u32(byte_seq, index):
    """Parses a u32 value at the given index from the byte_seq."""
    return (byte_seq[index] |
                (byte_seq[index + 1] << 8) |
                (byte_seq[index + 2] << 16) |
                (byte_seq[index + 3] << 24))


def parse_str(byte_seq, index, length=None):
    """Parses a string of length chars."""
    if (length is None):
        return ''.join([chr(c) for c in byte_seq[index:]])
    else:
        return ''.join([chr(c) for c in byte_seq[index:(index + length)]])


def parse_null_terminated_str(byte_seq, index, length):
    """Parses a null-terminated string of up to length chars."""
    result = []

    for i in range(index, (index + length)):
        if (0x00 != byte_seq[i]):
            result.append(chr(byte_seq[i]))
        else:
            break

    return ''.join(result)


def parse_float(byte_seq, index):
    """Parses a 32bit floating point number."""
    str_value = ''.join([chr(c) for c in byte_seq[index:(index + 4)]])
    return struct.unpack('<f', str_value)[0]


def append_float(byte_list, value):
    """Appends a 32bit floating point number."""
    value_str = struct.pack('<f', value).ljust(4, '\0')
    map(byte_list.append, [ord(c) for c in value_str])


def append_u8(byte_list, value):
    """Appends the given value to the list."""
    byte_list.append(value & 0xFF)


def append_u16(byte_list, value):
    """Appends the given value to the list in little-endian order."""
    byte_list.append(value & 0xFF)
    byte_list.append((value >> 8) & 0xFF)


def append_u32(byte_list, value):
    """Appends the given value to the list in little-endian order."""
    byte_list.append(value & 0xFF)
    byte_list.append((value >> 8) & 0xFF)
    byte_list.append((value >> 16) & 0xFF)
    byte_list.append((value >> 24) & 0xFF)


def append_str(byte_list, str_value):
    """Appends a null-terminated string."""
    if ('\0' != str_value[-1]):
        str_value += '\0'

    for c in str_value:
        byte_list.append(ord(c))


def _read_bytes(port, num_bytes):
    return [ord(i) for i in port.read(num_bytes)]


def _write_bytes(port, byte_seq):
    port.write(''.join([chr(i) for i in byte_seq]))
