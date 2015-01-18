package sys

type Meta struct {
	ID string `xml:"id,attr"`
	// server ipv4 address
	IPv4Server string `xml:"serverv4"`
	// client ipv4 address
	IPv4Client string `xml:"clientv4"`
	// client ipv6 address
	IPv6Client string `xml:"serverv6"`
	// router ipv6
	Router6 string `xml:"routed64"`
}
