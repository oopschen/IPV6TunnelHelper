#!/usr/bin/env python
# -*- coding: utf-8 -*-
if __name__ == "__main__" :
    import sys, os.path
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import model
import socket
import errno
from spiderx.core import errortrace
from spiderx.core import ilog

logger = ilog.get(__file__)

def _IS_HEX(byte) :
    return byte in "0123456789abcdefABCDEF"

class Parse :

    def __init__(self, retry, sock) :
        if retry > 0 :
            self._retry = retry
        else :
            self._retry = 1
        self._sock = sock
        self._buf = ""

    """
    read nBytes data from sock
    """
    def _read_retry(self, sock, nBytes = 4096) :
        r = 0
        while r < self._retry :
            try :
                buf = sock.recv(nBytes)
                if 0 < len(buf):
                    self._buf += buf
                    return True
            except socket.error as e :
                global logger
                logger.error(errortrace.trace_str())
            # end 
            r += 1
        # end 
        return False

    """
    read total nBytes data from sock
    the size must be fullfill
    """
    def _read_all(self, sock, nBytes = 4096) :
        ret = ""
        left = nBytes

        while 0 < left :
            buf = self._read(sock, left)
            if False == buf :
                break
            left -= len(buf)
            ret += buf
        # end while

        if 0 == left :
            return ret
        if None != ret :
            self._buf = ret + self._buf
        return False

    def _read(self, sock, nBytes) :
        if nBytes > len(self._buf) :
            # try read some
            self._read_retry(sock)
            if 1 > len(self._buf) :
                return False

        # read as many as buf can
        size = nBytes
        s = len(self._buf)
        if nBytes > s :
            size = s
        buf = self._buf[0: size]
        self._buf = self._buf[size:]
        return buf

    """
    read until the byte found
    return None: read the byte but none string before it
    return False read until eof
    """
    def _read_until(self, sock, byte) :
        a = ""
        while True :
            buf = self._read(sock, 1)
            if False == buf :
                return False
            if byte == buf[0] :
                break
            a += buf
        # end while
        if 1 > len(a) :
            return None
        return a

    def _read_chunk(self, sock) :
        chunkSizeBuf = ""
        readed = None
        while True :
            buf = self._read_all(sock, 1)
            if False == buf :
                return None
            if not _IS_HEX(buf) :
                readed = buf
                break
            chunkSizeBuf += buf[0]

        if None == chunkSizeBuf :
            return None
        chunkSize = int(chunkSizeBuf, 16)
        # if crlf
        if "\r" == readed :
            buf = self._read_all(sock, 1)
            if False == buf or "\n" == buf :
                return chunkSize
        # read ext if any
        while True :
            buf = self._read_all(sock, 1)
            if False == buf :
                return chunkSize
            if "\r" == buf :
                buf1 = self._read_all(sock, 1)
                if False == buf1 or "\n" == buf1 :
                    return chunkSize

    def parse(self) :
        res = model.HTTPResponse()
        if not self.parse_status_line(self._sock, res) :
            return None
        if not self.parse_headers(self._sock, res) :
            return None

        if not self.parse_transfer_encoding(self._sock, res) :
            self.parse_msgbody(self._sock, res)

        return res


    def parse_status_line(self, sock, res) :
        # parse status line
        buf = self._read_all(self._sock, 6)
        if False == buf :
            return False
        # HTTP/1
        if "http/1" != buf.lower() :
            return False
        # 1*digits
        ret = self._read_until(sock, ".")
        if False == ret :
            return False
        if None == ret :
            res.vmaj = "1"
        else :
            res.vmaj = ret.strip()

        # 1 cannot found
        buf = self._read_all(self._sock, 1)
        if False == buf :
            return False
        if "1" != buf :
            return False

        # *digit
        ret = self._read_until(sock, " ")
        if False == ret :
            return False
        if None == ret :
            res.vmin = "1"
        else :
            res.vmin = ret.strip()

        # status(3) sp
        buf = self._read_all(sock, 4)
        if False == buf :
            return False
        # status
        res.status = int(buf[0:3])
        if " " != buf[3] :
            return False

        # reason
        buf = self._read_until(sock, "\r")
        if False == buf :
            return False
        res.reason = buf

        buf = self._read_all(sock, 1)
        if False == buf :
            return False
        if "\n" == buf :
            return True
        return False

    def parse_headers(self, sock, res) :
        while True :
            #test crlf
            p = self._read_all(sock, 2)
            if False == p :
                return False
            if "\r\n" == p :
                return res

            # read field name until :
            buf = self._read_until(sock, ":")
            if False == buf :
                return False
            key = p + buf

            buf = self._read_until(sock, "\r")
            if False == buf :
                return False
            val = buf

            p = self._read_all(sock, 1)
            if False == p :
                return False
            if "\n" == p :
                res.add_header(key, val)
            else :
                return False

    def parse_msgbody(self, sock, res) :
        length = res.header("content-length")
        if None == length:
            return False
        il = int(length.strip())
        if 1 > il :
            return False
        buf = self._read_all(sock, il)
        if False == buf :
            return False
        res.msg = buf
        return True

    def parse_transfer_encoding(self, sock, res) :
        encoding = res.header("transfer-encoding")
        if None == encoding or encoding.strip().lower() != "chunked":
            return False
        buf = ""
        isEOF = False
        # read chunk
        while True :
            chunkSize = self._read_chunk(sock)
            # end of sock or last-chunk
            if None == chunkSize or 0 == chunkSize:
                # skip CRLF
                _last = self._read_all(sock, 2)
                if "\r\n" == _last :
                    isEOF = True
                else :
                    # push back
                    self.pushback(_last)
                break
            b = self._read_all(sock, chunkSize)
            if False == b :
                return False
            buf += b
            # skip CRLF
            self._read_all(sock, 2)
        # end 
        res.msg = buf
        # read trailer
        if not isEOF :
            self.parse_headers(sock, res)
        return True

    def pushback(self, buf) :
        self._buf = buf + self._buf
