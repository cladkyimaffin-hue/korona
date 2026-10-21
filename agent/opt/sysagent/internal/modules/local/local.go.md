### Шаг 16 — Создаём и подключаем первый модуль функций internal/modules/local
Этот модуль даёт и вам, и будущей ИИ-модели «глаза и руки» на Linux-сервере:

-  local.summary (read) — хост, ОС, ядро, uptime, нагрузка CPU, RAM/Swap, диски;
-  local.logs (read) — ошибки из journalctl со склейкой дубликатов (чтобы не сжигать лимиты бесплатных моделей повторами);
-  local.failed (read) — список упавших служб systemd;
-  local.unit (read) — подробный статус конкретной службы и хвост её журнала;
-  local.netping (read) — безопасная проверка DNS + 3 пакета ping (без shell);
-  local.service_restart (write) — перезапуск некритичной службы строго через подтверждение [y/N], причём ssh и сетевые службы жёстко защищены от случайного обрыва доступа.

  mkdir -p /opt/sysagent/internal/modules/local
cat <<'EOF' > /opt/sysagent/internal/modules/local/local.go
// Пакет local реализует модуль локальной диагностики Linux-сервера:
//   - local.summary         (read)  — сводка хоста: ОС, ядро, uptime, CPU load, RAM/Swap, диски;
//   - local.logs            (read)  — ошибки из journalctl со склейкой повторов (экономия токенов ИИ);
//   - local.failed          (read)  — список упавших служб systemd;
//   - local.unit            (read)  — подробный статус конкретной службы systemd;
//   - local.netping         (read)  — безопасная проверка DNS и ICMP ping узла (без shell);
//   - local.service_restart (write) — перезапуск службы systemd (только после подтверждения [y/N],
//                                     с жёсткой защитой от обрыва SSH и сети).
package local

import (
	"bufio"
	"context"
	"fmt"
	"net"
	"os"
	"os/exec"
	"regexp"
	"runtime"
	"sort"
	"strconv"
	"strings"
	"syscall"
	"time"

	"sysagent/internal/core"
)

var (
	validUnitRe = regexp.MustCompile(`^[a-zA-Z0-9_.@-]{1,128}$`)
	validHostRe = regexp.MustCompile(`^[a-zA-Z0-9._:-]{1,253}$`)
	validSpanRe = regexp.MustCompile(`^-[0-9]{1,4}[smhdw]$`)

	// Службы, перезапуск которых запрещён удалённо во избежание потери SSH/сети.
	protectedUnits = map[string]bool{
		"ssh.service":              true,
		"sshd.service":             true,
		"networking.service":       true,
		"systemd-networkd.service": true,
		"NetworkManager.service":   true,
		"ifup@ens18.service":       true,
		"sysagentd.service":        true,
	}
)

// Module — подключаемый модуль локальной диагностики Linux.
type Module struct{}

// New создаёт экземпляр модуля local.
func New() *Module { return &Module{} }

func (m *Module) Name() string { return "local" }

func (m *Module) Description() string {
	return "Локальная диагностика Linux-хоста (ресурсы, диски, службы systemd, журнал ошибок, сеть)"
}

