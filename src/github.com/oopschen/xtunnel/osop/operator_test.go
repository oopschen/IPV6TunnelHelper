// Package osop provides ...
package osop

import (
	"github.com/oopschen/xtunnel/sys"
	"testing"
)

func TestLinuxOperatoer(t *testing.T) {

	meta := &sys.Meta{
		IPv4Server: "72.52.104.74",
		IPv4Client: "183.138.123.18",
		IPv6Client: "2001:470:1f04:568::2",
		IPv6Server: "2001:470:1f04:568::1",
	}

	op := GetOperatorIns(meta)
	if !op.Open() {
		t.Fatalf("linux operator open fail")
	}

	if !op.Close() {
		t.Fatalf("linux operator close fail")
	}
}
