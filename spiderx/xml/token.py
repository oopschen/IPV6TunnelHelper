#!/usr/bin/env python
# -*- coding: utf-8 -*-
if __name__ == "__main__" :
    import sys, os.path
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import StringIO
from spiderx.core import text

# <
TT_BRACK_START = 0x1
# >
TT_BRACK_END = 0x2
# a b c 123
TT_STR = 0x4
# "a"
TT_QUOTE_STR = 0x8
# =
TT_EQ = 0x10
# /
TT_SLASH = 0x20
# !--
TT_COMMENT= 0x40
# ?xml
TT_XML = 0x80
# !doctype
TT_DOC = 0x100

class Token :

    def __init__(self, typ = TT_STR, data = None) :
        self.typ = typ
        self.data = data

class BaseTokenLizer :

    def __init__(self, doc) :
        self._doc = doc
        self._doc_len = len(doc)
        self._doc_pos = 0

    def reload(self) :
        self._doc_pos = 0

    def read(self, nchar = 1) :
        s = self._doc_pos
        if (self._doc_pos + nchar) < self._doc_len :
            self._doc_pos += nchar
        else :
            self._doc_pos = self._doc_len
        if s == self._doc_len :
            return False
        if 1 == nchar :
            return self._doc[s]
        return self._doc[s : self._doc_pos]

    def pushback(self, num=1) :
        self._doc_pos -= num
        if 0 > self._doc_pos :
            self._doc_pos = 0

