#!/usr/bin/env python
# -*- coding: utf-8 -*-
if __name__ == "__main__" :
    import sys, os.path
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import cStringIO
import urllib
import socket
import gzip
import zlib

import model
import cookie
import parser
from spiderx.core import errortrace
from spiderx.core import ilog
from spiderx.core import dateutil
from spiderx.net import urlutil 

logger = ilog.get(__file__)

_DEFAULT_HEADERS = {
        "ACCEPT" : "*/*",
        "ACCEPT-LANGUAGE" : "zh_CN,en;q=0.8",
        "ACCEPT-ENCODING" : "gzip",
        "ACCEPT-CHARSET" : "utf-8",
        "USER-AGENT" : "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.97 Safari/537.11",
        }

class DomainMeta :

    def __init__(self) :
        # domain timeout and same domain fetch delay
        self.domain_time = self.time = dateutil.get_timestamp_ms()
        self.p = 0
        self.domains = None

class Req :
    def __init__(self, url) :
        self.headers = {}
        for k,v in _DEFAULT_HEADERS.iteritems() :
            self.headers[k] = v

        parseRet = urlutil.parse(url)
        self.host = parseRet[0]
        self.port = parseRet[1]
        self.schema = parseRet[2]
        self.path = parseRet[3]

        self.addr = None
        self.isProxy = False
        self.data = None

    def get_url(self) :
        port = None
        if ("https" == self.schema.lower() and 443 == self.port) or \
                ("http" == self.schema.lower() and 80 == self.port) :
            port=""
        else :
            port = ":" + str(self.port)
        return "%s://%s%s%s" % (self.schema, self.host, port, self.path)

    def is_secure(self) :
        return "https" == self.schema.lower()

class BaseClient :
    VERSION = "HTTP/1.1"
    MARK_AND = "&"
    MARK_EQ = "="
    CR = unichr(13)
    LF = unichr(10)
    SP = unichr(32)
    COLON = ":"
    GET = "GET"
    POST = "POST"

    def __init__(self, isEnCk=False) :
        self._ck = None
        if isEnCk :
            self._ck = cookie.Cookie()

    def formatPostData(self, data) :
        if None == data :
            return None
        if type(data) is not dict or 1 > len(data):
            return str(data)

        return urllib.urlencode(data)

    def req_lines(self, req, method, cookies=None) :
        httpMsg = cStringIO.StringIO()
        httpMsg.write(method)
        httpMsg.write(self.SP)
        # proxy 
        if req.isProxy :
            httpMsg.write(req.get_url())
        else :
            httpMsg.write(req.path)
        httpMsg.write(self.SP)
        httpMsg.write(self.VERSION)
        httpMsg.write(self.CR)
        httpMsg.write(self.LF)
        # end request-line

        httpMsg.write("HOST:")
        httpMsg.write(req.host)
        isSecure = req.is_secure()
        if (isSecure and 443 != req.port) or (not isSecure and 80 != req.port) :
            httpMsg.write(self.COLON)
            httpMsg.write(str(req.port))
        httpMsg.write(self.CR)
        httpMsg.write(self.LF)

        # cookie header
        if None != self._ck :
            ck = self.cookie_line(req, cookies)
            if None != ck :
                httpMsg.write("Cookie")
                httpMsg.write(self.COLON)
                httpMsg.write(ck)
                httpMsg.write(self.CR)
                httpMsg.write(self.LF)

        if None != req.headers :
            for key,v in req.headers.iteritems() :
                k = key.upper()
                if type(k) is not str :
                    continue
                if type(v) is list :
                    for e in v:
                        httpMsg.write(k)
                        httpMsg.write(self.COLON)
                        if type(v) is str :
                            httpMsg.write(v)
                        else :
                            httpMsg.write(str(v))
                        httpMsg.write(self.CR)
                        httpMsg.write(self.LF)
                else :
                    httpMsg.write(k)
                    httpMsg.write(self.COLON)
                    if type(v) is str :
                        httpMsg.write(v)
                    else :
                        httpMsg.write(str(v))
                    httpMsg.write(self.CR)
                    httpMsg.write(self.LF)

        # end headers

        httpMsg.write(self.CR)
        httpMsg.write(self.LF)
        s = httpMsg.getvalue()
        httpMsg.close()
        return s

    def get(self, req, cookies=None) :
        return self.req_lines(req, self.GET, cookies)

    def post(self, req, cookies=None) :
        if None == req.headers :
            req.headers = {}
        req.headers["CONTENT-TYPE"] = "application/x-www-form-urlencoded"
        return self.req_lines(req, self.POST, cookies)

    def cookie_line(self, req, cookies=None) :
        fc = [(req.host, req.path, None, req.is_secure())]
        if None != cookies :
            fc += cookies
        c = self._ck.getCookies(fc)
        if None == c or 0 == len(c):
            return None

        scookies = ""
        for k,v in c.iteritems() :
            	scookies += "%s=%s;" % (k, v)
        return scookies

    def retrieve_cookie(self, req, res) :
        if None == self._ck :
            return
        hdrs = res.header("set-cookie")
        curDate = res.header("date")
        if type(hdrs) is list :
            for val in hdrs :
                self._ck.addFromText(req.host, val, curDate)
        else :
            self._ck.addFromText(req.host, hdrs, curDate)

    def uncompress_body(self, res) :
        if None == res.msg :
            return 
        # auto unzip
        v = res.header("content-encoding")
        if None == v :
            return

        ce = v.lower()
        if "gzip" == ce:
            try : 
                res.msg = gzip.GzipFile(fileobj = cStringIO.StringIO(res.msg)).read()
            except Exception as e :
                logger.error("%s ungzip %s", self.__class__, errortrace.trace_str())
        elif "deflate" == ce:
            try : 
                res.msg = zlib.decompress(cStringIO.StringIO(res.msg).getvalue())
            except Exception as e :
                logger.error("%s unzlib %s", self.__class__, errortrace.trace_str())

    def charset_decode(self, res, decodeMode=None) :
        if None == res.msg:
            return

        v = res.header("content-type")
        eqSignPos = v.find("=")
        if 0 > eqSignPos :
            return

        encoding = v[eqSignPos + 1 :].strip().lower()
        dm = "ignore"
        if None != decodeMode :
            dm = decodeMode
        res.msg = res.msg.decode(encoding, dm)


