package iputil

import (
	"regexp"
	"strings"
	"testing"
)

func TestGetLocalAddress(t *testing.T) {
	ipPattern, err := regexp.Compile(`(?m)^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$`)
	if nil != err {
		t.Fatalf("ip pattern not correct: %s\n", err)

	}

	ip, natIP := GetLocalAddress()
	if 1 > len(ip) || strings.HasPrefix(ip, "192.168") {
		t.Fatalf("ip not correct: %s\n", ip)
	}

	if !ipPattern.MatchString(ip) {
		t.Fatalf("ip not match pattern: %s\n", ip)

	}

	if 1 > len(natIP) || !strings.HasPrefix(natIP, "192.168") {
		t.Fatalf("ip not correct: %s\n", natIP)
	}

	if !ipPattern.MatchString(natIP) {
		t.Fatalf("ip not match pattern: %s\n", natIP)

	}
}
