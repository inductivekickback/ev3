"""System commands are defined as commands that aren't executed in byte code
(no VM intervention).

All multi-byte words are little endian.

System Command Bytes:
------------------------------
Byte 0 - 1: Command size
Byte 2 - 3: Message counter
Byte 4:     CommandType
Byte 5:     Command
Byte 6 - n: payload

System Command response Bytes:
------------------------------
Byte 0 - 1: Reply size
Byte 2 - 3: Message counter
Byte 4:     ReplyType
Byte 5:     original Command
Byte 6:     ReturnCode
Byte 7 - N: payload

"""


import itertools


import message


MAX_REPLY_BYTES = 1014  # According to c_com.h comments.
MAX_TX_BYTES = 1016


class SystemCommandError(Exception):
    """Subclass for reporting errors."""
    pass


class CommandType(object):
    """Every System Command must be one of these two types."""
    SYSTEM_COMMAND_REPLY    = 0x01
    SYSTEM_COMMAND_NO_REPLY = 0x81


class ReplyType(object):
    """Every reply to a System Command must be one of these two types."""
    SYSTEM_REPLY            = 0x03
    SYSTEM_REPLY_ERROR      = 0x05


class Command(object):
    """Enumerated System Commands."""
    BEGIN_DOWNLOAD          = 0x92  # Begin file down load
    CONTINUE_DOWNLOAD       = 0x93  # Continue file down load
    BEGIN_UPLOAD            = 0x94  # Begin file upload
    CONTINUE_UPLOAD         = 0x95  # Continue file upload
    BEGIN_GETFILE           = 0x96  # Begin get bytes from a file (while writing to the file)
    CONTINUE_GETFILE        = 0x97  # Continue get byte from a file (while writing to the file)
    CLOSE_FILEHANDLE        = 0x98  # Close file handle
    LIST_FILES              = 0x99  # List files
    CONTINUE_LIST_FILES     = 0x9A  # Continue list files
    CREATE_DIR              = 0x9B  # Create directory
    DELETE_FILE             = 0x9C  # Delete
    LIST_OPEN_HANDLES       = 0x9D  # List handles
    WRITEMAILBOX            = 0x9E  # Write to mailbox
    BLUETOOTHPIN            = 0x9F  # Transfer trusted pin code to brick
    ENTERFWUPDATE           = 0xA0  # Restart the brick in Firmware update mode
    SETBUNDLEID             = 0xA1  # Set Bundle ID for mode 2
    SETBUNDLESEEDID         = 0xA2  # Set Bundle Seed ID for mode 2


class ReturnCode(object):
    """Enumerated System Command return codes."""
    SUCCESS                 = 0x00
    UNKNOWN_HANDLE          = 0x01
    HANDLE_NOT_READY        = 0x02
    CORRUPT_FILE            = 0x03
    NO_HANDLES_AVAILABLE    = 0x04
    NO_PERMISSION           = 0x05
    ILLEGAL_PATH            = 0x06
    FILE_EXITS              = 0x07
    END_OF_FILE             = 0x08
    SIZE_ERROR              = 0x09
    UNKNOWN_ERROR           = 0x0A
    ILLEGAL_FILENAME        = 0x0B
    ILLEGAL_CONNECTION      = 0x0C


def write_mailbox(ev3_obj, mailbox_name_str, byte_seq):
    """Writes a sequence of bytes to the mailbox with the given name."""
    if ('\0' != mailbox_name_str[-1]):
        mailbox_name_str += '\0'

    cmd = []
    cmd.append(CommandType.SYSTEM_COMMAND_NO_REPLY)
    cmd.append(Command.WRITEMAILBOX)

    message.append_u8(cmd, len(mailbox_name_str))
    message.append_str(cmd, mailbox_name_str)

    message.append_u16(cmd, len(byte_seq))
    map(cmd.append, byte_seq)

    ev3_obj.send_message(cmd)


def list_files(ev3_obj, path_str):
    """Returns a tuple in the form (DIRS, FILES). DIRS is a tuple of directory
    names (i.e. 'foo/'). FILES is a tuple of file information tuples in the form
    (MD5_SUM, FILE_LENGTH, FILE_NAME).

    """
    dirs = []
    files = []
    list_str = ''
    continue_list_str = ''

    if (not isinstance(path_str, str)):
        raise ValueError('The path_str param must be of type str.')

    list_str, handle, needs_continue = _list_files(ev3_obj, path_str)

    if (needs_continue):
        continue_list_str = _continue_list_files(ev3_obj, handle)

    result = (list_str + continue_list_str)
    for line in result.strip().split('\n'):
        if (line.endswith('/')):
            # Directories have the format: '[DIR_NAME]/\n'
            dirs.append(line)
        elif (line):
            # Files have the format: '[MD5] [HEX_SIZE] [FILE_NAME]\n'
            fields = line.split()
            files.append((fields[0], int(fields[1], 16), ' '.join(fields[2:])))

    return (dirs, files)


