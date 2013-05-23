#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
this module is responsible for parsing <> like doc, do not loss any data , any things under unclosed tag is the child of the tag

1. when a tag(either start tag or end tag or <x /> tag) and content found callback a given funtion, callback has two argument: type, tag/content
2. skip any chars outside <x></x> pairs
3. do not distinguish <!-- > <x> tags
"""
if __name__ == "__main__" :
    import sys, os.path
    sys.path.append(os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "..")
    ))

from cStringIO import StringIO
from spiderx.xml import token
import collections


class Tag :
    
    def __init__(self, name) :
        self.name = name
        self._attrs = None
        self.content = None

    def add_attr(self, attrName, attrValue) :
        if None == self._attrs :
            self._attrs = {}
        self._attrs[attrName] = attrValue

    def attrs(self, attrName = None) :
        if None == attrName :
            return self._attrs
        if attrName not in self._attrs :
            return None
        return self._attrs[attrName]

"""
<>语言解析，返回列表
"""
class MarkLangParser :

    def start_tag(self, tag) :
        pass

    def end_tag(self, tag) :
        pass

    def content(self, content) :
        pass

    def __init__(self, doc) :
        self._token = token.Tokenlizer(doc)
        self._readedToken = None
        self._readedTokenLen = 0

    def reload(self) :
        self._token.reload()
        self._readedTokenLen = 0

    def read(self) :
        if self._readedTokenLen > 0:
            self._readedTokenLen -= 1
            return self._readedToken.popleft()
        return self._token.next()

    def read_cdata(self, isRecQuote = False) :
        if 0 < self._readedTokenLen :
            return None
        return self._token.read_cdata(isRecQuote)

    def pushback(self, token) :
        if None == self._readedToken :
            self._readedToken = collections.deque()
        self._readedToken.append(token)
        self._readedTokenLen += 1

    def _read_attrs(self, node) :
        while True :
            # read until --, >, =
            eof = False
            name = ""
            tn = None
            while True:
                tn = self.read()
                if None == tn :
                    eof = True
                    break
                if token.TT_STR ^ tn.typ :
                    break
                if "--" == tn.data :
                    self.pushback(tn)
                    break
                name +=  tn.data
            # end

            if eof :
                if 0 < len(name) :
                    node.add_attr(name, None)
                return

            # read =
            if token.TT_EQ  ^  tn.typ :
                if 0 < len(name) :
                    node.add_attr(name, None)
                self.pushback(tn)
                return 

            # read value
            tn = self.read()
            if None == tn :
                break
            if not (token.TT_QUOTE_STR  &  tn.typ or token.TT_STR  &  tn.typ) :
                node.add_attr(name, None)
                self.pushback(tn)
                break
            value = None
            if 0 < len(tn.data) :
                value = tn.data

            node.add_attr(name, value)

            # read one char more to discard the quote besides attrVal
            char = self._token.read()
            if False != char and \
                ("'" == char or "\"" == char) :
                pass
            else :
                self._token.pushback()
    # end

    def parse(self) :
        isRecQuote = False
        while True :
            content = self.read_cdata(isRecQuote)
            if None != content and -1 < len(content) :
                self.content(content)
            # restore to default recQuote mode
            isRecQuote = False

            # read start tag
            tn = self.read()
            if None == tn :
                break
            # not <
            if token.TT_BRACK_START  ^  tn.typ :
                break
            tn = self.read()
            if None == tn :
                break
            # <xx find start tag ,read attrs and content if any
            if token.TT_STR  &  tn.typ :
                ele = tn.data
                # <SP, < a not allowed
                if 1 > len(ele) or " " == ele[0] :
                    break
                tag = Tag(ele)

                # read atrrs
                self._read_attrs(tag)

                tn = self.read()
                if None == tn :
                    break
                # > 
                if token.TT_BRACK_END  &  tn.typ :
                    self.start_tag(tag)
                    if "script" == ele.lower() :
                        isRecQuote = True
                    continue
                # />
                elif token.TT_SLASH  &  tn.typ :
                    tn = self.read()
                    if None == tn :
                        break
                    if token.TT_BRACK_END  ^  tn.typ :
                        break
                    self.start_tag(tag)
                    self.end_tag(tag.name)
                    continue
            # </ end tag
            elif token.TT_SLASH  &  tn.typ :
                # tag name
                tn = self.read()
                if None == tn :
                    break
                if token.TT_STR  ^  tn.typ :
                    break
                tname = tn.data

                # tag end
                tn = self.read()
                if None == tn :
                    break
                if token.TT_BRACK_END  ^  tn.typ :
                    break
                # callback end tag found
                self.end_tag(tname)
                continue
            elif token.TT_COMMENT  &  tn.typ :
                tag = Tag(tn.data)

                self.start_tag(tag)

                content = self._token.next_until("-->")
                if None != content : 
                    self.content(content.strip())

                self.end_tag(tag.name)
                continue
            elif token.TT_XML  &  tn.typ :
                tag = Tag(tn.data)
                self.start_tag(tag)

                c = self._token.next_until("?>")
                if None != c :
                    self.content(c.strip())

                self.end_tag(tag.name)
                continue
            elif token.TT_DOC  &  tn.typ :
                tag = Tag(tn.data)
                self.start_tag(tag)

                c = self._token.next_until(">")
                if None != c :
                    self.content(c.strip())

                self.end_tag(tag.name)
                continue
            # other case break
            break

if __name__ == "__main__" :
    import unittest

    class CMarl (MarkLangParser) :

        def __init__(self, doc) :
            MarkLangParser.__init__(self, doc)
            self.tags = []

        def start_tag(self, tag) :
            if None != tag : 
                self.tags.append(tag)

        end_tag = content = start_tag

    class MarkLangParserTest(unittest.TestCase) :

        def test_correct_doc_parse(self) :
            doc = """
            <html> 
                <body name="1" c=   a>\\"\\'a"dfdf"<= <ddfsd
                        <c />
                </body>
            </html>
            """.decode("utf8")
            mlp = CMarl(doc)
            mlp.parse()

            tags = mlp.tags
            self.assertTrue(7 == len(tags), "tags len error %d" % (len(tags)))
            root = tags[0]
            self.assertTrue("html" == root.name, "tag name")

            #body check
            body = tags[1]
            self.assertTrue("body" == body.name)
            self.assertTrue("1" == body.attrs("name"))
            self.assertTrue("a" == body.attrs("c"))
            # body content
            content = tags[2]
            self.assertTrue("\\\"\\'a\"dfdf\"<= <ddfsd" == content, content)

            #c check
            c = tags[3]
            self.assertTrue("c" == c.name)

        def test_doc_lack_end_tag(self) :
            doc = u"""
            <!doctype a b c >
            <!-- abdcdc -->
            <html> 
                <body>
                    <c id="abc">
            <!-- abd
