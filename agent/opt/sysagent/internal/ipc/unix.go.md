### Зачем нужен этот файл:
Он отвечает за локальное общение с демоном через Unix-сокет (/run/sysagentd/sysagentd.sock):

-  не открывает никаких сетевых портов наружу (достучаться из сети нельзя физически);
-  выставляет права 0660 (обращаться могут только владелец и разрешённая группа);
-  ограничивает размер входящего запроса (64 КиБ), чтобы никто не мог забить 2 ГБ оперативки ВМ мусорным запросом;
-  аккуратно удаляет файл сокета при остановке демона (Ctrl+C / SIGTERM).

  cat <<'EOF' > /opt/sysagent/internal/ipc/unix.go
// Пакет ipc реализует локальный транспорт между CLI/адаптерами и демоном
// поверх Unix domain socket без открытия сетевых TCP-портов.
package ipc

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"log"
	"net"
	"os"
	"path/filepath"
	"sync"
	"time"

	"sysagent/internal/core"
)

const (
	// Максимальный размер входящего JSON-запроса (64 КиБ) — защита от переполнения памяти.
	maxRequestBytes = 64 * 1024
	dialTimeout     = 3 * time.Second
)

// ServeUnix запускает прослушивание Unix-сокета и обрабатывает запросы до отмены ctx.
func ServeUnix(ctx context.Context, socketPath string, engine *core.Engine) error {
	if err := os.MkdirAll(filepath.Dir(socketPath), 0o750); err != nil {
		return fmt.Errorf("создание каталога для сокета %s: %w", socketPath, err)
	}
	// Удаляем старый файл сокета, если остался после некорректного завершения.
	_ = os.Remove(socketPath)

	listener, err := net.Listen("unix", socketPath)
	if err != nil {
		return fmt.Errorf("открытие Unix-сокета %s: %w", socketPath, err)
	}
	if chmodErr := os.Chmod(socketPath, 0o660); chmodErr != nil {
		_ = listener.Close()
		_ = os.Remove(socketPath)
		return fmt.Errorf("установка прав 0660 на сокет %s: %w", socketPath, chmodErr)
	}

	var wg sync.WaitGroup
	go func() {
		<-ctx.Done()
		_ = listener.Close()
	}()

	defer func() {
		_ = listener.Close()
		wg.Wait()
		_ = os.Remove(socketPath)
	}()

	log.Printf("sysagentd %s запущен: socket=%s mode=%s pid=%d",
		core.Version, socketPath, engine.Config().Policy.Mode, os.Getpid())

	connDeadline := time.Duration(engine.Config().Policy.CommandTimeoutSec+10) * time.Second

	for {
		conn, acceptErr := listener.Accept()
		if acceptErr != nil {
			if ctx.Err() != nil || errors.Is(acceptErr, net.ErrClosed) {
				return nil
			}
			log.Printf("предупреждение: ошибка accept: %v", acceptErr)
			continue
		}
		wg.Add(1)
		go func(c net.Conn) {
			defer wg.Done()
			handleConn(ctx, c, engine, connDeadline)
		}(conn)
	}
}

func handleConn(ctx context.Context, conn net.Conn, engine *core.Engine, deadline time.Duration) {
	defer conn.Close()
	_ = conn.SetDeadline(time.Now().Add(deadline))

	var req core.Request
	dec := json.NewDecoder(io.LimitReader(conn, maxRequestBytes))
	dec.DisallowUnknownFields()
	if err := dec.Decode(&req); err != nil {
		_ = json.NewEncoder(conn).Encode(core.Response{
			OK:      false,
			Error:   "некорректный JSON-запрос: " + err.Error(),
			Elapsed: "0s",
		})
		return
	}

	if req.Caller == "" {
		req.Caller = "unix-socket"
	}
	resp := engine.Execute(ctx, req)
	_ = json.NewEncoder(conn).Encode(resp)
}

// CallUnix отправляет один запрос демону через Unix-сокет и возвращает структурированный ответ.
func CallUnix(socketPath string, req core.Request, timeout time.Duration) (core.Response, error) {
	if timeout <= 0 {
		timeout = 30 * time.Second
	}
	conn, err := net.DialTimeout("unix", socketPath, dialTimeout)
	if err != nil {
		return core.Response{}, err
	}
	defer conn.Close()
	_ = conn.SetDeadline(time.Now().Add(timeout))

	if req.Caller == "" {
		req.Caller = "cli"
	}
	if err := json.NewEncoder(conn).Encode(req); err != nil {
		return core.Response{}, fmt.Errorf("отправка запроса демону: %w", err)
	}

	var resp core.Response
	if err := json.NewDecoder(conn).Decode(&resp); err != nil {
		return core.Response{}, fmt.Errorf("чтение ответа демона: %w", err)
	}
	return resp, nil
}
EOF
cd /opt/sysagent && go build ./internal/ipc && echo "ipc: OK"
