### Шаг 13 — Обновляем main.go, пересобираем бинарник и делаем команду sysagentd глобальной
## Что делает этот шаг:

-  подключает команды start, stop, restart, status, audit и интерактивную консоль при запуске без параметров;
-  пересобирает бинарник /opt/sysagent/sysagentd;
-  ставит символьную ссылку /usr/local/bin/sysagentd, чтобы вы могли из любой папки просто набрать sysagentd.

  cat <<'EOF' > /opt/sysagent/cmd/sysagentd/main.go
// Единая точка входа sysagentd:
//   - "sysagentd" (без аргументов)      — интерактивная консоль управления и тестирования;
//   - "sysagentd start|stop|restart|status" — управление фоновым демоном;
//   - "sysagentd daemon ..."            — внутренний режим фонового процесса;
//   - "sysagentd <операция> ..."        — разовый вызов операции из командной строки.
package main

import (
	"bufio"
	"context"
	"encoding/json"
	"flag"
	"fmt"
	"log"
	"os"
	"os/signal"
	"strings"
	"syscall"
	"time"

	"sysagent/internal/config"
	"sysagent/internal/core"
	"sysagent/internal/ipc"
)

func main() {
	os.Exit(run(os.Args[1:]))
}

// buildEngine собирает ядро и регистрирует все подключённые модули функций.
// Новые модули (local, proxmox, linuxssh, windows) подключаются именно здесь.
func buildEngine(cfg config.Config) (*core.Engine, error) {
	engine, err := core.NewEngine(cfg)
	if err != nil {
		return nil, err
	}
	return engine, nil
}

func run(argv []string) int {
	// Запуск без аргументов открывает интерактивную консоль управления.
	if len(argv) == 0 {
		cfg, err := config.Load("")
		if err != nil {
			fmt.Fprintf(os.Stderr, "ошибка конфигурации: %v\n", err)
			return 1
		}
		return runInteractiveConsole(cfg, "")
	}

	switch argv[0] {
	case "-h", "--help", "help":
		printUsage()
		return 0
	case "console", "shell":
		return runConsoleCmd(argv[1:])
	case "start", "stop", "restart", "status":
		return runServiceCmd(argv[0], argv[1:])
	case "audit":
		return runAuditCmd(argv[1:])
	case "daemon":
		return runDaemonCmd(argv[1:])
	default:
		return runToolCmd(argv[0], argv[1:])
	}
}

func runConsoleCmd(args []string) int {
	fs := flag.NewFlagSet("console", flag.ContinueOnError)
	cfgPath := fs.String("config", "", "путь к файлу конфигурации")
	socket := fs.String("socket", "", "путь к Unix-сокету демона")
	if err := fs.Parse(args); err != nil {
		return 2
	}
	cfg, err := config.Load(*cfgPath)
	if err != nil {
		fmt.Fprintf(os.Stderr, "ошибка конфигурации: %v\n", err)
		return 1
	}
	if *socket != "" {
		cfg.SocketPath = *socket
	}
	return runInteractiveConsole(cfg, *cfgPath)
}

func runServiceCmd(action string, args []string) int {
	fs := flag.NewFlagSet(action, flag.ContinueOnError)
	cfgPath := fs.String("config", "", "путь к файлу конфигурации")
	socket := fs.String("socket", "", "переопределить путь к Unix-сокету")
	mode := fs.String("mode", "", "режим политики при запуске: readonly | ask | auto")
	if err := fs.Parse(args); err != nil {
		return 2
	}
	cfg, err := config.Load(*cfgPath)
	if err != nil {
		fmt.Fprintf(os.Stderr, "ошибка конфигурации: %v\n", err)
		return 1
	}
	if *socket != "" {
		cfg.SocketPath = *socket
	}
	if *mode != "" {
		cfg.Policy.Mode = *mode
	}
	if err := cfg.Validate(); err != nil {
		fmt.Fprintf(os.Stderr, "некорректные параметры: %v\n", err)
		return 1
	}
	return handleServiceControl(action, cfg, *cfgPath)
}

func runAuditCmd(args []string) int {
	fs := flag.NewFlagSet("audit", flag.ContinueOnError)
	cfgPath := fs.String("config", "", "путь к файлу конфигурации")
	lines := fs.Int("n", 15, "количество последних записей")
	if err := fs.Parse(args); err != nil {
		return 2
	}
	cfg, err := config.Load(*cfgPath)
	if err != nil {
		fmt.Fprintf(os.Stderr, "ошибка конфигурации: %v\n", err)
		return 1
	}
	printAuditTail(cfg.Audit.Path, *lines)
	return 0
}

func runDaemonCmd(args []string) int {
	fs := flag.NewFlagSet("daemon", flag.ContinueOnError)
	cfgPath := fs.String("config", "", "путь к файлу конфигурации (.jsonc / .json)")
	socket := fs.String("socket", "", "переопределить путь к Unix-сокету")
	mode := fs.String("mode", "", "переопределить режим политики: readonly | ask | auto")
	if err := fs.Parse(args); err != nil {
		return 2
	}

	cfg, err := config.Load(*cfgPath)
	if err != nil {
		fmt.Fprintf(os.Stderr, "ошибка конфигурации: %v\n", err)
		return 1
	}
	if *socket != "" {
		cfg.SocketPath = *socket
	}
	if *mode != "" {
		cfg.Policy.Mode = *mode
	}
	if err := cfg.Validate(); err != nil {
		fmt.Fprintf(os.Stderr, "некорректные параметры запуска: %v\n", err)
		return 1
	}

	engine, err := buildEngine(cfg)
	if err != nil {
		fmt.Fprintf(os.Stderr, "ошибка инициализации ядра: %v\n", err)
		return 1
	}

	ctx, stop := signal.NotifyContext(context.Background(), syscall.SIGINT, syscall.SIGTERM)
	defer stop()

	if err := ipc.ServeUnix(ctx, cfg.SocketPath, engine); err != nil {
		fmt.Fprintf(os.Stderr, "ошибка работы демона: %v\n", err)
		return 1
	}
	log.Println("sysagentd штатно остановлен")
	return 0
}

