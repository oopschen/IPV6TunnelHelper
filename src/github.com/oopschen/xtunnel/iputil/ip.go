package iputil

import (
	"github.com/oopschen/xtunnel/sys"
	"io/ioutil"
	"net/http"
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

	ip = string(body)
	return
}
