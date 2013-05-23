#!/usr/bin/env python
# -*- coding: utf-8 -*-

from spiderx.core.ilog import get
from tunnelbroker import Broker
import os
import os.path
import pickle

logger = get(__file__)
OPEN = 0x1
CLOSE = 0x2

class BaseRunner :
    
    def __init__(self, name, uname, upwd) :
        self._n = name
        self._m = None
        self._un = uname
        self._upwd = upwd
        
    """
    mode  OPEN CLOSE 
    when mode == OPEN | CLOSE : CLOSE : OPEN
    """
    def run(self, mode) :
        if mode & CLOSE :
            self.close()

        if mode & OPEN :
            b = Broker()
            if not b.login(self._un, self._upwd) :
                return
            self._m = b.nonexist_tunnel_create_or_set()
            if False == self._m :
                return
            self.open()

    def open(self) :
        pass

    def close(self) :
        pass

class Win7Runner(BaseRunner) :

    def __init__(self, name, pwd) :
        BaseRunner.__init__(self, "tmpTunnelv4v6", name, pwd)
        self._fp = os.path.join(os.path.dirname(__file__), "win7", ".data")

    def open(self) :
        logger.info("write to file %s", self._fp)
        with open(self._fp, 'wb+') as output :
            pickle.dump(self._m, output)

        cmd = "%s %s %s %s %s %s %s" % (
            os.path.realpath(os.path.join(os.path.dirname(__file__), "win7", "open.bat")),
            self._n,
            self._m.cip4,
            self._m.cip6,
            self._m.sip4,
            self._m.sip6,
            self._m.routepre
            )
        logger.info("open cmd: %s", cmd)
        return os.system(cmd)

    def close(self) :
        if os.path.exists(self._fp) :
            logger.info("read from file %s", self._fp)
            with open(self._fp, 'rb') as input :
                self._m = pickle.load(input)

            cmd = "%s %s %s" % (
                os.path.realpath(os.path.join(os.path.dirname(__file__), "win7", "close.bat")),
                self._n,
                self._m.cip6
                )
            logger.info("close cmd: %s", cmd)
            ret = os.system(cmd)
            if 0 == ret :
                os.remove(self._fp)
            return ret
        else :
            logger.info("no previous configuration found")
            return True


if __name__ == "__main__" :
    from tunnelbroker import Meta
    meta = Meta()
    meta.cip4 = meta.sip4 = "127.0.0.1"
    meta.cip6 = meta.sip6 = "2001:23::0"
    r = Win7Runner(meta)
    r.run(OPEN | CLOSE)
