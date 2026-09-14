---
document_id: "PROXMOX-VAULTWARDEN-INSTALL-2026-001"
title: "Установка Vaultwarden (сервер паролей) в LXC Debian 12 — CT 600 (passwd)"
document_type: "setup"
status: "completed"
priority: "medium"
date_created: 2026-09-08
date_modified: 2026-09-09
next_review: 2026-12-01
author: "cladkyimaffin-hue"
category: "07_Vaultwarden"
tags:
  - "Vaultwarden"
  - "LXC"
  - "Debian12"
  - "ProxmoxVE"
ai_summary: "Vaultwarden 1.37.2 + Web-Vault первоначально 2026.7.0 (позже понижен до v2025.12.2 из-за несовместимости API, см. примечание) установлены в LXC-контейнере CT 600 (hostname passwd, полный клон шаблона 1000 debian12-pattern, ceph-fast, 192.168.200.230/22) для централизованного хранения паролей администраторов/сервисных учёток, отдельно от AD DS. Автоматическая установка через apt из vaultwarden-deb.pages.dev невозможна (блокировка HTTPS к Cloudflare Pages на уровне шлюза) — пакеты .deb загружены вручную и переданы через pct push (с переименованием в .iso для обхода фильтра загрузки в Proxmox). Служба подтверждённо работает (HTTP 200 OK на порту 8000), ADMIN_TOKEN сгенерирован в формате Argon2id."
dont_repeat:
  - "Не использовать pct clone без --full для production-контейнеров — по умолчанию создаётся linked clone."
  - "Не указывать local-lvm как storage для production CT — production в этой инфраструктуре только на ceph-fast."
  - "Не задавать --net0 в pct clone — параметр не поддерживается, сеть настраивается отдельно через pct set (та же особенность, что и в PROXMOX-LXC-DEBIAN12-TEMPLATE-2026-001)."
  - "Не использовать текстовый ADMIN_TOKEN — Vaultwarden принимает только Argon2id hash, текстовый токен отклоняется ошибкой Authorization failed."
  - "Не рассчитывать на автоматическую установку через apt из vaultwarden-deb.pages.dev — репозиторий недоступен из-за блокировки HTTPS к Cloudflare Pages на уровне шлюза/провайдера."
  - "Технически шаблон называется debian12-pattern, не debian12-template — в вебе Proxmox может отображаться под вторым именем, это одно и то же."
  - "Пакет vaultwarden-web-vault устанавливает файлы в /usr/share/vaultwarden/web-vault, а не в /var/lib/vaultwarden/web-vault — путь в конфиге должен указывать именно на share."
  - "Web-Vault 2026.7.0 несовместим с Vaultwarden 1.37.2 (ошибка «missing field newMasterPasswordHash» при смене пароля) — использовать Web-Vault v2025.12.2, а не последнюю версию."
  - "Значение ADMIN_TOKEN (hash Argon2id) содержит символы $ — /etc/vaultwarden.env подключён как systemd EnvironmentFile (не Environment), которая читает файл БУКВАЛЬНО: писать одинарные $, без кавычек и БЕЗ удвоения $$ (удвоение — правило для директивы Environment= внутри .service-файла, здесь оно не действует и само ломает токен). Предпочтительно использовать команду `vaultwarden hash` вместо ручного openssl+argon2."
related_files:
  - "PROXMOX-LXC-DEBIAN12-TEMPLATE-2026-001"
schema_version: "1.0"
---

# Установка Vaultwarden (CT 600, passwd)

## Что настраивается и зачем
Централизованное хранилище паролей администраторов, сервисных учётных
записей и root-доступа к Proxmox/сетевому оборудованию — отдельно от
пользовательской аутентификации Active Directory.

## Предварительные условия
- [ ] Шаблон LXC `1000` (`debian12-pattern`) существует (`PROXMOX-LXC-DEBIAN12-TEMPLATE-2026-001`).
- [ ] .deb-пакеты Vaultwarden и Web-Vault скачаны заранее на локальный ПК (прямая загрузка на сервере заблокирована — см. ниже).

## Шаги

**1. Создать контейнер (обязательно `--full`, сеть — отдельной командой):**
```bash
pct clone 1000 600 --hostname passwd --storage ceph-fast --full
pct set 600 --net0 name=eth0,bridge=vmbr0,ip=192.168.200.230/22,gw=192.168.200.1
pct start 600
```

## ⚠️ Известная проблема: блокировка HTTPS к Cloudflare Pages

Прямая загрузка пакетов с GitHub Releases и `vaultwarden-deb.pages.dev`
**блокируется на уровне шлюза/провайдера** (TLS timeout к Cloudflare
Pages) — это внешнее ограничение сети, не связано с конфигурацией
Proxmox. `apt`-репозиторий тоже недоступен по той же причине.

