package sys

import (
	"fmt"
	"log"
	"os"
	"strings"
)

const (
	ENV_LOG_FILE = "XTUNNEL_LOG"
	ENV_MODE     = "XTUNNEL_MODE"
)

var Logger *log.Logger = nil

func init() {
	out := os.Stdout
	logFile := os.Getenv(ENV_LOG_FILE)
	debug := os.Getenv(ENV_MODE)

	if 0 < len(logFile) {
		outFile, err := os.OpenFile(logFile, os.O_WRONLY|os.O_CREATE, 0600)
		if nil != err {
			fmt.Printf("open log file(%s): %T\n", logFile, err)
			return

		}

		out = outFile

	}

	flag := log.Ldate | log.Ltime
	if "debug" == strings.ToLower(debug) {
		flag |= log.Llongfile
	}

	Logger = log.New(out, "", flag)

}
