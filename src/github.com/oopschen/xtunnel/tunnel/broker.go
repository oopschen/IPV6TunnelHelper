package tunnel

import (
	"github.com/oopschen/xtunnel/sys"
)

type Broker interface {
	// init broker based on config
	Init(cfg *sys.Config) bool
	// get ip meta info
	GetMeta() *sys.Meta
	// destroy
	Destroy() bool
}
