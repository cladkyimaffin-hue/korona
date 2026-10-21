### Зачем нужен этот файл:
Любое обращение к агенту (и разрешённое, и отклонённое политикой) дописывается отдельной строкой в файл /var/log/sysagentd/audit.jsonl.

-  Защищён мьютексом (безопасен при одновременных запросах).
-  Автоматически маскирует секреты: если параметр содержит слова password, token, secret, key и т.п., в журнал записывается "****".

  cat <<'EOF' > /opt/sysagent/internal/core/audit.go
package core

import (
	"encoding/json"
	"os"
	"path/filepath"
	"strings"
	"sync"
	"time"
)

// AuditRecord представляет одну запись в журнале аудита audit.jsonl.
type AuditRecord struct {
	Timestamp  string            `json:"ts"`
	PID        int               `json:"pid"`
	Caller     string            `json:"caller,omitempty"`
	Tool       string            `json:"tool"`
	Module     string            `json:"module,omitempty"`
	Risk       RiskLevel         `json:"risk,omitempty"`
	Args       map[string]string `json:"args,omitempty"`
	Allowed    bool              `json:"allowed"`
	OK         bool              `json:"ok"`
	Reason     string            `json:"reason,omitempty"`
	Error      string            `json:"error,omitempty"`
	DurationMs int64             `json:"duration_ms"`
}

// Auditor потокобезопасно записывает события аудита в файл JSON Lines.
type Auditor struct {
	path string
	mu   sync.Mutex
}

// NewAuditor создаёт экземпляр журнала аудита по указанному пути.
func NewAuditor(path string) *Auditor {
	return &Auditor{path: path}
}

// Path возвращает путь к файлу журнала аудита.
func (a *Auditor) Path() string {
	return a.path
}

// Write добавляет одну JSON-строку в журнал аудита с автоматическим маскированием секретов.
func (a *Auditor) Write(rec AuditRecord) error {
	if a == nil || strings.TrimSpace(a.path) == "" {
		return nil
	}
	rec.Timestamp = time.Now().Format(time.RFC3339)
	rec.PID = os.Getpid()
	rec.Args = RedactArgs(rec.Args)

	line, err := json.Marshal(rec)
	if err != nil {
		return err
	}

	a.mu.Lock()
	defer a.mu.Unlock()

	if mkErr := os.MkdirAll(filepath.Dir(a.path), 0o750); mkErr != nil {
		return mkErr
	}
	f, openErr := os.OpenFile(a.path, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0o640)
	if openErr != nil {
		return openErr
	}
	defer f.Close()

	_, writeErr := f.Write(append(line, '\n'))
	return writeErr
}

// RedactArgs маскирует любые аргументы, имена которых могут содержать секреты.
func RedactArgs(args map[string]string) map[string]string {
	if len(args) == 0 {
		return nil
	}
	out := make(map[string]string, len(args))
	for k, v := range args {
		if isSensitiveKey(k) {
			out[k] = "****"
		} else {
			out[k] = v
		}
	}
	return out
}

func isSensitiveKey(key string) bool {
	lower := strings.ToLower(strings.TrimSpace(key))
	sensitiveTokens := []string{
		"password", "passwd", "secret", "token", "apikey", "api_key",
		"private_key", "key", "auth", "credential",
	}
	for _, tok := range sensitiveTokens {
		if strings.Contains(lower, tok) {
			return true
		}
	}
	return false
}
EOF
cd /opt/sysagent && go build ./internal/core && echo "audit: OK"
