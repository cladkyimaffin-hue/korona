### Шаг 10 — Создаём точку входа main.go и компилируем готовый бинарник sysagentd
## Зачем нужен этот файл:
/opt/sysagent/cmd/sysagentd/main.go собирает все наши части (config + core + ipc) в один готовый исполняемый файл /opt/sysagent/sysagentd:

-  sysagentd daemon — запускает демона в памяти;
-  sysagentd ping, version, tools — отправляет запрос демону (или запускает сразу на месте с флагом --local);
-  функция buildEngine(...) — именно то место, куда одной строкой мы дальше будем подключать новые модули (local, proxmox и т.д.).
-  Скопируйте и выполните на root@agent — эта команда создаст main.go и сразу откомпилирует готовый бинарник /opt/sysagent/sysagentd:

  cat <<'EOF' > /opt/sysagent/cmd/sysagentd/main.go
// Единая точка входа sysagentd:
//   - "sysagentd daemon ..." — запуск фонового демона на локальном Unix-сокете;
//   - "sysagentd <операция> ..." — обращение клиента к демону (или локально с --local).
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
	if len(argv) == 0 {
		printUsage()
		return 2
	}

	switch argv[0] {
	case "-h", "--help", "help":
		printUsage()
		return 0
	case "daemon":
		return runDaemonCmd(argv[1:])
	default:
		return runToolCmd(argv[0], argv[1:])
	}
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
		fmt.Fprintln(os.Stderr, "запустите 'sysagentd daemon' либо добавьте флаг '--local'")
		return 1
	}

	// Если политика вернула запрос интерактивного подтверждения — спрашиваем у оператора в терминале.
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

Использование:
  sysagentd daemon [--config PATH] [--socket PATH] [--mode readonly|ask|auto]
  sysagentd <операция> [--arg ключ=значение ...] [--socket PATH] [--local]

Базовые операции ядра:
  sysagentd ping       — проверка связи и uptime демона
  sysagentd version    — версия агента, режим политики и источник конфига
  sysagentd tools      — список подключённых модулей и всех доступных операций

Переменные окружения:
  SYSAGENTD_CONFIG     — путь к файлу конфигурации
  SYSAGENTD_SOCKET     — путь к Unix-сокету демона
  SYSAGENTD_MODE       — режим политики (readonly | ask | auto)
  SYSAGENTD_AUDIT      — путь к файлу журнала аудита
`)
}
EOF
cd /opt/sysagent && CGO_ENABLED=0 go build -trimpath -ldflags="-s -w" -o /opt/sysagent/sysagentd ./cmd/sysagentd && ls -lh /opt/sysagent/sysagentd
