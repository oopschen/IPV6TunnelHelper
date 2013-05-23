#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import logging.config
import os.path
import __main__

_defaultlogConfPath = os.path.join(os.path.dirname(__file__), "log.conf.default")
_logConfPath = os.path.join(os.path.dirname(__main__.__file__), "log.conf")

if not os.path.exists(_logConfPath) :
    _logConfPath= _defaultlogConfPath
_logConfPath = os.path.realpath(_logConfPath)

print "ilog configuration:[%s]" % (_logConfPath)
logging.config.fileConfig(_logConfPath)

def get(name) :
    return logging.getLogger(name)

if __name__ == "__main__" :
    get("test_logger").info("hello")