class Tokenlizer(BaseTokenLizer) :

    def __init__(self, doc) :
        BaseTokenLizer.__init__(self, doc)

    def _try_read_start_tag_close(self, t) :
        self._try_read_start_tag_found(t)
        return False

    def _try_read_start_tag_found(self, t) :
        ct = t.getvalue()
        t.close()
        self.pushback(len(ct))
        return True

    """xxx xxx="xx"; xxx >; xxxx/>;"""
    def _try_read_start_tag(self) :
        t = StringIO.StringIO()
        # read tagname as if there is
        rCount = 0
        while True :
            char = self.read()
            if None == char :
                return self._try_read_start_tag_close(t)
            # maybe space, >, /
            if not text.isLetter(char) :
                self.pushback()
                break
            t.write(char)
            rCount += 1

        # if read none fail
        if 1 > rCount :
            return self._try_read_start_tag_close(t)

        # skip whitespace
        rCount = 0
        while True :
            char = self.read()
            if None == char :
                return self._try_read_start_tag_close(t)
            if text.isWS(char) or text.isNL(char) :
                t.write(char)
                rCount += 1
                continue
            self.pushback()
            break

        # incase >, />
        char = self.read()
        if ">" == char :
            self.pushback()
            return self._try_read_start_tag_found(t)
        elif "/" == char :
            char1 = self.read()
            if None == char1 :
                self.pushback()
                return self._try_read_start_tag_close(t)
            self.pushback(2)
            if ">" != char1 :
                return self._try_read_start_tag_close(t)
            return self._try_read_start_tag_found(t)
        else :
            self.pushback()

            # if not <xx> <xx/> must have at least one space
            if 1 > rCount :
                return self._try_read_start_tag_close(t)

        # maybe pattern, <xxx xx
        rCount = 0
        while True :
            char = self.read()
            if None == char :
                return self._try_read_start_tag_close(t)
            if not text.isLetter(char) :
                self.pushback()
                break
            t.write(char)
            rCount += 1

        if 1 > rCount :
            return self._try_read_start_tag_close(t)


        # skip Ws
        while True :
            char = self.read()
            if None == char :
                return self._try_read_start_tag_close(t)
            if text.isWS(char) or text.isNL(char) :
                t.write(char)
                continue
            self.pushback()
            break

        char = self.read()
        self.pushback()

        if "=" == char :
            return self._try_read_start_tag_found(t)
        elif ">" == char :
            return self._try_read_start_tag_found(t)

        return self._try_read_start_tag_close(t)

    def _read_quote_str(self, quoteChar) :
        string = StringIO.StringIO()
        last = None
        while True :
            char = self.read()
            if False == char :
                break
            if "\\" != last and quoteChar == char :
                break
            string.write(char)
            last = char
        s = string.getvalue()
        string.close()
        return Token(TT_QUOTE_STR, s)

    def _read_str(self, c) :
        string = StringIO.StringIO()
        string.write(c)
        while True :
            char = self.read()
            if False == char :
                break
            if text.isLetter(char) :
                string.write(char)
                continue
            self.pushback()
            break
        s = string.getvalue()
        string.close()
        return Token(TT_STR, s)

    """
    read content until starttag
    any start tags between quote are ignored based on the argument "isRegcQuote" :
        if isRegcQuote :
            any tag-like literal which is quote are included as content 
        else :
            any tag-like literal which is quote are not included as content 
    """
    def read_cdata(self, isRegcQuote = False) :
        string = StringIO.StringIO()
        isInQuote = False
        quoteMark = None
        last = None
        while True :
            char = self.read()
            if False == char :
                break
            if isRegcQuote :
                if ("\"" == char or "'" == char) and "\\" != last :
                    if None == quoteMark :
                        isInQuote = not isInQuote
                        quoteMark = char
                    elif char == quoteMark :
                        isInQuote = not isInQuote
                        quoteMark = None
                    string.write(char)
                    last = char
                    continue

                if isInQuote :
                    string.write(char)
                    last = char
                    continue
            # end rec
                    
            if "<" != char :
                string.write(char)
                last = char
                continue

            char1 = self.read()
            if False == char1 :
                string.write(char)
                break
            # </ then break
            if "/" == char1 :
                self.pushback(2)
                break
            # <xxxxx [a="b"]* >
            elif " " == char1 :
                string.write(char)
                string.write(char1)
                last = char
                continue
            # <!-- <?xml
            elif "!" == char1 or "?" == char1 :
                eq = False
                expectedTexts = None
                # <?xml 
                if "?" == char1 :
                    expectedTexts = ["xml"]
                else :
                    expectedTexts = ["--", "doctype"]

                for expectedText in expectedTexts :
                    if self._read_expected_str_caseinsensitive(expectedText, True) :
                        eq = True
                        break
                # end 

                # pushback char1 char
                if eq :
                    self.pushback(2)
                    break
                # not eq then read the char char1
                string.write(char)
                string.write(char1)
            # find start tag break
            else :
                # find start tag return True until start tag else return False roll back to pos next to char
                self.pushback()
                s = self._try_read_start_tag()
                if not s :
                    string.write(char)
                    continue
                self.pushback()
                break

        s = string.getvalue().strip()
        string.close()
        if 1 > len(s) :
            return None
        return s

    def next(self) :
        while True :
            char = self.read()
            if False == char :
                return None

            if text.isWS(char) or text.isNL(char) :
                continue

            if "<" == char :
                return Token(TT_BRACK_START)
            elif ">" == char :
                return Token(TT_BRACK_END)
            elif "=" == char :
                return Token(TT_EQ)
            elif "/" == char :
                return Token(TT_SLASH)
            elif "\"" == char or "'" == char :
                return self._read_quote_str(char)
            elif "!" == char :
                return self._read_comment(char)
            elif "?" == char :
                return self._read_xml(char)
            return self._read_str(char)

    def next_until(self, string) :
        if None == string or 1 > len(string.strip()) :
            return None
        s = None
        size = len(string)
        while True :
            char = self.read()
            if False == char :
                break
            if string[0] == char :
                cur = 1
                isFound = True
                while cur < size :
                    char = self.read()
                    if False == char :
                        break
                    # if not eq return
                    if char != string[cur] :
                        isFound = False
                        self.pushback()
                        break
                    cur += 1
                # end while 
                if isFound :
                    break
                self.pushback(cur - 1)
                if None == s :
                    s = StringIO.StringIO()
                s.write(string[0])
                continue
            # record char
            if None == s :
                s = StringIO.StringIO()
            s.write(char)
        # end while 
        if None == s :
            return None
        content = s.getvalue()
        s.close()
        return content

    def _read_comment(self, char) :
        if self._read_expected_str_caseinsensitive("--") :
            return Token(TT_COMMENT, "!--")
        return self._read_doctype(char)

    def _read_doctype(self, char) :
        if self._read_expected_str_caseinsensitive("doctype"):
            return Token(TT_DOC, "!doctype")
        return self._read_str(char)

    def _read_xml(self, char) :
        if self._read_expected_str_caseinsensitive("xml") :
            return Token(TT_XML, "?xml")
        return self._read_str(char)

    def _read_expected_str_caseinsensitive(self, expected, pushback = False) :
        eq = True
        readCounts = 0
        for lt in expected :
            tmp = self.read()
            readCounts += 1
            if False == tmp :
                eq = False
                break

            if lt.lower() == tmp.lower() :
                continue
            eq = False
            break

        if eq :
            if pushback :
                self.pushback(readCounts)
            return True

        self.pushback(readCounts)
        return False

