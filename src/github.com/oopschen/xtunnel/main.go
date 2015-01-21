package main

/*
*	<p>xtunnel main entry</p>
* <p>Usage:</p>
*	<p>xtunnel -(u|user) user -(p|passwd) pwd open </p>
*	<p>xtunnel close</p>
 */

import (
	"flag"
	"fmt"
	"github.com/oopschen/xtunnel/osop"
	"github.com/oopschen/xtunnel/sys"
	"github.com/oopschen/xtunnel/tunnel"
	"strings"
)

func main() {
	/*
		parse args
		get os operator

		if open:
			init broker
			get meta info
			open it
		else:
			close it
	*/

	var (
		user, pwd, action string
		userUsage         = "user name for the tunnel"
		userDefaultVal    = ""
		pwdUsage          = "password for the tunnel"
		pwdDefaultVal     = ""
	)

	const (
		actionOpen  = "open"
		actionClose = "close"
	)

	// parse command line args
	flag.StringVar(&user, "u", userDefaultVal, userUsage)
	flag.StringVar(&user, "user", userDefaultVal, userUsage)
	flag.StringVar(&pwd, "p", pwdDefaultVal, pwdUsage)
	flag.StringVar(&pwd, "passwd", pwdDefaultVal, pwdUsage)

	flag.Parse()
	cmdArgsRemain := flag.Args()
	if nil == cmdArgsRemain || 1 > len(cmdArgsRemain) {
		printUsage()
		return

	}
	// get action from args
	action = strings.ToLower(cmdArgsRemain[0])

	// do the operator
	if actionOpen == action {
		// open
		cfg := &sys.Config{user, pwd}
		broker := &tunnel.HEBroker{}
		if !broker.Init(cfg) {
			sys.Logger.Printf("Init broker fail\n")
			return

		}

		meta := broker.GetMeta()
		if nil == meta {
			sys.Logger.Printf("Get tunnel fail\n")
			return

		}
		op := osop.GetOperatorIns(meta)
		if nil == op {
			sys.Logger.Println("Get operator fail")
			return

		}

		if op.Open() {
			sys.Logger.Println("Open tunnel success")
		}

		broker.Destroy()

	} else if actionClose == action {
		// close
		op := osop.GetOperatorIns(&sys.Meta{})
		if nil == op {
			sys.Logger.Println("Get operator fail")
			return

		}

		if op.Close() {
			sys.Logger.Println("Close tunnel success")

		}

	} else {
		printUsage()

	}
}

func printUsage() {
	fmt.Printf("Xtunnel setup your IPV6 tunnel automatically.\nUsage:\n\txtunnel [-u user] [-p passwd] open | close\n")
}
