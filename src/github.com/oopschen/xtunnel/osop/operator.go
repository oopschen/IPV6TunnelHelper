// Package osop provides ...
package osop

import (
	"github.com/oopschen/xtunnel/sys"
	"os/exec"
	"runtime"
)

const (
	tunnelName = "xtunnel"
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
	cmds[0] = exec.Command("netsh", "interface", "teredo", "set", "state", "disabled")
	cmds[1] = exec.Command("netsh", "interface", "ipv6", "add", "v6v4tunnel", "interface="+tunnelName, meta.IPv4Client, meta.IPv4Server)
	cmds[2] = exec.Command("netsh", "interface", "ipv6", "add", "address", tunnelName, meta.IPv6Client)
	cmds[3] = exec.Command("netsh", "interface", "ipv6", "add", "route", "::/0", meta.IPv6Server)

	return runCmds(cmds)
}

func (o *defaultWinTunnelOperator) Close() bool {
	cmds := make([]*exec.Cmd, 1)
	cmds[0] = exec.Command("netsh", "interface", "ipv6", "delete", "interface", tunnelName)
	return runCmds(cmds)
}

func (o *defaultLinuxTunnelOperator) Open() bool {
	meta := o.meta
	cmds := make([]*exec.Cmd, 4)
	cmds[0] = exec.Command("ip", "tunnel", "add", tunnelName, "mode", "sit", "remote", meta.IPv4Server, "local", meta.IPv4Client, "ttl", "255")
	cmds[1] = exec.Command("ip", "link", "set", tunnelName, "up")
	cmds[2] = exec.Command("ip", "addr", "add", meta.IPv6Client+"/"+meta.Router6Mask, "dev", tunnelName)
	cmds[3] = exec.Command("ip", "route", "add", "::/0", "dev", tunnelName)

	return runCmds(cmds)
}

func (o *defaultLinuxTunnelOperator) Close() bool {
	cmds := make([]*exec.Cmd, 1)
	cmds[0] = exec.Command("ip", "tunnel", "del", tunnelName)
	return runCmds(cmds)
}

func runCmds(cmds []*exec.Cmd) bool {
	if nil == cmds {
		return false
	}

	for _, cmd := range cmds {
		bytes, err := cmd.CombinedOutput()
		if nil != err {
			sys.Logger.Printf("cmd fail:\noutput=>\n\t%s\ncmd=>\n\t%#v\nerror:\n\t%s\n", string(bytes), cmd, err)
			return false
		}
	}

	return true
}
