#!/usr/bin/env python

import os
import logging
import ctypes
import cPickle
from threading import Thread


def split_lines(buffer):
    """Split ``buffer`` into lines.

    If the last line is not terminated by a \\n,
    it is an incomplete line.
    """
    lines = buffer.split('\n')
    last_line = lines.pop()

    if last_line == '':
        # The last line was terminated with a line return
        incomplete = str()
    else:
        # The last line wasn't terminated with a line return,
        # could be an incomplete line.
        incomplete = last_line

    return lines, incomplete


class PipeForwarder(Thread):
    """Poll a file descriptor and forward data to a callback.
    """
    def __init__(self, fd, callback):
        super(PipeForwarder, self).__init__()
        self.fd = fd
        self.callback = callback

    def run(self):
        while True:
            data = os.read(self.fd, 1024)

            if data:  # New data
                self.handle(data)

            else:  # No more data
                self.stop()
                break

    def handle(self, data):
        self.callback(data)

    def stop(self):
        pass


class LinePipeForwarder(PipeForwarder):
    """Poll a file descriptor and forward each line to a callback.
    """
    def __init__(self, fd, callback):
        super(LinePipeForwarder, self).__init__(fd, callback)
        self.buffer = str()

    def handle(self, data):
        # Append it to the buffer
        self.buffer += data
        # Extract complete lines from the buffer
        lines, incomplete = split_lines(self.buffer)
        # Forward complete lines
        for line in lines:
            self.callback(line)
        # Keep this in buffer, waiting for more data
        self.buffer = incomplete

    def stop(self):
        if self.buffer:
            # Split buffer into lines
            lines, incomplete = split_lines(self.buffer)

            if incomplete:
                lines.append(incomplete)

            # Send each line to the callback
            for line in lines:
                self.callback(line)

            self.buffer = str()


class Worker(object):

    def __init__(self, target, *args, **kwargs):
        super(Worker, self).__init__()
        self.target = target
        self.args = args
        self.kwargs = kwargs
        self.stdout_streamer = None
        self.stderr_streamer = None
        self.result_streamer = None
        self.child_pid = None
        self.raw_result = None
        self.result = None

    def start(self):
        out_read, out_write = os.pipe()
        err_read, err_write = os.pipe()
        result_read, result_write = os.pipe()
        pid = os.fork()

        if pid:  # In parent
            self.child_pid = pid
            #logging.debug('Worker PID: %s', pid)
            # Close write side of pipes
            os.close(out_write)
            os.close(err_write)
            os.close(result_write)
            # Stream out and err to their queues
            self.stdout_streamer = LinePipeForwarder(out_read, logging.info)
            self.stderr_streamer = LinePipeForwarder(err_read, logging.error)
            self.result_streamer = PipeForwarder(result_read,
                                                 self._append_raw_result)
            self.stdout_streamer.start()
            self.stderr_streamer.start()
            self.result_streamer.start()

            return self

        else:  # In child
            # Close read side of pipes
            os.close(out_read)
            os.close(err_read)
            # Connect stdout to its pipe
            os.dup2(out_write, 1)
            # Connect stderr to its pipe
            os.dup2(err_write, 2)
            # Ensure the worker process do not inherits its parent logging
            # handlers.
            root_logger = logging.getLogger()
            root_logger.handlers = [logging.NullHandler()]
            # Run target
            raw_result = self.target(*self.args, **self.kwargs)
            result = cPickle.dumps(raw_result)
            # Feed the result to the result pipe
            os.write(result_write, result)

            raise SystemExit

    def _append_raw_result(self, raw_result_part):
        if self.raw_result is None:
            self.raw_result = raw_result_part
        else:
            self.raw_result += raw_result_part

    def join(self):
        if self.child_pid:
            os.waitpid(self.child_pid, 0)

            self.stdout_streamer.join()
            self.stdout_streamer = None

            self.stderr_streamer.join()
            self.stderr_streamer = None

            self.result_streamer.join()
            self.result_streamer = None

            if self.raw_result:
                self.result = cPickle.loads(self.raw_result)

        return self


def go(callable_, *args, **kwargs):
    """Run ``callable_``, passing it ``args`` and ``kwargs``.
    """
    return Worker(callable_, *args, **kwargs).start().join().result


def libgo(lib_name, func_name, *args, **kwargs):
    """Load ``func_name`` from ``lib_name``,
    then call it, passing ``args`` and ``kwargs``.
    """
    lib = ctypes.cdll.LoadLibrary(lib_name)
    func = getattr(lib, func_name)
    return go(func, *args, **kwargs)
