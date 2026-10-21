### Зачем нужен этот файл:
Это главный «разъём», к которому мы потом будем подключать любые библиотеки функций (local, proxmox, linuxssh, windows):

-  Module — интерфейс подключаемого модуля функций;
-  Tool и ToolSpec — описание одной операции, её уровня риска (read / write / dangerous) и строго закрытого списка разрешённых параметров;
-  Request и Response — единый формат запроса и ответа для CLI, сокета и будущих Web / Claude (MCP).

cat <<'EOF' > /opt/sysagent/internal/core/types.go
// Пакет core реализует неизменяемое ядро агента sysagentd:
// контракт подключаемых модулей, реестр инструментов, проверку политики и аудит.
package core

import (
	"context"
	"encoding/json"
)

// Version — текущая версия ядра агента.
const Version = "0.2.0"

// RiskLevel определяет класс риска конкретной операции.
type RiskLevel string

const (
	RiskRead      RiskLevel = "read"      // только чтение, не меняет состояние системы
	RiskWrite     RiskLevel = "write"     // изменяет состояние службы/конфигурации
	RiskDangerous RiskLevel = "dangerous" // потенциально разрушительная операция
)

// ParamSpec описывает один допустимый входной параметр инструмента.
type ParamSpec struct {
	Name        string `json:"name"`
	Description string `json:"description"`
	Required    bool   `json:"required,omitempty"`
}

// ToolSpec содержит метаданные и правила вызова одного инструмента.
type ToolSpec struct {
	Name        string      `json:"name"`              // полное имя: <модуль>.<операция>
	Aliases     []string    `json:"aliases,omitempty"` // короткие псевдонимы для CLI (опционально)
	Module      string      `json:"module"`            // имя модуля-владельца
	Description string      `json:"description"`       // описание на русском языке
	Risk        RiskLevel   `json:"risk"`              // read | write | dangerous
	Params      []ParamSpec `json:"params,omitempty"`  // строго закрытый список параметров
}

// InputJSONSchema формирует JSON Schema параметров инструмента (готово для MCP и Web API).
func (s ToolSpec) InputJSONSchema() map[string]any {
	props := make(map[string]any, len(s.Params))
	var required []string
	for _, p := range s.Params {
		props[p.Name] = map[string]any{
			"type":        "string",
			"description": p.Description,
		}
		if p.Required {
			required = append(required, p.Name)
		}
	}
	schema := map[string]any{
		"type":                 "object",
		"properties":           props,
		"additionalProperties": false,
	}
	if len(required) > 0 {
		schema["required"] = required
	}
	return schema
}

// Tool — единый интерфейс любой диагностической или управляющей функции.
type Tool interface {
	Spec() ToolSpec
	Run(ctx context.Context, args map[string]string) (any, error)
}

// Module — единый интерфейс подключаемой «библиотеки функций» (local, proxmox, linuxssh и т.д.).
type Module interface {
	Name() string
	Description() string
	Tools() []Tool
}

// FuncTool — удобная обёртка, позволяющая создавать инструменты из обычной функции.
type FuncTool struct {
	ToolSpec ToolSpec
	Handler  func(ctx context.Context, args map[string]string) (any, error)
}

func (ft FuncTool) Spec() ToolSpec { return ft.ToolSpec }

func (ft FuncTool) Run(ctx context.Context, args map[string]string) (any, error) {
	return ft.Handler(ctx, args)
}

// Request представляет единый формат запроса от любого клиента (CLI, сокет, будущий Web/MCP).
type Request struct {
	Tool     string            `json:"tool"`
	Args     map[string]string `json:"args,omitempty"`
	Approved bool              `json:"approved,omitempty"` // подтверждение человеком для режима ask
	Caller   string            `json:"caller,omitempty"`   // источник вызова для аудита (cli, local, mcp)
}

// Response представляет единый формат ответа ядра.
type Response struct {
	OK            bool            `json:"ok"`
	Tool          string          `json:"tool,omitempty"`
	Risk          RiskLevel       `json:"risk,omitempty"`
	NeedsApproval bool            `json:"needs_approval,omitempty"`
	Data          json.RawMessage `json:"data,omitempty"`
	Error         string          `json:"error,omitempty"`
	Elapsed       string          `json:"elapsed"`
}
EOF
cd /opt/sysagent && go build ./internal/core && echo "types: OK"
