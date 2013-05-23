#!/usr/bin/env python
# -*- coding: utf-8 -*-
import unicodedata

_ws = [
    0x9, 
    0xB,
    0xC,
    0x20,
    0xA0,
    0xFEFF,
    0x1680,
    0x180E,
    0x2000, 0x2001, 0x2002, 0x2003, 0x2004,
    0x2005, 0x2006, 0x2007, 0x2008, 0x2009,
    0x200A, 0x202F, 0x205F, 0x3000
]
_nl = [13, 10]

_letter = ['Ll', 'Lt', 'Lu', 'Lm', 'lo', 'Nl', 'Mn', 'Mc', 'Nd', 'Pc', 'Pd']

def isWS(char) :
    return ord(char) in _ws

def isNL(char) :
    return ord(char) in _nl

def isLetter(char) :
    return unicodedata.category(char) in _letter  or \
            "!" == char or "?" == char or ":" == char

if __name__ == "__main__" :
    import unittest 

    class TxTest(unittest.TestCase) :
        def test(self) :
            self.assertTrue(isWS(" "))

            self.assertTrue(isNL("\n"))
            self.assertTrue(isNL("\r"))
            self.assertTrue(isNL("""
"""))
            string = "a1".decode("utf8")
            self.assertTrue(isLetter(string[0]))
            self.assertTrue(isLetter(string[1]))
            self.assertTrue(isLetter(u"_"))
            self.assertTrue(isLetter(u"-"))
            self.assertTrue(isLetter(u"!"))
            self.assertTrue(isLetter(u"?"))
            self.assertFalse(isLetter(u">"))
            self.assertFalse(isLetter(u" "))
            self.assertTrue(isLetter(u":"))
    unittest.main()
