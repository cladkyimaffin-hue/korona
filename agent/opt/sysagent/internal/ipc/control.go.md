### Сделаем полноценное управление прямо внутри самого sysagentd — работать будет и интерактивно из меню/консоли, и обычными командами:

просто набираете sysagentd → открывается интерактивная консоль с живым индикатором (sysagent [○]> остановлен / sysagent [●]> запущен), где работают и цифры 1..7, 0 (даже на русской раскладке!), и команды словами (start, stop, restart, status, ping, tools, audit, любая операция);
из обычного терминала точно так же работают sysagentd start, sysagentd stop, sysagentd restart, sysagentd status.

## Шаг 11 — Добавляем модуль управления демоном /opt/sysagent/internal/ipc/control.go
# Зачем нужен этот файл:
Берёт на себя всю «грязную» системную работу вместо ручных команд:

-  StartDaemon — запускает демона в отдельной сессии в фоне (чтобы закрытие SSH его не убивало), сохраняет PID, пишет лог в daemon.log и сам ждёт готовности сокета;
-  StopDaemon — находит процесс, шлёт штатный SIGTERM, ждёт чистого завершения без zombie-процессов и подчищает хвосты;
-  RestartDaemon — аккуратно останавливает старый процесс и поднимает новый;
-  GetStatus — проверяет живой отклик сокета, uptime и реальный расход памяти VmRSS из /proc/<pid>/status.

pkill -TERM sysagentd 2>/dev/null || true

cat <<'EOF' > /opt/sysagent/internal/ipc/control.go
package ipc

import (
	"bufio"
	"bytes"
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strconv"
	"strings"
	"syscall"
	"time"

	"sysagent/internal/config"
	"sysagent/internal/core"
)

// DaemonStatus содержит полную сводку о текущем состоянии фонового демона.
type DaemonStatus struct {
	Running    bool   `json:"running"`
	SocketOK   bool   `json:"socket_ok"`
	PID        int    `json:"pid,omitempty"`
	RSSKB      int64  `json:"rss_kb,omitempty"`
	Uptime     string `json:"uptime,omitempty"`
	Version    string `json:"version,omitempty"`
	PolicyMode string `json:"policy_mode,omitempty"`
	SocketPath string `json:"socket_path"`
	PIDPath    string `json:"pid_path"`
	DaemonLog  string `json:"daemon_log"`
	AuditPath  string `json:"audit_path"`
}

// PIDPath возвращает путь к PID-файлу рядом с Unix-сокетом.
func PIDPath(cfg config.Config) string {
	return filepath.Join(filepath.Dir(cfg.SocketPath), "sysagentd.pid")
}

// DaemonLogPath возвращает путь к логу фонового процесса демона рядом с журналом аудита.
func DaemonLogPath(cfg config.Config) string {
	return filepath.Join(filepath.Dir(cfg.Audit.Path), "daemon.log")
}

// IsRunningFast выполняет мгновенную локальную проверку процесса и сокета без записи в аудит
// (используется для индикатора ● / ○ в строке приглашения консоли).
func IsRunningFast(cfg config.Config) (bool, int) {
	pid := resolveRunningPID(PIDPath(cfg), cfg.SocketPath)
	if pid <= 0 {
		return false, 0
	}
	if _, err := os.Stat(cfg.SocketPath); err != nil {
		return false, pid
	}
	return true, pid
}

// GetStatus проверяет процесс демона, потребление памяти RSS и живой отклик по сокету.
func GetStatus(cfg config.Config) DaemonStatus {
	st := DaemonStatus{
		SocketPath: cfg.SocketPath,
		PIDPath:    PIDPath(cfg),
		DaemonLog:  DaemonLogPath(cfg),
		AuditPath:  cfg.Audit.Path,
		PolicyMode: cfg.Policy.Mode,
	}

	pid := resolveRunningPID(st.PIDPath, cfg.SocketPath)
	if pid > 0 {
		st.Running = true
		st.PID = pid
		st.RSSKB = readProcRSSKB(pid)
	}

	// Проверяем реальный отклик демона по Unix-сокету.
	if pingResp, err := CallUnix(cfg.SocketPath, core.Request{Tool: "ping", Caller: "status"}, 2*time.Second); err == nil && pingResp.OK {
		st.SocketOK = true
		st.Running = true
		var data map[string]any
		if json.Unmarshal(pingResp.Data, &data) == nil {
			if up, ok := data["uptime"].(string); ok {
				st.Uptime = up
			}
			if ver, ok := data["version"].(string); ok {
				st.Version = ver
			}
		}
		if verResp, vErr := CallUnix(cfg.SocketPath, core.Request{Tool: "version", Caller: "status"}, 2*time.Second); vErr == nil && verResp.OK {
			var vData map[string]any
			if json.Unmarshal(verResp.Data, &vData) == nil {
				if mode, ok := vData["policy_mode"].(string); ok {
					st.PolicyMode = mode
				}
				if audit, ok := vData["audit_path"].(string); ok {
					st.AuditPath = audit
				}
			}
		}
	}

	return st
}

