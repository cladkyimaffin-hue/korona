package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"log"
	"net"
	"os"
	"os/signal"
	"strings"
	"sync"
	"syscall"
	"time"
)

// runDaemon — «зависает в оперативке»: слушает unix-сокет и выполняет запросы.
// Ничего не делает в фоне, пока его не спросят (кроме режима watch).
func runDaemon(args []string) {
	fs := flag.NewFlagSet("daemon", flag.ExitOnError)
	socket := fs.String("socket", "", "путь к unix-сокету")
	mode := fs.String("mode", "ask", "readonly | ask | auto")
	_ = fs.Parse(args)

	path := socketPath(*socket)
	if err := ensureDir(path); err != nil {
		log.Fatalf("не создать каталог для сокета: %v", err)
	}
	_ = os.Remove(path) // сокет от прошлого запуска

	listener, err := net.Listen("unix", path)
	if err != nil {
		log.Fatalf("не удалось открыть сокет %s: %v", path, err)
	}
	// только владелец демона может им управлять
	if err := os.Chmod(path, 0o660); err != nil {
		log.Printf("предупреждение: chmod сокета: %v", err)
	}

	policy := &Policy{Mode: *mode, AllowDangerous: os.Getenv("SYSAGENTD_ALLOW_DANGEROUS") == "1"}

	log.Printf("sysagentd %s слушает %s (mode=%s, pid=%d)", Version, path, policy.Mode, os.Getpid())

	// корректное завершение: убрать сокет за собой
	stop := make(chan os.Signal, 1)
	signal.Notify(stop, syscall.SIGINT, syscall.SIGTERM)
	go func() {
		<-stop
		log.Println("получен сигнал, завершаюсь")
		_ = listener.Close()
		_ = os.Remove(path)
		os.Exit(0)
	}()

	for {
		conn, err := listener.Accept()
		if err != nil {
			return // listener закрыт -> штатный выход
		}
		go serveConn(conn, policy) // каждый запрос в своей горутине: стоит ~2 КБ
	}
}

func serveConn(conn net.Conn, policy *Policy) {
	defer conn.Close()
	started := time.Now()
	_ = conn.SetDeadline(time.Now().Add(90 * time.Second))

	var req Request
	if err := json.NewDecoder(conn).Decode(&req); err != nil {
		_ = json.NewEncoder(conn).Encode(Response{OK: false, Error: "плохой запрос: " + err.Error()})
		return
	}

	resp := handle(req, policy)
	resp.Elapsed = time.Since(started).Round(time.Millisecond).String()
	_ = json.NewEncoder(conn).Encode(resp)

	Audit(map[string]any{
		"cmd": req.Cmd, "args": req.Args, "ok": resp.OK,
		"error": resp.Error, "elapsed": resp.Elapsed,
	})
}

// handle — единственное место, где запрос превращается в действие.
// Здесь же (через policy.Check) решается, можно ли выполнить команду.
func handle(req Request, policies ...*Policy) Response {
	policy := &Policy{Mode: "readonly"}
	if len(policies) > 0 && policies[0] != nil {
		policy = policies[0]
	}
	data, err := dispatch(req, policy)
	if err != nil {
		return Response{OK: false, Error: err.Error()}
	}
	raw, err := json.Marshal(data)
	if err != nil {
		return Response{OK: false, Error: err.Error()}
	}
	return Response{OK: true, Data: raw}
}

func dispatch(req Request, policy *Policy) (any, error) {
	switch req.Cmd {
	case "ping":
		return map[string]any{"pong": true, "version": Version, "uptime": time.Since(startedAt).Round(time.Second).String()}, nil

	case "version":
		return map[string]any{"version": Version, "go": goVersion(), "mode": policy.Mode}, nil

	case "logs":
		return JournalErrors(req.Args["unit"], req.Args["since"], atoi(req.Args["limit"], 200), policy)

	case "failed":
		return FailedUnits(policy)

	case "status":
		unit := strings.TrimSpace(req.Args["unit"])
		if unit == "" {
			return nil, fmt.Errorf("нужен --unit")
		}
		return UnitStatus(unit, policy)

	case "disk":
		return RunReadOnly("df", "-h", "-x", "tmpfs", "-x", "devtmpfs")

	case "mem":
		return RunReadOnly("free", "-h")

	default:
		return nil, fmt.Errorf("неизвестная команда: %s", req.Cmd)
	}
}

// runWatch — единственная фоновая активность демона-клиента: опрос журнала.
func runWatch(local bool, socket string, interval time.Duration) {
	if interval < 10*time.Second {
		interval = 10 * time.Second
	}
	seen := map[string]bool{}
	var mu sync.Mutex
	log.Printf("watch: интервал %s", interval)
	for {
		req := Request{Cmd: "logs", Args: map[string]string{"since": "-2min", "limit": "500"}}
		var resp Response
		var err error
		if local {
			resp = handle(req)
		} else {
			resp, err = callDaemon(socket, req)
		}
		if err == nil && resp.OK {
			var report struct {
				Groups []struct {
					Unit    string `json:"unit"`
					Message string `json:"message"`
					Count   int    `json:"count"`
				} `json:"groups"`
			}
			_ = json.Unmarshal(resp.Data, &report)
			mu.Lock()
			for _, g := range report.Groups {
				key := g.Unit + "|" + g.Message
				if seen[key] {
					continue
				}
				seen[key] = true
				log.Printf("НОВАЯ ОШИБКА [%s] x%d %s", g.Unit, g.Count, truncate(g.Message, 180))
			}
			mu.Unlock()
		}
		time.Sleep(interval)
	}
}

func atoi(s string, def int) int {
	if s == "" {
		return def
	}
	var n int
	if _, err := fmt.Sscanf(s, "%d", &n); err != nil || n <= 0 {
		return def
	}
	return n
}