func (m *Module) Tools() []core.Tool {
	return []core.Tool{
		core.FuncTool{
			ToolSpec: core.ToolSpec{
				Name:        "local.summary",
				Module:      "local",
				Description: "Полная сводка по локальному серверу: hostname, ОС, ядро, uptime, нагрузка CPU, память RAM/Swap и заполнение дисков.",
				Risk:        core.RiskRead,
			},
			Handler: runSummary,
		},
		core.FuncTool{
			ToolSpec: core.ToolSpec{
				Name:        "local.logs",
				Module:      "local",
				Description: "Последние ошибки и критические записи из системного журнала journalctl со склейкой дубликатов.",
				Risk:        core.RiskRead,
				Params: []core.ParamSpec{
					{Name: "since", Description: "Интервал времени в формате -15m, -1h, -24h (по умолчанию -1h)", Required: false},
					{Name: "unit", Description: "Необязательный фильтр по имени службы systemd (например cron.service)", Required: false},
				},
			},
			Handler: runLogs,
		},
		core.FuncTool{
			ToolSpec: core.ToolSpec{
				Name:        "local.failed",
				Module:      "local",
				Description: "Список упавших (failed) юнитов systemd.",
				Risk:        core.RiskRead,
			},
			Handler: runFailed,
		},
		core.FuncTool{
			ToolSpec: core.ToolSpec{
				Name:        "local.unit",
				Module:      "local",
				Description: "Подробное состояние конкретной службы systemd и последние строки её журнала.",
				Risk:        core.RiskRead,
				Params: []core.ParamSpec{
					{Name: "unit", Description: "Имя службы systemd, например ssh.service или cron.service", Required: true},
				},
			},
			Handler: runUnitStatus,
		},
		core.FuncTool{
			ToolSpec: core.ToolSpec{
				Name:        "local.netping",
				Module:      "local",
				Description: "Безопасная проверка DNS-разрешения и сетевой доступности (3 пакета ping) указанного хоста или IP.",
				Risk:        core.RiskRead,
				Params: []core.ParamSpec{
					{Name: "host", Description: "Доменное имя или IP-адрес узла, например 192.168.200.1 или deb.debian.org", Required: true},
				},
			},
			Handler: runNetPing,
		},
		core.FuncTool{
			ToolSpec: core.ToolSpec{
				Name:        "local.service_restart",
				Module:      "local",
				Description: "Штатный перезапуск некритичной службы systemd (требует подтверждения администратора; SSH и сеть защищены от обрыва).",
				Risk:        core.RiskWrite,
				Params: []core.ParamSpec{
					{Name: "unit", Description: "Имя перезапускаемой службы systemd, например cron.service", Required: true},
				},
			},
			Handler: runServiceRestart,
		},
	}
}

func normalizeUnit(raw string) (string, error) {
	u := strings.TrimSpace(raw)
	if u == "" || strings.HasPrefix(u, "-") || !validUnitRe.MatchString(u) {
		return "", fmt.Errorf("недопустимое имя службы %q", raw)
	}
	if !strings.Contains(u, ".") {
		u += ".service"
	}
	return u, nil
}

func runSummary(_ context.Context, _ map[string]string) (any, error) {
	host, _ := os.Hostname()
	osName := readOSRelease()
	kernel := readTrimmedFile("/proc/sys/kernel/osrelease")
	uptimeSec, uptimeHuman := readUptime()
	load1, load5, load15 := readLoadAvg()
	mem := readMemInfo()
	disks := readDisks([]string{"/", "/var"})

	return map[string]any{
		"hostname":     host,
		"os":           osName,
		"kernel":       kernel,
		"cpu_cores":    runtime.NumCPU(),
		"uptime_sec":   uptimeSec,
		"uptime_human": uptimeHuman,
		"load_avg": map[string]float64{
			"1m":  load1,
			"5m":  load5,
			"15m": load15,
		},
		"memory_mb": mem,
		"disks":     disks,
	}, nil
}

func readOSRelease() string {
	f, err := os.Open("/etc/os-release")
	if err != nil {
		return runtime.GOOS
	}
	defer f.Close()
	sc := bufio.NewScanner(f)
	for sc.Scan() {
		line := sc.Text()
		if strings.HasPrefix(line, "PRETTY_NAME=") {
			return strings.Trim(strings.TrimPrefix(line, "PRETTY_NAME="), `"'`)
		}
	}
	return runtime.GOOS
}

func readTrimmedFile(path string) string {
	b, err := os.ReadFile(path)
	if err != nil {
		return "unknown"
	}
	return strings.TrimSpace(string(b))
}

func readUptime() (int64, string) {
	raw := readTrimmedFile("/proc/uptime")
	fields := strings.Fields(raw)
	if len(fields) == 0 {
		return 0, "unknown"
	}
	secFloat, err := strconv.ParseFloat(fields[0], 64)
	if err != nil {
		return 0, "unknown"
	}
	sec := int64(secFloat)
	return sec, (time.Duration(sec) * time.Second).String()
}

func readLoadAvg() (float64, float64, float64) {
	fields := strings.Fields(readTrimmedFile("/proc/loadavg"))
	if len(fields) < 3 {
		return 0, 0, 0
	}
	l1, _ := strconv.ParseFloat(fields[0], 64)
	l5, _ := strconv.ParseFloat(fields[1], 64)
	l15, _ := strconv.ParseFloat(fields[2], 64)
	return l1, l5, l15
}

