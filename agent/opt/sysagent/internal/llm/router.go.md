-  Сразу 5 бесплатных моделей в одном конфиге /etc/sysagentd/llm.jsonc (chmod 0600) на двух площадках, которые реально ответили с вашей ВМ без VPN:
-  GitHub Models: GPT-4.1-mini (быстрый, высокий суточный лимит), GPT-4.1 (глубокий разбор), DeepSeek-V3 (второе мнение);
-  Mistral API (бесплатный тариф Experiment): Mistral Small и Codestral.
-  (Ключ прописывается один раз вверху файла — достаточно хотя бы одного ключа github или mistral, а если вставить оба, их лимиты объединятся!)
-  Автообход лимитов (HTTP 429): если модель упёрлась в лимит или задумалась, роутер ставит её «остывать» на 90 секунд и прозрачно передаёт вопрос следующей модели.
-  Бережёт бесплатные токены: сырые JSON-ответы инструментов не раздувают историю следующих реплик.

  ### Шаг 17 — Создаём каскадный ИИ-роутер /opt/sysagent/internal/llm/router.go
 1. Записываем файл /opt/sysagent/internal/llm/router.go
 2. mkdir -p /opt/sysagent/internal/llm

-	cat <<'EOF' > /opt/sysagent/internal/llm/router.go
// Пакет llm реализует каскадный клиент языковых моделей (OpenAI-совместимый /chat/completions:
// GitHub Models, Mistral API, Ollama, OpenRouter и др.) с автоматическим обходом лимитов (HTTP 429),
// ручным выбором основной модели и безопасным вызовом инструментов ядра sysagentd.
package llm

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"os"
	"path/filepath"
	"strings"
	"sync"
	"time"

	"sysagent/internal/core"
)

const (
	DefaultRootLLMConfig = "/etc/sysagentd/llm.jsonc"
	maxToolRounds        = 6
	maxHistoryMessages   = 16
	defaultCooldownSec   = 90
	defaultTimeoutSec    = 45
)

const systemPromptRU = `Ты — встроенный ИИ-ассистент системного администратора в агенте диагностики sysagentd.
Отвечай всегда кратко, чётко и по делу на русском языке.

Правила работы:
1. Никогда не выдумывай состояние сервера, служб, дисков, памяти или сети — всегда вызывай доступные инструменты диагностики, чтобы получить реальные данные.
2. Сначала используй безопасные инструменты чтения (read).
3. Инструменты изменения (write) вызывай ТОЛЬКО тогда, когда пользователь явно попросил выполнить действие (например, перезапустить службу). Ядро само запросит у администратора подтверждение [y/N].
4. Если администратор отклонил подтверждение или активен режим readonly — НЕ вызывай инструмент повторно, а напиши точную и безопасную команду для ручной проверки/выполнения.
5. Никогда не проси у пользователя пароли, приватные ключи или API-токены.`

// Profile описывает одну подключённую языковую модель.
type Profile struct {
	ID         string `json:"id"`
	Title      string `json:"title"`
	BaseURL    string `json:"base_url"`
	KeyRef     string `json:"key_ref,omitempty"`
	APIKey     string `json:"api_key,omitempty"`
	APIKeyEnv  string `json:"api_key_env,omitempty"`
	Model      string `json:"model"`
	ProxyURL   string `json:"proxy_url,omitempty"`
	TimeoutSec int    `json:"timeout_sec,omitempty"`
}

// Config хранит ключи и список профилей моделей.
type Config struct {
	Keys          map[string]string `json:"keys"`
	ActiveProfile string            `json:"active_profile"` // "auto" или ID конкретного профиля
	Fallback      bool              `json:"fallback"`       // подстраховка другой моделью при HTTP 429/сбое
	CooldownSec   int               `json:"cooldown_sec"`
	Profiles      []Profile         `json:"profiles"`
}

// Message представляет одно сообщение в истории диалога.
type Message struct {
	Role       string     `json:"role"`
	Content    string     `json:"content"`
	ToolCalls  []ToolCall `json:"tool_calls,omitempty"`
	ToolCallID string     `json:"tool_call_id,omitempty"`
}