class IPShardProxyBaseClient(BaseClient) :

    """
    timeout seconds, delayMS milliseconds
    """
    def __init__(self, delayMS = 50, proxies = None, isEnCk=False) :
        BaseClient.__init__(self, isEnCk)
        self._delayMS = delayMS
        self._minDelayMS = 10
        # domain : DomainMeta
        self._domain_rec = {}

        self._proxy_list = proxies
        if None != self._proxy_list :
            self._domain_proxy_rec = {}
        self._domain_timeout_ms = 10000

    def _has_proxy(self, domain) :
        if None == self._proxy_list or 1 > len(self._proxy_list) :
            return None
        if domain not in self._domain_proxy_rec :
            self._domain_proxy_rec[domain] = DomainMeta()
            return self._proxy_list[0]

        meta = self._domain_proxy_rec[domain]
        if len(self._proxy_list) <=  meta.p :
            now = dateutil.get_timestamp_ms()
            gap = now - meta.time
            if gap < self._delayMS and self._minDelayMS < gap :
                return None
            meta.p = 0
        meta.time = dateutil.get_timestamp_ms()
        ret = self._proxy_list[meta.p]
        meta.p += 1
        return ret

    def _next_proxy_addr(self, req) :
        ip = self._has_proxy(req.host)
        if None == ip :
            return None
        addrInfos = None
        try :
            addrInfos = socket.getaddrinfo(ip[0], ip[1], socket.AF_INET, socket.SOCK_STREAM, 0)
        except Exception as e :
            logger.error("%s proxy getaddrinfo %s", self.__class__, errortrace.trace_str())
        if None == addrInfos or 1 > len(addrInfos) :
            return None
        return addrInfos[0]

    def _next_addr(self, req) :
        if req.host not in self._domain_rec :
            self._domain_rec[req.host] = DomainMeta()

        # timeout for the domain
        meta = self._domain_rec[req.host]
        addrInfos = None
        curMS = dateutil.get_timestamp_ms()
        if None != meta.domains and self._domain_timeout_ms > (curMS - meta.domain_time):
            addrInfos = meta.domains
        else :
            try :
                addrInfos = socket.getaddrinfo(req.host, req.port, socket.AF_INET, socket.SOCK_STREAM, 0)
                if None == meta.domains :
                    meta.domains = addrInfos
                else :
                    for addr in addrInfos :
                        if addr not in meta.domains :
                            meta.domains.append(addr)
                    addrInfos = meta.domains
                # update domain update time
                meta.domain_time = dateutil.get_timestamp_ms()
            except Exception as e :
                logger.error("%s addr getaddrinfo %s", self.__class__, errortrace.trace_str())

        if None == addrInfos or 1 > len(addrInfos) :
            return None

        inx = meta.p
        if inx >= len(addrInfos) :
            # round-robin time update
            gap = dateutil.get_timestamp_ms() - meta.time
            if gap < self._delayMS and self._minDelayMS < gap :
                return False, float(gap)/10**3, addrInfos[0]
            meta.p = inx = 0
        else :
            meta.p += 1
        meta.time = dateutil.get_timestamp_ms()
        return True, addrInfos[inx]

    """
    1. parse status line
    2. parse headers
    3. if has content-length read length else read until no data
    """
    def _parse_res(self, req, sock, retry = 1, decodeMode=None):
        res = parser.Parse(retry, sock).parse()
        if None == res :
            return None
        self.retrieve_cookie(req, res)
        self.uncompress_body(res)
        self.charset_decode(res, decodeMode)
        return res


