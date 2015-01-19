// Package osop provides ...
package osop

import (
	"github.com/oopschen/xtunnel/sys"
)

type Operator interface {
	/**
	* create tunnel named "xxxx"
	* @param meta meta info for tunnel
	* @return true if success
	 */
	Create(meta *sys.Meta) bool

	/**
	* delete tunnel
	* @return true if success
	 */
	Delete() bool
}
