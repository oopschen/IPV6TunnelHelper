package sys

type Meta struct {
	ID string `xml:"id,attr"`
	// server ipv4 address
	IPv4Server string `xml:"serverv4"`
	// client ipv4 address
	IPv4Client string `xml:"clientv4"`
	// client ipv6 address
	IPv6Client string `xml:"clientv6"`
	// server ipv6 address
	IPv6Server string `xml:"serverv6"`
	// router ipv6
	Router6 string `xml:"routed64"`
	// router ipv6 mask
	Router6Mask string
}

func (m *Meta) Eq(q *Meta) bool {
	if nil == q {
		return false
	}

	if "" != m.IPv4Server && m.IPv4Server == q.IPv4Server {
		return true
	}

	if "" != m.IPv6Client && m.IPv6Client == q.IPv6Client {
		return true
	}

	if "" != m.IPv6Server && m.IPv6Server == q.IPv6Server {
		return true
	}
	return false
}