if __name__ == "__main__" :
    import unittest
    import urllib

    class BaseClientTest(unittest.TestCase) :

        def test_format_post_data(self) :
            b = BaseClient()
            self.assertTrue(None == b.formatPostData(None))
            self.assertTrue("1"== b.formatPostData(1))

            data = {"你" : "你", "b" :1}
            expected = urllib.urlencode(data) 
            actual = b.formatPostData(data)
            self.assertTrue(expected == actual, actual)

        def test_get(self) :
            req = Req("http://www.baidu.com")
            actual = BaseClient().get(req)
            expected = "GET / HTTP/1.1\r\nHOST:www.baidu.com\r\nACCEPT-CHARSET:utf-8\r\nACCEPT-LANGUAGE:zh_CN,en;q=0.8\r\nACCEPT-ENCODING:gzip\r\nACCEPT:*/*\r\nUSER-AGENT:Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.97 Safari/537.11\r\n\r\n"
            self.assertTrue(expected == actual, actual)

            req = Req("http://www.baidu.com")
            req.headers = {
                    "a" : 1,
                    "B" : 2
                    }
            actual = BaseClient().get(req)
            expected = "GET / HTTP/1.1\r\nHOST:www.baidu.com\r\nA:1\r\nB:2\r\n\r\n"
            self.assertTrue(expected == actual, actual)

        def test_post(self) :
            req = Req("http://www.baidu.com")
            actual = BaseClient().post(req)
            expected = "POST / HTTP/1.1\r\nHOST:www.baidu.com\r\nACCEPT-LANGUAGE:zh_CN,en;q=0.8\r\nACCEPT-ENCODING:gzip\r\nACCEPT:*/*\r\nUSER-AGENT:Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.97 Safari/537.11\r\nACCEPT-CHARSET:utf-8\r\nCONTENT-TYPE:application/x-www-form-urlencoded\r\n\r\n"
            self.assertTrue(expected == actual, actual)

        def test_https(self) :
            req = Req("https://www.baidu.com")
            actual = BaseClient().post(req)
            expected = "POST / HTTP/1.1\r\nHOST:www.baidu.com\r\nACCEPT-LANGUAGE:zh_CN,en;q=0.8\r\nACCEPT-ENCODING:gzip\r\nACCEPT:*/*\r\nUSER-AGENT:Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.97 Safari/537.11\r\nACCEPT-CHARSET:utf-8\r\nCONTENT-TYPE:application/x-www-form-urlencoded\r\n\r\n"
            self.assertTrue(expected == actual, actual)

        def test_charset_decode(self) :
            import model
            res = model.HTTPResponse()
            res.add_header("content-type", "text/html;charset=gbk")
            res.msg = "helo悄虚你阿华哦得到的打算看风景阿里卡感觉阿哥"

            client = BaseClient()
            client.charset_decode(res)
            self.assertTrue(None != res.msg)


    class ReqTest(unittest.TestCase) :

        def test_url(self) :
            req = Req("http://www.taobao.com")
            self.assertTrue("/" == req.path, req.path)
            self.assertTrue(80 == req.port, req.port)

            req = Req("http://www.taobao.com:21211/a/bfd/s")
            self.assertTrue("/a/bfd/s" == req.path, req.path)
            self.assertTrue(21211 == req.port, req.port)

            req = Req("http://www.taobao.com/")
            self.assertTrue("/" == req.path, req.path)
            self.assertTrue(80 == req.port, req.port)
    unittest.main()
