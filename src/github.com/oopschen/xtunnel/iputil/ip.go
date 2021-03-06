package iputil

import (
	"github.com/oopschen/xtunnel/sys"
	"io/ioutil"
	"net"
	"net/http"
	"net/url"
	"regexp"
	"time"
)

const (
	// 3 seconds
	DIAL_TIMEOUT_NANOSEC = 5 * time.Second
	TEST_WEBSITE_FOR_IP  = "http://www.ip.cn"
)

var (
	transport = &http.Transport{
		DisableKeepAlives:  true,
		DisableCompression: false,
	}

	ipRegex *regexp.Regexp
)

func init() {
	ipRegex = regexp.MustCompile(`(?i)([0-9.]+)`)

}

/**
* <p>get local address</p>
* @return ip address of current network(globally) and the real ip address of current network(behind a nat)
 */
func GetLocalAddress() (ipv4, localIpv4 string) {
	/*
		get http://ip-lookup.net/
		parse ip address
	*/
	req, err := http.NewRequest("GET", TEST_WEBSITE_FOR_IP, nil)
	if nil != err {
		sys.Logger.Printf("init request %s: %s\n", TEST_WEBSITE_FOR_IP, err)
		return

	}

	req.Header.Add("User-Agent", "curl/7.43.0")
	req.Header.Add("Accept", "*/*")

	client := &http.Client{
		Timeout:   DIAL_TIMEOUT_NANOSEC,
		Transport: transport,
	}

	resp, err := client.Do(req)
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

	// parse ip
	matches := ipRegex.FindStringSubmatch(string(body))
	if nil != matches {
		ipv4 = matches[1]
	}

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

	host, _, err := net.SplitHostPort(conn.LocalAddr().String())
	if nil != err {
		sys.Logger.Printf("get ip %s\n", err)
		return ""
	}

	return host
}
