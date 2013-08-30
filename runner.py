#!/usr/bin/env python
# -*- coding: utf-8 -*-

from spiderx.core.ilog import get
from cmdrunner import *
import sys
import argparse

parse = argparse.ArgumentParser(description="helper for ipv6 tunnel")
parse.add_argument("username", help="username for login")
parse.add_argument("password", help="password for login")
parse.add_argument("-m", dest="mode", choices=['o', 'c'], help="mode for operation open(o), close(c)", default="o")
args = parse.parse_args()

if "c" == args.mode :
    mode = CLOSE
else :
    mode = OPEN

r = OSRunner(args.username, args.password)
r.run(mode)
