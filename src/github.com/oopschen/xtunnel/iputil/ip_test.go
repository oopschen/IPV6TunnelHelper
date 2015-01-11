package iputil

import (
	"strings"
	"testing"
)

func TestGetLocalAddress(t *testing.T) {
	ip := GetLocalAddress()
	if 1 > len(ip) || strings.HasPrefix(ip, "192.168") {
		t.Fatalf("ip not correct: %s\n", ip)
	}
}
