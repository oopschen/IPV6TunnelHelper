package tunnel

import (
	"encoding/xml"
	"fmt"
	"github.com/oopschen/xtunnel/iputil"
	"github.com/oopschen/xtunnel/sys"
	"io"
	"io/ioutil"
	"net/http"
	"net/http/cookiejar"
	"net/url"
	"regexp"
	"strings"
)

const (
	maxTunnelNum = 5
)

var (
	ipListPattern       *regexp.Regexp
	deleteTunnelPattern *regexp.Regexp
)

func init() {
	pattern, err := regexp.Compile(`(?i)<span\s+style\s*=\s*"\s*float:\s*right;\s*color:\s*darkgray\s*"\s*>\s*([^\s<]+)\s*</span>`)

	if nil != err {
		sys.Logger.Printf("init ip list pattern for he\n")

	}
	ipListPattern = pattern

	pattern, err := regexp.Compile(`(?i)tunnel\s+has\s+been\s+deleted`)

	if nil != err {
		sys.Logger.Printf("init delete tunnel pattern for he\n")

	}
	deleteTunnelPattern = pattern
}

type HEBroker struct {
	config *sys.Config
	client *http.Client
}

func (broker *HEBroker) Init(cfg *sys.Config) bool {
	if 1 > len(cfg.Username) || 1 > len(cfg.Userpasswd) {
		sys.Logger.Printf("username(%s) or userpwd(%s) must not bu nil\n", cfg.Username, cfg.Userpasswd)
		return false

	}

	broker.config = cfg

	// set up client
	var (
		transport   http.RoundTripper
		cookiJarIns http.CookieJar
	)

	transport = &http.Transport{
		DisableKeepAlives:  true,
		DisableCompression: false,
	}

	cookiJarIns, err := cookiejar.New(nil)
	if nil != err {
		sys.Logger.Printf("init cookie jar %s\n", err)
		return false
	}

	broker.client = &http.Client{
		Transport: transport,
		Jar:       cookiJarIns,
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
	sys.Logger.Printf("Get local address......\n")
	curIP := iputil.GetLocalAddress()
	if 1 > len(curIP) {
		sys.Logger.Printf("Get local address\n")
		return nil

	}
	sys.Logger.Printf("Get local address: Success\n")

	// find tunnels
	sys.Logger.Printf("Login HE Tunnel......\n")
	if !broker.login() {
		sys.Logger.Printf("Login as %s fail\n", broker.config.Username)
		return nil

	}
	sys.Logger.Printf("Login HE Tunnel: Success \n")

	var (
		tunnels         []*sys.Meta
		foundMeta, meta *sys.Meta
	)

	sys.Logger.Printf("Query HE Tunnels......\n")
	tunnels = broker.findAllTunnels()
	sys.Logger.Printf("Query HE Tunnels: Success\n")
	// set up metas
	meta = &sys.Meta{}
	meta.IPv4Server = broker.getBestIP()
	meta.IPv4Client = curIP

	if "" == meta.IPv4Server {
		sys.Logger.Printf("Get Best Server fail\n")
		return nil

	}
	sys.Logger.Printf("Choose %s for tunnel %s\n", meta.IPv4Server, meta.IPv4Client)

	// find matched tunnel
	if nil != tunnels {
		for _, m := range tunnels {
			sys.Logger.Printf("Found Tunnel: %#v\n", m)

			// if ipclient exists, delete it
			if meta.IPv4Client == m.IPv6Client {
				sys.Logger.Printf("Delete Tunnel......\n")
				if !broker.deleteTunnel(m) {
					return nil

				}

				sys.Logger.Printf("Delete Tunnel: Success\n")
			}

			if meta.IPv4Server == m.IPv4Server {
				foundMeta = m
				break
			}

		}

	} else {
		sys.Logger.Printf("No Tunnels found\n")

	}

	// create or update tunnel
	if nil == foundMeta {
		// max tunnel number reached
		if maxTunnelNum <= len(tunnels) {
			sys.Logger.Printf("max tunnel number(%d) reached, please delete some tunnels at https://tunnelbroker.net", maxTunnelNum)
			return nil

		} else if !broker.createTunnel(meta) {
			sys.Logger.Printf("Create Tunnel fail\n")
			// create tunnel
			return nil

		}

	} else if meta.ID = foundMeta.ID; !broker.updateTunnel(meta) {
		sys.Logger.Printf("Update Tunnel fail \n")
		// update
		return nil

	}

	sys.Logger.Printf("Fetch tunnel info success\n")
	return meta
}

func (broker *HEBroker) Destroy() bool {
	return true
}

// internal methods
func (broker *HEBroker) login() bool {
	var (
		loginUrl = "https://tunnelbroker.net/login.php"
		postData = url.Values{}
	)

	// post
	postData.Add("f_user", broker.config.Username)
	postData.Add("f_pass", broker.config.Userpasswd)
	postData.Add("Login", "Login")
	postData.Add("redir", "/")

	resp := broker.doHttpPost(loginUrl, postData)
	if nil == resp {
		return false

	}

	// check cookie
	cookieUrl, err := url.Parse(loginUrl)
	if nil != err {
		sys.Logger.Printf("Login fail cookie url: %s\n", err)
		return false

	}
	cookies := broker.client.Jar.Cookies(cookieUrl)
	if nil == cookies {
		sys.Logger.Printf("Login fail no cookie found\n")
		return false
	}

	foundHETB := false
	for _, c := range cookies {
		if "hetb" == strings.ToLower(c.Name) {
			foundHETB = true
			break

		}

	}

	if !foundHETB {
		sys.Logger.Printf("Login fail no cookie \"HETB\"found\n")
		return false

	}

	// check logout keyword in main page
	bodyBytes, err := ioutil.ReadAll(resp.Body)
	if nil != err {
		sys.Logger.Printf("Login redirect read body: %s, status: %s\n", err, resp.Status)
		return false

	}

	body := string(bodyBytes)

	if strings.Contains(body, "Logout") && strings.Contains(body, "Main Page") {
		return true

	}

	sys.Logger.Printf("Login redirect page do not contain keywords: status=%s, body=%s\n", resp.Status, body)
	return false
}

func (broker *HEBroker) findAllTunnels() []*sys.Meta {
	tunnelURL := fmt.Sprintf("https://%s:%s@tunnelbroker.net/tunnelInfo.php", broker.config.Username, broker.config.Userpasswd)
	resp := broker.doHttpGet(tunnelURL)
	if nil == resp {
		return nil

	}

	defer resp.Body.Close()

	return parseTunnels(resp.Body)
}

func (broker *HEBroker) updateTunnel(meta *sys.Meta) bool {
	sys.Logger.Printf("Update Tunnel: %#v\n", meta)
	/*
		update client server ip only
	*/
	updateURL := fmt.Sprintf("https://tunnelbroker.net/tunnel_detail.php?tid=%s&ajax=true", meta.ID)
	postData := url.Values{}
	postData.Add("ipv4z", meta.IPv4Client)

	resp := broker.doHttpPost(updateURL, postData)
	if nil == resp {
		return false

	}

	defer resp.Body.Close()

	// check result
	body, err := ioutil.ReadAll(resp.Body)
	if nil != err {
		sys.Logger.Printf("update tunnel read body %s\n", err)
		return false
	}

	if "" == string(body) {
		return true

	}

	sys.Logger.Printf("update tunnel fail: %s\n", string(body))
	return false
}

func (broker *HEBroker) createTunnel(meta *sys.Meta) bool {
	sys.Logger.Printf("Create Tunnel: %#v\n", meta)
	/*
		create tunnel
		parse server router info
	*/
	createUrl := "https://tunnelbroker.net/new_tunnel.php"
	postData := url.Values{}
	postData.Add("ipv4z", meta.IPv4Client)
	postData.Add("tserv", meta.IPv4Server)
	postData.Add("normaltunnel", "Create Tunnel")

	resp := broker.doHttpPost(createUrl, postData)
	if nil == resp {
		return false

	}

	// TODO check resp

	defer resp.Body.Close()

	// parse tunnel
	metas := broker.findAllTunnels()
	if nil == metas {
		sys.Logger.Printf("Create tunnel: empty tunnels\n")
		return false

	}

	for _, m := range metas {
		if m.IPv4Server == meta.IPv4Server {
			meta.ID = m.ID
			meta.IPv6Client = m.IPv6Client
			meta.IPv6Server = m.IPv6Server
			meta.Router6 = m.Router6
			return true

		}

	}

	sys.Logger.Printf("Create tunnel: can not find created tunnel(%#v)\n", meta)
	return false
}

/**
* <p>get best meta info </p>
* <p>test by icmp</p>
* @return the ip ping the fastest
 */
func (broker *HEBroker) getBestIP() string {
	sys.Logger.Printf("Determinate Best Tunnel Server End......\n")
	defer func() {
		sys.Logger.Printf("Determinate Best Tunnel Server End: Finish\n")

	}()

	/*
		visit https://tunnelbroker.net/new_tunnel.php
		parse ips
	*/
	ipUrl := "https://tunnelbroker.net/new_tunnel.php"

	// do request
	resp := broker.doHttpGet(ipUrl)

	if nil == resp {
		return ""
	}

	defer resp.Body.Close()

	// read body
	body, err := ioutil.ReadAll(resp.Body)
	if nil != err {
		sys.Logger.Printf("Read best server body %s\n", err)
		return ""
	}

	// parse ips
	ips := ipListPattern.FindAllStringSubmatch(string(body), -1)
	if nil == ips {
		sys.Logger.Printf("Find best server body %s\n", string(body))
		return ""

	}

	ipSlice := make([]string, len(ips))
	for inx, ipMatches := range ips {
		ipSlice[inx] = ipMatches[1]

	}

	return iputil.GetBestIP(ipSlice)

}

func (b *HEBroker) doHttpGet(reqUrl string) *http.Response {
	resp, err := b.client.Get(reqUrl)

	if nil != err {
		sys.Logger.Printf("Get request %s: %s\n", reqUrl, err)
		return nil
	}
	return resp
}

func (b *HEBroker) doHttpPost(reqUrl string, vals url.Values) *http.Response {
	resp, err := b.client.PostForm(reqUrl, vals)

	if nil != err {
		sys.Logger.Printf("Post request %s: %s\n", reqUrl, err)
		return nil
	}

	return resp
}

func parseTunnels(xmlText io.Reader) []*sys.Meta {
	var (
		metas      []*sys.Meta
		xmlDecoder = xml.NewDecoder(xmlText)
	)

	for {
		token, err := xmlDecoder.Token()
		// end
		if nil == token && io.EOF == err {
			break
		}

		switch tokenType := token.(type) {
		case xml.StartElement:
			if "tunnel" == strings.ToLower(tokenType.Name.Local) {
				tunnel := &sys.Meta{}
				err := xmlDecoder.DecodeElement(&tunnel, &tokenType)
				if nil != err {
					sys.Logger.Printf("parse xml fail: %s, %#v\n", err, xmlText)
					return nil

				}

				if nil == metas {
					metas = make([]*sys.Meta, 1)
					metas[0] = tunnel

				} else {
					metas = append(metas, tunnel)

				}

			}

		}

	}

	return metas
}

func (broker *HEBroker) deleteTunnel(meta *sys.Meta) bool {
	sys.Logger.Printf("Delete tunnel(%#v)......\n", meta)

	delURL := fmt.Sprintf("https://tunnelbroker.net/tunnel_detail.php?tid=%s", meta.ID)
	postData := url.Values{}
	postData.Add("delete", "Delete Tunnel")

	// post
	resp := doHttpPost(delURL, postData)
	if nil == resp {
		return false
	}

	defer resp.Body.Close()
	body, err := ioutil.ReadAll(resp.Body)
	if nil != err {
		sys.Logger.Printf("Delete tunnel Error: %s\n", err)
		return false

	}

	if 200 != resp.StatusCode {
		sys.Logger.Printf("Delete tunnel Error: code=%d, %s\n", resp.StatusCode, string(body))
		return false

	}

	if !deleteTunnelPattern.MatchString(string(body)) {
		sys.Logger.Printf("Delete tunnel Error: pattern not match, %s\n", string(body))
		return false

	}

	return true
}
