package iputil

import (
	"github.com/oopschen/xtunnel/sys"
	"io/ioutil"
	"net/http"
)

const (
	DIAL_TIMEOUT_NANOSEC = 3 * 1000 * 1000 * 1000 * 1000
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
* @return ip address of current network
 */
func GetLocalAddress() (ip string) {
	/*
		get http://ip-lookup.net/
		parse ip address
	*/
	client := &http.Client{
		Timeout:   DIAL_TIMEOUT_NANOSEC,
		Transport: transport,
	}

	req, err := http.NewRequest("GET", TEST_WEBSITE_FOR_IP, nil)
	if nil != err {
		sys.Logger.Printf("create req for %s: %s\n", TEST_WEBSITE_FOR_IP, err)
		return

	}

	req.Header.Add("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8")
	req.Header.Add("Accept-Encoding", "gzip,deflate,sdch")
	req.Header.Add("User-Agent", "curl 1.0")

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

	ip = string(body)
	return
}
