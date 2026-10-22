// sysagentd — демон администрирования Linux на Go.
//
// Один бинарник, три роли:
//
//	sysagentd daemon            — висит в памяти, слушает unix-сокет
//	sysagentd logs|status|...    — клиент: шлёт команду демону и печатает ответ
//	sysagentd logs --local ...   — тот же запрос без демона (для cron/отладки)
package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"net"
	"os"
	"path/filepath"
	"time"
)

const defaultSocket = "/run/sysagentd.sock"

func main() {
	if len(os.Args) < 2 {
		usage()
		os.Exit(2)
	}
	cmd := os.Args[1]
	args := os.Args[2:]

	switch cmd {
	case "daemon":
		runDaemon(args)
	case "logs", "failed", "status", "disk", "mem", "watch", "ping", "version":
		runClient(cmd, args)
	case "-h", "--help", "help":
		usage()
	default:
		fmt.Fprintf(os.Stderr, "неизвестная команда %q\n\n", cmd)
		usage()
		os.Exit(2)
	}
}

func usage() {
	fmt.Print(`sysagentd — демон администрирования Linux

Демон:
  sysagentd daemon [--socket PATH] [--mode readonly|ask|auto]

Клиент (обращается к демону через unix-сокет):
  sysagentd logs   [--unit nginx.service] [--since -1h] [--limit 200]
  sysagentd failed
  sysagentd status --unit nginx.service
  sysagentd disk
  sysagentd mem
  sysagentd ping
  sysagentd version

Любой запрос можно выполнить без демона, добавив --local (полезно для cron).

Переменные: SYSAGENTD_SOCKET, SYSAGENTD_MODE
`)
}

// ---------------------------------------------------------------------------
// протокол: одна строка JSON в запросе, одна строка JSON в ответе
// ---------------------------------------------------------------------------

type Request struct {
	Cmd  string            `json:"cmd"`
	Args map[string]string `json:"args,omitempty"`
}

type Response struct {
	OK      bool            `json:"ok"`
	Data    json.RawMessage `json:"data,omitempty"`
	Error   string          `json:"error,omitempty"`
	Elapsed string          `json:"elapsed"`
}

func socketPath(flagValue string) string {
	if flagValue != "" {
		return flagValue
	}
	if v := os.Getenv("SYSAGENTD_SOCKET"); v != "" {
		return v
	}
	return defaultSocket
}

func runClient(cmd string, args []string) {
	fs := flag.NewFlagSet(cmd, flag.ExitOnError)
	socket := fs.String("socket", "", "путь к unix-сокету демона")
	local := fs.Bool("local", false, "выполнить локально, без демона")
	unit := fs.String("unit", "", "имя systemd-юнита")
	since := fs.String("since", "-1h", "период журнала")
	limit := fs.Int("limit", 200, "сколько записей прочитать")
	_ = fs.Parse(args)

	req := Request{Cmd: cmd, Args: map[string]string{}}
	if *unit != "" {
		req.Args["unit"] = *unit
	}
	req.Args["since"] = *since
	req.Args["limit"] = fmt.Sprint(*limit)

	if cmd == "watch" {
		runWatch(*local, *socket, time.Duration(*limit)*time.Second)
		return
	}

	var resp Response
	if *local {
		resp = handle(req)
	} else {
		var err error
		resp, err = callDaemon(*socket, req)
		if err != nil {
			fmt.Fprintf(os.Stderr, "демон недоступен (%v)\n", err)
			fmt.Fprintln(os.Stderr, "запустите: sysagentd daemon   |   либо повторите с --local")
			os.Exit(1)
		}
	}

	if !resp.OK {
		fmt.Fprintln(os.Stderr, "ошибка:", resp.Error)
		os.Exit(1)
	}
	var pretty any
	_ = json.Unmarshal(resp.Data, &pretty)
	out, _ := json.MarshalIndent(pretty, "", "  ")
	fmt.Println(string(out))
}

func callDaemon(path string, req Request) (Response, error) {
	path = socketPath(path)
	conn, err := net.DialTimeout("unix", path, 3*time.Second)
	if err != nil {
		return Response{}, err
	}
	defer conn.Close()
	_ = conn.SetDeadline(time.Now().Add(60 * time.Second))

	if err := json.NewEncoder(conn).Encode(req); err != nil {
		return Response{}, err
	}
	var resp Response
	if err := json.NewDecoder(conn).Decode(&resp); err != nil {
		return Response{}, fmt.Errorf("не удалось прочитать ответ: %w", err)
	}
	return resp, nil
}

func ensureDir(path string) error {
	return os.MkdirAll(filepath.Dir(path), 0o755)
}
