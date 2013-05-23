#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import traceback

def trace() :
    traceback.print_exc(file=sys.stdout)

def trace_str() :
    return traceback.format_exc()
