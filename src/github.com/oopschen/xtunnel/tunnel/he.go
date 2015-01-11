package he

import (
	"github.com/oopschen/xtunnel/iputil"
	"github.com/oopschen/xtunnel/sys"
	"net/http"
	"net/http/cookiejar"
	"net/url"
	"regexp"
)

const (
	maxTunnelNum  = 5
	ipListPattern = regexp.Compile(`<span\s+style\s*=\s*"\s*float:\s*right;\s*color:\s*darkgray\s*"\s*>\s*([^\s<]+)\s*</span>`)
)

type HEBroker struct {
	config    sys.Config
	cookieJar http.CookieJar
	header    http.Header
	client    http.Client
}

func (broker *HEBroker) Init(cfg sys.Config) bool {
	if nil == cfg || 1 > len(cfg.username) || 1 > len(cfg.userpasswd) {
		return false

	}

	broker.config = cfg

	transport := http.Transport{
		DisableKeepAlives:  false,
		DisableCompression: false,
	}

	broker.Header = http.Header
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
		sys.Logger.Printf("login as %s fail\n", broker.cfg.username)
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
	// TODO
}

func (broker *HEBroker) findAllTunnels() []sys.Meta {
	// TODO
}

func (broker *HEBroker) updateTunnel(meta sys.Meta) bool {
	// TODO
}

func (broker *HEBroker) createTunnel() bool {
	// TODO
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
	url := "https://tunnelbroker.net/new_tunnel.php"
	req, err := http.NewRequest("GET", url, nil)
	if nil != err {
		sys.Logger.Printf("create req for %s: %s\n", url, err)
		return ""
	}

	// set cookies
	cookieUrl, err := url.Parse(url)
	if nil != err {
		sys.Logger.Printf("parse url for %s: %s\n", url, err)
		return ""

	}

	cookies := broker.cookieJar.Cookies(cookieUrl)
	if nil != cookies && 0 < len(cookies) {
		for _, cookie := range cookies {
			req.AddCookie(cookie)

		}

	}

	resp, err := client.Do(req)
	if nil != err {
		sys.Logger.Printf("request %s: %s\n", url, err)
		return ""
	}

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
