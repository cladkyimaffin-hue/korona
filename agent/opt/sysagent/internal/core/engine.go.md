### Зачем нужен этот файл:
Это сердце всего проекта (Engine):

-  RegisterModule(...) — подключает к ядру новые библиотеки функций и проверяет, нет ли совпадений имён;
-  Execute(...) — единственная точка запуска любой операции: проверяет наличие команды, прогоняет её через policy.go, вешает таймаут и записывает итог в audit.go;
-  содержит встроенный модуль core с тремя базовыми командами: ping, version, tools.

-  cat <<'EOF' > /opt/sysagent/internal/core/engine.go
package core

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"runtime"
	"sort"
	"strings"
	"sync"
	"time"

	"sysagent/internal/config"
)

// Engine связывает воедино конфигурацию, реестр модулей/инструментов, политику и аудит.
type Engine struct {
	cfg       config.Config
	auditor   *Auditor
	startedAt time.Time

	mu      sync.RWMutex
	modules []ModuleInfo
	tools   map[string]Tool   // каноническое имя -> инструмент
	aliases map[string]string // псевдоним -> каноническое имя
}

// ModuleInfo хранит сводку о подключённом модуле для инспекции.
type ModuleInfo struct {
	Name        string   `json:"name"`
	Description string   `json:"description"`
	Tools       []string `json:"tools"`
}

// NewEngine инициализирует ядро и автоматически регистрирует встроенный системный модуль "core".
func NewEngine(cfg config.Config) (*Engine, error) {
	if err := cfg.Validate(); err != nil {
		return nil, err
	}
	e := &Engine{
		cfg:       cfg,
		auditor:   NewAuditor(cfg.Audit.Path),
		startedAt: time.Now(),
		tools:     make(map[string]Tool),
		aliases:   make(map[string]string),
	}
	if err := e.RegisterModule(e.builtinCoreModule()); err != nil {
		return nil, err
	}
	return e, nil
}

// Config возвращает копию активной конфигурации ядра.
func (e *Engine) Config() config.Config {
	return e.cfg
}

// RegisterModule подключает к ядру новый пакет функций (модуль).
func (e *Engine) RegisterModule(m Module) error {
	if m == nil {
		return fmt.Errorf("попытка зарегистрировать пустой модуль")
	}
	modName := strings.TrimSpace(m.Name())
	if modName == "" {
		return fmt.Errorf("имя модуля не может быть пустым")
	}

	e.mu.Lock()
	defer e.mu.Unlock()

	for _, existing := range e.modules {
		if existing.Name == modName {
			return fmt.Errorf("модуль %q уже зарегистрирован", modName)
		}
	}

	var registeredNames []string
	for _, t := range m.Tools() {
		spec := t.Spec()
		name := strings.TrimSpace(spec.Name)
		if name == "" {
			return fmt.Errorf("пустое имя инструмента в модуле %q", modName)
		}
		if _, exists := e.tools[name]; exists {
			return fmt.Errorf("дублирование имени инструмента %q", name)
		}
		if target, exists := e.aliases[name]; exists {
			return fmt.Errorf("имя инструмента %q конфликтует с псевдонимом для %q", name, target)
		}
		for _, alias := range spec.Aliases {
			a := strings.TrimSpace(alias)
			if a == "" {
				continue
			}
			if _, exists := e.tools[a]; exists {
				return fmt.Errorf("псевдоним %q конфликтует с инструментом %q", a, a)
			}
			if target, exists := e.aliases[a]; exists {
				return fmt.Errorf("дублирование псевдонима %q (уже привязан к %q)", a, target)
			}
			e.aliases[a] = name
		}
		e.tools[name] = t
		registeredNames = append(registeredNames, name)
	}
	sort.Strings(registeredNames)

	e.modules = append(e.modules, ModuleInfo{
		Name:        modName,
		Description: m.Description(),
		Tools:       registeredNames,
	})
	return nil
}

