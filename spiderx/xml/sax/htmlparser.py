#!/usr/bin/env python
# -*- coding: utf-8 -*-
if __name__ == "__main__" :
    import sys, os.path
    sys.path.append(os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "..")
    ))

from spiderx.xml import xpathcmd
from spiderx.xml.sax.marklang import MarkLangParser

"""
usage :
    p = HTMLParser(doc)
    p.search("html body div@id=1")
"""
class HTMLParser(MarkLangParser) :

    def __init__(self, doc) :
        MarkLangParser.__init__(self, doc)
        self._targets = None
        self._currentList = None

    def search(self, cmdline) :
        if None == cmdline or 1 > len(cmdline) :
            return False
        self._cmds = xpathcmd.parse_cmd(cmdline)
        if None == self._cmds :
            return False
        self.reload()
        self._targets = None
        # do parse job
        self.parse()
        self._clean_up()
        return self._targets

    def _clean_up(self) :
        if None != self._currentList :
            del self._currentList[0:]
            self._currentList = None
        self._cmds = None

    def _add_to_target(self, target) :
        if None == self._targets :
            self._targets = []
        self._targets.append(target)

    def start_tag(self, tag) :
        if None == self._currentList :
            self._currentList = []
        self._currentList.append(tag)

    def content(self, content) :
        if None == content or None == self._currentList :
            return

        cl = len(self._currentList) - 1
        tag = self._currentList[cl]
        if None == tag.content :
            tag.content = content
            return
        tag.content += content

    def end_tag(self, tagname) :
        if None == self._currentList :
            return

        cl = len(self._currentList) - 1
        tag = self._currentList[cl]
        # ingore end tag without correspoding start tag
        if tag.name != tagname :
            return

        if self._compare_tag() :
            self._add_to_target(tag)
        del self._currentList[cl]

    def _compare_tag(self) :
        # compare last cmd and tag
        tagInx = len(self._currentList) - 1
        lastTag = self._currentList[tagInx]
        cmdInx = len(self._cmds) - 1
        cmdEle = self._cmds[cmdInx]
        if not cmdEle.eq(lastTag.name, lastTag.attrs()) :
            return False

        mode = cmdEle.mode
        while True:
            # has more cmd
            cmdInx -= 1
            if 0 > cmdInx :
                break
            cmdEle = self._cmds[cmdInx]

            # has more tag
            tagInx -= 1
            if 0 > tagInx :
                return False
            curTag = self._currentList[tagInx]
            if cmdEle.eq(curTag.name, curTag.attrs()) :
                mode = cmdEle.mode
                continue

            # elements eq but mode do not eq return false
            if xpathcmd.MODE_SEARCH_DIRECT_CHILDS & mode :
                return False
            else :
                # not direct cmd go to previous tag
                tagInx -= 1
                isFound = False
                while -1 < tagInx :
                    curTag = self._currentList[tagInx]
                    if not cmdEle.eq(curTag.name, curTag.attrs()) :
                        tagInx -= 1
                        continue
                    isFound = True
                    break
                # end while 
                if isFound :
                    mode = cmdEle.mode
                    continue
                return False
        # end while
        return True

if __name__ == "__main__" :
    import unittest
    import os.path
    html = None
    with open(os.path.dirname(__file__) + "/../test/sina.html", "r") as f :
        html = "".join(f.readlines())
    html = html.decode("utf8")

    class HTMLTest(unittest.TestCase) :

        def test_read_correct(self) : 
            global html
            parser = HTMLParser(html)
            divNodes = parser.search("html > body > div@class = W_miniblog")
            self.assertTrue(None != divNodes, "None found")
            self.assertTrue(1 == len(divNodes), "len error")
            self.assertTrue(divNodes[0].name == "div")
            self.assertTrue(divNodes[0].attrs("class") == "W_miniblog")
            self.assertTrue(None == divNodes[0].content, divNodes[0].content)
            
            divNodes = parser.search("html div@class = W_miniblog_fb div@id=pl_content_top")
            self.assertTrue(None != divNodes, str(divNodes))
            self.assertTrue(1 == len(divNodes), divNodes)
            self.assertTrue(None  == divNodes[0].content, divNodes[0].content)

            divNodes = parser.search("html div@class = W_miniblog_fb div@id=pl_content_top")

        def test_auto_close_tag(self) : 
            doc = u"""
            <html>
                <head>
                <meta />
                <meta>
                <body>
                <div id=1>
                </body>
            </html>
            """
            parser = HTMLParser(doc)
            divNodes = parser.search("html > body > div@id=1")
            self.assertTrue(None == divNodes ,divNodes)

        def test_doc(self) :
            doc = u"""
            <html>
                <body>
                    <form>
                        <div>
                            <input type="hidden" />
                        </div>
                        <input type="hidden" />
                        <div>
                            <div><input type="hidden" /></div>
                        </div>
                    </form>
                </body>
            </html>
            """
            parser = HTMLParser(doc)
            divNodes = parser.search("html > body form input")
            self.assertTrue(None != divNodes, "None found")
            self.assertTrue(3 == len(divNodes), len(divNodes))

            divNodes = parser.search("form input")
            self.assertTrue(None != divNodes, "None found")
            self.assertTrue(3 == len(divNodes), len(divNodes))

    unittest.main()
