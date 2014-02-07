"""A simple thread subclass for making ev3 function calls asynchronous.

EXAMPLE USAGE:
    import time

    from ev3 import *


    finished = False


    def keep_alive_finished(result):
        global finished
        print 'The keep_alive() function returned: ', result
        finished = True


    if ("__main__" == __name__):
        try:
            async_thread = async.AsyncThread()

            with ev3.EV3() as brick:
                async_thread.put(brick.keep_alive, keep_alive_finished)

                while (not finished):
                    print 'Waiting...'
                    time.sleep(0.1)

        except ev3.EV3Error as ex:
            print 'An error occurred: ', ex

        async_thread.stop()

"""


import threading
import Queue


class AsyncThread(threading.Thread):
    """A simple thread subclass maintains a queue of functions to call."""


    _STOP_QUEUE_ITEM = 'STOP'


    def __init__(self):
        """Creates and starts a new thread."""
        super(AsyncThread, self).__init__()

        self._daemon = True
        self._queue = Queue.Queue()

        self.start()


    def run(self):
        """This function is called automatically by the Thread class."""
        try:
            while(True):
                item = self._queue.get(block=True)

                if (self._STOP_QUEUE_ITEM == item):
                    break

                ev3_func, cb, args, kwargs = item

                cb(ev3_func(*args, **kwargs))

        except KeyboardInterrupt:
            pass


    def stop(self):
        """Instructs the thread to exit after the current function is
        finished.

        """
        with self._queue.mutex:
            self._queue.queue.clear()

        self._queue.put(self._STOP_QUEUE_ITEM)


    def put(self, ev3_func, cb, *args, **kwargs):
        """Adds a new function to the queue. The cb (callback) parameter should
        be a function that accepts the result as its only parameter.

        """
        self._queue.put((ev3_func, cb, args, kwargs))
