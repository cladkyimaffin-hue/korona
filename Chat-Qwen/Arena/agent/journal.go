package main

import (
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"regexp"
	"runtime"
	"strconv"
	"strings"
	"time"
)

const Version = "0.1.0"

var startedAt = time.Now()

// ---------------------------------------------------------------------------
// политика: тот же принцип, что в Python-версии, но короче.
// Разрешено только то, что явно перечислено. Без shell.
// ---------------------------------------------------------------------------

type Policy struct {
	Mode           string // readonly | ask | auto
	AllowDangerous bool
}

var readOnlyTools = map[string]bool{
	"journalctl": true, "systemctl": true, "df": true, "free": true, "ps": true,
	"tail": true, "dmesg": true, "ss": true, "ip": true, "uptime": true,
}

// RunReadOnly запускает команду из фиксированного списка (без shell, без пайпов).
func RunReadOnly(name string, args ...string) (map[string]any, error) {
	if !readOnlyTools[name] {
		return nil, fmt.Errorf("программа %q не разрешена политикой", name)
	}
	for _, a := range args {
		if strings.ContainsAny(a, ";|&$`><\n") {
			return nil, fmt.Errorf("недопустимые символы в аргументе: %q", a)
		}
	}
	out, err := exec.Command(name, args...).CombinedOutput()
	code := 0
	if err != nil {
		if ee, ok := err.(*exec.ExitError); ok {
			code = ee.ExitCode()
		} else {
			return nil, err
		}
	}
	limit := 20000
	text := string(out)
	truncated := false
	if len(text) > limit {
		text, truncated = text[:limit], true
	}
	return map[string]any{
		"command": name + " " + strings.Join(args, " "),
		"output":  text, "exit_code": code, "truncated": truncated,
	}, nil
}

// ---------------------------------------------------------------------------
// журнал
// ---------------------------------------------------------------------------

var unitName = regexp.MustCompile(`^[A-Za-z0-9@._:\\-]+$`)

type Group struct {
	Unit    string `json:"unit"`
	Message string `json:"message"`
	Count   int    `json:"count"`
	First   string `json:"first"`
	Last    string `json:"last"`
}

func JournalErrors(unit, since string, limit int, p *Policy) (any, error) {
	if _, err := exec.LookPath("journalctl"); err != nil {
		return nil, fmt.Errorf("journalctl не найден (не systemd-система?)")
	}
	if since == "" {
		since = "-1h"
	}
	if limit <= 0 || limit > 2000 {
		limit = 200
	}
	args := []string{"--no-pager", "-o", "json", "-p", "err", "--since", since, "-n", strconv.Itoa(limit)}
	if unit != "" {
		if !unitName.MatchString(unit) {
			return nil, fmt.Errorf("некорректное имя юнита")
		}
		args = append([]string{"-u", unit}, args...)
	}
	if p.Mode != "readonly" && p.Mode != "ask" && p.Mode != "auto" {
		return nil, fmt.Errorf("неизвестный режим политики %q", p.Mode)
	}

	res, err := RunReadOnly("journalctl", args...)
	if err != nil {
		return nil, err
	}
	output, _ := res["output"].(string)
	if code, _ := res["exit_code"].(int); code != 0 && strings.TrimSpace(output) == "" {
		return nil, fmt.Errorf("journalctl вернул код %d", code)
	}

	var groups []Group
	index := map[string]*Group{}
	total := 0
	for _, line := range strings.Split(output, "\n") {
		line = strings.TrimSpace(line)
		if line == "" {
			continue
		}
		var entry struct {
			Message  any    `json:"MESSAGE"`
			Unit     string `json:"_SYSTEMD_UNIT"`
			Ident    string `json:"SYSLOG_IDENTIFIER"`
			Realtime string `json:"__REALTIME_TIMESTAMP"`
		}
		if err := json.Unmarshal([]byte(line), &entry); err != nil {
			continue
		}
		total++
		u := entry.Unit
		if u == "" {
			u = entry.Ident
		}
		if u == "" {
			u = "?"
		}
		msg := normalizeMessage(fmt.Sprint(entry.Message))
		ts := formatMicro(entry.Realtime)
		key := u + "|" + msg
		if g, ok := index[key]; ok {
			g.Count++
			g.Last = ts
		} else {
			index[key] = &Group{Unit: u, Message: msg, Count: 1, First: ts, Last: ts}
		}
	}
	for _, g := range index {
		groups = append(groups, *g)
	}
	// сортировка: сначала самые частые
	for i := 0; i < len(groups); i++ {
		for j := i + 1; j < len(groups); j++ {
			if groups[j].Count > groups[i].Count {
				groups[i], groups[j] = groups[j], groups[i]
			}
		}
	}
	if len(groups) > 25 {
		groups = groups[:25]
	}
	return map[string]any{"since": since, "unit": unit, "total_events": total, "groups": groups}, nil
}

