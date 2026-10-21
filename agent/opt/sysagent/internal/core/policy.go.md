### Зачем нужен этот файл:
Это «охранник на входе» ядра — ни одна функция не запустится в обход него:

-  проверяет, не отключён ли инструмент администратором в конфиге;
-  проверяет параметры по строгому белому списку и рубит любые спецсимволы shell (; | & $ > <), чтобы исключить инъекции команд;
-  проверяет уровень риска: в режиме readonly разрешает только чтение (read) и блокирует любые изменения.

  cat <<'EOF' > /opt/sysagent/internal/core/policy.go
package core

import (
	"fmt"
	"strings"

	"sysagent/internal/config"
)

const (
	maxArgKeyLen = 64
	maxArgValLen = 512

	// Символы командной оболочки запрещены на уровне ядра для любых аргументов:
	// агент никогда не конструирует shell-строки и не допускает инъекций.
	forbiddenArgChars = ";|&$`><\n\r\x00"
)

// Decision описывает вердикт политики безопасности по запросу.
type Decision struct {
	Allowed       bool
	NeedsApproval bool
	Reason        string
	Risk          RiskLevel
}

// EvaluatePolicy проверяет, разрешено ли выполнение инструмента с переданными аргументами.
func EvaluatePolicy(cfg config.PolicyConfig, spec ToolSpec, req Request) Decision {
	// 1. Проверка отключения инструмента в конфигурации администратора.
	for _, disabled := range cfg.DisabledTools {
		d := strings.TrimSpace(disabled)
		if d == spec.Name || containsString(spec.Aliases, d) {
			return Decision{
				Allowed: false,
				Risk:    spec.Risk,
				Reason:  fmt.Sprintf("инструмент %q отключён в конфигурации (policy.disabled_tools)", spec.Name),
			}
		}
	}

	// 2. Проверка списка допустимых параметров и безопасности их значений.
	if err := validateArgs(spec, req.Args); err != nil {
		return Decision{
			Allowed: false,
			Risk:    spec.Risk,
			Reason:  err.Error(),
		}
	}

	// 3. Проверка уровня риска операции согласно режиму политики.
	switch spec.Risk {
	case RiskRead:
		return Decision{Allowed: true, Risk: RiskRead, Reason: "разрешено (чтение)"}

	case RiskWrite:
		switch cfg.Mode {
		case config.ModeReadOnly:
			return Decision{
				Allowed: false,
				Risk:    RiskWrite,
				Reason:  "отклонено: активен режим readonly (изменения запрещены)",
			}
		case config.ModeAsk:
			if !req.Approved {
				return Decision{
					Allowed:       false,
					NeedsApproval: true,
					Risk:          RiskWrite,
					Reason:        "требуется явное подтверждение пользователя (режим ask)",
				}
			}
			return Decision{Allowed: true, Risk: RiskWrite, Reason: "разрешено (подтверждено пользователем)"}
		case config.ModeAuto:
			return Decision{Allowed: true, Risk: RiskWrite, Reason: "разрешено (режим auto)"}
		default:
			return Decision{Allowed: false, Risk: RiskWrite, Reason: "неизвестный режим политики"}
		}

	case RiskDangerous:
		if !cfg.AllowDangerous {
			return Decision{
				Allowed: false,
				Risk:    RiskDangerous,
				Reason:  "отклонено: опасные операции запрещены политикой (allow_dangerous=false)",
			}
		}
		if cfg.Mode == config.ModeReadOnly {
			return Decision{
				Allowed: false,
				Risk:    RiskDangerous,
				Reason:  "отклонено: активен режим readonly",
			}
		}
		if !req.Approved {
			return Decision{
				Allowed:       false,
				NeedsApproval: true,
				Risk:          RiskDangerous,
				Reason:        "опасная операция всегда требует явного подтверждения",
			}
		}
		return Decision{Allowed: true, Risk: RiskDangerous, Reason: "разрешено (опасная операция подтверждена)"}

	default:
		return Decision{
			Allowed: false,
			Risk:    spec.Risk,
			Reason:  fmt.Sprintf("неизвестный уровень риска %q у инструмента %q", spec.Risk, spec.Name),
		}
	}
}

func validateArgs(spec ToolSpec, args map[string]string) error {
	allowed := make(map[string]ParamSpec, len(spec.Params))
	for _, p := range spec.Params {
		allowed[p.Name] = p
	}

	for k, v := range args {
		if len(k) == 0 || len(k) > maxArgKeyLen {
			return fmt.Errorf("некорректное имя параметра %q", k)
		}
		if _, ok := allowed[k]; !ok {
			return fmt.Errorf("неизвестный параметр %q для инструмента %q", k, spec.Name)
		}
		if len(v) > maxArgValLen {
			return fmt.Errorf("значение параметра %q превышает лимит %d символов", k, maxArgValLen)
		}
		if strings.ContainsAny(v, forbiddenArgChars) {
			return fmt.Errorf("недопустимые управляющие/shell-символы в параметре %q", k)
		}
	}

	for _, p := range spec.Params {
		if p.Required && strings.TrimSpace(args[p.Name]) == "" {
			return fmt.Errorf("не указан обязательный параметр %q", p.Name)
		}
	}
	return nil
}

func containsString(items []string, target string) bool {
	for _, item := range items {
		if item == target {
			return true
		}
	}
	return false
}
EOF
cd /opt/sysagent && go build ./internal/core && echo "policy: OK"