func readMemInfo() map[string]any {
	vals := make(map[string]uint64)
	f, err := os.Open("/proc/meminfo")
	if err == nil {
		defer f.Close()
		sc := bufio.NewScanner(f)
		for sc.Scan() {
			parts := strings.Fields(sc.Text())
			if len(parts) >= 2 {
				key := strings.TrimSuffix(parts[0], ":")
				v, err := strconv.ParseUint(parts[1], 10, 64)
				if err == nil {
					vals[key] = v
				}
			}
		}
	}
	totalMB := vals["MemTotal"] / 1024
	availMB := vals["MemAvailable"] / 1024
	var usedMB uint64
	if totalMB > availMB {
		usedMB = totalMB - availMB
	}
	var usedPct float64
	if totalMB > 0 {
		usedPct = float64(usedMB*1000/totalMB) / 10.0
	}
	return map[string]any{
		"total_mb":     totalMB,
		"used_mb":      usedMB,
		"available_mb": availMB,
		"used_percent": usedPct,
		"swap_total":   vals["SwapTotal"] / 1024,
		"swap_free":    vals["SwapFree"] / 1024,
	}
}

func readDisks(paths []string) []map[string]any {
	seenDev := make(map[uint64]bool)
	var out []map[string]any
	for _, p := range paths {
		fi, err := os.Stat(p)
		if err != nil {
			continue
		}
		if st, ok := fi.Sys().(*syscall.Stat_t); ok {
			if seenDev[uint64(st.Dev)] {
				continue
			}
			seenDev[uint64(st.Dev)] = true
		}
		var fs syscall.Statfs_t
		if err := syscall.Statfs(p, &fs); err != nil || fs.Blocks == 0 {
			continue
		}
		totalBytes := fs.Blocks * uint64(fs.Bsize)
		availBytes := fs.Bavail * uint64(fs.Bsize)
		usedBytes := totalBytes - (fs.Bfree * uint64(fs.Bsize))
		pct := float64(usedBytes*1000/totalBytes) / 10.0
		out = append(out, map[string]any{
			"mount":        p,
			"total_gb":     float64(totalBytes/(1024*1024*102)) / 10.0,
			"used_gb":      float64(usedBytes/(1024*1024*102)) / 10.0,
			"available_gb": float64(availBytes/(1024*1024*102)) / 10.0,
			"used_percent": pct,
		})
	}
	return out
}

func runLogs(ctx context.Context, args map[string]string) (any, error) {
	since := strings.TrimSpace(args["since"])
	if since == "" {
		since = "-1h"
	}
	if !validSpanRe.MatchString(since) {
		return nil, fmt.Errorf("параметр since должен иметь вид -15m, -1h, -24h (получено %q)", since)
	}

	cmdArgs := []string{"-p", "err..alert", "--no-pager", "-n", "200", "--since", since}
	if rawUnit := strings.TrimSpace(args["unit"]); rawUnit != "" {
		u, err := normalizeUnit(rawUnit)
		if err != nil {
			return nil, err
		}
		cmdArgs = append(cmdArgs, "-u", u)
	}

	out, err := exec.CommandContext(ctx, "journalctl", cmdArgs...).CombinedOutput()
	if err != nil && len(out) == 0 {
		return nil, fmt.Errorf("ошибка чтения journalctl: %w", err)
	}

	type grouped struct {
		Message string `json:"message"`
		Count   int    `json:"count"`
	}
	counts := make(map[string]int)
	var order []string
	totalRaw := 0

	for _, rawLine := range strings.Split(string(out), "\n") {
		line := strings.TrimSpace(rawLine)
		if line == "" || strings.HasPrefix(line, "-- ") {
			continue
		}
		totalRaw++
		normalized := scrubLogLine(stripJournalPrefix(line))
		if counts[normalized] == 0 {
			order = append(order, normalized)
		}
		counts[normalized]++
	}

	items := make([]grouped, 0, len(order))
	for _, msg := range order {
		items = append(items, grouped{Message: msg, Count: counts[msg]})
	}
	sort.Slice(items, func(i, j int) bool { return items[i].Count > items[j].Count })
	if len(items) > 25 {
		items = items[:25]
	}

	return map[string]any{
		"since":          since,
		"total_raw_rows": totalRaw,
		"unique_errors":  len(order),
		"entries":        items,
	}, nil
}

func stripJournalPrefix(line string) string {
	idx := strings.Index(line, ": ")
	if idx > 0 && idx < 80 {
		return line[idx+2:]
	}
	return line
}

