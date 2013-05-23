#!/usr/bin/env python
# -*- coding: utf-8 -*-

from spiderx.core.ilog import get
from cmdrunner import *
import sys

argc = len(sys.argv)
if 2 > argc :
    print """
    usage : 
            o(open), username, pwd
            c(close)
    """
    sys.exit(1)

mode = CLOSE
imode = sys.argv[1].strip().lower()
name = pwd = None
if 2 < argc :
    name = sys.argv[2]
    pwd = sys.argv[3]

if "o" == imode or "open" == imode :
    mode |= OPEN

r = Win7Runner(name, pwd)
r.run(mode)
