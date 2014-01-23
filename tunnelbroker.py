#!/usr/bin/env python
# -*- coding: utf-8 -*-

from spiderx.httpclient.ipshardclient import IPShardDelayClient
from spiderx.xml.sax.htmlparser import HTMLParser
from spiderx.core.ilog import get
import re
import socket

logger = get(__file__)

class Meta :
    
    def __init__(self) :
        self.sip6 = sip4 = None
        self.cip6 = cip4 = None
        self.routepre = None

TIDPattern = re.compile("tid=([0-9]+)", re.S)
IPV4ADDRPATTERN = re.compile("[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}", re.S)
WIN7_CLIENTIP6 = re.compile("netsh\s+interface\s+ipv6\s+add\s+address\s+IP6Tunnel\s+([:0-9a-zA-Z]+)", re.S)
WIN7_SERVERIP6 = re.compile("netsh\s+interface\s+ipv6\s+add\s+route\s+([^\s]+)\s+IP6Tunnel\s+([:0-9a-zA-Z]+)", re.S)
"""
login tunnelbroker.net
get 2 paires ip to use
"""
class Broker :

    def __init__(self) :
        self._client = IPShardDelayClient(delayMS=30, timeout=30, isEnCK=True)
        self._bip = self._lip = None

    def login(self, username, pwd) :
        # login index
        logger.info("index page......")
        prelogin = self._client.open(self.getHEURL())

        if None == prelogin or 200 != prelogin.status : 
            logger.error("index: %s", prelogin.msg)
            return False

        logger.info("logining......")
        login = self._client.open(self.getHEURL("login.php"), headers={
            "Referer" : "http://tunnelbroker.net/"
            }, data = {
                "f_user":username,
                "f_pass":pwd,
                "redir":"",
                "Login":"Login"
        })

        if None == login :
            logger.error("login: null")
            return False
        if 302 != login.status : 
            logger.error("login: %s", login.msg)
            return False
        logger.info("login: %s", username)
        return True

    def destroy_exists(self) :
        pass

    """
    return Meta ins
    """
    def create(self) :
        if not self.get_bestip_localip() :
            return False

        bestip = self._bip
        localIP = self._lip
        # create process
        logger.info("Go to New Tunnel(local ip = %s, best ip = %s)......", localIP, bestip)
        newPage = self._client.open(self.getHEURL("new_tunnel.php"), headers = {
            "Origin":"http://tunnelbroker.net",
            "Referer":self.getHEURL("new_tunnel.php")
            },
                data = "ipv4z=%s&tserv=%s&normaltunnel=Create+Tunnel" % (localIP, bestip)
        )
        if None == newPage or 302 != newPage.status :
            if None == newPage :
                logger.error("new page: None")
            else :
                logger.error("new page: %d %s", newPage.status, newPage.msg)
            return False
        return True

    def get_tunnel_meta(self, tid) :
        # get win7 command
        logger.info("Fetch win7 cmd json......")
        cmdsJson = self._client.open(self.getHEURL("tunnel_detail.php?tid=%s&ajax=true") % (tid), data={"config": "10"});
        if None == cmdsJson or 200 != cmdsJson.status or None == cmdsJson.msg :
            logger.error("cmd page: %d", cmdsJson.status)
            return False

        return self.parse_cmd(cmdsJson.msg)

    def parse_cmd(self, html) :
        meta = Meta()
        # server ip 6 and route prefix
        m = WIN7_SERVERIP6.search(html)
        if None == m or 2 > len(m.groups()):
            logger.error("parse server ip6: %s", html)
            return False
        meta.routepre = m.group(1).strip().replace("\\", "")
        meta.sip6 = m.group(2).strip()

        # server ip 4
        ipv4all = IPV4ADDRPATTERN.findall(html)
        if None == ipv4all or 2 > len(ipv4all):
            logger.error("parse server ip4: %s", html)
            return False
        meta.cip4 = ipv4all[0]
        meta.sip4 = ipv4all[1]

        # client ip 6
        m = WIN7_CLIENTIP6.search(html)
        if None == m or 1 > len(m.groups()):
            logger.error("parse client ip6: %s", html)
            return False
        meta.cip6 = m.group(1).strip()
        return meta

    def get_localnet_ip(self) :
        # client ip 4
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("www.tunnelbroker.net",80))
        cip4 = s.getsockname()[0]
        s.close()
        return cip4

    def delete(self, tid) :
        deletePage = self._client.open(self.getHEURL("tunnel_detail.php?tid=%s&delete=true") % (tid))
        if None == deletePage or 200 != deletePage.status :
            logger.error("deleting %s", tid)
            return False
        return True

    def delete_all(self) :
        tids = self.get_all_tunnel_ids()
        if None == tids or 1 > len(tids) :
            logger.info("no tunnel to delete")
            return True
        for tid in tids :
            if not self.delete(tid) :
                logger.error("deleting tid: %s", tid)
                return False
        #end
        logger.info("deleted all: %s", str(tids))
        return True

    def get_all_tunnel_ids(self) :
        logger.info("get all tunnel ids......")
        indexPage = self._client.open(self.getHEURL())
        if None == indexPage or None == indexPage.msg :
            logger.error("delete index %d %s", indexPage.status, indexPage.msg)
            return None
        return TIDPattern.findall(indexPage.msg)

    def get_bestip_localip(self) :
        if None != self._bip :
            return True
        # create tunel get best location ip
        logger.info("BestLocation......")
        blpage = self._client.open("http://anycast.tunnelbroker.net/info.html?r=1")
        if None == blpage or 200 != blpage.status or None == blpage.msg :
            logger.error("get best location: %s", blpage.msg)
            return False

        # re retrieve best IP
        mt = IPV4ADDRPATTERN.search(blpage.msg)
        if None == mt : 
            logger.error("url re match: %s", blpage.msg)
            return False
        locTuple = mt.span()
        self._bip = blpage.msg[locTuple[0] : locTuple[1]]

        # parse local ip
        page = self._client.open("http://ip38.com")
        if None == page or 200 != page.status or None == page.msg :
            logger.error("get localip page : %s", page.msg)
            self._bip = None
            return False
        m = IPV4ADDRPATTERN.search(page.msg)
        if None == m :
            logger.error("local ip 404: %s", page.msg)
            self._bip = None
            return False
        locTuple = m.span()
        self._lip = page.msg[locTuple[0]: locTuple[1]]

        logger.info("BestLocation Fetch Done: server(%s), local(%s)", self._bip, self._lip)
        return True

    def modify_local_ip(self, tid, newip) :
        # create tunel get best location ip
        logger.info("modify local ip......")
        blpage = self._client.open(self.getHEURL("tunnel_detail.php?tid=%s&ajax=true")%(tid), data={"ipv4z":newip})
        if None == blpage or 200 != blpage.status :
            logger.error("modify local ip: %d", blpage.status)
            return False

        if None == blpage.msg or 0 == len(blpage.msg) :
            return True

        logger.error("modify local ip fail: '%s'", blpage.msg)
        return False

    def get_matched_tunnel(self) :
        tids = self.get_all_tunnel_ids()
        if None == tids or 1 > len(tids) :
            logger.error("all tunnel id fetch ......")
            return False

        if not self.get_bestip_localip() :
            return False
        bestip = self._bip
        localip = self._lip

        # 4
        for tid in tids :
            meta = self.get_tunnel_meta(tid)
            if False == meta :
                logger.error("tunnel meta %s", tid)
                continue
            if meta.sip4 == bestip :
                logger.info("matched (%s,%s) found", bestip, localip)
                return meta, tid, localip
        # end
        logger.info("no matched (%s,%s) found", bestip, localip)
        return False

    """
    1. have any tunnel 
    2. get the best ip
    3. get the local ip
    4. do have then : loop get the matchted best ip tunnel id else create return
    5. set the locol ip
    6. get cmd and execute
    """
    def nonexist_tunnel_create_or_set(self) :
        # 1
        metaPairs = self.get_matched_tunnel()
        meta = tid = localip = None
        if False == metaPairs :
            try :
                self.create()
            except :
                pass
            metaPairs = self.get_matched_tunnel()
            if False == metaPairs :
                return False

        meta = metaPairs[0]
        tid = metaPairs[1]
        localip = metaPairs[2]

        if localip != meta.cip4 :
            # 5 
            logger.info("modify local ip from %s to %s", meta.cip4, localip)
            if not self.modify_local_ip(tid, localip) :
                return False
        else :
            # tunnel exist
            logger.info("tunnel exist(%s,%s) found", meta.sip4, meta.cip4) 

        # 6
        meta.cip4 = self.get_localnet_ip()
        return meta

    def getHEURL(self, path = "") :
        return "https://tunnelbroker.net/" + path


if __name__ == "__main__" :
    html = """
    {"commands":"netsh interface teredo set state disabled\r\nnetsh interface ipv6 add v6v4tunnel IP6Tunnel 115.221.184.71 66.220.18.42\r\nnetsh interface ipv6 add address IP6Tunnel 2001:470:c:ba4::2\r\nnetsh interface ipv6 add route ::\/0 IP6Tunnel 2001:470:c:ba4::1","additionalNotes":"","description":"Copy and paste the following commands into a command window:"}
    """
    b = Broker()
    m = b.parse_cmd(html)
    print m.cip4, m.cip6, m.sip4, m.sip6, m.routepre
