// Package osop provides ...
package osop

import (
	"fmt"
	"github.com/oopschen/xtunnel/sys"
	"os/exec"
	"runtime"
)

const (
	tunnelName = "xtunnel_auto_create"
)

type TunnelOperator interface {
	Open() bool
	Close() bool
}

type defaultWinTunnelOperator struct {
	meta *sys.Meta
}

type defaultLinuxTunnelOperator struct {
	meta *sys.Meta
}

func GetOperatorIns(meta *sys.Meta) TunnelOperator {
	if nil == meta {
		return nil
	}

	switch runtime.GOOS {
	case "windows":
		return &defaultWinTunnelOperator{meta: meta}

	case "linux":
		return &defaultLinuxTunnelOperator{meta: meta}

	default:
		sys.Logger.Printf("Can not operate on OS=%s\n", runtime.GOOS)
	}

	return nil
}

func (o *defaultWinTunnelOperator) Open() bool {
	meta := o.meta
	cmds := make([]*exec.Cmd, 4)
	cmds[0] = exec.Command("netsh", "interface teredo set state disabled")
	cmds[1] = exec.Command("netsh", fmt.Sprintf("interface ipv6 add %s interface=IP6Tunnel %s %s", tunnelName, meta.IPv4Client, meta.IPv4Server))
	cmds[2] = exec.Command("netsh", fmt.Sprintf("interface ipv6 add address IP6Tunnel %s", meta.IPv6Client))
	cmds[3] = exec.Command("netsh", fmt.Sprintf("interface ipv6 add route ::/0 %s", meta.IPv6Server))

	return runCmds(cmds)
}

func (o *defaultWinTunnelOperator) Close() bool {
	// TODO
}

func (o *defaultLinuxTunnelOperator) Open() bool {
	meta := o.meta
	cmds := make([]*exec.Cmd, 5)
	cmds[0] = exec.Command("ip", fmt.Sprintf("tunnel add %s mode sit remote %s local %s ttl 255", tunnelName, meta.IPv4Server, meta.IPv4Client))
	cmds[1] = exec.Command("ip", fmt.Sprintf("link set %s up", tunnelName))
	cmds[2] = exec.Command("ip", fmt.Sprintf("addr add %s/64 dev %s", meta.IPv6Client, tunnelName))
	cmds[3] = exec.Command("ip", fmt.Sprintf("route add ::/0 dev %s", tunnelName))
	cmds[4] = exec.Command("ip", "-f inet6 addr")

	return runCmds(cmds)
}

func (o *defaultLinuxTunnelOperator) Close() bool {
	// TODO
}

func runCmds(cmds []*exec.Cmd) bool {
	if nil == cmds {
		return false
	}

	for _, cmd := range cmds {
		err := cmd.Run()
		if nil != err {
			sys.Logger.Printf("cmd %#v fail: %s\n", cmd, err)
			return false
		}
	}

	return true
}
