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
	timeoutNanoMS = 1 * time.Second
	tryCount      = 8
	minTimeMS     = measureTime(30)
	defaultIP     = "0.0.0.0"
)

type measureTime uint16
type ipMeta struct {
	ip    string
	mTime measureTime
}

type icmpEchoRequest struct {
	typ       uint8
	code      uint8
	checksum  uint16
	id        uint16
	seq       uint16
	timestamp uint64
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

	ipMetaList := make([]chan ipMeta, len(ips))

	// send start
	for i, ip := range ips {
		if 1 > len(ip) {
			continue
		}

		ipMetaList[i] = make(chan ipMeta)
		go sendRecvPackets(ipMetaList[i], ip)
	}

	// recv packets
	bestIP := ""
	bestTime := measureTime(65535)
	for _, ipChan := range ipMetaList {
		recvRes := <-ipChan

		if defaultIP == recvRes.ip {
			continue
		}

		if bestTime > recvRes.mTime {
			bestTime = recvRes.mTime
			bestIP = recvRes.ip
		}

	}

	return bestIP
}

func sendPkt(ip string, conn net.Conn) {
	var (
		pId  uint16 = 0x78
		pSeq uint16 = 0x45
	)

	// send pkts
	for i := 0; i < tryCount; i++ {
		pkt := createPkt(ip, pId, pSeq)
		if nil == pkt {
			return

		}

		_, err := conn.Write(pkt)
		if nil != err {
			sys.Logger.Printf("write packet %s", err)
			return

		}
		pId++
		pSeq++
	}

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
	icmpReq.timestamp = uint64(time.Now().UnixNano())

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

func sendRecvPackets(result chan ipMeta, ip string) {
	var (
		returnIp = defaultIP
		mTime    = measureTime(0)
		recvChan = make(chan int16)
		conn     net.Conn
	)

	// always close conn if opened
	defer func() {
		if nil != conn {
			conn.Close()
		}
		result <- ipMeta{ip: returnIp, mTime: mTime}
	}()

	// init connection
	conn, err := net.Dial("ip4:icmp", ip)
	if nil != err {
		sys.Logger.Printf("socket %s", err)
		return
	}

	// recvs
	go recvPkt(recvChan, conn)

	// sends
	sendPkt(ip, conn)

	// check recvs
	recvMs := <-recvChan
	if 0 > recvMs {
		return
	}

	mTime = measureTime(recvMs)

	returnIp = ip
}

func recvPkt(result chan int16, conn net.Conn) {
	// recv pkts
	var (
		recvBuf          = make([]byte, 72) // only type code header id seq and timestamp: 60 bytes ip header + 12 icmp
		ms        int16  = -1
		tmpNano   uint64 = 0
		startNano int64
		icmpBuf   []byte
		cnt       uint64 = 0
	)

	defer func() {
		result <- ms
	}()

	for cnt = 0; cnt < tryCount; {
		conn.SetReadDeadline(time.Now().Add(timeoutNanoMS))
		byteNum, err := conn.Read(recvBuf)
		if nil != err {
			if errT, ok := err.(net.Error); ok && errT.Timeout() {
				break

			}

			sys.Logger.Printf("wait for packet %s", err)
			continue

		} else if len(recvBuf) > byteNum {
			// check is icmp, 10th bytes
			if 1 != recvBuf[9] {
				sys.Logger.Printf("wait for packet %x", recvBuf[8])
				continue
			}

			// parse ip header
			icmpBuf = recvBuf[uint16(0x0F&recvBuf[0])*4:]

			// not icmp echo reply and not enough bytes recv
			if 0 != icmpBuf[0] || 0 != icmpBuf[1] {
				sys.Logger.Printf("invalid packet, bytes=%d, type=0x%x, code=0x%x", byteNum, icmpBuf[0], icmpBuf[1])
				continue
			}

		}

		// parse timestamp and ip
		readBuf := bytes.NewReader(icmpBuf[8:])
		err = binary.Read(readBuf, binary.BigEndian, &startNano)
		if nil == err {
			cnt += 1
			tmpNano += uint64((time.Now().UnixNano() - startNano))
		} else {
			sys.Logger.Printf("read timestamp %s", err)

		}

	}

	if 0 < cnt {
		ms = int16(tmpNano / cnt / 1000000)
	}
}