// StartDaemon запускает sysagentd в фоновом режиме (отвязанным от терминала) и ждёт готовности сокета.
func StartDaemon(cfg config.Config, cfgPath string) (DaemonStatus, bool, error) {
	if up, _ := IsRunningFast(cfg); up {
		st := GetStatus(cfg)
		if st.Running && st.SocketOK {
			return st, true, nil
		}
	}

	exePath, err := os.Executable()
	if err != nil {
		return DaemonStatus{}, false, fmt.Errorf("не удалось определить путь к исполняемому файлу: %w", err)
	}

	pidFile := PIDPath(cfg)
	logFile := DaemonLogPath(cfg)

	if err := os.MkdirAll(filepath.Dir(pidFile), 0o750); err != nil {
		return DaemonStatus{}, false, fmt.Errorf("создание каталога PID %s: %w", filepath.Dir(pidFile), err)
	}
	if err := os.MkdirAll(filepath.Dir(logFile), 0o750); err != nil {
		return DaemonStatus{}, false, fmt.Errorf("создание каталога логов %s: %w", filepath.Dir(logFile), err)
	}

	lf, err := os.OpenFile(logFile, os.O_CREATE|os.O_APPEND|os.O_WRONLY, 0o640)
	if err != nil {
		return DaemonStatus{}, false, fmt.Errorf("открытие лог-файла демона %s: %w", logFile, err)
	}
	defer lf.Close()

	daemonArgs := []string{"daemon", "--socket", cfg.SocketPath, "--mode", cfg.Policy.Mode}
	if strings.TrimSpace(cfgPath) != "" {
		daemonArgs = append(daemonArgs, "--config", cfgPath)
	}

	cmd := exec.Command(exePath, daemonArgs...)
	cmd.Stdout = lf
	cmd.Stderr = lf
	cmd.Stdin = nil
	cmd.Env = append(os.Environ(), "SYSAGENTD_AUDIT="+cfg.Audit.Path)
	// Отвязываем дочерний процесс в собственную сессию, чтобы закрытие SSH не останавливало демона.
	cmd.SysProcAttr = &syscall.SysProcAttr{Setsid: true}

	if err := cmd.Start(); err != nil {
		return DaemonStatus{}, false, fmt.Errorf("ошибка запуска фонового процесса: %w", err)
	}

	pid := cmd.Process.Pid
	_ = os.WriteFile(pidFile, []byte(strconv.Itoa(pid)+"\n"), 0o640)

	// Снимаем код завершения в фоне, если родительская консоль остаётся открытой (защита от zombie-процессов).
	go func() {
		_ = cmd.Wait()
	}()

	// Ждём фактического поднятия Unix-сокета (до 3 секунд).
	deadline := time.Now().Add(3 * time.Second)
	for time.Now().Before(deadline) {
		if _, statErr := os.Stat(cfg.SocketPath); statErr == nil {
			st := GetStatus(cfg)
			if st.Running && st.SocketOK {
				return st, false, nil
			}
		}
		if !isProcessAlive(pid) {
			break
		}
		time.Sleep(50 * time.Millisecond)
	}

	tail := strings.Join(ReadTailLines(logFile, 5), "\n")
	return DaemonStatus{}, false, fmt.Errorf("демон не вышел на связь по сокету %s; последние строки лога:\n%s", cfg.SocketPath, tail)
}

// StopDaemon штатно завершает работающего демона сигналом SIGTERM и ждёт остановки.
func StopDaemon(cfg config.Config) (int, bool, error) {
	pidFile := PIDPath(cfg)
	pid := resolveRunningPID(pidFile, cfg.SocketPath)
	if pid <= 0 {
		_ = os.Remove(pidFile)
		return 0, false, nil
	}

	if err := syscall.Kill(pid, syscall.SIGTERM); err != nil && !errors.Is(err, syscall.ESRCH) {
		return pid, true, fmt.Errorf("не удалось отправить SIGTERM процессу %d: %w", pid, err)
	}

	deadline := time.Now().Add(5 * time.Second)
	for time.Now().Before(deadline) {
		if !isProcessAlive(pid) {
			_ = os.Remove(pidFile)
			_ = os.Remove(cfg.SocketPath)
			return pid, true, nil
		}
		time.Sleep(50 * time.Millisecond)
	}

	return pid, true, fmt.Errorf("процесс %d не завершился за 5 секунд", pid)
}