// ListSpecs возвращает отсортированный список спецификаций всех подключённых инструментов.
func (e *Engine) ListSpecs() []ToolSpec {
	e.mu.RLock()
	defer e.mu.RUnlock()

	specs := make([]ToolSpec, 0, len(e.tools))
	for _, t := range e.tools {
		specs = append(specs, t.Spec())
	}
	sort.Slice(specs, func(i, j int) bool {
		return specs[i].Name < specs[j].Name
	})
	return specs
}

// ListModules возвращает список подключённых модулей.
func (e *Engine) ListModules() []ModuleInfo {
	e.mu.RLock()
	defer e.mu.RUnlock()

	out := make([]ModuleInfo, len(e.modules))
	copy(out, e.modules)
	return out
}

func (e *Engine) resolveTool(name string) (Tool, bool) {
	e.mu.RLock()
	defer e.mu.RUnlock()

	key := strings.TrimSpace(name)
	if t, ok := e.tools[key]; ok {
		return t, true
	}
	if canonical, ok := e.aliases[key]; ok {
		t, found := e.tools[canonical]
		return t, found
	}
	return nil, false
}

func (e *Engine) writeAudit(rec AuditRecord) {
	if err := e.auditor.Write(rec); err != nil {
		log.Printf("предупреждение: не удалось записать событие в журнал аудита %s: %v", e.auditor.Path(), err)
	}
}

// Execute — единственная точка выполнения любых запросов к ядру.
// Ни один инструмент не может обойти проверку политики, таймаут или запись в аудит.
func (e *Engine) Execute(ctx context.Context, req Request) Response {
	started := time.Now()
	requestedName := strings.TrimSpace(req.Tool)

	tool, found := e.resolveTool(requestedName)
	if !found {
		errMsg := fmt.Sprintf("неизвестная операция %q (вызовите 'tools' для списка доступных)", requestedName)
		elapsed := time.Since(started)
		e.writeAudit(AuditRecord{
			Caller:     req.Caller,
			Tool:       requestedName,
			Args:       req.Args,
			Allowed:    false,
			OK:         false,
			Reason:     "операция отсутствует в реестре ядра",
			Error:      errMsg,
			DurationMs: elapsed.Milliseconds(),
		})
		return Response{
			OK:      false,
			Tool:    requestedName,
			Error:   errMsg,
			Elapsed: elapsed.Round(time.Microsecond).String(),
		}
	}

	spec := tool.Spec()
	decision := EvaluatePolicy(e.cfg.Policy, spec, req)
	if !decision.Allowed {
		elapsed := time.Since(started)
		e.writeAudit(AuditRecord{
			Caller:     req.Caller,
			Tool:       spec.Name,
			Module:     spec.Module,
			Risk:       spec.Risk,
			Args:       req.Args,
			Allowed:    false,
			OK:         false,
			Reason:     decision.Reason,
			Error:      decision.Reason,
			DurationMs: elapsed.Milliseconds(),
		})
		return Response{
			OK:            false,
			Tool:          spec.Name,
			Risk:          spec.Risk,
			NeedsApproval: decision.NeedsApproval,
			Error:         decision.Reason,
			Elapsed:       elapsed.Round(time.Microsecond).String(),
		}
	}

	timeout := time.Duration(e.cfg.Policy.CommandTimeoutSec) * time.Second
	runCtx, cancel := context.WithTimeout(ctx, timeout)
	defer cancel()

	argsCopy := make(map[string]string, len(req.Args))
	for k, v := range req.Args {
		argsCopy[k] = v
	}

	result, err := tool.Run(runCtx, argsCopy)
	elapsed := time.Since(started)

	if err != nil {
		errText := err.Error()
		if runCtx.Err() == context.DeadlineExceeded {
			errText = fmt.Sprintf("превышен таймаут выполнения (%s)", timeout)
		}
		e.writeAudit(AuditRecord{
			Caller:     req.Caller,
			Tool:       spec.Name,
			Module:     spec.Module,
			Risk:       spec.Risk,
			Args:       req.Args,
			Allowed:    true,
			OK:         false,
			Reason:     decision.Reason,
			Error:      errText,
			DurationMs: elapsed.Milliseconds(),
		})
		return Response{
			OK:      false,
			Tool:    spec.Name,
			Risk:    spec.Risk,
			Error:   errText,
			Elapsed: elapsed.Round(time.Millisecond).String(),
		}
	}

	raw, marshalErr := json.Marshal(result)
	if marshalErr != nil {
		e.writeAudit(AuditRecord{
			Caller:     req.Caller,
			Tool:       spec.Name,
			Module:     spec.Module,
			Risk:       spec.Risk,
			Args:       req.Args,
			Allowed:    true,
			OK:         false,
			Error:      marshalErr.Error(),
			DurationMs: elapsed.Milliseconds(),
		})
		return Response{
			OK:      false,
			Tool:    spec.Name,
			Risk:    spec.Risk,
			Error:   fmt.Sprintf("ошибка сериализации ответа: %v", marshalErr),
			Elapsed: elapsed.Round(time.Millisecond).String(),
		}
	}

	e.writeAudit(AuditRecord{
		Caller:     req.Caller,
		Tool:       spec.Name,
		Module:     spec.Module,
		Risk:       spec.Risk,
		Args:       req.Args,
		Allowed:    true,
		OK:         true,
		Reason:     decision.Reason,
		DurationMs: elapsed.Milliseconds(),
	})

	return Response{
		OK:      true,
		Tool:    spec.Name,
		Risk:    spec.Risk,
		Data:    raw,
		Elapsed: elapsed.Round(time.Microsecond).String(),
	}
}

