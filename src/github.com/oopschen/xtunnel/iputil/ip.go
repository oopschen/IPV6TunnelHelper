package iputil

import (
	"github.com/oopschen/xtunnel/sys"
	"io/ioutil"
	"net"
	"net/http"
	"net/url"
	"time"
)

const (
	// 3 seconds
	DIAL_TIMEOUT_NANOSEC = 5 * time.Second
	TEST_WEBSITE_FOR_IP  = "http://ipv4.infobyip.com/ipdetector.php"
)

var (
	transport = &http.Transport{
		DisableKeepAlives:  true,
		DisableCompression: false,
	}
)

/**
* <p>get local address</p>
* @return ip address of current network(globally) and the real ip address of current network(behind a nat)
 */
func GetLocalAddress() (ipv4, localIpv4 string) {
	/*
		get http://ip-lookup.net/
		parse ip address
	*/
	client := &http.Client{
		Timeout:   DIAL_TIMEOUT_NANOSEC,
		Transport: transport,
	}

	resp, err := client.Get(TEST_WEBSITE_FOR_IP)
	if nil != err {
		sys.Logger.Printf("request %s: %s\n", TEST_WEBSITE_FOR_IP, err)
		return

	}

	defer resp.Body.Close()

	// read body
	body, err := ioutil.ReadAll(resp.Body)
	if nil != err {
		sys.Logger.Printf("read body %s\n", err)
		return
	}

	ipv4 = string(body)
	localIpv4 = getLocalAddr()
	return
}

func getLocalAddr() string {
	urlIns, err := url.Parse(TEST_WEBSITE_FOR_IP)
	if nil != err {
		sys.Logger.Printf("parse url %s\n", err)
		return ""

	}

	conn, err := net.DialTimeout("tcp", urlIns.Host+":http", DIAL_TIMEOUT_NANOSEC)
	if nil != err {
		sys.Logger.Printf("connect url %s\n", err)
		return ""

	}

	defer conn.Close()

	return conn.LocalAddr().String()
}