// RestartDaemon выполняет штатную остановку и чистый запуск демона.
func RestartDaemon(cfg config.Config, cfgPath string) (int, DaemonStatus, error) {
	oldPID, _, err := StopDaemon(cfg)
	if err != nil {
		return oldPID, DaemonStatus{}, err
	}
	st, _, startErr := StartDaemon(cfg, cfgPath)
	return oldPID, st, startErr
}

// ReadTailLines читает последние n непустых строк текстового файла (аудит или лог демона).
func ReadTailLines(path string, n int) []string {
	if n <= 0 {
		n = 10
	}
	f, err := os.Open(path)
	if err != nil {
		return nil
	}
	defer f.Close()

	var lines []string
	scanner := bufio.NewScanner(f)
	for scanner.Scan() {
		line := strings.TrimSpace(scanner.Text())
		if line != "" {
			lines = append(lines, line)
		}
	}
	if len(lines) > n {
		lines = lines[len(lines)-n:]
	}
	return lines
}

func resolveRunningPID(pidFile, socketPath string) int {
	if raw, err := os.ReadFile(pidFile); err == nil {
		if pid, convErr := strconv.Atoi(strings.TrimSpace(string(raw))); convErr == nil && pid > 1 {
			if isSysagentDaemonPID(pid) {
				return pid
			}
		}
	}
	return scanProcForDaemon(socketPath)
}

// isProcessAlive проверяет, что процесс существует и не находится в состоянии zombie (Z).
func isProcessAlive(pid int) bool {
	if pid <= 1 {
		return false
	}
	if syscall.Kill(pid, 0) != nil {
		return false
	}
	raw, err := os.ReadFile(fmt.Sprintf("/proc/%d/status", pid))
	if err != nil {
		return false
	}
	for _, line := range strings.Split(string(raw), "\n") {
		if strings.HasPrefix(line, "State:") && strings.Contains(line, "\tZ") {
			return false
		}
	}
	return true
}

func isSysagentDaemonPID(pid int) bool {
	if !isProcessAlive(pid) {
		return false
	}
	raw, err := os.ReadFile(fmt.Sprintf("/proc/%d/cmdline", pid))
	if err != nil || len(raw) == 0 {
		return false
	}
	parts := bytes.Split(bytes.TrimRight(raw, "\x00"), []byte{0})
	if len(parts) < 2 {
		return false
	}
	exeBase := filepath.Base(string(parts[0]))
	return strings.Contains(exeBase, "sysagent") && string(parts[1]) == "daemon"
}

func scanProcForDaemon(socketPath string) int {
	entries, err := os.ReadDir("/proc")
	if err != nil {
		return 0
	}
	selfPID := os.Getpid()
	for _, entry := range entries {
		if !entry.IsDir() {
			continue
		}
		pid, convErr := strconv.Atoi(entry.Name())
		if convErr != nil || pid <= 1 || pid == selfPID {
			continue
		}
		if !isSysagentDaemonPID(pid) {
			continue
		}
		raw, readErr := os.ReadFile(fmt.Sprintf("/proc/%d/cmdline", pid))
		if readErr != nil {
			continue
		}
		cmdStr := strings.ReplaceAll(string(raw), "\x00", " ")
		if socketPath == "" || strings.Contains(cmdStr, socketPath) || !strings.Contains(cmdStr, "--socket") {
			return pid
		}
	}
	return 0
}

func readProcRSSKB(pid int) int64 {
	raw, err := os.ReadFile(fmt.Sprintf("/proc/%d/status", pid))
	if err != nil {
		return 0
	}
	for _, line := range strings.Split(string(raw), "\n") {
		if strings.HasPrefix(line, "VmRSS:") {
			fields := strings.Fields(line)
			if len(fields) >= 2 {
				val, convErr := strconv.ParseInt(fields[1], 10, 64)
				if convErr == nil {
					return val
				}
			}
		}
	}
	return 0
}
EOF
cd /opt/sysagent && go build ./internal/ipc && echo "control: OK"
