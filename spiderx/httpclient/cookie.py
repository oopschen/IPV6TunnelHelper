#!/usr/bin/env python
# -*- coding: utf-8 -*-
if __name__ == "__main__" :
    import sys, os.path
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import datetime
from spiderx.core import dateutil
from spiderx.net import urlutil


"""
a tool record weibo process cookie
data structure description:
{
    domain : {
        path : {
            key : [expires(datetime), value]
        }
    }
    ...
}
"""
class Cookie :
    
    date_formats = [
        "%a, %d-%b-%Y %H:%M:%S %Z",
        "%a, %d %b %Y %H:%M:%S %Z",
        "%A, %d-%b-%y %H:%M:%S %Z",
        "%A, %d-%b-%Y %H:%M:%S %Z",
        "%a, %d-%b-%y %H:%M:%S %Z"
    ]


    def __init__(self) :
        self._ck = {}

    def _format_domain(self, domain) :
        if None == domain :
            return None
        d = domain
        if "." != d[0] :
            d = "." + d
        return d

    def _getCookiesByPath(self, obj, key =None, secure = False) :
        if None == obj :
            return None;

        if None == key :
            ret = {}
            now = dateutil.get_timestamp_ms()
            for k,v in obj.iteritems() :
                # secure get all; unsecure get unsecure
                # expires
                if (secure or not v[2]) and (None == v[0] or now < v[0]):
                    ret[k] = v[1]
            return ret

        if key not in obj :
            return None

        now = dateutil.get_timestamp_ms()
        ele = obj[key]
        if (secure or not ele[2]) and (None == ele[0] or now < ele[0]):
            return {key : ele[1]}

        return None
        
    def _getCookiesByDomain(self, obj, path = None, key =None, secure = False) :
        if None == obj :
            return None;

        ret = {}
        if None == path :
            for p, pval in obj.iteritems() :
            	val = self._getCookiesByPath(pval, key, secure)
                if None == val :
                    continue
                for k,v in val.iteritems() :
                    ret[k] = v
        else :
            for p, pval in obj.iteritems() :
            	pos = path.find(p)
                if 0 != pos :
                    continue
                val = self._getCookiesByPath(pval, key, secure)
                if None != val :
                    for k,v in val.iteritems() :
                        ret[k] = v
        return ret

    def add(self, domain, path, key, val, expires, baseDate=None, secure=False) :
        d = self._format_domain(domain)
        if None == d or 1 > len(d) :
            return False

        if d not in self._ck :
            self._ck[d] = {}

        if path not in self._ck[d] :
            self._ck[d][path] = {}

        exp = None
        if None != expires :
            exp = self.__parse_date(expires)
            if None == exp :
                return False

            # if has baseDate then calculate the expire time: (expires - baseDate) + now
            if None == baseDate :
                exp = dateutil.get_timestamp_ms(exp)
            else :
                expBaseDate =  self.__parse_date(baseDate)
                if None == expBaseDate :
                    return False
                exp = dateutil.get_timestamp_ms(exp) - dateutil.get_timestamp_ms(expBaseDate) + dateutil.get_timestamp_ms()

        self._ck[d][path][key] = [exp, val, secure]

    def addFromText(self, domain=None, setIns = None, baseDate = None) :
        if None == domain or 1 > len(domain) or setIns == None or 1 > len(setIns):
            return

        path = "/"
        expires = None
        secure = False

        stripedIns = setIns.strip()
        pos = stripedIns.find(":")
        if -1 < pos and "set-cookie" == stripedIns[0:pos].lower() :
            stripedIns = stripedIns[pos+1 :]

        vals = stripedIns.strip().split(";")
        keys = {}
        for kv in vals :
            kvpair = kv.strip().split("=")
            if 2 > len(kvpair) :
                if "secure" == kv.strip().lower() :
                    secure = True
                continue
            if "domain" == kvpair[0].strip().lower() :
                domain = kvpair[1]
            elif "expires" == kvpair[0].strip().lower():
                expires = kvpair[1]
            elif "path" == kvpair[0].strip().lower() :
                path = kvpair[1]
            else :
                keys[kvpair[0]] = kvpair[1]

        for i, v in keys.iteritems() :
            self.add(domain, path, i, v, expires, baseDate, secure)

    """
        includes instructs the program to include domain cookies. [(domain, path, key, secure)...]
    """
    def getCookies(self, includes = None) :
        ret = {}
        if None == includes or 0 == len(includes) :
            return None

        for ele in includes :
            d = p = k = None
            s = False
            size = len(ele)
            # more common case
            if 2 == size :
            	d = ele[0]
            	p = ele[1]
            elif 3 == size :
            	d = ele[0]
            	p = ele[1]
            	k = ele[2]
            elif 1 == size :
            	d = ele[0]
            elif 4 == size :
            	d = ele[0]
            	p = ele[1]
                s = ele[3]
            else :
            	continue

            for domain,obj in self._ck.iteritems() :
                if None != d and domain != d and not urlutil.is_parent(domain, d) :
                    continue
                mp = self._getCookiesByDomain(obj, p, k, s)
                if None == mp :
                    continue
                for ky,v in mp.iteritems() :
                    ret[ky] = v
        if 0 == len(ret) :
            return None
        return ret

    """ delete cookie, args the same as getCookies """
    def delete(self, includes = None) :
        if None == includes :
            return False
        for ele in includes :
            d = p = k = None
            if 3 == len(ele) :
            	d = ele[0]
            	p = ele[1]
            	k = ele[2]
            elif 2 == len(ele) :
            	d = ele[0]
            	p = ele[1]
            elif 1 == len(ele) :
            	d = ele[0]
            else :
            	continue
            d = self._format_domain(d)

            if None != d and \
            	None != p and \
                None != k :
                    if d not in self._ck :
                    	continue
                    if p not in self._ck[d] :
                    	continue
                    if k not in self._ck[d][p] :
                    	continue
                    del self._ck[d][p][k]

            elif None != d and \
                None != p and \
                None == k :
                    if d not in self._ck :
                    	continue
                    if p not in self._ck[d] :
                    	continue
                    del self._ck[d][p]

            elif None != d and \
                None == p and \
                None == k :
                    if d not in self._ck :
                    	continue
                    del self._ck[d]
        return True

    def clear() :
        self._ck.clear()

    def __parse_date(self, date) :
        parsedDate = None
        for formats in Cookie.date_formats :
            try :
                parsedDate = datetime.datetime.strptime(date, formats)
                break
            except ValueError as e:
                pass

        return parsedDate


