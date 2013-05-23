#!/usr/bin/env python 
# -*- coding: utf-8 -*-
import urlparse
import urllib

"""
(domain, port, schema, path)
"""
def parse(url) :
    domain = path = None

    rt = urlparse.urlparse(url)
    netloc = rt.netloc.split(":")
    if 2 > len(netloc) :
        domain = rt.netloc
    else :
        domain = netloc[0]

    port = 80
    if "https" == rt.scheme.lower() :
        port = 443

    # path;parameters?query#fragment
    if None == rt.path or 1 >len(rt.path):
    	path = "/"
    else :
        path = rt.path

    # add parameters to path
    if None != rt.params and 0 < len(rt.params) :
        path +=  ";" + rt.params

    # add query to path
    if None != rt.query and 0 < len(rt.query) :
        path +=  "?" + rt.query

    # add fragment to path
    if None != rt.fragment and 0 < len(rt.fragment) :
        path +=  "#" + rt.fragment

    if None != rt.port :
        port = rt.port 

    return (domain, port, rt.scheme, path)

"""
domain1 is parent of domain2
www.a.com is not parent of www2.a.com
www.a.com is not parent of www.a.com
a.com is parent of www.a.com
.a.com is parent of www.a.com
.a.com is parent of a.com
"""
def is_parent(domain1, domain2) :
    if domain1 == domain2 or None == domain1 or None == domain2 :
        return False
    d2 = domain2
    if "." != d2[0] :
        d2 = "." + d2
    pos = d2.find(domain1)
    if -1 == pos :
    	return False
    if len(d2) == (pos + len(domain1)) :
    	return True
    return False

"""
data is map
return a=b&c=d
"""
def encode(data, isQuote = True) :
    if None == data :
    	return None
    if isQuote :
        return urllib.urlencode(data)

    s = ""
    for k,v in data.iteritems() :
    	s += "%s=%s&" % (str(k), str(val))
    return s[:len(s) - 1]

if __name__ == "__main__" :
    import unittest

    class Test (unittest.TestCase) :

        def test_parent(self) :
            self.assertTrue(is_parent("a.com", "a.a.com"))
            self.assertFalse(is_parent("b.com", "a.a.com"))
            self.assertTrue(is_parent(".a.com", "a.a.com"))

        def test_parse(self) :
            ret = parse("http://www.taobao.com")
            self.assertTrue("www.taobao.com" == ret[0])
            self.assertTrue(80 == ret[1])
            self.assertTrue("http" == ret[2])
            self.assertTrue("/" == ret[3], ret[3])

            ret = parse("https://www.taobao.com/test/ab?q=1")
            self.assertTrue("www.taobao.com" == ret[0])
            self.assertTrue(443 == ret[1], ret[1])
            self.assertTrue("https" == ret[2])
            self.assertTrue("/test/ab?q=1" == ret[3], ret[3])

            ret = parse("https://www.taobao.com/test/ab;pdf?q=1#abc")
            self.assertTrue("/test/ab;pdf?q=1#abc" == ret[3], ret[3])
    unittest.main()