cdc -->
                    </c      >
                    </d      >
                </body>
            </html>
            """
            mlp = CMarl(doc)
            mlp.parse()

            tags = mlp.tags
            self.assertTrue(16 == len(tags), "tags len error %d" % (len(tags)))

            # doctype
            self.assertTrue(tags[1] == "a b c", "%s %d" %(tags[1], len(tags[1])))

            self.assertTrue(tags[4] == "abdcdc")

            html = tags[6]
            self.assertTrue(html.name == "html")

            unclosedTagC = tags[12]
            self.assertTrue(unclosedTagC == "c")

        def test_correct_sina(self) :
            html = None
            with open(os.path.dirname(__file__) + "/../test/sina.html", "r") as f :
                html = "".join(f.readlines())
            html = html.decode("utf8")
            mlp = CMarl(html)
            mlp.parse()

            tags = mlp.tags
            c30expected = r"""STK && STK.pageletM && STK.pageletM.view({"pid":"pl_guide_tips","js":["home\/js\/pl\/guide\/tips.js?version=1e3ddb9956e31d8a"],"css":[],"html":"<!--\u9996\u9875\u4e2d\u95f4tips\u63a8\u8350\u4f4d-->\r\n<div class=\"tips_wrapper\" >\r\n\t\t<div class=\"tips_type\">\r\n\t\t\t<div class=\"con\">\u627e\u4eba<\/div>\r\n\t\t<\/div>\r\n\t\t<div class=\"tips_player\">\r\n\t\t\t<a href=\"javascript:void(0);\" class=\"close\" href=\"javascript:void(0);\" onclick=\"STK.core.util.cookie.set('tips_'+$CONFIG['uid'],'1');STK.E('pl_guide_tips').style.display='none'\">x<\/a>\r\n\t\t\t<a href=\"javascript:void(0);\">\r\n<a href=\"http:\/\/weibo.com\/find\/f?from=tips\">\r\n\t\t\t\r\n\t\t\t<img src=\"http:\/\/www.sinaimg.cn\/blog\/miniblog\/khd2.png\" ><\/a>\r\n\t\t<\/div>\r\n\t<\/div>\r\n\t\r\n<!--\/\u9996\u9875\u4e2d\u95f4tips\u63a8\u8350\u4f4d-->\r\n"})""".decode("utf8")
            content = tags[len(tags) - 12]
            self.assertTrue(c30expected == content, content)

        def test_doc_content_urly(self) :
            doc = """
            <html> 
                content
                <body>
                    content
                </body>
                content
                <b/>
                content
            </html>
            """.decode("utf8")
            mlp = CMarl(doc)
            mlp.parse()
            
            tags = mlp.tags
            self.assertTrue(10 == len(tags), "tags len error %d" % (len(tags)))

        def test_discard_unuse_quote_besides_attrs_value(self) :
            doc = """
            <html name="@"' test='1'" > 
                <body name="1"">
                </body>
            </html>
            """.decode("utf8")
            mlp = CMarl(doc)
            mlp.parse()

            tags = mlp.tags
            self.assertTrue(4 == len(tags), "tags len error %d" % (len(tags)))

    unittest.main()
