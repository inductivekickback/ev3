"""A simple demo that allows the user to drive the 'Robot Arm H25' located
here: http://robotsquare.com/2013/10/01/education-ev3-45544-instruction/

The program waits for key presses and responds to the following keys:
    'w' - Raises the claw
    's' - Lowers the claw
    'a' - Swivels the claw left
    'd' - Swivels the claw right
    'c' - Opens the claw
    'v' - Closes the claw
    'q' - Exits the program

Before running the program ensure that you have binded the brick to rfcomm0
(i.e. 'sudo rfcomm bind /dev/rfcomm0 XX:XX:XX:XX:XX:XX').

"""


import sys
import tty
import termios

from ev3 import *


def getch():
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        return sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


# Ensures that the claw is firmly closed.
close_claw_cmd = direct_command.DirectCommand()
close_claw_cmd.add_output_speed(direct_command.OutputPort.PORT_D, 10)
close_claw_cmd.add_output_start(direct_command.OutputPort.PORT_D)
close_claw_cmd.add_timer_wait(1000)
close_claw_cmd.add_output_stop(direct_command.OutputPort.PORT_D,
                                            direct_command.StopType.BRAKE)


# Opens the claw about half way.
open_claw_cmd = direct_command.DirectCommand()
open_claw_cmd.add_output_speed(direct_command.OutputPort.PORT_D, -10)
open_claw_cmd.add_output_start(direct_command.OutputPort.PORT_D)
open_claw_cmd.add_timer_wait(600)
open_claw_cmd.add_output_stop(direct_command.OutputPort.PORT_D,
                                            direct_command.StopType.BRAKE)


raise_claw_cmd = direct_command.DirectCommand()
raise_claw_cmd.add_output_step_speed(direct_command.OutputPort.PORT_B,
                                            -15,
                                            0,
                                            20,
                                            10,
                                            direct_command.StopType.BRAKE)
raise_claw_cmd.add_output_ready(direct_command.OutputPort.PORT_B)
raise_claw_cmd.add_keep_alive()


lower_claw_cmd = direct_command.DirectCommand()
lower_claw_cmd.add_output_step_speed(direct_command.OutputPort.PORT_B,
                                            15,
                                            0,
                                            20,
                                            10,
                                            direct_command.StopType.BRAKE)
lower_claw_cmd.add_output_ready(direct_command.OutputPort.PORT_B)
lower_claw_cmd.add_keep_alive()


swivel_left_cmd = direct_command.DirectCommand()
swivel_left_cmd.add_output_step_speed(direct_command.OutputPort.PORT_C,
                                            -15,
                                            0,
                                            20,
                                            10,
                                            direct_command.StopType.BRAKE)
swivel_left_cmd.add_output_ready(direct_command.OutputPort.PORT_C)
swivel_left_cmd.add_keep_alive()


swivel_right_cmd = direct_command.DirectCommand()
swivel_right_cmd.add_output_step_speed(direct_command.OutputPort.PORT_C,
                                            15,
                                            0,
                                            20,
                                            10,
                                            direct_command.StopType.BRAKE)
swivel_right_cmd.add_output_ready(direct_command.OutputPort.PORT_C)
swivel_right_cmd.add_keep_alive()


if ("__main__" == __name__):
    with ev3.EV3() as brick:
        print "Connection opened (press 'q' to quit)."

        while (True):
            c = getch()

            if ('c' == c):
                print 'Opening claw.'
                open_claw_cmd.send(brick)
            elif ('v' == c):
                print 'Closing claw.'
                close_claw_cmd.send(brick)
            elif ('w' == c):
                print 'Raising claw.'
                raise_claw_cmd.send(brick)
            elif ('s' == c):
                print 'Lowering claw.'
                lower_claw_cmd.send(brick)
            elif ('a' == c):
                print 'Swivel left.'
                swivel_left_cmd.send(brick)
            elif ('d' == c):
                print 'Swivel right.'
                swivel_right_cmd.send(brick)
            elif ('q' == c):
                break
