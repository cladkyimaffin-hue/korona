---
document_id: "PROXMOX-POSTINSTALL-SCRIPT-2026-001"
title: "Скрипт первичной настройки Proxmox VE (pstInstall) — типовые ответы для одного узла без подписки"
document_type: "setup"
status: "completed"
priority: "medium"
date_created: 2026-08-30
date_modified: 2026-09-02
next_review: 2026-12-01
author: "cladkyimaffin-hue"
category: "02_Installation"
tags:
  - "ProxmoxVE"
  - "Automation"
  - "Bash"
  - "Setup"
ai_summary: "Разбор диалогов whiptail-скрипта пост-установочной настройки Proxmox VE (репозитории enterprise/no-subscription, subscription nag, HA, Corosync) с рекомендованными ответами для сценария «один сервер, без подписки, кластер не планируется». Плюс известная проблема: на Proxmox VE 9 (Debian trixie) репозитории хранятся в новом deb822-формате (.sources), команды под старый .list формат не сработают."
dont_repeat:
  - "Не комментировать `/etc/apt/sources.list.d/pve-enterprise.list` без предварительной проверки, что репозитории вообще в старом .list-формате — на PVE 9/Debian trixie используется deb822 (.sources), команды `sed 's/^deb/#deb/'` там ничего не найдут."
  - "Не предлагать сторонние скрипты отключения nag-экрана из непроверенных источников — использовать штатный патч proxmoxlib.js или официальный community-скрипт."
  - "Не убивать процесс apt/dpkg и не удалять lock-файлы «для ускорения» при `Waiting for cache lock` — обычно апт освобождается сам за 1-10 минут."
related_files:
  - "PROXMOX-NODE-RENAME-2026-001"
schema_version: "1.0"
---

# Скрипт первичной настройки Proxmox VE (pstInstall)

## Что настраивается и зачем
Автоматизация типовых пост-установочных задач на свежем узле Proxmox VE:
переключение репозиториев с enterprise на no-subscription, отключение
subscription nag-экрана, вопросы про HA и Corosync. Скрипт запускается
через whiptail-диалоги сразу после установки, до добавления узла в кластер.

## Предварительные условия
- [ ] Сервер имеет доступ в интернет для загрузки пакетов.
- [ ] Скрипт запускается **до** объединения узла в кластер.

## Диалоги скрипта и рекомендованные ответы (сценарий: один сервер, дом, без подписки)

| Диалог | Ответ | Почему |
|---|---|---|
| `'pve-enterprise' repository already exists` | **disable** | Без ключа подписки репозиторий даёт ошибку 401 при каждом `apt update` |
| `'ceph enterprise' repository already exists` | **disable** | То же самое; при необходимости Ceph — отдельно добавить `ceph-no-subscription` |
| `'pve-no-subscription' repository is currently ENABLED` | **keep** | Именно из него приходят обновления без подписки |
| `Disable subscription nag?` | **yes** | Убирает всплывающее напоминание в веб-интерфейсе; чисто косметическое |
| `Support Subscriptions` (информационное окно) | **Ok** (Enter) | Выбирать нечего |
| `Enable high availability?` | **no** (один узел) / **yes** (кластер 3+ узла или 2+QDevice) | HA бессмысленна и потенциально вредна на одиночном узле |
| `Corosync` — отключить? | **yes** (один узел, кластер не планируется) / **no** (планируется кластер/HA) | Corosync обязателен для кластера, живой миграции, HA |

Для сценария с подпиской (production) — обратная логика по первым трём
строкам: **keep** enterprise-репозитории, **disable/delete**
no-subscription.

## Шаги после завершения диалогов
```bash
apt update
apt full-upgrade -y
reboot
```
Убедиться, что `apt update` проходит без ошибок 401 и пакеты идут с `download.proxmox.com`.

## Проверка результата
- [ ] `apt update` без ошибок 401/`NO_PUBKEY`.
- [ ] Веб-интерфейс без nag-баннера о подписке.
- [ ] На одиночном узле: `systemctl status corosync` — по решению (отключён, если выбрано `yes` на этом шаге).

## ⚠️ Известная проблема: PVE 9 / Debian trixie использует deb822 (`.sources`), не `.list`

Команды вида `sed -i 's/^deb/#deb/' /etc/apt/sources.list.d/pve-enterprise.list`
на **Proxmox VE 9 (Debian 13, trixie)** завершатся ошибкой
`sed: can't read ...: No such file or directory` — репозитории там хранятся
в новом структурированном формате `.sources` (deb822), а не в старых `.list`.

**Проверить формат:**
```bash
ls -l /etc/apt/sources.list.d/
```

**Отключить enterprise-репозитории в deb822-формате:**
```bash
for f in /etc/apt/sources.list.d/pve-enterprise.sources /etc/apt/sources.list.d/ceph.sources; do
  [ -f "$f" ] && { grep -q '^Enabled:' "$f" && sed -i 's/^Enabled:.*/Enabled: no/' "$f" || sed -i '1i Enabled: no' "$f"; }
done
```
Логика: если строка `Enabled:` уже есть — заменить на `Enabled: no`, если нет — добавить в начало файла.

**Проверить, что no-subscription включён:**
```bash
grep -ri 'no-subscription' /etc/apt/sources.list.d/
```

**Прочие типовые ошибки `apt update` (exit code 100) и что делать:**

| Симптом | Причина | Решение |
|---|---|---|
| `401 Unauthorized` на `enterprise.proxmox.com` | Enterprise-репозиторий всё ещё включён | Отключить по инструкции выше (`.sources`) или `sed` для старого `.list` |
| `Could not get lock ... held by process ...` | Фоновый `apt-daily.service`/`apt-daily-upgrade.service` ещё работает | Подождать 1-10 минут; не убивать процесс, проверить `ps -p <pid> -o pid,etime,cmd` |
| `NO_PUBKEY ...` | Не хватает ключа Proxmox | `wget https://enterprise.proxmox.com/debian/proxmox-release-bookworm.gpg -O /etc/apt/trusted.gpg.d/proxmox-release-bookworm.gpg` (для trixie — `proxmox-release-trixie.gpg`) |
| `Temporary failure resolving ...` | Проблема сети/DNS | `ping -c3 download.proxmox.com`, проверить `/etc/resolv.conf` |
| `Malformed entry ... in list file ...` | Некорректное комментирование строки | Открыть указанный файл и поправить/закомментировать строку целиком |

**Подтверждено фактическим выполнением на `pve02`** (PVE 9/trixie): после
перехода на deb822-команды `apt update` прошёл чисто (`All packages are up
to date`), `apt full-upgrade` не нашёл пакетов для обновления.

## ⛔ Don't repeat
- Не предполагать формат `.list` — сначала проверить `ls /etc/apt/sources.list.d/`.
- Не убивать apt/dpkg процессы и не удалять lock-файлы при обычном ожидании блокировки.
- Не использовать сторонние no-nag скрипты из непроверенных источников.

## Связанные документы
- «Смена hostname узла Proxmox VE» — тоже выполняется до вступления узла в кластер, логичный сосед по порядку операций после установки

---
*Примечание при миграции (2026-09-11): в исходном файле объединены (1)
разбор диалогов скрипта и (2) реальный инцидент с ошибкой apt на `pve02`
из-за формата `.sources` — оставлены в одном документе (не разделялись на
troubleshooting/setup, как `bond0.md`), так как это один короткий связанный
эпизод настройки одного и того же узла, а не два самостоятельных объёмных
расследования. Убрана диалоговая рамка USER/ASSISTANT, содержание не
изменено.*