if __name__ == "__main__" :
    import unittest

    class CookieTest(unittest.TestCase) :
        def setUp(self) :
            c = self._cookie = Cookie()
            baseDate = "Fri, 06 Dec 2013 00:36:32 GMT"
            c.addFromText("domain1", setIns = "set-cookie:a=b;path=/abc;", baseDate = baseDate)
            c.addFromText("domain1", setIns = "set-cookie:o=b;path=/;", baseDate = baseDate)
            c.addFromText("domain2", setIns = "set-cookie:a=b;expires=Sat, 15-Dec-22 03:40:15 GMT;", baseDate = baseDate)
            c.addFromText("domain3", setIns = "a=b;expires=Sat, 15-Dec-22 03:40:15 GMT;", baseDate = baseDate)
            c.addFromText("domain4", setIns = "a=b;expires=Sat, 15-Dec-22 03:40:15 GMT;secure", baseDate = baseDate)
            c.addFromText("domain4", setIns = "c=b;expires=Sat, 15-Dec-22 03:40:15 GMT;httponly", baseDate = baseDate)

        def test_domain(self) :
            cookie = self._cookie.getCookies([("domain")])
            self.assertTrue(None == cookie , "cookie a in ret")

            cookie = self._cookie.getCookies([("domain1", None, None)])
            self.assertTrue(None != cookie and "a" in cookie, "cookie a not in ret")
            self.assertTrue(None != cookie and "o" in cookie, "cookie o not in ret")
            self.assertEqual(cookie["a"], "b", "cookie a not found")

            cookie = self._cookie.getCookies([("domain1", "/abc", "a")])
            self.assertTrue(None != cookie and "a" in cookie, "path cookie a not in ret")
            self.assertEqual(cookie["a"], "b", "path cookie a not found")

            cookie = self._cookie.getCookies([("a.domain1", "/abc/a", "a")])
            self.assertTrue(None != cookie and "a" in cookie, "subdomain path cookie a not in ret")
            self.assertEqual(cookie["a"], "b", "subdomain path cookie a not found")

            self._cookie.delete([("domain1", "/")])
            cookie = self._cookie.getCookies([("domain1", "/", "o")])
            self.assertTrue(None == cookie, "delete path cookie 0 not in ret")
            cookie = self._cookie.getCookies([("domain1", "/abc", "a")])
            self.assertTrue(None != cookie and "a" in cookie, "delete path cookie a not in ret")

            cookie = self._cookie.getCookies([("domain3", None, "a")])
            self.assertTrue(None != cookie and "a" in cookie, "cookie a not in ret domain3")

            cookie = self._cookie.getCookies([("domain4", None, None)])
            self.assertTrue(None != cookie and "a" not in cookie, "cookie a in ret domain4 unsecurely")
            self.assertTrue(None != cookie and "c" in cookie, "cookie c not in ret domain4")
            cookie = self._cookie.getCookies([("domain4", None, None, True)])
            self.assertTrue(None != cookie and "a" in cookie, "cookie a not in ret domain4")
            self.assertTrue(None != cookie and "c" in cookie, "cookie c not in ret domain4")
    unittest.main()
