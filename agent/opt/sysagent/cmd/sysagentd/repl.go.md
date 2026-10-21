### Шаг 12 — Создаём интерактивную консоль /opt/sysagent/cmd/sysagentd/repl.go
## Зачем нужен этот файл:
Это ваша интерактивная панель управления прямо в терминале:

-  живой индикатор в приглашении: sysagent [○]> (остановлен) / sysagent [●]> (работает);
-  управление одной кнопкой или словом:
-  1 / start — запуск демона;
-  2 / stop — штатная остановка;
-  3 / restart — перезагрузка демона;
-  4 / status — статус, PID, uptime и память RSS;
-  5 / ping, 6 / tools, 7 / audit, 0 / exit;
-  плюс в этой же строке можно вводить любую операцию ядра напрямую.

  cat <<'EOF' > /opt/sysagent/cmd/sysagentd/repl.go
package main

import (
	"bufio"
	"encoding/json"
	"fmt"
	"io"
	"os"
	"strings"
	"time"
	"unicode"

	"sysagent/internal/config"
	"sysagent/internal/core"
	"sysagent/internal/ipc"
)

func runInteractiveConsole(cfg config.Config, cfgPath string) int {
	printConsoleHeader(cfg)
	printStatusSummary(ipc.GetStatus(cfg))
	printConsoleMenu()

	scanner := bufio.NewScanner(os.Stdin)
	for {
		up, _ := ipc.IsRunningFast(cfg)
		stateDot := "○"
		if up {
			stateDot = "●"
		}
		fmt.Printf("\nsysagent [%s]> ", stateDot)

		if !scanner.Scan() {
			fmt.Println()
			return 0
		}

		line := strings.TrimSpace(scanner.Text())
		if line == "" {
			continue
		}

		// Поддержка быстрых цифровых пунктов меню (удобно независимо от раскладки клавиатуры).
		switch line {
		case "1":
			line = "start"
		case "2":
			line = "stop"
		case "3":
			line = "restart"
		case "4":
			line = "status"
		case "5":
			line = "ping"
		case "6":
			line = "tools"
		case "7":
			line = "audit"
		case "0":
			line = "exit"
		}

		tokens, err := splitConsoleLine(line)
		if err != nil {
			fmt.Fprintf(os.Stderr, "✗ Ошибка разбора строки: %v\n", err)
			continue
		}
		if len(tokens) == 0 {
			continue
		}

		cmd := tokens[0]
		rest := tokens[1:]

		switch cmd {
		case "exit", "quit", "q":
			stNow := ipc.GetStatus(cfg)
			if stNow.Running {
				fmt.Printf("Выход из консоли. Демон продолжает работать в фоне (pid=%d).\n", stNow.PID)
			} else {
				fmt.Println("Выход из консоли (демон остановлен).")
			}
			return 0

		case "help", "h", "?":
			printConsoleMenu()

		case "start":
			_ = handleServiceControl("start", cfg, cfgPath)

		case "stop":
			_ = handleServiceControl("stop", cfg, cfgPath)

		case "restart", "reload":
			_ = handleServiceControl("restart", cfg, cfgPath)

		case "status":
			printStatusSummary(ipc.GetStatus(cfg))

		case "audit":
			printAuditTail(cfg.Audit.Path, 10)

		case "log", "daemon-log":
			printLogTail(ipc.DaemonLogPath(cfg), 15)

		default:
			execConsoleTool(cfg, cmd, rest)
		}
	}
}

func handleServiceControl(action string, cfg config.Config, cfgPath string) int {
	switch action {
	case "start":
		st, already, err := ipc.StartDaemon(cfg, cfgPath)
		if err != nil {
			fmt.Fprintf(os.Stderr, "✗ Ошибка запуска: %v\n", err)
			return 1
		}
		if already {
			fmt.Printf("• Демон уже запущен (pid=%d, uptime=%s, память=%.1f МБ)\n",
				st.PID, st.Uptime, float64(st.RSSKB)/1024.0)
			return 0
		}
		fmt.Printf("✓ Демон запущен (pid=%d, режим=%s, память=%.1f МБ)\n",
			st.PID, st.PolicyMode, float64(st.RSSKB)/1024.0)
		return 0

	case "stop":
		pid, wasRunning, err := ipc.StopDaemon(cfg)
		if err != nil {
			fmt.Fprintf(os.Stderr, "✗ Ошибка остановки: %v\n", err)
			return 1
		}
		if !wasRunning {
			fmt.Println("• Демон уже остановлен.")
			return 0
		}
		fmt.Printf("✓ Демон штатно остановлен (pid=%d)\n", pid)
		return 0

	case "restart":
		oldPID, st, err := ipc.RestartDaemon(cfg, cfgPath)
		if err != nil {
			fmt.Fprintf(os.Stderr, "✗ Ошибка перезапуска: %v\n", err)
			return 1
		}
		if oldPID > 0 {
			fmt.Printf("✓ Старый процесс остановлен (pid=%d)\n", oldPID)
		}
		fmt.Printf("✓ Демон перезапущен (новый pid=%d, режим=%s, память=%.1f МБ)\n",
			st.PID, st.PolicyMode, float64(st.RSSKB)/1024.0)
		return 0

	case "status":
		st := ipc.GetStatus(cfg)
		printStatusSummary(st)
		if !st.Running {
			return 3
		}
		return 0
	}
	return 2
}

