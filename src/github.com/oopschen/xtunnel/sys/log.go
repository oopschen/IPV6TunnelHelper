package sys

import (
	"fmt"
	"log"
	"os"
)

const (
	ENV_LOG_FILE = "XTUNNEL_LOG"
)

var Logger *log.Logger = nil

func init() {
	out := os.Stdout
	logFile := os.Getenv(ENV_LOG_FILE)

	if 0 < len(logFile) {
		outFile, err := os.OpenFile(logFile, os.O_WRONLY|os.O_CREATE, 0600)
		if nil != err {
			fmt.Printf("open log file(%s): %T\n", logFile, err)
			return

		}

		out = outFile

	}

	Logger = log.New(out, "", log.Ldate|log.Ltime|log.Llongfile)

}
