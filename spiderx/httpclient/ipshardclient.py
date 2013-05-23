#!/usr/bin/env python
# -*- coding: utf-8 -*-
if __name__ == "__main__" :
    import sys, os.path
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import socket
import ssl
import time
import array

import baseclient
from spiderx.core import errortrace
from spiderx.core import ilog

logger = ilog.get(__file__)

"""
                round-robin select domain's ip and proxy support
"""
class IPShardDelayClient(baseclient.IPShardProxyBaseClient) :

    def __init__(self, delayMS = 50, timeout = 5, proxies = None, isEnCK=False) :
        baseclient.IPShardProxyBaseClient.__init__(self, delayMS, proxies, isEnCK)
        self._timout = timeout

    def _fetch(self, req, decodeMode=None) :
        lines = None
        if None == req.data :
            lines = self.get(req)
        else :
            lines = self.post(req) + req.data
        addr = req.addr
        sock = None
        if req.is_secure() :
            sock = ssl.wrap_socket(
                    socket.socket(addr[0], addr[1]),
                    cert_reqs=ssl.CERT_NONE
            )
        else :
            sock = socket.socket(addr[0], addr[1])

        sock.settimeout(self._timout)
        try :
            sock.connect(addr[4])
            sock.sendall(lines)
            #read all
            ret = self._parse_res(req, sock, decodeMode)
            sock.close()
            return ret
        except Exception as e:
            sock.close()
            logger.error("%s socket %s", self.__class__, errortrace.trace_str())
        return None

    def open(self, url, data = None, headers = None, decodeMode = None) :
        if None == url or 1 > len(url) :
            return None
        req = baseclient.Req(url)
        # get addr
        addr = self._next_proxy_addr(req)
        if None == addr :
            addrRet = self._next_addr(req)
            if None == addrRet :
                return None
            elif False == addrRet[0] :
                addr = addrRet[2]
                logger.info("%s %s(%s) wait %0.2fsec", self.__class__, req.host, addr, addrRet[1])
                time.sleep(addrRet[1])
            elif True == addrRet[0] :
                addr = addrRet[1]
            else :
                return None
        else :
            req.isProxy = True
        req.addr = addr
        logger.debug("%s %s-->%s", self.__class__, req.host, req.addr[4][0])
        # extra data
        if None != headers :
            for k,v in headers.iteritems() :
                req.headers[k] = v
        # req request body if any
        if None != data :
            req.data = self.formatPostData(data)
            # add content-length header
            req.headers["CONTENT-LENGTH"] = len(array.array("B", req.data))

        return self._fetch(req, decodeMode)

if __name__ == "__main__" :
    import unittest

    class Test(unittest.TestCase) :
        def test_no_cookie(self) :
            client = IPShardDelayClient(timeout=1, isEnCK = True)
            res = client.open("http://www.tudou.com")
            self.assertTrue(None != res, "tudou None")
            self.assertTrue("1" == res.vmaj, res.vmaj)
            self.assertTrue("1" == res.vmin, res.vmin)
            self.assertTrue(200 == res.status, res.status)

        def test_zcookie(self) :
            client = IPShardDelayClient(timeout=60, isEnCK = True)

            res = client.open("http://tunnelbroker.net/")
            self.assertTrue(None != res, "tunnel index None")
            self.assertTrue(200 == res.status, res.status)

            res = client.open("http://tunnelbroker.net/login.php", headers={
                "Referer" : "http://tunnelbroker.net/"
                }, data = {
                    "f_user":"testipv6acc",
                    "f_pass":"xidnDt5md",
                    "redir":"",
                    "Login":"Login"
            })
            self.assertTrue(None != res, "tunnel login None")
            self.assertTrue(302 == res.status, res.status)

            res = client.open("http://tunnelbroker.net/")
            self.assertTrue(None != res, "tunnel index after login None")
            self.assertTrue(200 == res.status, res.status)
            self.assertTrue(0 < res.msg.find("Account"), res.msg)

        def test_https(self) :
            client = IPShardDelayClient(timeout=20, isEnCK = True)
            res = client.open("https://login.taobao.com/member/login.jhtml")
            self.assertTrue(None != res, "login taobao None")
            self.assertTrue(200 == res.status, res.status)
            self.assertTrue(0 < res.msg.find("body"), res.msg)

    unittest.main()
