#!/usr/bin/env python

import sys
import ctypes
import logging


def setup_logging(level=logging.DEBUG, logger=None):
    #msg_format = '%(process)d:%(thread)d:%(threadName)s:' \
    #    '%(module)s:%(funcName)s:%(lineno)d:%(asctime)s.%(msecs)03d:' \
    #    '%(levelname)s:%(name)s:%(message)s'
    msg_format = '%(levelname)s %(message)s'
    time_format = '%H:%M:%S'
    formatter = logging.Formatter(msg_format, time_format)
    logger = logger or logging.getLogger()
    logger.setLevel(level)
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)


if __name__ == '__main__':
    if sys.platform == 'darwin':
        libext = 'dylib'
    else:
        libext = 'so'
    libname = 'libhello.%s' % libext
    setup_logging()
    from wrapper import libgo
    # INFO hello world!
    libgo(libname, "hello", "world!")
    # ERROR hello Error!
    libgo(libname, "err_hello", "Error!")
    # INFO hello Joe (0)
    # INFO hello Joe (1)
    # INFO hello Joe (2)
    libgo(libname, "many_hello", "Joe", 3)
    assert libgo(libname, "add", 40, 2) == 42