// ToolCall описывает вызов функции, запрошенный моделью.
type ToolCall struct {
	ID       string       `json:"id"`
	Type     string       `json:"type"`
	Function FunctionCall `json:"function"`
}

// FunctionCall содержит имя и JSON-аргументы вызываемой функции.
type FunctionCall struct {
	Name      string `json:"name"`
	Arguments string `json:"arguments"`
}

// ToolExecutor выполняет инструмент через ядро/сокет (включая интерактивный запрос [y/N] при необходимости).
type ToolExecutor func(ctx context.Context, toolName string, args map[string]string) (string, error)

// EventLogger выводит промежуточные шаги в консоль (вызовы инструментов, переключение при 429).
type EventLogger func(msg string)

// Router управляет выбором модели, кулдаунами при лимитах 429 и историей диалога.
type Router struct {
	mu        sync.Mutex
	cfgPath   string
	cfg       Config
	cooldowns map[string]time.Time
	history   []Message
}

// DefaultConfigPath определяет путь к защищённому файлу конфигурации ИИ (0600).
func DefaultConfigPath() string {
	if env := strings.TrimSpace(os.Getenv("SYSAGENTD_LLM_CONFIG")); env != "" {
		return env
	}
	if os.Geteuid() == 0 {
		return DefaultRootLLMConfig
	}
	if home, err := os.UserHomeDir(); err == nil {
		return filepath.Join(home, ".config", "sysagentd", "llm.jsonc")
	}
	return DefaultRootLLMConfig
}

const defaultConfigTemplate = `{
  // Защищённый файл настроек ИИ sysagentd (права 0600 — доступен только владельцу).
  // Достаточно вставить хотя бы ОДИН бесплатный ключ ("github" или "mistral"),
  // а если заполнить оба — агент автоматически объединит их лимиты в единый каскад!
  "keys": {
    // 1) Бесплатный GitHub Token: https://github.com/settings/personal-access-tokens/new
    //    Account permissions -> Models -> Read-only (доступ к репозиториям НЕ нужен)
    "github": "",

    // 2) Бесплатный ключ Mistral AI (тариф Experiment): https://console.mistral.ai/api-keys
    "mistral": ""
  },

  // "auto" — автоматический выбор первой доступной модели, либо id профиля (например "mistral-small")
  "active_profile": "auto",

  // Автоматически переключаться на следующую модель при лимите (HTTP 429) или таймауте
  "fallback": true,
  "cooldown_sec": 90,

  "profiles": [
    {
      "id": "gh-mini",
      "title": "GitHub GPT-4.1-mini (быстрый, высокий суточный лимит)",
      "base_url": "https://models.github.ai/inference",
      "key_ref": "github",
      "model": "openai/gpt-4.1-mini"
    },
    {
      "id": "mistral-small",
      "title": "Mistral Small (большой бесплатный пул)",
      "base_url": "https://api.mistral.ai/v1",
      "key_ref": "mistral",
      "model": "mistral-small-latest"
    },
    {
      "id": "gh-gpt41",
      "title": "GitHub GPT-4.1 (глубокий анализ инцидентов)",
      "base_url": "https://models.github.ai/inference",
      "key_ref": "github",
      "model": "openai/gpt-4.1"
    },
    {
      "id": "gh-deepseek",
      "title": "GitHub DeepSeek-V3 (альтернативное мнение)",
      "base_url": "https://models.github.ai/inference",
      "key_ref": "github",
      "model": "deepseek/DeepSeek-V3-0324"
    },
    {
      "id": "mistral-codestral",
      "title": "Mistral Codestral (разбор логов и служб)",
      "base_url": "https://api.mistral.ai/v1",
      "key_ref": "mistral",
      "model": "codestral-latest"
    }
  ]
}
`

