// Package tunnel provides ...
package tunnel

import (
	"github.com/oopschen/xtunnel/sys"
	"testing"
)

var (
	testUser    = "unittest"
	testUserPwd = "unittest"
	/*
		DO NOT COMMIT YOUR USER/PWD
	*/
	myUser    = ""
	myUserPwd = ""
)

func TestFailLogin(t *testing.T) {
	var (
		broker = HEBroker{}
		config = sys.Config{testUser, testUserPwd}
	)

	if !broker.Init(&config) {
		t.Fatalf("init fail")

	}

	if broker.login() {
		t.Fatalf("login success but must be fail")
	}

	broker.Destroy()
}

func TestLogin(t *testing.T) {
	var (
		broker = HEBroker{}
		config = sys.Config{myUser, myUserPwd}
	)

	if !broker.Init(&config) {
		t.Fatalf("init fail")

	}

	meta := broker.GetMeta()
	if nil == meta {
		t.Fatalf("get Meta fail: %#v\n", meta)

	} else if "" == meta.ID {
		t.Fatalf("get Meta ID fail: %#v\n", meta)

	} else if "" == meta.IPv4Server {
		t.Fatalf("get Meta IPv4Server fail: %#v\n", meta)

	} else if "" == meta.IPv4Client {
		t.Fatalf("get Meta IPv4Client fail: %#v\n", meta)

	} else if "" == meta.IPv6Client {
		t.Fatalf("get Meta IPv6Client fail: %#v\n", meta)

	} else if "" == meta.Router6 {
		t.Fatalf("get Meta Router6  fail: %#v\n", meta)

	}

	broker.Destroy()
}

func TestFindAllTunnels(t *testing.T) {
	var (
		broker = HEBroker{}
		config = sys.Config{myUser, myUserPwd}
	)

	if !broker.Init(&config) {
		t.Fatalf("init fail")

	}

	if !broker.login() {
		t.Fatalf("login fail")
	}

	meta := broker.findAllTunnels()
	if nil == meta {
		t.Fatalf("get Meta fail: %#v\n", meta)
	}

	broker.Destroy()

}
