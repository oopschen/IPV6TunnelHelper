package iputil

import (
	"regexp"
	"strings"
	"testing"
)

func TestGetLocalAddress(t *testing.T) {
	ipPattern, err := regexp.Compile(`[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}`)
	if nil != err {
		t.Fatalf("ip pattern not correct: %s\n", err)

	}

	ip := GetLocalAddress()
	if 1 > len(ip) || strings.HasPrefix(ip, "192.168") {
		t.Fatalf("ip not correct: %s\n", ip)
	}

	if !ipPattern.MatchString(ip) {
		t.Fatalf("ip not match pattern: %s\n", ip)

	}
}