// EnsureConfigFile создаёт шаблон llm.jsonc с правами 0600, если он ещё не существует.
func EnsureConfigFile(path string) error {
	if _, err := os.Stat(path); err == nil {
		_ = os.Chmod(path, 0o600)
		return nil
	}
	if err := os.MkdirAll(filepath.Dir(path), 0o700); err != nil {
		return err
	}
	return os.WriteFile(path, []byte(defaultConfigTemplate), 0o600)
}

// NewRouter создаёт и загружает каскадный роутер моделей.
func NewRouter(path string) (*Router, error) {
	if strings.TrimSpace(path) == "" {
		path = DefaultConfigPath()
	}
	if err := EnsureConfigFile(path); err != nil {
		return nil, err
	}
	r := &Router{
		cfgPath:   path,
		cooldowns: make(map[string]time.Time),
	}
	if err := r.Reload(); err != nil {
		return nil, err
	}
	return r, nil
}

// ConfigPath возвращает путь к используемому файлу конфигурации ИИ.
func (r *Router) ConfigPath() string { return r.cfgPath }

// Reload перечитывает llm.jsonc с диска на лету без перезапуска демона.
func (r *Router) Reload() error {
	raw, err := os.ReadFile(r.cfgPath)
	if err != nil {
		return err
	}
	var cfg Config
	if err := json.Unmarshal(stripJSONC(raw), &cfg); err != nil {
		return fmt.Errorf("ошибка чтения %s: %w", r.cfgPath, err)
	}
	if cfg.ActiveProfile == "" {
		cfg.ActiveProfile = "auto"
	}
	if cfg.CooldownSec <= 0 {
		cfg.CooldownSec = defaultCooldownSec
	}
	r.mu.Lock()
	r.cfg = cfg
	r.mu.Unlock()
	return nil
}

// ResetHistory очищает контекст текущего диалога в консоли.
func (r *Router) ResetHistory() {
	r.mu.Lock()
	r.history = nil
	r.mu.Unlock()
}

// ProfileStatus возвращает сводку по всем профилям (без раскрытия ключей!).
type ProfileStatus struct {
	ID            string
	Title         string
	Model         string
	HasKey        bool
	CoolingSecRem int
}

// Status возвращает текущий режим выбора, путь к конфигу и список профилей.
func (r *Router) Status() (active string, readyCount int, items []ProfileStatus) {
	r.mu.Lock()
	defer r.mu.Unlock()

	now := time.Now()
	active = r.cfg.ActiveProfile
	for _, p := range r.cfg.Profiles {
		hasKey := r.resolveKeyLocked(p) != ""
		if hasKey {
			readyCount++
		}
		rem := 0
		if until, ok := r.cooldowns[p.ID]; ok && until.After(now) {
			rem = int(until.Sub(now).Seconds())
		}
		items = append(items, ProfileStatus{
			ID:            p.ID,
			Title:         p.Title,
			Model:         p.Model,
			HasKey:        hasKey,
			CoolingSecRem: rem,
		})
	}
	return active, readyCount, items
}

// SetActiveProfile переключает активную модель ("auto" или конкретный ID профиля) в памяти.
func (r *Router) SetActiveProfile(id string) error {
	r.mu.Lock()
	defer r.mu.Unlock()

	if id == "auto" {
		r.cfg.ActiveProfile = "auto"
		return nil
	}
	for _, p := range r.cfg.Profiles {
		if p.ID == id {
			r.cfg.ActiveProfile = id
			return nil
		}
	}
	return fmt.Errorf("профиль %q не найден", id)
}

func (r *Router) resolveKeyLocked(p Profile) string {
	if strings.TrimSpace(p.APIKey) != "" {
		return strings.TrimSpace(p.APIKey)
	}
	if p.KeyRef != "" && r.cfg.Keys != nil {
		if v := strings.TrimSpace(r.cfg.Keys[p.KeyRef]); v != "" {
			return v
		}
	}
	if p.APIKeyEnv != "" {
		if v := strings.TrimSpace(os.Getenv(p.APIKeyEnv)); v != "" {
			return v
		}
	}
	if strings.Contains(p.BaseURL, "127.0.0.1") || strings.Contains(p.BaseURL, "localhost") || strings.Contains(p.BaseURL, "11434") {
		return "ollama-local"
	}
	return ""
}