def upload_file(ev3_obj, path_str, save_path_str=None):
    """Uploads the file from the given path on the brick to the PC. If save_path_str
    is not None then the file will be written to disk. Otherwise, the file data
    will be returned as a tuple of bytes.

    """
    if (not isinstance(path_str, str)):
        raise ValueError('The path_str param must be of type str.')

    result, handle, needs_continue = _upload_file(ev3_obj, path_str)

    if (needs_continue):
        result += _continue_upload_file(ev3_obj, handle)

    if (save_path_str is not None):
        with open(save_path_str, 'w') as out_file:
            out_file.write(message.parse_str(result, 0, len(result)))
    else:
        return tuple(result)


def download_file_from_path(ev3_obj, save_path_str, file_path_str):
    """Downloads the file from file_path_str on the PC to save_path_str on the brick.

    NOTE:   This function creates intermediary directories automatically.

    """
    if (not isinstance(file_path_str, str)):
        raise ValueError('The data_path_str param must be of type str.')

    with open(file_path_str, 'r') as read_file:
        return download_file(ev3_obj, read_file.read(), save_path_str)


def download_file(ev3_obj, save_path_str, file_data):
    """Downloads the file_data to save_path_str on the brick.

    NOTE:   This function creates intermediary directories automatically.

    """
    if (not isinstance(save_path_str, str)):
        raise ValueError('The save_path_str param must be of type str.')

    cmd = []
    cmd.append(CommandType.SYSTEM_COMMAND_REPLY)
    cmd.append(Command.BEGIN_DOWNLOAD)

    message.append_u32(cmd, len(file_data))
    message.append_str(cmd, save_path_str)

    reply = ev3_obj.send_message_for_reply(cmd)

    print 'reply: ', reply

    if (reply[0] == ReplyType.SYSTEM_REPLY_ERROR):
        raise SystemCommandError('A command failed.')

    if (reply[1] != Command.BEGIN_DOWNLOAD):
        raise SystemCommandError('Sync error detected.')

    if (reply[2] == ReturnCode.UNKNOWN_ERROR):
        raise SystemCommandError('An error occurred.')

    handle = reply[3]

    _continue_download_file(ev3_obj, handle, file_data)


def create_dir(ev3_obj, path_str):
    """Creates the directory at the given path_str."""
    cmd = []
    cmd.append(CommandType.SYSTEM_COMMAND_NO_REPLY)
    cmd.append(Command.CREATE_DIR)
    message.append_str(cmd, path_str)
    ev3_obj.send_message(cmd)


def delete_path(ev3_obj, path_str):
    """Deletes the file or directory specified by the given path_str.

    NOTE:   Directories must be empty before they can be deleted.

    """
    cmd = []
    cmd.append(CommandType.SYSTEM_COMMAND_NO_REPLY)
    cmd.append(Command.DELETE_FILE)
    message.append_str(cmd, path_str)
    ev3_obj.send_message(cmd)


def delete_directory(ev3_obj, dir_path_str):
    """Convenience function for deleting directories that may or may not be
    empty.

    """
    if (not dir_path_str.endswith('/')):
        dir_path_str += '/'

    directories, files = list_files(ev3_obj, dir_path_str)

    for f in files:
        md5, length, file_name = f
        delete_path_str(ev3_obj, (dir_path_str + file_name))

    for d in directories:
        # Ignore './' and '../'.
        if (not d.startswith('.')):
            delete_directory(ev3_obj, (dir_path_str + d))

    delete_path_str(ev3_obj, dir_path_str)


def _list_files(ev3_obj, path_str):
    handle = None
    needs_continue = False

    cmd = []
    cmd.append(CommandType.SYSTEM_COMMAND_REPLY)
    cmd.append(Command.LIST_FILES)

    message.append_u16(cmd, MAX_REPLY_BYTES)
    message.append_str(cmd, path_str)

    reply = ev3_obj.send_message_for_reply(cmd)

    if (reply[0] == ReplyType.SYSTEM_REPLY_ERROR):
        raise SystemCommandError('A command failed.')

    if (reply[1] != Command.LIST_FILES):
        raise SystemCommandError('Sync error detected.')

    if (reply[2] == ReturnCode.UNKNOWN_ERROR):
        raise SystemCommandError('An error occurred.')

    list_size = message.parse_u32(reply, 3)
    handle = reply[7]

    result = message.parse_str(reply, 8)

    return (result, handle, (reply[2] != ReturnCode.END_OF_FILE))