if __name__ == "__main__" :
    import unittest

    class TokenlizerTest(unittest.TestCase) :

        def test(self) :
            doc = """
                <a a="c" b=''>
        'abcd你ddsafif(1<1dsfs){}a=1<b;c=1<9<!-<f/><!--n--><d /></a>
            """.decode("utf8")
            tokenL = Tokenlizer(doc)

            token = tokenL.next()
            self.assertTrue(TT_BRACK_START  &  token.typ)

            token = tokenL.next()
            self.assertTrue(TT_STR  &  token.typ and "a" == token.data)

            token = tokenL.next()
            self.assertTrue(TT_STR  &  token.typ and "a" == token.data)

            token = tokenL.next()
            self.assertTrue(TT_EQ  &  token.typ)

            token = tokenL.next()
            self.assertTrue(TT_QUOTE_STR &  token.typ and "c" == token.data)

            token = tokenL.next()
            self.assertTrue(TT_STR &  token.typ and "b" == token.data)

            token = tokenL.next()
            self.assertTrue(TT_EQ  &  token.typ)

            token = tokenL.next()
            self.assertTrue(TT_QUOTE_STR &  token.typ and "" == token.data)

            token = tokenL.next()
            self.assertTrue(TT_BRACK_END  &  token.typ)

            sr = tokenL.read_cdata()
            self.assertTrue(sr == u"'abcd你ddsafif(1<1dsfs){}a=1<b;c=1<9<!-", sr)

            token = tokenL.next()
            self.assertTrue(TT_BRACK_START  &  token.typ)

            token = tokenL.next()
            self.assertTrue(TT_STR  &  token.typ and "f" == token.data, token.data)

            token = tokenL.next()
            self.assertTrue(TT_SLASH  &  token.typ)

            token = tokenL.next()
            self.assertTrue(TT_BRACK_END  &  token.typ)

            token = tokenL.next()
            self.assertTrue(TT_BRACK_START  &  token.typ)

            token = tokenL.next()
            self.assertTrue(TT_COMMENT  &  token.typ)

            token = tokenL.next()
            self.assertTrue(TT_STR  &  token.typ and "n--"== token.data, token.data)

            token = tokenL.next()
            self.assertTrue(TT_BRACK_END  &  token.typ)

            token = tokenL.next()
            self.assertTrue(TT_BRACK_START  &  token.typ)

            token = tokenL.next()
            self.assertTrue(TT_STR  &  token.typ and "d" == token.data)

            token = tokenL.next()
            self.assertTrue(TT_SLASH  &  token.typ)

            token = tokenL.next()
            self.assertTrue(TT_BRACK_END  &  token.typ)

            token = tokenL.next()
            self.assertTrue(TT_BRACK_START  &  token.typ)

            token = tokenL.next()
            self.assertTrue(TT_SLASH  &  token.typ)

            token = tokenL.next()
            self.assertTrue(TT_STR  &  token.typ and "a" == token.data)

            token = tokenL.next()
            self.assertTrue(TT_BRACK_END  &  token.typ)

            token = tokenL.next()
            self.assertTrue(None == token)

        def test_next_until(self) :
            doc = """
                <a a="c" b=''>
abcd你"ddsaf"</a>
            """.decode("utf8")
            tokenL = Tokenlizer(doc)
            aeq = tokenL.next_until("a=")
            self.assertTrue("""
                <a """ == aeq, aeq)

            token = tokenL.next()
            self.assertTrue(TT_QUOTE_STR  &  token.typ and "c" == token.data)

            aeq = tokenL.next_until("b")
            self.assertTrue(" " == aeq)

        def test_1(self) :
            doc = u"""
                <a>abd<!<a c-_d  ="1"</a>
            """
            tokenL = Tokenlizer(doc)

            token = tokenL.next()
            self.assertTrue(TT_BRACK_START  &  token.typ)

            token = tokenL.next()
            self.assertTrue(TT_STR  &  token.typ and "a" == token.data)

            token = tokenL.next()
            self.assertTrue(TT_BRACK_END  &  token.typ)

            token = tokenL.read_cdata()
            self.assertTrue("abd<!"== token, token)

            token = tokenL.next()
            self.assertTrue(TT_BRACK_START  &  token.typ)

            token = tokenL.next()
            self.assertTrue(TT_STR  &  token.typ and "a" == token.data)

    unittest.main()
