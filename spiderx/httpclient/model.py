#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
a model represents http response
"""
class HTTPResponse :

    def __init__(self, url=None):
        self.status = 501
        self._header = {}
        # byte array
        self.msg = None
        self.vmaj = 1
        self.vmin = 1
        self.reason = None
        self.url = url

    def add_header(self, header, content) :
        if None == content :
            return
        header = header.strip().lower()
        content = content.strip()

        if header not in self._header :
            if type(content) is list :
                if 1 == len(content) :
                    self._header[header] = content[0]
                    return 
            self._header[header] = content
            return

        if type(self._header[header]) is list :
            if type(content) is list :
                self._header[header] += content
            else :
               self._header[header].append(content)
        else :
            if type(content) is list :
               self._header[header] = [self._header[header]] + content
            else :
               self._header[header] = [self._header[header]]
               self._header[header].append(content)

    def header(self, header=None) :
        if None == header :
            return self._header
        h = header.lower()
        if h not in self._header :
            return None
        return self._header[h]