def _continue_list_files(ev3_obj, handle):
    result = []

    cmd = []
    cmd.append(CommandType.SYSTEM_COMMAND_REPLY)
    cmd.append(Command.CONTINUE_LIST_FILES)
    cmd.append(handle)

    message.append_u16(cmd, MAX_REPLY_BYTES)

    while (True):
        reply = ev3_obj.send_message_for_reply(cmd)

        if (reply[0] == ReplyType.SYSTEM_REPLY_ERROR):
            raise SystemCommandError('A command failed.')

        if (reply[1] != Command.CONTINUE_LIST_FILES):
            raise SystemCommandError('Sync error detected.')

        if (reply[2] == ReturnCode.UNKNOWN_ERROR):
            raise SystemCommandError('An error occurred.')

        handle = reply[3]

        result.append(message.parse_str(reply, 4))

        if (reply[2] == ReturnCode.END_OF_FILE):
            break

    return ''.join(result)


def _upload_file(ev3_obj, path_str):
    handle = None
    needs_continue = False

    cmd = []
    cmd.append(CommandType.SYSTEM_COMMAND_REPLY)
    cmd.append(Command.BEGIN_UPLOAD)

    message.append_u16(cmd, MAX_REPLY_BYTES)
    message.append_str(cmd, path_str)

    reply = ev3_obj.send_message_for_reply(cmd)

    if (reply[0] == ReplyType.SYSTEM_REPLY_ERROR):
        raise SystemCommandError('A command failed.')

    if (reply[1] != Command.BEGIN_UPLOAD):
        raise SystemCommandError('Sync error detected.')

    if (reply[2] == ReturnCode.UNKNOWN_ERROR):
        raise SystemCommandError('An error occurred.')

    data_size = message.parse_u32(reply, 3)
    handle = reply[7]

    result = reply[8:]

    return (result, handle, (reply[2] != ReturnCode.END_OF_FILE))


def _continue_upload_file(ev3_obj, handle):
    result = []

    cmd = []
    cmd.append(CommandType.SYSTEM_COMMAND_REPLY)
    cmd.append(Command.CONTINUE_UPLOAD)
    cmd.append(handle)

    message.append_u16(cmd, MAX_REPLY_BYTES)

    while (True):
        reply = ev3_obj.send_message_for_reply(cmd)

        if (reply[0] == ReplyType.SYSTEM_REPLY_ERROR):
            raise SystemCommandError('A command failed.')

        if (reply[1] != Command.CONTINUE_UPLOAD):
            raise SystemCommandError('Sync error detected.')

        if (reply[2] == ReturnCode.UNKNOWN_ERROR):
            raise SystemCommandError('An error occurred.')

        handle = reply[3]

        result.append(reply[4:])

        if (reply[2] == ReturnCode.END_OF_FILE):
            break

    return itertools.chain.from_iterable(result)


def _continue_download_file(ev3_obj, handle, data):
    offset = 0

    data_len = len(data)

    cmd = []
    cmd.append(CommandType.SYSTEM_COMMAND_REPLY)
    cmd.append(Command.CONTINUE_DOWNLOAD)
    cmd.append(handle)

    if (MAX_TX_BYTES >= data_len):
        offset = data_len
    else:
        offset = MAX_TX_BYTES

    map(cmd.append, data[:offset])

    while (True):
        reply = ev3_obj.send_message_for_reply(cmd)

        if (reply[0] == ReplyType.SYSTEM_REPLY_ERROR):
            raise SystemCommandError('A command failed.')

        if (reply[1] != Command.CONTINUE_DOWNLOAD):
            raise SystemCommandError('Sync error detected.')

        if (reply[2] == ReturnCode.UNKNOWN_ERROR):
            raise SystemCommandError('An error occurred.')

        if (data_len == offset):
            break

        del (cmd[3:])

        if (MAX_TX_BYTES >= (data_len - offset)):
            map(cmd.append, data[offset:])
            offset = data_len
        else:
            new_offset = (offset + MAX_TX_BYTES)
            map(cmd.append, data[offset:new_offset])
            offset = new_offset
