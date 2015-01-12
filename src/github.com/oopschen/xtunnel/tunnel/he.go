package tunnel

import (
	// "fmt"
	"github.com/oopschen/xtunnel/iputil"
	"github.com/oopschen/xtunnel/sys"
	"io/ioutil"
	"net/http"
	"net/url"
	"regexp"
	"strings"
)

const (
	maxTunnelNum = 5
)

var (
	ipListPattern *regexp.Regexp
)

func init() {
	ipListPattern, err := regexp.Compile(`<span\s+style\s*=\s*"\s*float:\s*right;\s*color:\s*darkgray\s*"\s*>\s*([^\s<]+)\s*</span>`)

	if nil != err {
		sys.Logger.Printf("init ip list pattern for he\n")

	}
}

type HEBroker struct {
	config    sys.Config
	cookieJar http.CookieJar
	header    http.Header
	client    http.Client
}

func (broker *HEBroker) Init(cfg sys.Config) bool {
	if 1 > len(cfg.Username) || 1 > len(cfg.Userpasswd) {
		return false

	}

	broker.config = cfg

	transport := http.Transport{
		DisableKeepAlives:  false,
		DisableCompression: false,
	}

	broker.header = http.Header{}
	broker.header.Add("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8")
	broker.header.Add("Accept-Encoding", "gzip,deflate,sdch")
	broker.header.Add("User-Agent", "xtunnel 1.0")

	broker.client = http.Client{
		Timeout:   3 * 1000 * 1000 * 1000 * 1000,
		Transport: transport,
	}
	return true
}

func (broker *HEBroker) GetMeta() *sys.Meta {
	/*
	   get current ip
	   login
	   get all tunnels
	   if exists:
	     update cfg
	     parse meta
	   else:
	     visit create page
	     get meta
	*/
	curIP := iputil.GetLocalAddress()
	if 1 > len(curIP) {
		sys.Logger.Printf("get local address\n")
		return nil

	}

	// find tunnels
	if !broker.login() {
		sys.Logger.Printf("login as %s fail\n", broker.cfg.Username)
		return nil

	}

	tunnels := broker.findAllTunnels()
	// set up metas
	var meta sys.Meta
	meta.IPv4Server = broker.getBestIP()
	meta.IPv4Client = curIP

	if nil == tunnels || 1 > len(tunnels) {
		createTunnel(&meta)

	} else {
		var foundMeta *sys.Meta = nil
		for _, m := range metas {
			if meta.IPv4Server == m.IPv4Server {
				foundMeta = &m
				break
			}

		}

		if nil == foundMeta {
			if maxTunnelNum <= len(tunnels) {
				sys.Logger.printf("max tunnel number(%d) reached, please delete some tunnels at https://tunnelbroker.net", maxTunnelNum)

			} else {
				createTunnel(&meta)

			}

		} else {
			meta.ID = foundMeta.ID
			updateTunnel(&meta)

		}

	}

	return nil
}

func (broker *HEBroker) Destroy() bool {
	return true
}

// internal methods
func (broker *HEBroker) login() bool {
	var (
		loginUrl = "https://tunnelbroker.net/login.php"
		postData = htpp.Values{}
	)
	postData.Add("f_user", broker.config.Username)
	postData.Add("f_pass", broker.config.Userpasswd)
	postData.Add("Login", "Login")
	postBody := ioutil.NopCloser(strings.NewReader(postData.Encode()))

	cookieUrl, err := url.Parse(loginUrl)
	if nil != err {
		sys.Logger.Printf("parse url for %s: %s\n", loginUrl, err)
		return false

	}

	resp := doHttpFetch("POST", loginUrlurl, postBody, broker.cookieJar.Cookies(cookieUrl))
	if nil == resp {
		return false

	}

	// get cookies
	cookies = resp.Cookies()
	if nil != cookies && 0 < len(cookies) {
		broker.cookieJar.SetCookies(cookieUrl, cookies)

	}

	return true
}

func (broker *HEBroker) findAllTunnels() []sys.Meta {
	// TODO
	// url := fmt.Sprintf("https://%s:%s@tunnelbroker.net/tunnelInfo.php")
	return nil
}

func (broker *HEBroker) updateTunnel(meta sys.Meta) bool {
	// TODO
	return false
}

func (broker *HEBroker) createTunnel() bool {
	// TODO
	return false
}

/**
* <p>get best meta info </p>
* <p>test by icmp</p>
* @return the ip ping the fastest
 */
func (broker *HEBroker) getBestIP() string {
	/*
		visit https://tunnelbroker.net/new_tunnel.php
		parse ips
	*/
	ipUrl := "https://tunnelbroker.net/new_tunnel.php"

	// set cookies
	cookieUrl, err := url.Parse(ipUrl)
	if nil != err {
		sys.Logger.Printf("parse url for %s: %s\n", ipUrl, err)
		return ""

	}

	// do request
	resp := doHttpFetch("GET", ipUrl, nil, broker.cookieJar.Cookies(cookieUrl))

	if nil == resp {
		return ""
	}

	defer resp.Body.Close()

	// read body
	body, err := ioutil.ReadAll(resp.Body)
	if nil != err {
		sys.Logger.Printf("read body %s\n", err)
		return ""
	}

	// parse ips
	ips := ipListPattern.FindAllStringSubmatch(string(body), -1)
	if nil == ips {
		return ""

	}

	ipSlice := make([]string, len(ips))
	for inx, ipMatches := range ips {
		ipSlice[inx] = ipMatches[1]

	}

	return iputil.GetBestIP(ipSlice)

}

func doHttpFetch(method string, url string, body io.Reader, cookies []Cookies) http.Response {
	req, err := http.NewRequest(method, url, body)
	if nil != err {
		sys.Logger.Printf("create req for %s: %s\n", url, err)
		return nil
	}

	if nil != cookies && 0 < len(cookies) {
		for _, cookie := range cookies {
			req.AddCookie(cookie)

		}

	}

	resp, err := client.Do(req)
	if nil != err {
		sys.Logger.Printf("request %s: %s\n", url, err)
		return nil
	}

	return resp
}