func (r *Router) candidateOrder() ([]Profile, map[string]string) {
	r.mu.Lock()
	defer r.mu.Unlock()

	now := time.Now()
	keys := make(map[string]string)
	var fresh []Profile
	var cooling []Profile

	push := func(p Profile) {
		k := r.resolveKeyLocked(p)
		if k == "" {
			return
		}
		keys[p.ID] = k
		if until, ok := r.cooldowns[p.ID]; ok && until.After(now) {
			cooling = append(cooling, p)
		} else {
			fresh = append(fresh, p)
		}
	}

	if r.cfg.ActiveProfile != "" && r.cfg.ActiveProfile != "auto" {
		for _, p := range r.cfg.Profiles {
			if p.ID == r.cfg.ActiveProfile {
				push(p)
			}
		}
		if r.cfg.Fallback {
			for _, p := range r.cfg.Profiles {
				if p.ID != r.cfg.ActiveProfile {
					push(p)
				}
			}
		}
	} else {
		for _, p := range r.cfg.Profiles {
			push(p)
		}
	}

	return append(fresh, cooling...), keys
}

func (r *Router) markCooldown(profileID string) int {
	r.mu.Lock()
	defer r.mu.Unlock()
	sec := r.cfg.CooldownSec
	if sec <= 0 {
		sec = defaultCooldownSec
	}
	r.cooldowns[profileID] = time.Now().Add(time.Duration(sec) * time.Second)
	return sec
}

// ErrNoKeys возвращается, когда ни для одного профиля ещё не прописан API-ключ.
var ErrNoKeys = errors.New("не настроен ни один API-ключ в llm.jsonc")

type apiError struct {
	StatusCode int
	Retryable  bool
	Message    string
}

func (e *apiError) Error() string { return e.Message }

// Ask отправляет вопрос пользователя в каскад моделей, выполняет разрешённые инструменты ядра и возвращает ответ.
func (r *Router) Ask(
	ctx context.Context,
	userQuestion string,
	specs []core.ToolSpec,
	execTool ToolExecutor,
	onEvent EventLogger,
) (answer string, usedProfile Profile, err error) {
	_ = r.Reload()

	candidates, keyMap := r.candidateOrder()
	if len(candidates) == 0 {
		return "", Profile{}, ErrNoKeys
	}

	apiTools, llmToReal := encodeTools(specs)

	r.mu.Lock()
	baseHistory := make([]Message, len(r.history))
	copy(baseHistory, r.history)
	r.mu.Unlock()

	userMsg := Message{Role: "user", Content: userQuestion}
	turnMessages := append(baseHistory, userMsg)

	idx := 0
	current := candidates[idx]

	for round := 0; round < maxToolRounds; round++ {
		var assistantMsg Message
		var callErr error

		for idx < len(candidates) {
			current = candidates[idx]
			assistantMsg, callErr = callCompletionAPI(ctx, current, keyMap[current.ID], turnMessages, apiTools)
			if callErr == nil {
				break
			}
			var ae *apiError
			if errors.As(callErr, &ae) && ae.Retryable && idx+1 < len(candidates) {
				sec := r.markCooldown(current.ID)
				idx++
				next := candidates[idx]
				if onEvent != nil {
					onEvent(fmt.Sprintf("⚡ Лимит/сбой у %s (HTTP %d, пауза %dс) → авто-переключение на %s",
						current.ID, ae.StatusCode, sec, next.Title))
				}
				continue
			}
			return "", current, callErr
		}

		if len(assistantMsg.ToolCalls) == 0 {
			finalText := strings.TrimSpace(assistantMsg.Content)
			turnMessages = append(turnMessages, Message{Role: "assistant", Content: finalText})
			r.saveHistory(turnMessages)
			return finalText, current, nil
		}

		turnMessages = append(turnMessages, assistantMsg)

		for _, tc := range assistantMsg.ToolCalls {
			realName, ok := llmToReal[tc.Function.Name]
			if !ok {
				realName = strings.ReplaceAll(tc.Function.Name, "__", ".")
			}
			parsedArgs := parseToolArguments(tc.Function.Arguments)

			if onEvent != nil {
				onEvent(fmt.Sprintf("↳ ИИ вызывает %s(%s)", realName, formatShortArgs(parsedArgs)))
			}

			toolOutput, execErr := execTool(ctx, realName, parsedArgs)
			if execErr != nil {
				toolOutput = fmt.Sprintf(`{"ok":false,"error":%q}`, execErr.Error())
			}

			turnMessages = append(turnMessages, Message{
				Role:       "tool",
				ToolCallID: tc.ID,
				Content:    toolOutput,
			})
		}
	}

	return "", current, fmt.Errorf("превышен лимит шагов вызова инструментов (%d)", maxToolRounds)
}

