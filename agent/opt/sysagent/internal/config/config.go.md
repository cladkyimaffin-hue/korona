###Зачем нужен этот файл:
Он отвечает за загрузку и проверку настроек агента (путь к сокету, режим политики readonly / ask / auto, таймаут команд, путь к журналу аудита).

По умолчанию жёстко включает безопасный режим readonly.
Позволяет писать обычные человеческие комментарии (// и #) внутри файла настроек.
Скопируйте и выполните этот блок целиком на root@agent (он запишет файл и сразу проверит его компилятором Go):



cat <<'EOF' > /opt/sysagent/internal/config/config.go
// Пакет config отвечает за чтение, разбор и валидацию конфигурации агента.
// Поддерживается формат JSON с однострочными комментариями (// и #),
// чтобы не тянуть внешние зависимости ради конфигурационного файла.
package config

import (
	"bytes"
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"strings"
)

const (
	ModeReadOnly = "readonly"
	ModeAsk      = "ask"
	ModeAuto     = "auto"

	DefaultSocketPath = "/run/sysagentd/sysagentd.sock"
	DefaultAuditPath  = "/var/log/sysagentd/audit.jsonl"
)

// PolicyConfig задаёт ограничения безопасности ядра.
type PolicyConfig struct {
	Mode              string   `json:"mode"`
	AllowDangerous    bool     `json:"allow_dangerous"`
	DisabledTools     []string `json:"disabled_tools"`
	CommandTimeoutSec int      `json:"command_timeout_sec"`
	MaxOutputBytes    int      `json:"max_output_bytes"`
}

// AuditConfig задаёт параметры журнала аудита.
type AuditConfig struct {
	Path string `json:"path"`
}

// Config объединяет все настройки ядра sysagentd.
type Config struct {
	SocketPath string       `json:"socket_path"`
	Policy     PolicyConfig `json:"policy"`
	Audit      AuditConfig  `json:"audit"`
	SourcePath string       `json:"-"`
}

// Default возвращает безопасную конфигурацию по умолчанию (строгий readonly).
func Default() Config {
	auditPath := DefaultAuditPath
	if home, err := os.UserHomeDir(); err == nil {
		if _, statErr := os.Stat(filepath.Dir(DefaultAuditPath)); statErr != nil {
			auditPath = filepath.Join(home, ".local", "state", "sysagentd", "audit.jsonl")
		}
	}
	return Config{
		SocketPath: DefaultSocketPath,
		Policy: PolicyConfig{
			Mode:              ModeReadOnly,
			AllowDangerous:    false,
			DisabledTools:     []string{},
			CommandTimeoutSec: 20,
			MaxOutputBytes:    20_000,
		},
		Audit: AuditConfig{
			Path: auditPath,
		},
	}
}

// DefaultSearchPaths возвращает стандартные пути поиска конфига по приоритету.
func DefaultSearchPaths() []string {
	var paths []string
	if home, err := os.UserHomeDir(); err == nil {
		paths = append(paths,
			filepath.Join(home, ".config", "sysagentd", "config.jsonc"),
			filepath.Join(home, ".config", "sysagentd", "config.json"),
		)
	}
	paths = append(paths,
		"/etc/sysagentd/config.jsonc",
		"/etc/sysagentd/config.json",
	)
	return paths
}

// Load загружает конфигурацию из указанного файла (или из стандартных путей),
// применяет переопределения из переменных окружения и проверяет корректность.
func Load(explicitPath string) (Config, error) {
	cfg := Default()

	candidate := strings.TrimSpace(explicitPath)
	if candidate == "" {
		candidate = strings.TrimSpace(os.Getenv("SYSAGENTD_CONFIG"))
	}

	if candidate != "" {
		if err := loadFromFile(candidate, &cfg); err != nil {
			return Config{}, err
		}
	} else {
		for _, p := range DefaultSearchPaths() {
			if info, err := os.Stat(p); err == nil && !info.IsDir() {
				if err := loadFromFile(p, &cfg); err != nil {
					return Config{}, err
				}
				break
			}
		}
	}

	applyEnvOverrides(&cfg)

	if err := cfg.Validate(); err != nil {
		return Config{}, err
	}
	return cfg, nil
}

func loadFromFile(path string, cfg *Config) error {
	raw, err := os.ReadFile(path)
	if err != nil {
		return fmt.Errorf("чтение конфига %s: %w", path, err)
	}
	clean := StripJSONComments(raw)
	dec := json.NewDecoder(bytes.NewReader(clean))
	dec.DisallowUnknownFields()
	if err := dec.Decode(cfg); err != nil {
		return fmt.Errorf("разбор конфига %s: %w", path, err)
	}
	cfg.SourcePath = path
	return nil
}

func applyEnvOverrides(cfg *Config) {
	if v := strings.TrimSpace(os.Getenv("SYSAGENTD_SOCKET")); v != "" {
		cfg.SocketPath = v
	}
	if v := strings.TrimSpace(os.Getenv("SYSAGENTD_MODE")); v != "" {
		cfg.Policy.Mode = v
	}
	if v := strings.TrimSpace(os.Getenv("SYSAGENTD_AUDIT")); v != "" {
		cfg.Audit.Path = v
	}
}

// Validate проверяет допустимость всех параметров конфигурации.
func (c *Config) Validate() error {
	if strings.TrimSpace(c.SocketPath) == "" {
		return errors.New("socket_path не может быть пустым")
	}
	switch c.Policy.Mode {
	case ModeReadOnly, ModeAsk, ModeAuto:
	default:
		return fmt.Errorf("недопустимый policy.mode=%q (ожидается readonly, ask или auto)", c.Policy.Mode)
	}
	if c.Policy.CommandTimeoutSec < 1 || c.Policy.CommandTimeoutSec > 600 {
		return fmt.Errorf("policy.command_timeout_sec=%d вне допустимого диапазона 1..600", c.Policy.CommandTimeoutSec)
	}
	if c.Policy.MaxOutputBytes < 512 || c.Policy.MaxOutputBytes > 10_000_000 {
		return fmt.Errorf("policy.max_output_bytes=%d вне допустимого диапазона 512..10000000", c.Policy.MaxOutputBytes)
	}
	if strings.TrimSpace(c.Audit.Path) == "" {
		return errors.New("audit.path не может быть пустым")
	}
	return nil
}

// StripJSONComments удаляет комментарии // и # вне строковых литералов JSON,
// сохраняя номера строк для понятных сообщений об ошибках синтаксиса.
func StripJSONComments(src []byte) []byte {
	out := make([]byte, 0, len(src))
	inString := false
	escaped := false

	for i := 0; i < len(src); i++ {
		ch := src[i]
		if inString {
			out = append(out, ch)
			if escaped {
				escaped = false
			} else if ch == '\\' {
				escaped = true
			} else if ch == '"' {
				inString = false
			}
			continue
		}

		if ch == '"' {
			inString = true
			out = append(out, ch)
			continue
		}

		// Однострочный комментарий # ... или // ...
		if ch == '#' || (ch == '/' && i+1 < len(src) && src[i+1] == '/') {
			for i < len(src) && src[i] != '\n' {
				i++
			}
			if i < len(src) && src[i] == '\n' {
				out = append(out, '\n')
			}
			continue
		}

		out = append(out, ch)
	}
	return out
}
EOF
cd /opt/sysagent && go build ./internal/config && echo "config: OK"