func runFailed(ctx context.Context, _ map[string]string) (any, error) {
	out, err := exec.CommandContext(ctx, "systemctl", "--failed", "--no-legend", "--no-pager", "--plain").CombinedOutput()
	if err != nil && len(out) == 0 {
		return nil, fmt.Errorf("ошибка вызова systemctl: %w", err)
	}

	var failed []map[string]string
	for _, raw := range strings.Split(string(out), "\n") {
		fields := strings.Fields(raw)
		if len(fields) >= 4 {
			failed = append(failed, map[string]string{
				"unit":        fields[0],
				"load":        fields[1],
				"active":      fields[2],
				"sub":         fields[3],
				"description": strings.Join(fields[4:], " "),
			})
		}
	}
	return map[string]any{
		"healthy":      len(failed) == 0,
		"failed_count": len(failed),
		"units":        failed,
	}, nil
}

func runUnitStatus(ctx context.Context, args map[string]string) (any, error) {
	unit, err := normalizeUnit(args["unit"])
	if err != nil {
		return nil, err
	}

	propsOut, err := exec.CommandContext(
		ctx,
		"systemctl", "show", unit,
		"--no-pager",
		"--property=Id,Description,LoadState,ActiveState,SubState,MainPID,NRestarts,ActiveEnterTimestamp",
	).CombinedOutput()
	if err != nil {
		return nil, fmt.Errorf("ошибка чтения статуса %s: %w", unit, err)
	}

	props := make(map[string]string)
	for _, line := range strings.Split(string(propsOut), "\n") {
		idx := strings.IndexByte(line, '=')
		if idx > 0 {
			props[line[:idx]] = strings.TrimSpace(line[idx+1:])
		}
	}

	logOut, _ := exec.CommandContext(ctx, "journalctl", "-u", unit, "-n", "8", "--no-pager").CombinedOutput()
	var tail []string
	for _, ln := range strings.Split(string(logOut), "\n") {
		ln = strings.TrimSpace(ln)
		if ln != "" && !strings.HasPrefix(ln, "-- ") {
			tail = append(tail, scrubLogLine(ln))
		}
	}

	return map[string]any{
		"unit":        unit,
		"status":      props,
		"recent_logs": tail,
	}, nil
}

var secretKVRe = regexp.MustCompile(`(?i)(password|passwd|secret|token|apikey|api_key|bearer)(\s*[:=]\s*|\s+)\S+`)

func scrubLogLine(s string) string {
	return secretKVRe.ReplaceAllString(s, "$1$2****")
}

func runNetPing(ctx context.Context, args map[string]string) (any, error) {
	host := strings.TrimSpace(args["host"])
	if host == "" || strings.HasPrefix(host, "-") || !validHostRe.MatchString(host) {
		return nil, fmt.Errorf("недопустимое имя узла или IP %q", args["host"])
	}

	ips, dnsErr := net.DefaultResolver.LookupHost(ctx, host)
	dnsOK := dnsErr == nil && len(ips) > 0

	out, pingErr := exec.CommandContext(ctx, "ping", "-n", "-c", "3", "-W", "2", "--", host).CombinedOutput()
	summaryLines := []string{}
	for _, ln := range strings.Split(string(out), "\n") {
		ln = strings.TrimSpace(ln)
		if strings.Contains(ln, "packets transmitted") || strings.Contains(ln, "rtt ") || strings.Contains(ln, "round-trip") {
			summaryLines = append(summaryLines, ln)
		}
	}

	res := map[string]any{
		"host":         host,
		"dns_resolved": dnsOK,
		"resolved_ips": ips,
		"ping_ok":      pingErr == nil,
		"summary":      summaryLines,
	}
	if dnsErr != nil {
		res["dns_error"] = dnsErr.Error()
	}
	return res, nil
}

func runServiceRestart(ctx context.Context, args map[string]string) (any, error) {
	unit, err := normalizeUnit(args["unit"])
	if err != nil {
		return nil, err
	}
	if protectedUnits[unit] {
		return nil, fmt.Errorf("перезапуск критичной сетевой/системной службы %s заблокирован защитой от потери доступа", unit)
	}

	out, err := exec.CommandContext(ctx, "systemctl", "restart", unit).CombinedOutput()
	if err != nil {
		return nil, fmt.Errorf("ошибка перезапуска %s: %v (%s)", unit, err, strings.TrimSpace(string(out)))
	}

	stateOut, _ := exec.CommandContext(ctx, "systemctl", "is-active", unit).CombinedOutput()
	return map[string]any{
		"restarted":    true,
		"unit":         unit,
		"active_state": strings.TrimSpace(string(stateOut)),
	}, nil
}
EOF
