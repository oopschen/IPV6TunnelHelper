package iputil

import (
	"bytes"
	"encoding/binary"
	"github.com/oopschen/xtunnel/sys"
	"net"
	"time"
)

const (
	// 5 seconds
	timeoutNanoMS = 5 * time.Second
	tryCount      = 4
	minTimeMS     = measureTime(30)
)

type measureTime uint16
type ipMeta struct {
	ip    string
	avgMS measureTime
}

type icmpEchoRequest struct {
	typ      uint8
	code     uint8
	checksum uint16
	id       uint16
	seq      uint16
}

/**
* <p>find the nearest ip address in ips</p>
* @param ips the list of ip
* @return the chosen ip in the ips
 */
func GetBestIP(ips []string) string {
	if nil == ips || 1 > len(ips) {
		return ""

	}

	ipTimeMap := make(map[string]measureTime)
	for _, ip := range ips {
		if 1 > len(ip) {
			continue
		}

		meta := checkPermform(ip)
		if "" == meta.ip {
			continue
		}

		// if <= minTime then return it directly
		if minTimeMS <= meta.avgMS {
			return meta.ip
		}

		ipTimeMap[meta.ip] = meta.avgMS

	}

	bestIP := ""
	bestTime := measureTime(10000)
	for ip, time := range ipTimeMap {
		if bestTime > time {
			bestTime = time
			bestIP = ip

		}

	}

	return bestIP
}

func checkPermform(ip string) (resultMeta *ipMeta) {
	resultMeta = &ipMeta{}
	conn, err := net.DialTimeout("ip4:icmp", ip, timeoutNanoMS)
	if nil != err {
		sys.Logger.Printf("socket %s", err)
		return

	}
	// always close conn if opened
	defer conn.Close()

	var (
		tolTime uint64 = 0
		pId     uint16 = 0x78
		pSeq    uint16 = 0x45
		recvBuf        = make([]byte, 8) // only type code header id seq
	)

	// start time
	timeStart := time.Now()

	// send pkts
	for i := 0; i < tryCount; i++ {
		pkt := createPkt(ip, pId, pSeq)
		if nil == pkt {
			sys.Logger.Printf("create packet %s", err)
			return

		}

		_, err := conn.Write(pkt)
		if nil != err {
			sys.Logger.Printf("write packet %s", err)
			return

		}
	}

	// recv pkts
	conn.SetReadDeadline(time.Now().Add(timeoutNanoMS))
	for i := 0; i < tryCount; i++ {
		_, err = conn.Read(recvBuf)
		if nil != err {
			sys.Logger.Printf("read packet %s", err)
			return
		}

	}

	tolTime = uint64(time.Now().Sub(timeStart).Nanoseconds())

	// send result to channel
	resultMeta.ip = ip
	// ms
	resultMeta.avgMS = measureTime(uint16(tolTime/1000000) / tryCount)
	return
}

func createPkt(ip string, id uint16, seq uint16) []byte {
	out := new(bytes.Buffer)
	// type, code, checksum
	var icmpReq icmpEchoRequest
	icmpReq.typ = 8
	icmpReq.code = 0
	icmpReq.checksum = 0
	icmpReq.id = id
	icmpReq.seq = seq

	err := binary.Write(out, binary.BigEndian, icmpReq)
	if nil != err {
		return nil

	}

	// set checksum
	icmpReq.checksum = checksum(out.Bytes())

	// reset buf
	out.Reset()

	err = binary.Write(out, binary.BigEndian, icmpReq)
	if nil != err {
		return nil

	}

	return out.Bytes()
}

func checksum(data []byte) uint16 {
	var (
		sum    uint32
		length int = len(data)
		index  int
	)
	for length > 1 {
		sum += uint32(data[index])<<8 + uint32(data[index+1])
		index += 2
		length -= 2
	}
	if length > 0 {
		sum += uint32(data[index])
	}
	sum += (sum >> 16)

	return uint16(^sum)
}
