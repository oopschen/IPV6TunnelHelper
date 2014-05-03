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
        self.n = name
        self.m = None
        self.un = uname
        self.upwd = upwd
        
    """
    mode  OPEN CLOSE 
    when mode == OPEN | CLOSE : CLOSE : OPEN
    """
    def run(self, mode) :
        if mode & CLOSE :
            self.close()

        if mode & OPEN :
            b = Broker()
            if not b.login(self.un, self.upwd) :
                return
            self.m = b.nonexist_tunnel_create_or_set()
            if False == self.m :
                return
            self.open()

    def open(self) :
        pass

    def close(self) :
        pass

class OSRunner(BaseRunner) :

    def __init__(self, name, pwd) :
        BaseRunner.__init__(self, "tmpTunnelv4v6", name, pwd)
        self._fp = self.__getTMPDataFileByOSTYP()

    def open(self) :
        if os.path.exists(self._fp) :
          self.close()

        # create data file
        logger.info("write to file %s", self._fp)
        with open(self._fp, 'wb+') as output :
            pickle.dump(self.m, output)

        openRoutine = self.__getRoutineByOSTYP(True)
        if None == openRoutine :
          logger.error("open cmd: not found")
          return False

        cmd = openRoutine(self)
        logger.info("open cmd: %s", cmd)
        return os.system(cmd)

    def close(self) :
        if os.path.exists(self._fp) :
            logger.info("read from file %s", self._fp)
            with open(self._fp, 'rb') as f :
                self.m = pickle.load(f)

            closeRoutine = self.__getRoutineByOSTYP(False)
            if None == closeRoutine :
              logger.error("close cmd: not found")
              return False

            cmd = closeRoutine(self)
            logger.info("close cmd: %s", cmd)
            ret = os.system(cmd)
            if 0 == ret :
                os.remove(self._fp)
            return ret
        else :
            logger.info("no previous configuration found")
            return True

    def __getRoutineByOSTYP(self, isOpen) :
      if "nt" == os.name :
        if isOpen :
          return routine_open_nt
        else :
          return routine_close_nt

      elif "posix" == os.name :
        if isOpen :
          return routine_open_linux
        else :
          return routine_close_linux

      return None

    def __getTMPDataFileByOSTYP(self) :
      tmpfile = "xtunnel.tmp"

      if "nt" == os.name :
        tmpfile = os.path.join(os.path.dirname(__file__), tmpfile)

      elif "posix" == os.name :
        tmpfile = os.path.join("/tmp", tmpfile)

      return tmpfile

# routine for diffrent os
def routine_open_nt (self) :
    return "%s %s %s %s %s %s %s" % (
        os.path.realpath(os.path.join(os.path.dirname(__file__), "win7", "open.bat")),
        self.n,
        self.m.cip4,
        self.m.cip6,
        self.m.sip4,
        self.m.sip6,
        self.m.routepre
        )

def routine_close_nt(self) :
    return "%s %s %s" % (
        os.path.realpath(os.path.join(os.path.dirname(__file__), "win7", "close.bat")),
        self.n,
        self.m.cip6
        )
# end windows

def routine_open_linux(self) :
    return "sh %s %s %s %s %s %s %s" % (
        os.path.realpath(os.path.join(os.path.dirname(__file__), "linux", "open.sh")),
        self.n,
        self.m.cip4,
        self.m.cip6,
        self.m.sip4,
        self.m.sip6,
        self.m.routepre
        )

def routine_close_linux(self) :
    return "sh %s %s %s %s %s %s %s" % (
        os.path.realpath(os.path.join(os.path.dirname(__file__), "linux", "close.sh")),
        self.n,
        self.m.cip4,
        self.m.cip6,
        self.m.sip4,
        self.m.sip6,
        self.m.routepre
        )