func (r *Router) saveHistory(msgs []Message) {
	var compact []Message
	for _, m := range msgs {
		if (m.Role == "user" || m.Role == "assistant") && len(m.ToolCalls) == 0 && strings.TrimSpace(m.Content) != "" {
			compact = append(compact, Message{Role: m.Role, Content: m.Content})
		}
	}
	if len(compact) > maxHistoryMessages {
		compact = compact[len(compact)-maxHistoryMessages:]
	}
	r.mu.Lock()
	r.history = compact
	r.mu.Unlock()
}

type chatRequest struct {
	Model       string           `json:"model"`
	Messages    []Message        `json:"messages"`
	Tools       []map[string]any `json:"tools,omitempty"`
	Temperature float64          `json:"temperature"`
}

type chatResponse struct {
	Choices []struct {
		Message Message `json:"message"`
	} `json:"choices"`
	Error *struct {
		Message string `json:"message"`
	} `json:"error,omitempty"`
}

func callCompletionAPI(
	ctx context.Context,
	p Profile,
	apiKey string,
	history []Message,
	tools []map[string]any,
) (Message, error) {
	timeoutSec := p.TimeoutSec
	if timeoutSec <= 0 {
		timeoutSec = defaultTimeoutSec
	}

	transport := &http.Transport{}
	if strings.TrimSpace(p.ProxyURL) != "" {
		u, err := url.Parse(strings.TrimSpace(p.ProxyURL))
		if err != nil {
			return Message{}, fmt.Errorf("некорректный proxy_url в профиле %s: %w", p.ID, err)
		}
		transport.Proxy = http.ProxyURL(u)
	}
	client := &http.Client{
		Timeout:   time.Duration(timeoutSec) * time.Second,
		Transport: transport,
	}

	wireMsgs := make([]Message, 0, len(history)+1)
	wireMsgs = append(wireMsgs, Message{Role: "system", Content: systemPromptRU})
	wireMsgs = append(wireMsgs, history...)

	payload := chatRequest{
		Model:       p.Model,
		Messages:    wireMsgs,
		Tools:       tools,
		Temperature: 0.2,
	}
	bodyBytes, err := json.Marshal(payload)
	if err != nil {
		return Message{}, err
	}

	reqCtx, cancel := context.WithTimeout(ctx, time.Duration(timeoutSec)*time.Second)
	defer cancel()

	endpoint := buildCompletionsURL(p.BaseURL)
	httpReq, err := http.NewRequestWithContext(reqCtx, http.MethodPost, endpoint, bytes.NewReader(bodyBytes))
	if err != nil {
		return Message{}, err
	}
	httpReq.Header.Set("Content-Type", "application/json")
	httpReq.Header.Set("Accept", "application/json")
	httpReq.Header.Set("Authorization", "Bearer "+apiKey)

	resp, err := client.Do(httpReq)
	if err != nil {
		return Message{}, &apiError{
			StatusCode: 0,
			Retryable:  true,
			Message:    fmt.Sprintf("сетевой сбой %s: %v", p.ID, err),
		}
	}
	defer resp.Body.Close()

	respBytes, _ := io.ReadAll(io.LimitReader(resp.Body, 2<<20))
	if resp.StatusCode >= 300 {
		retryable := resp.StatusCode == 429 || resp.StatusCode == 408 || resp.StatusCode >= 500 ||
			resp.StatusCode == 401 || resp.StatusCode == 403
		shortBody := strings.TrimSpace(string(respBytes))
		if len(shortBody) > 220 {
			shortBody = shortBody[:220] + "..."
		}
		return Message{}, &apiError{
			StatusCode: resp.StatusCode,
			Retryable:  retryable,
			Message:    fmt.Sprintf("ошибка API %s (HTTP %d): %s", p.ID, resp.StatusCode, shortBody),
		}
	}

	var parsed chatResponse
	if err := json.Unmarshal(respBytes, &parsed); err != nil {
		return Message{}, fmt.Errorf("некорректный JSON от %s: %w", p.ID, err)
	}
	if len(parsed.Choices) == 0 {
		return Message{}, &apiError{
			StatusCode: resp.StatusCode,
			Retryable:  true,
			Message:    fmt.Sprintf("пустой ответ choices от %s", p.ID),
		}
	}
	msg := parsed.Choices[0].Message
	if msg.Role == "" {
		msg.Role = "assistant"
	}
	return msg, nil
}

