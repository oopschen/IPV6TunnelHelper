#!/usr/bin/env python
# -*- coding: utf-8 -*-
import datetime

_start_ts = datetime.datetime.today()

def time_to_ms(td) :
    return (td.microseconds + (td.seconds + td.days * 24 * 3600) * 10**6) / 10**3

def get_timestamp_ms(date=None) :
    d = date
    if None == d :
        d = datetime.datetime.today()

    global _start_ts
    return time_to_ms(d - _start_ts)

def get_timestamp_sec(date=None) :
    return get_timestamp_ms(date) / 10**3
