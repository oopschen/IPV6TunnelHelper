#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
xpath cmd format :
    ele > ele@attrName = attrValue [@attrName = attrValue]
    escape @ = > using \: 
"""
if __name__ == "__main__" :
    import sys, os.path
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from cStringIO import StringIO
import collections
import token
from spiderx.core import text

_cache = None
_TK_STR = 0x1
_TK_AT = 0x2
_TK_EQ = 0x4
_TK_GT = 0x8

class CMDTokenLizer(token.BaseTokenLizer) :

    def __init__(self, cmd) :
        token.BaseTokenLizer.__init__(self, cmd)
        self._q = None

    def _read_str(self) :
        s = last = None
        while True :
            char = self.read()
            if False == char :
                break
            if text.isWS(char) or text.isNL(char) :
                break
            # encounter \ but not \\
            if "\\" == char and "\\" != last :
                last = char
                continue

            # encounter not escape @ = >
            if last != "\\" and \
                    ("@" == char or "=" == char or ">" == char) :
                self.pushback()
                break
            last = char
            if None == s :
                s = StringIO()
            s.write(char)

        t = token.Token(_TK_STR, s.getvalue())
        s.close()
        return t

    def _next(self) :
        char = False
        while True :
            char = self.read()
            if False == char :
                break
            if text.isWS(char) or text.isNL(char) :
                continue
            break
        if False == char :
            return None
        elif "@" == char :
            return token.Token(_TK_AT)
        elif ">" == char :
            return token.Token(_TK_GT)
        elif "=" == char :
            return token.Token(_TK_EQ)
        self.pushback()
        return self._read_str()

    def next(self) :
        if None == self._q or 1 > len(self._q) :
            return self._next()
        return self._q.popleft()

    def pb_token(self, token) : 
        if None == self._q :
            self._q = collections.deque()
        self._q.append(token)

MODE_SEARCH_DIRECT_CHILDS = 0x1
MODE_SEARCH_CHILDS = 0x2

class Element :

    def __init__(self, name) :
        self.mode = MODE_SEARCH_DIRECT_CHILDS
        self.name = name
        self._attrs = None

    def add_attr(self, name, value = None) :
        if None == name :
            return
        if None == self._attrs :
            self._attrs = {}
        self._attrs[name] = value

    """
    name equals and self._attrs is subset of attrs
    """
    def eq(self, name, attrs = None) :
        if name != self.name :
            return False

        if None == self._attrs:
            return True

        if None == attrs :
            return False

        for k, v in self._attrs.iteritems() :
            if k not in attrs or v != attrs[k]:
                return False
        return True

def _parse_attrs(tokenl, ele) :
    while True :
        tn = tokenl.next()
        if None == tn :
            break
        if _TK_AT ^ tn.typ :
            tokenl.pb_token(tn)
            return
        # read attrname
        tn = tokenl.next()
        if None == tn :
            break
        if _TK_STR ^ tn.typ :
            tokenl.pb_token(tn)
            return
        name = tn.data

        # eq
        tn = tokenl.next()
        if None == tn :
            break
        if _TK_EQ ^ tn.typ :
            tokenl.pb_token(tn)
            return

        # value
        tn = tokenl.next()
        if None == tn :
            break
        if _TK_STR ^ tn.typ :
            tokenl.pb_token(tn)
            return
        ele.add_attr(name, tn.data)

"""
parse xpath like cmd line with cache :
    element[@attrName=attrVal]
    > means direct child
"""
def parse_cmd(cmd) :
    if None == cmd or 1 > len(cmd) :
        return None

    global _cache
    if None != _cache and cmd in _cache :
        return _cache[cmd]

    tokenl = CMDTokenLizer(cmd)
    cmds = None
    m = MODE_SEARCH_CHILDS
    while True :
        tn = tokenl.next()
        if None == tn :
            break
        if _TK_STR ^ tn.typ :
            return None

        e = Element(tn.data)
        e.mode = m

        # init cmds list
        if None == cmds :
            cmds = []
        cmds.append(e)

        _parse_attrs(tokenl, e)
        # read if > then MODE_SEARCH_DIRECT_CHILDS  else MODE_SEARCH_CHILDS
        tn = tokenl.next()
        if None == tn :
            break

        if _TK_GT & tn.typ :
            m = MODE_SEARCH_DIRECT_CHILDS
            continue
        elif _TK_STR & tn.typ :
            tokenl.pb_token(tn)
            m = MODE_SEARCH_CHILDS
        else :
            return None

    # end while
    if None == cmds :
        return None
    if None == _cache :
        _cache = {}
    cmds[0].mode = MODE_SEARCH_CHILDS
    _cache[cmd] = cmds
    return cmds

if __name__ == "__main__" :
    import unittest 

    class CMDTest(unittest.TestCase) :

        def test_correct_cmd(self) :
            cmds = parse_cmd("html > body@\\@1=12\\=3 \ndiv@a=\\>")
            self.assertTrue(3 == len(cmds), cmds)

            self.assertTrue(cmds[0].eq("html"))
            self.assertTrue(cmds[0].mode == MODE_SEARCH_CHILDS)
            self.assertTrue(cmds[1].eq("body", {"@1" : "12=3"}))
            self.assertTrue(cmds[1].eq("body", {"@1" : "12=3", "1" : 2}))
            self.assertTrue(cmds[1].mode == MODE_SEARCH_DIRECT_CHILDS)
            self.assertTrue(cmds[2].eq("div", {"a" : ">"}))

            cmds = parse_cmd("html > body iframe > div a@d=1@c=d")
            self.assertTrue(5 == len(cmds), cmds)
            self.assertTrue(MODE_SEARCH_DIRECT_CHILDS & cmds[1].mode, "2nd fail")
            self.assertTrue(MODE_SEARCH_CHILDS & cmds[2].mode, "3rd fail")
            self.assertTrue(MODE_SEARCH_DIRECT_CHILDS & cmds[3].mode, "4rd fail")
            self.assertTrue(MODE_SEARCH_CHILDS & cmds[4].mode, "5rd fail")
            self.assertTrue(cmds[4].eq("a", {"d" : "1", "c":"d"}), "a attr d")

        def test_uncorrect_cmds(self) :
            cmds = parse_cmd("html > @")
            self.assertTrue(None == cmds)

            cmds = parse_cmd("html > a >")
            self.assertTrue(2 == len(cmds))

            cmds = parse_cmd("html@abc=@ > a >")
            self.assertTrue(None == cmds)

            cmds = parse_cmd("html = a")
            self.assertTrue(None == cmds)
    unittest.main()
