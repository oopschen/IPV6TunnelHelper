package iputil

import (
	"testing"
)

func TestGetBestIP(t *testing.T) {
	ips := make([]string, 2)
	ips[0] = "115.239.211.112"
	ips[1] = "122.227.164.241"

	ipChosen := GetBestIP(ips)

	if ipChosen != ips[0] && ipChosen != ips[1] {
		t.Fatalf("ip not correct returned : %s\n", ipChosen)

	}

}
