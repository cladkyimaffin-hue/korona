---
document_id: "PROXMOX-VAULTWARDEN-HTTPS-CADDY-2026-001"
title: "Настройка HTTPS для Vaultwarden через Caddy (reverse proxy, самоподписанный сертификат)"
document_type: "setup"
status: "completed"
priority: "medium"
date_created: 2026-09-10
date_modified: 2026-09-10
next_review: 2026-12-01
author: "cladkyimaffin-hue"
category: "07_Vaultwarden"
tags:
  - "Vaultwarden"
  - "ProxmoxVE"
  - "LXC"
  - "Debian12"
ai_summary: "HTTPS для Vaultwarden (CT 600, passwd.krnn.ru) через Caddy 2.11.4 как reverse proxy на 127.0.0.1:8000, tls internal (самоподписанный сертификат от внутреннего Caddy CA — нет публичного домена/DNS). Без HTTPS браузеры блокируют Subtle Crypto API, необходимый Vaultwarden для шифрования в браузере. Проверено curl и браузером: HTTP/2 200, заголовки Server: Rocket/Via: 1.1 Caddy."
dont_repeat:
  - "Не считать «HTTP страница не открывается» багом Vaultwarden — это осознанное ограничение браузеров: Subtle Crypto API работает только на HTTPS, обязателен обратный прокси с сертификатом (даже самоподписанным для внутренней сети)."
  - "Не пугаться вывода curl `subject: [NONE]` для сертификата — это особенность отображения curl для сертификатов, полагающихся только на SAN без classic CN; наличие `issuer: CN=Caddy Local Authority` и успешный handshake — признак, что всё работает."
  - "Не забывать, что предупреждение браузера о недоверенном сертификате при tls internal — ожидаемое поведение, а не ошибка настройки; ваш компьютер просто не доверяет внутреннему Caddy CA."
related_files:
  - "PROXMOX-VAULTWARDEN-INSTALL-2026-001"
  - "PROXMOX-VAULTWARDEN-ADMIN-TOKEN-2026-001"
schema_version: "1.0"
---

# Настройка HTTPS для Vaultwarden через Caddy

## Почему это обязательно
Vaultwarden шифрует данные прямо в браузере через Web Crypto (Subtle
Crypto) API. Современные браузеры (Chrome/Firefox/Edge) **запрещают**
использование этого API на обычном HTTP — без HTTPS главная страница
входа не заработает (админ-панель на HTTP при этом может открываться —
разные требования у разных частей интерфейса).

## Шаги

**1. Установить Caddy из официального репозитория:**
```bash
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https curl
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
# добавить репозиторий Caddy stable, затем:
sudo apt update && sudo apt install -y caddy
```

**2. Настроить `/etc/caddy/Caddyfile`** (проксирование с TLS на внутренний Vaultwarden):
```caddy
192.168.200.230, passwd.krnn.ru {
    # Самоподписанный сертификат для указанных имён (нет публичного DNS)
    tls internal

    reverse_proxy 127.0.0.1:8000 {
        header_up Host {host}
        header_up X-Real-IP {remote_host}
        header_up X-Forwarded-For {remote_host}
        header_up X-Forwarded-Proto {scheme}
    }
}
```
`tls internal` заставляет Caddy сгенерировать сертификат от собственного
внутреннего CA — это осознанный выбор для внутренней сети без публичного
домена, не временное решение по недосмотру.

**3. Перезапустить/перезагрузить конфигурацию:**
```bash
sudo systemctl restart caddy    # при первой установке
sudo systemctl reload caddy      # при последующих правках Caddyfile — без разрыва соединений
```

## Проверка результата — подтверждено
```bash
curl -kvI https://192.168.200.230
```
Подтверждено: TLS 1.3, `HTTP/2 200`, заголовки `server: Rocket`,
`via: 1.1 Caddy` — Caddy успешно принимает HTTPS и проксирует в Vaultwarden.

- [x] Caddy 2.11.4 установлен и работает как reverse proxy.
- [x] TLS через `tls internal`, оба имени (`192.168.200.230`, `passwd.krnn.ru`) покрыты сертификатом.
- [x] Главная страница входа Vaultwarden открывается по HTTPS без ошибки Subtle Crypto API.
- [ ] Сертификат остаётся недоверенным для клиентских машин (ожидаемо для `tls internal`) — при необходимости отдельно распространить корневой сертификат Caddy Local CA на клиентские машины, либо перейти на сертификат от внутреннего/публичного CA.

## Откат
```bash
sudo apt remove --purge caddy
sudo rm /etc/apt/sources.list.d/caddy-stable.list
```

## ⛔ Don't repeat
См. `dont_repeat` во фронтматтере.

## Связанные документы
- «Установка Vaultwarden CT600» — базовая установка, на которую настраивается этот reverse proxy
- «ADMIN_TOKEN и смена мастер-пароля» — следующая проблема этой же сессии

---
*Примечание при миграции (2026-09-11): исходный файл («Настройка HTTPS для
Vaultwarden #2.md», 3496 строк) охватывал три разные темы — сама настройка
HTTPS, отдельная проблема с ADMIN_TOKEN/мастер-паролем, и начало темы
управления пользователями. Разделено на документы по теме; этот покрывает
только HTTPS/Caddy. Содержание не изменено, убрана диалоговая рамка.*