type builtinModule struct {
	name        string
	description string
	tools       []Tool
}

func (m builtinModule) Name() string        { return m.name }
func (m builtinModule) Description() string { return m.description }
func (m builtinModule) Tools() []Tool       { return m.tools }

func (e *Engine) builtinCoreModule() Module {
	return builtinModule{
		name:        "core",
		description: "Встроенные служебные операции ядра (проверка связи, версия, список подключённых модулей)",
		tools: []Tool{
			FuncTool{
				ToolSpec: ToolSpec{
					Name:        "core.ping",
					Aliases:     []string{"ping"},
					Module:      "core",
					Description: "Проверка работоспособности ядра и времени непрерывной работы демона",
					Risk:        RiskRead,
				},
				Handler: func(_ context.Context, _ map[string]string) (any, error) {
					return map[string]any{
						"pong":    true,
						"version": Version,
						"uptime":  time.Since(e.startedAt).Round(time.Second).String(),
					}, nil
				},
			},
			FuncTool{
				ToolSpec: ToolSpec{
					Name:        "core.version",
					Aliases:     []string{"version"},
					Module:      "core",
					Description: "Сведения о версии агента, среде выполнения Go и активном режиме политики",
					Risk:        RiskRead,
				},
				Handler: func(_ context.Context, _ map[string]string) (any, error) {
					source := "(по умолчанию)"
					if e.cfg.SourcePath != "" {
						source = e.cfg.SourcePath
					}
					return map[string]any{
						"version":       Version,
						"go":            runtime.Version(),
						"os_arch":       runtime.GOOS + "/" + runtime.GOARCH,
						"policy_mode":   e.cfg.Policy.Mode,
						"config_source": source,
						"audit_path":    e.auditor.Path(),
					}, nil
				},
			},
			FuncTool{
				ToolSpec: ToolSpec{
					Name:        "core.tools",
					Aliases:     []string{"tools"},
					Module:      "core",
					Description: "Перечень всех подключённых модулей и доступных операций с уровнями риска",
					Risk:        RiskRead,
				},
				Handler: func(_ context.Context, _ map[string]string) (any, error) {
					return map[string]any{
						"modules": e.ListModules(),
						"tools":   e.ListSpecs(),
					}, nil
				},
			},
		},
	}
}
EOF
cd /opt/sysagent && go build ./internal/core && echo "engine: OK"