type kvFlags map[string]string

func (kv kvFlags) String() string { return "" }

func (kv kvFlags) Set(val string) error {
	idx := strings.IndexByte(val, '=')
	if idx <= 0 {
		return fmt.Errorf("ожидается формат ключ=значение, получено %q", val)
	}
	k := strings.TrimSpace(val[:idx])
	v := strings.TrimSpace(val[idx+1:])
	kv[k] = v
	return nil
}

func runToolCmd(toolName string, args []string) int {
	fs := flag.NewFlagSet(toolName, flag.ContinueOnError)
	cfgPath := fs.String("config", "", "путь к файлу конфигурации")
	socket := fs.String("socket", "", "путь к Unix-сокету демона")
	local := fs.Bool("local", false, "выполнить напрямую без обращения к демону")
	yes := fs.Bool("yes", false, "подтвердить операцию записи без интерактивного вопроса")
	kv := make(kvFlags)
	fs.Var(kv, "arg", "параметр инструмента в виде ключ=значение (можно указывать несколько раз)")
	if err := fs.Parse(args); err != nil {
		return 2
	}

	cfg, err := config.Load(*cfgPath)
	if err != nil {
		fmt.Fprintf(os.Stderr, "ошибка конфигурации: %v\n", err)
		return 1
	}
	if *socket != "" {
		cfg.SocketPath = *socket
	}

	req := core.Request{
		Tool:     toolName,
		Args:     kv,
		Approved: *yes,
		Caller:   "cli",
	}

	dispatch := func(r core.Request) (core.Response, error) {
		if *local {
			r.Caller = "cli-local"
			engine, buildErr := buildEngine(cfg)
			if buildErr != nil {
				return core.Response{}, buildErr
			}
			return engine.Execute(context.Background(), r), nil
		}
		timeout := time.Duration(cfg.Policy.CommandTimeoutSec+5) * time.Second
		return ipc.CallUnix(cfg.SocketPath, r, timeout)
	}

	resp, err := dispatch(req)
	if err != nil {
		fmt.Fprintf(os.Stderr, "демон недоступен (%v)\n", err)
		fmt.Fprintln(os.Stderr, "запустите 'sysagentd start' (или 'sysagentd') либо добавьте '--local'")
		return 1
	}

	if !resp.OK && resp.NeedsApproval {
		if promptConfirmation(resp.Tool, string(resp.Risk), resp.Error) {
			req.Approved = true
			resp, err = dispatch(req)
			if err != nil {
				fmt.Fprintf(os.Stderr, "ошибка повторного вызова: %v\n", err)
				return 1
			}
		} else {
			fmt.Fprintln(os.Stderr, "операция отменена пользователем")
			return 1
		}
	}

	if !resp.OK {
		fmt.Fprintf(os.Stderr, "отказ / ошибка [%s]: %s\n", resp.Tool, resp.Error)
		return 1
	}

	var pretty any
	if err := json.Unmarshal(resp.Data, &pretty); err != nil {
		fmt.Println(string(resp.Data))
		return 0
	}
	out, _ := json.MarshalIndent(pretty, "", "  ")
	fmt.Println(string(out))
	return 0
}

func promptConfirmation(toolName, risk, reason string) bool {
	fmt.Fprintf(os.Stderr, "\n⚠️  Требуется подтверждение\n   Операция: %s (риск: %s)\n   Причина:  %s\n   Выполнить? [y/N]: ",
		toolName, risk, reason)
	reader := bufio.NewReader(os.Stdin)
	line, err := reader.ReadString('\n')
	if err != nil {
		return false
	}
	ans := strings.ToLower(strings.TrimSpace(line))
	return ans == "y" || ans == "yes" || ans == "д" || ans == "да"
}

func printUsage() {
	fmt.Print(`sysagentd — модульный агент диагностики инфраструктуры

Интерактивный режим (меню + командная строка):
  sysagentd

Управление службой демона:
  sysagentd start     — запустить демона в фоне
  sysagentd stop      — штатно остановить демона
  sysagentd restart   — перезапустить демона
  sysagentd status    — показать состояние, PID, память RSS и режим
  sysagentd audit     — показать последние записи журнала аудита

Прямой вызов операций:
  sysagentd ping
  sysagentd version
  sysagentd tools
  sysagentd <операция> [--arg ключ=значение ...] [--local]
`)
}
EOF
cd /opt/sysagent && CGO_ENABLED=0 go build -trimpath -ldflags="-s -w" -o /opt/sysagent/sysagentd ./cmd/sysagentd && ln -sf /opt/sysagent/sysagentd /usr/local/bin/sysagentd && echo "BUILD OK"