var (
	reHex  = regexp.MustCompile(`\b0x[0-9a-fA-F]{6,}\b`)
	reUUID = regexp.MustCompile(`\b[0-9a-f]{8,}-[0-9a-f\-]{8,}\b`)
	reNum  = regexp.MustCompile(`\b\d{2,}\b`)
)

// normalizeMessage убирает избыточную энтропию, чтобы одинаковые ошибки
// действительно склеивались: адреса, uuid, длинные числа -> плейсхолдеры.
func normalizeMessage(s string) string {
	s = reHex.ReplaceAllString(s, "<addr>")
	s = reUUID.ReplaceAllString(s, "<uuid>")
	s = reNum.ReplaceAllString(s, "<n>")
	s = strings.Join(strings.Fields(s), " ")
	if len(s) > 400 {
		s = s[:400]
	}
	return s
}

func formatMicro(micro string) string {
	us, err := strconv.ParseInt(micro, 10, 64)
	if err != nil {
		return "?"
	}
	return time.Unix(0, us*1000).Format("2006-01-02 15:04:05")
}

// ---------------------------------------------------------------------------
// службы
// ---------------------------------------------------------------------------

func FailedUnits(p *Policy) (any, error) {
	res, err := RunReadOnly("systemctl", "list-units", "--state=failed", "--no-pager", "--plain", "--no-legend")
	if err != nil {
		return nil, err
	}
	output, _ := res["output"].(string)
	var units []string
	for _, line := range strings.Split(output, "\n") {
		line = strings.TrimSpace(line)
		if line == "" {
			continue
		}
		units = append(units, strings.Fields(line)[0])
	}
	return map[string]any{"failed_count": len(units), "units": units}, nil
}

func UnitStatus(unit string, p *Policy) (any, error) {
	if !unitName.MatchString(unit) {
		return nil, fmt.Errorf("некорректное имя юнита")
	}
	res, err := RunReadOnly("systemctl", "status", unit, "--no-pager", "-l")
	if err != nil {
		return nil, err
	}
	return res, nil
}

// ---------------------------------------------------------------------------
// аудит: JSON-lines, только на запись
// ---------------------------------------------------------------------------

func Audit(record map[string]any) {
	path := os.Getenv("SYSAGENTD_AUDIT")
	if path == "" {
		path = "/var/log/sysagentd/audit.jsonl"
	}
	if home, err := os.UserHomeDir(); err == nil && os.Getenv("SYSAGENTD_AUDIT") == "" {
		if _, statErr := os.Stat("/var/log/sysagentd"); statErr != nil {
			path = filepath.Join(home, ".local/state/sysagentd/audit.jsonl")
		}
	}
	_ = os.MkdirAll(filepath.Dir(path), 0o750)
	f, err := os.OpenFile(path, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0o640)
	if err != nil {
		return
	}
	defer f.Close()
	record["ts"] = time.Now().Format(time.RFC3339)
	record["pid"] = os.Getpid()
	line, _ := json.Marshal(record)
	_, _ = f.Write(append(line, '\n'))
}

func goVersion() string { return runtime.Version() }

func truncate(s string, n int) string {
	if len(s) <= n {
		return s
	}
	return s[:n] + "…"
}