func execConsoleTool(cfg config.Config, toolName string, rawArgs []string) {
	kv := make(map[string]string)
	for _, item := range rawArgs {
		idx := strings.IndexByte(item, '=')
		if idx <= 0 {
			fmt.Fprintf(os.Stderr, "✗ Параметры указываются в виде ключ=значение (получено %q)\n", item)
			return
		}
		kv[strings.TrimSpace(item[:idx])] = strings.TrimSpace(item[idx+1:])
	}

	req := core.Request{
		Tool:   toolName,
		Args:   kv,
		Caller: "console",
	}

	timeout := time.Duration(cfg.Policy.CommandTimeoutSec+5) * time.Second
	resp, err := ipc.CallUnix(cfg.SocketPath, req, timeout)
	if err != nil {
		fmt.Fprintf(os.Stderr, "✗ Демон не запущен (%v). Введите '1' или 'start', чтобы запустить его.\n", err)
		return
	}

	if !resp.OK && resp.NeedsApproval {
		if promptConfirmation(resp.Tool, string(resp.Risk), resp.Error) {
			req.Approved = true
			resp, err = ipc.CallUnix(cfg.SocketPath, req, timeout)
			if err != nil {
				fmt.Fprintf(os.Stderr, "✗ Ошибка повторного запроса: %v\n", err)
				return
			}
		} else {
			fmt.Println("• Операция отменена.")
			return
		}
	}

	if !resp.OK {
		fmt.Fprintf(os.Stderr, "✗ Отказ политики [%s]: %s\n", resp.Tool, resp.Error)
		return
	}

	var pretty any
	if err := json.Unmarshal(resp.Data, &pretty); err != nil {
		fmt.Println(string(resp.Data))
		return
	}
	out, _ := json.MarshalIndent(pretty, "", "  ")
	fmt.Println(string(out))
}

func printConsoleHeader(cfg config.Config) {
	fmt.Printf("============================================================\n")
	fmt.Printf("  sysagentd v%s — интерактивная консоль управления\n", core.Version)
	fmt.Printf("============================================================\n")
}

func printStatusSummary(st ipc.DaemonStatus) {
	if st.Running && st.SocketOK {
		fmt.Printf("  Состояние:   РАБОТАЕТ (●)\n")
		fmt.Printf("  PID:         %d\n", st.PID)
		fmt.Printf("  Uptime:      %s\n", st.Uptime)
		fmt.Printf("  Память RSS:  %.2f МБ (%d КБ)\n", float64(st.RSSKB)/1024.0, st.RSSKB)
		fmt.Printf("  Режим:       %s\n", st.PolicyMode)
		fmt.Printf("  Сокет:       %s\n", st.SocketPath)
		fmt.Printf("  Лог демона:  %s\n", st.DaemonLog)
		fmt.Printf("  Аудит:       %s\n", st.AuditPath)
	} else {
		fmt.Printf("  Состояние:   ОСТАНОВЛЕН (○)\n")
		fmt.Printf("  Режим конф.: %s\n", st.PolicyMode)
		fmt.Printf("  Сокет:       %s\n", st.SocketPath)
		fmt.Printf("  Аудит:       %s\n", st.AuditPath)
	}
}

func printConsoleMenu() {
	fmt.Print(`
Управление службой (можно вводить цифру или слово):
  [1] start      — запустить демона в фоне
  [2] stop       — штатно остановить демона
  [3] restart    — перезагрузить демона
  [4] status     — статус, PID, uptime и расход памяти

Проверка и диагностика:
  [5] ping       — проверка связи с ядром
  [6] tools      — список подключённых модулей и операций
  [7] audit      — последние 10 записей журнала аудита
  [0] exit       — выход из консоли (демон остаётся работать)

Также можно вводить любую операцию напрямую, например:
  version   или   "rm -rf /" (для проверки блокировки политикой)
`)
}

func printAuditTail(path string, n int) {
	lines := ipc.ReadTailLines(path, n)
	if len(lines) == 0 {
		fmt.Printf("Журнал аудита пока пуст (%s)\n", path)
		return
	}
	fmt.Printf("--- Последние записи аудита (%s) ---\n", path)
	for _, ln := range lines {
		fmt.Println(" ", ln)
	}
}

func printLogTail(path string, n int) {
	lines := ipc.ReadTailLines(path, n)
	if len(lines) == 0 {
		fmt.Printf("Лог демона пока пуст (%s)\n", path)
		return
	}
	fmt.Printf("--- Лог демона (%s) ---\n", path)
	for _, ln := range lines {
		fmt.Println(" ", ln)
	}
}

// splitConsoleLine разбирает введённую строку с поддержкой кавычек ("..." и '...').
func splitConsoleLine(input string) ([]string, error) {
	var tokens []string
	var buf strings.Builder
	var quote rune
	inToken := false

	for _, r := range input {
		switch {
		case quote != 0:
			if r == quote {
				quote = 0
			} else {
				buf.WriteRune(r)
			}
		case r == '"' || r == '\'':
			quote = r
			inToken = true
		case unicode.IsSpace(r):
			if inToken {
				tokens = append(tokens, buf.String())
				buf.Reset()
				inToken = false
			}
		default:
			buf.WriteRune(r)
			inToken = true
		}
	}
	if quote != 0 {
		return nil, io.ErrUnexpectedEOF
	}
	if inToken {
		tokens = append(tokens, buf.String())
	}
	return tokens, nil
}
EOF
cd /opt/sysagent && go build ./cmd/sysagentd && echo "repl: OK"
