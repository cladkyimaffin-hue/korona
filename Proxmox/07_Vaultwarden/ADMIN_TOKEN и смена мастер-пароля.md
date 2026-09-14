---
document_id: "PROXMOX-VAULTWARDEN-ADMIN-TOKEN-2026-001"
title: "Vaultwarden: «Invalid admin token» из-за лишнего экранирования $$ в EnvironmentFile, ошибка смены мастер-пароля"
document_type: "troubleshooting"
status: "completed"
priority: "medium"
date_created: 2026-09-10
date_modified: 2026-09-10
next_review: 2026-12-01
author: "cladkyimaffin-hue"
category: "07_Vaultwarden"
tags:
  - "Vaultwarden"
  - "Troubleshooting"
  - "ProxmoxVE"
ai_summary: "Две связанные проблемы Vaultwarden (CT 600). (1) «Invalid admin token» + «plain text ADMIN_TOKEN»: ADMIN_TOKEN лежит в /etc/vaultwarden.env, подключённом через systemd EnvironmentFile= (не Environment=) — экранирование $$ (правило для директивы Environment= внутри .service-файла) здесь НЕ нужно и является самой причиной ошибки: EnvironmentFile читает файл буквально, и systemd передаёт процессу строку с двойными $$, которую Vaultwarden не распознаёт как Argon2-хеш. Исправление — заменить $$ на одинарный $ в файле. Подтверждено через /proc/<PID>/environ и итоговый успешный вход в /admin. (2) Ошибка 422/«missing field newMasterPasswordHash» при смене мастер-пароля — несовместимость Vaultwarden 1.37.2 с Web-Vault 2026.7.0, решение — откат Web-Vault до v2025.12.2."
dont_repeat:
  - "Не экранировать $ как $$ в /etc/vaultwarden.env, если он подключён как systemd EnvironmentFile= (не Environment=) — правило удвоения относится к директиве Environment= внутри .service-файла или docker-compose.yml, а не к EnvironmentFile=. EnvironmentFile читает файл буквально: один $ — так и передаётся один $; удвоение только портит значение."
  - "Не гадать о причине несовпадения токена — проверять напрямую через `cat /proc/<PID>/environ | tr '\\0' '\\n' | grep -i admin_token`, это даёт однозначный ответ, что реально получил процесс."
  - "Не считать last resort («сбросить/пересоздать всё с нуля») первым шагом диагностики — сначала проверить config.json (приоритет над EnvironmentFile) и runtime-окружение процесса."
  - "Rate limit /admin (429 Too Many Requests) — временная защита, а не поломка; при повторных попытках входа во время отладки ожидать 5-15 минут или перезапустить службу; после успешной настройки — ограничить доступ к /admin по IP в Caddy, а не оставлять rate limit ослабленным навсегда."
  - "Не считать последнюю версию Web-Vault автоматически совместимой с текущей версией Vaultwarden — для 1.37.2 рабочая версия Web-Vault — v2025.12.2, не v2026.7.0."
  - "При ошибке смены мастер-пароля — сначала смотреть логи на конкретный код (422/missing field), не переходить сразу к деструктивному сбросу пароля через консоль."
related_files:
  - "PROXMOX-VAULTWARDEN-INSTALL-2026-001"
  - "PROXMOX-VAULTWARDEN-HTTPS-CADDY-2026-001"
schema_version: "1.0"
---

# ADMIN_TOKEN: экранирование $$ было причиной, а не решением

## Проблема 1: «Invalid admin token» / «you are using a plain text ADMIN_TOKEN»

**Симптомы:**
```
[NOTICE] You are using a plain text `ADMIN_TOKEN` which is insecure.
[ERROR] Invalid admin token. IP: 192.168.200.229
=> 401 Unauthorized
```
После нескольких попыток — `429 Too Many Requests` (временный rate limit).

**Ход диагностики (по порядку, все шаги read-only перед исправлением):**

1. **Проверка переопределения в `config.json`** (имеет приоритет над `EnvironmentFile`):
```bash
grep -i "admin_token" /var/lib/vaultwarden/data/config.json
# → No such file or directory — гипотеза исключена, файла нет
```

2. **Проверка, что реально передал systemd:**
```bash
systemctl show vaultwarden --property=Environment
# → Environment=  (пусто — ожидаемо для EnvironmentFile=, эта директива не отображается тут)
```

