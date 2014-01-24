"""A wrapper for using Python to interact with a Lego Mindstorms EV3.

Prerequisites:

    Make sure your sdp includes an SP (serial port):
    % sdptool browse local
        ...
        Service Name: Serial Port
        Service Description: COM Port

    If not:
    % sdptool add SP

    Then:
    % hcitool scan
        ...
        XX:XX:XX:XX:XX:XX   EV3

    % sudo rfcomm bind /dev/rfcomm0 XX:XX:XX:XX:XX:XX

    Now /dev/rfcomm0 can be opened and closed like a normal serial port.
    The opposite action is:
    % sudo rfcomm release /dev/rfcomm0

    Example usage:
        with EV3() as ev3:
            # Create DirectCommand objects and add commands to them.
            cmd = direct_command.DirectCommand()
            cmd.add_ui_draw_update()
            cmd.send(ev3)

            # Call single DirectCommand functions without creating DirectCommand
            # objects each time.
            ev3.output_stop(direct_command.OutputPort.PORT_C,
                                    direct_command.StopType.BRAKE)

            # Call single system_command functions.
            ev3.write_mailbox('foo', (0,1,2,3,4,5,6,7,8,9,0))

"""


import serial

import message
import system_command
import direct_command


class KnownPaths(object):
    """These are the default directories on the brick. All paths are
    relative to 'lms2012/sys' by default.

    """
    DEFAULT_PATH    = "."         # lms2012/sys
    PROJECTS_PATH   = "../prjs"   # lms2012/prjs
    APPS_PATH       = "../apps"   # lms2012/apps
    TOOLS_PATH      = "../tools"  # lms2012/tools
    SOURCE_PATH     = "../source" # lms2012/source


class EV3Error(Exception):
    """Subclass for reporting errrors."""
    pass


class EV3(object):
    """"""
    DEFAULT_RFCOMM_PORT = '/dev/rfcomm0'
    RFCOMM_BAUDRATE = 115200


    def __init__(self, port_str=DEFAULT_RFCOMM_PORT):
        """Creates a new object but doesn't open the port."""
        self._port_str = port_str
        self._port = None


    def open(self):
        """Opens the object's serial port."""
        if (self._port is None):
            self._port = serial.Serial(port=self._port_str,
                                        baudrate=self.RFCOMM_BAUDRATE,
                                        bytesize=serial.EIGHTBITS,
                                        parity=serial.PARITY_NONE,
                                        stopbits=serial.STOPBITS_ONE,
                                        timeout=None,
                                        xonxoff=False,
                                        rtscts=False,
                                        writeTimeout=None,
                                        dsrdtr=False,
                                        interCharTimeout=None)


    def close(self):
        """Closes the object's serial port."""
        if (self._port is not None):
            self._port.close()
            self._port = None


    def send_message(self, msg, message_counter=0x1234):
        """Allows for sending raw messages to the EV3. The msg parameter should
        be an array of byte values. The msg parameter should not include the
        length/message_counter header. Raises an EV3Error if the specified
        message is a type that expects a reply.

        """
        try:
            message.send_message_no_reply(self._port, msg, message_counter)
        except message.MessageError as ex:
            raise EV3Error(ex.message)


    def send_message_for_reply(self, msg, message_counter=0x1234):
        """Allows for sending raw messages to the EV3. The msg parameter should
        be an array of byte values. The msg parameter should not include the
        length/message_counter header. Raises an EV3Error if the specified
        message is a type that doesn't expect a reply.

        """
        try:
            return message.send_message_for_reply(self._port,
                                                            msg,
                                                            message_counter)
        except message.MessageError as ex:
            raise EV3Error(ex.message)


    def __dir__(self):
        """Add in functions from the system_command module as well as methods
        from the DirectCommand class because they can be called directly on an
        EV3 object.

        """
        result = dir(type(self))
        result += list(self.__dict__)
        result += [s for s in list(system_command.__dict__)
                                                    if not s.startswith('_')]
        result += [s[4:] for s in list(direct_command.DirectCommand.__dict__)
                                                        if s.startswith('add_')]
        return sorted(set(result))


    def __getattr__(self, name):
        """A little bit of magic is used in order to make it easier to work with
        EV3 objects.

        """
        if (hasattr(system_command, name)):
            # This allows functions from the system_command module to be called
            # from an EV3 object i.e. ev3.list_files(KnownPaths.PROJECTS_PATH).
            def execute_sc(*args):
                """This is just a wrapper around an individual function from the
                system_command module. See the system_command module for more
                information.

                """
                getattr(system_command, name)(self, *args)

            return execute_sc

        # This allows single functions from the DirectCommand class to be called
        # from an EV3 object i.e. ev3.ui_draw_update().
        dc_name = ('add_' + name)
        if (hasattr(direct_command.DirectCommand, dc_name)):
            def execute_dc(*args):
                """This is just a wrapper around an individual DirectCommand
                method. See the DirectCommand class for more information.

                """
                dc = direct_command.DirectCommand()
                getattr(dc, dc_name)(*args)
                return dc.send(self)

            return execute_dc

        return Object.__getattr__(self, name)


    def __enter__(self):
        self.open()
        return self


    def __exit__(self, type, value, traceback):
        self.close()