**Обходной путь — ручная загрузка через веб-интерфейс Proxmox:**
1. Скачать на локальном ПК:
   `vaultwarden_1.37.2-1_amd64.deb` и `vaultwarden-web-vault_2026.7.0-1_all.deb`
   с `https://vaultwarden-deb.pages.dev/dists/bookworm/main/binary-amd64/`.
2. **Переименовать файлы в `.iso`** — веб-интерфейс Proxmox фильтрует
   загрузку по расширению в разделе ISO Images, `.deb` не проходит фильтр,
   `.iso` проходит.
3. Загрузить оба файла через `local (pve01) → ISO Images → Upload`.
4. Передать в контейнер и вернуть настоящее расширение при установке:
```bash
pct push 600 /var/lib/vz/template/iso/vaultwarden_1.37.2-1_amd64.deb.iso /tmp/vaultwarden.deb
pct push 600 /var/lib/vz/template/iso/vaultwarden-web-vault_2026.7.0-1_all.deb.iso /tmp/vaultwarden-web-vault.deb
pct exec 600 -- dpkg -i /tmp/vaultwarden-web-vault.deb /tmp/vaultwarden.deb
pct exec 600 -- apt --fix-broken install -y
```

**2. Исправить путь к Web-Vault** (пакет ставит файлы в `share`, не в `lib`):
```bash
pct exec 600 -- bash -c "echo -e '\nROCKET_ADDRESS=0.0.0.0\nWEB_VAULT_FOLDER=/usr/share/vaultwarden/web-vault' >> /etc/vaultwarden.env"
pct exec 600 -- systemctl restart vaultwarden
```

**3. Сгенерировать `ADMIN_TOKEN` в формате Argon2id** (текстовый токен не работает):
```bash
pct exec 600 -- apt install -y argon2
pct exec 600 -- bash -c 'TOKEN=$(openssl rand -base64 48) && echo "$TOKEN" && echo -n "$TOKEN" | argon2 $(openssl rand -base64 16) -id -t 2 -m 16 -l 32'
# Полученный hash вписать в /etc/vaultwarden.env как ADMIN_TOKEN="<hash>"
pct exec 600 -- systemctl restart vaultwarden
```

## Итоговая конфигурация (`/etc/vaultwarden.env`, ключевые параметры)
```
ROCKET_ADDRESS=0.0.0.0
WEB_VAULT_FOLDER=/usr/share/vaultwarden/web-vault
ADMIN_TOKEN="$argon2id$v=19$m=65536,t=2,p=1$<SALT>$<HASH>"
```

## Проверка результата — подтверждено фактическим выполнением
```bash
pct exec 600 -- systemctl status vaultwarden --no-pager -l | grep -E 'Active:|Rocket has launched|ERROR'
pct exec 600 -- curl -s -I http://127.0.0.1:8000
```
Подтверждено: `Active: active (running)`, `Rocket has launched from
http://0.0.0.0:8000`, `curl` → `HTTP/1.1 200 OK`, без строк `ERROR`.

- [x] CT 600 (`passwd`) — full clone, `ceph-fast`, `192.168.200.230/22`.
- [x] Vaultwarden 1.37.2 + Web-Vault установлены и запущены (изначально 2026.7.0, впоследствии понижен до v2025.12.2 — см. примечание о миграции).
- [x] `ADMIN_TOKEN` в формате Argon2id, а не открытым текстом.
- [ ] HTTPS (обратный прокси) — **не настроен в рамках этого документа**, без него браузеры блокируют Subtle Crypto API и веб-интерфейс входа не заработает полноценно; см. отдельный документ по HTTPS.

## Потребление ресурсов
Vaultwarden в LXC Debian 12 потребляет ~9 МБ RAM в состоянии простоя —
выделенные 2 CPU / 4 GiB RAM / 100 GiB диска многократно избыточны для
текущей нагрузки.

## ⛔ Don't repeat
См. `dont_repeat` во фронтматтере — семь пунктов, каждый — реальная
преграда именно этой установки.

## Связанные документы
- «Создание шаблона Debian 12 LXC и клонирование» — исходный шаблон 1000
- Настройка HTTPS для Vaultwarden — обязательный следующий шаг (см. пачку)
- Настройка входа в /admin — панель администратора Vaultwarden

---
*Примечание при миграции (2026-09-11): фронтматтер использовал схему без
явного `document_id` — присвоен новый по формату `SCHEMA.md`. Содержание
не изменено, убрана диалоговая рамка чата. По документу «Настройка HTTPS
для Vaultwarden #2» (та же пачка) уточнено: Web-Vault 2026.7.0 оказался
несовместим с Vaultwarden 1.37.2 и был впоследствии понижен до v2025.12.2 —
отражено выше; также исправлен реальный gotcha про ADMIN_TOKEN — первая
версия примечания ошибочно рекомендовала экранирование `$$`, что на самом
деле является причиной ошибки, а не решением (см.
`PROXMOX-VAULTWARDEN-ADMIN-TOKEN-2026-001` для полной картины).*