3. **Абсолютная истина — окружение самого запущенного процесса:**
```bash
cat /proc/<PID>/environ | tr '\0' '\n' | grep -i admin_token
# → ADMIN_TOKEN=$$argon2id$$v=19$$m=65540,t=3,p=4$$...$$...
```
Токен пришёл в процесс **с двойными `$$`** — вот и причина.

**Корневая причина:** правило «экранировать `$` как `$$`» относится к
директиве **`Environment=`** внутри `.service`-файла (или
`docker-compose.yml`), где systemd/Docker сами разворачивают `$$` → `$`.
Но `/etc/vaultwarden.env` подключён через **`EnvironmentFile=`**, которая
читает файл **буквально, без какой-либо обработки `$`**. В результате
предыдущая попытка «исправить» проблему удвоением `$` сама стала причиной:
Vaultwarden получал строку с `$$`, не распознавал её как Argon2-хеш
(валидный хеш начинается с одного `$`) и трактовал всё значение как
небезопасный plain-text пароль.

**Решение:**
```bash
sed -i '/^ADMIN_TOKEN=/ s/\$\$/\$/g' /etc/vaultwarden.env
grep '^ADMIN_TOKEN=' /etc/vaultwarden.env      # проверить — должен остаться один $
systemctl restart vaultwarden
```
Значение в файле должно быть **без кавычек и с одинарными `$`**:
```
ADMIN_TOKEN=$argon2id$v=19$m=65540,t=3,p=4$MmeKRnGK5RW5mJS7h3TOL89GrpLPXJPAtTK8FTqj9HM$DqsstvoSAETl9YhnsXbf43WeaUwJC6JhViIvuPoig78
```

**Подтверждено:** после исправления в логе исчезло предупреждение о
plain-text токене, вход в `/admin` под исходным (нехешированным) паролем,
использованным при генерации хеша через `vaultwarden hash`, прошёл успешно.

⚠️ Если во время отладки сработал rate limit (`429`) — подождать 5-15
минут или перезапустить службу; после успешного входа рекомендуется
ограничить доступ к `/admin` по IP в конфигурации Caddy (подсеть
`192.168.200.0/22`), а не оставлять rate limit временно ослабленным.

## Проблема 2: ошибка 422 при смене мастер-пароля («missing field newMasterPasswordHash»)

**Причина:** несовместимость API между Vaultwarden 1.37.2 и Web-Vault
2026.7.0 (более новый Web-Vault использует формат запроса, которого этот
бэкенд не ожидает).

**Решение:**
```bash
sudo systemctl stop vaultwarden
sudo rm -rf /usr/share/vaultwarden/web-vault
# скачать и установить web-vault v2025.12.2
sudo systemctl start vaultwarden
```
Подтверждено: после отката смена мастер-пароля через веб-интерфейс
(`Настройки → Учётная запись → Изменить мастер-пароль`, зная текущий
пароль) проходит без ошибки 422.

## ⛔ Don't repeat
См. `dont_repeat` во фронтматтере — главное: `Environment=` и
`EnvironmentFile=` обрабатывают `$` по-разному, не переносить правило
одного на другой.

## Проверка результата
- [x] `cat /proc/<PID>/environ | grep admin_token` — одинарный `$`, без ошибок.
- [x] Вход в `/admin` — успешен.
- [x] Смена мастер-пароля через веб-интерфейс — работает после отката Web-Vault до v2025.12.2.

## Связанные документы
- «Установка Vaultwarden CT600» — там же обновлено упоминание версии Web-Vault и добавлена ссылка на этот документ по ADMIN_TOKEN
- «HTTPS для Vaultwarden через Caddy» — предшествующий шаг этой же сессии

---
*Примечание при миграции (2026-09-11): собрано из ДВУХ исходных файлов —
хвоста «Настройка HTTPS для Vaultwarden #2.md» (где проблема была впервые
обнаружена и передана в новый чат с неверной гипотезой про нужность `$$`)
и «Настройка Vaultwarden вход в _admin #3.md» (где найдена настоящая
причина и решение). Предыдущая версия этого документа (в рамках этой же
миграции) ошибочно опиралась только на самопротиворечивое резюме
`known_issues` из файла #2, где решение было названо «экранировать $$» —
это неверно и исправлено здесь на основе полного протокола диагностики
из файла #3, включая прямую проверку `/proc/<PID>/environ`.*