func buildCompletionsURL(base string) string {
	b := strings.TrimRight(strings.TrimSpace(base), "/")
	if strings.HasSuffix(b, "/chat/completions") {
		return b
	}
	return b + "/chat/completions"
}

func encodeTools(specs []core.ToolSpec) ([]map[string]any, map[string]string) {
	var out []map[string]any
	mapping := make(map[string]string, len(specs))

	for _, sp := range specs {
		if sp.Name == "core.tools" {
			continue
		}
		safeName := strings.ReplaceAll(sp.Name, ".", "__")
		mapping[safeName] = sp.Name

		out = append(out, map[string]any{
			"type": "function",
			"function": map[string]any{
				"name":        safeName,
				"description": fmt.Sprintf("[%s] %s", sp.Risk, sp.Description),
				"parameters":  sp.InputJSONSchema(),
			},
		})
	}
	return out, mapping
}

func parseToolArguments(raw string) map[string]string {
	out := make(map[string]string)
	raw = strings.TrimSpace(raw)
	if raw == "" || raw == "{}" {
		return out
	}
	var generic map[string]any
	if err := json.Unmarshal([]byte(raw), &generic); err != nil {
		return out
	}
	for k, v := range generic {
		if v == nil {
			continue
		}
		out[k] = fmt.Sprint(v)
	}
	return out
}

func formatShortArgs(args map[string]string) string {
	if len(args) == 0 {
		return ""
	}
	parts := make([]string, 0, len(args))
	for k, v := range args {
		parts = append(parts, fmt.Sprintf("%s=%s", k, v))
	}
	return strings.Join(parts, ", ")
}

func stripJSONC(src []byte) []byte {
	out := make([]byte, 0, len(src))
	inStr := false
	escaped := false

	for i := 0; i < len(src); i++ {
		c := src[i]
		if inStr {
			out = append(out, c)
			if escaped {
				escaped = false
				continue
			}
			if c == '\\' {
				escaped = true
			} else if c == '"' {
				inStr = false
			}
			continue
		}
		if c == '"' {
			inStr = true
			out = append(out, c)
			continue
		}
		if c == '/' && i+1 < len(src) && src[i+1] == '/' {
			i += 2
			for i < len(src) && src[i] != '\n' {
				i++
			}
			if i < len(src) {
				out = append(out, '\n')
			}
			continue
		}
		if c == '/' && i+1 < len(src) && src[i+1] == '*' {
			i += 2
			for i+1 < len(src) && !(src[i] == '*' && src[i+1] == '/') {
				i++
			}
			i++
			continue
		}
		out = append(out, c)
	}
	return out
}
EOF
