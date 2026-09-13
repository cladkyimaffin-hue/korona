---
document_id: "PROXMOX-CEPH-OSD-POOLS-DEPLOYMENT-2026-001"
title: "Развёртывание OSD и пулов Ceph на pve01/pve02 — до HEALTH_OK"
document_type: "setup"
status: "completed"
priority: "critical"
date_created: 2026-09-03
date_modified: 2026-09-03
next_review: 2026-12-01
author: "cladkyimaffin-hue"
category: "04_Storage_Ceph"
tags:
  - "ProxmoxVE"
  - "Ceph"
  - "OSD"
  - "Storage"
  - "Setup"
  - "pve01"
  - "pve02"
ai_summary: "Фактическое развёртывание Ceph до состояния HEALTH_OK: установка пакетов (устранены конфликт версий ceph-common и битый enterprise-репозиторий ceph-tentacle → ceph-squid no-subscription), создание 4 OSD (по 2 на узел: nvme0n1 класс nvme, sdb класс ssd), создание пулов ceph-fast (CRUSH только на nvme) и ceph-bulk (CRUSH только на ssd), исправление параметров Size/Min Size под реальные 2 узла — включая системный пул .mgr, который по умолчанию создаётся с Size=3."
dont_repeat:
  - "Не оставлять GUI-умолчания при создании пула на 2-узловом кластере — Proxmox по умолчанию предлагает Size=3/Min Size=2, что для 2 узлов даёт `active+undersized+degraded`; сразу ставить Size=2."
  - "Не забывать проверить и поправить системный пул `.mgr` — он создаётся автоматически при установке Ceph с Size=3 независимо от пользовательских пулов, и тоже блокирует HEALTH_OK на 2-узловом кластере."
  - "Не путать `.list`- и `.sources`-формат при правке репозиториев на PVE 9/trixie — создание нового `.list` рядом с уже настроенным `.sources` даёт предупреждения о дублировании источников (`configured multiple times`)."
  - "При проблемах установки Ceph первым делом проверять, не тянется ли автоматически enterprise-репозиторий с неверным/несуществующим релизом (например, `ceph-tentacle`) — заменять на актуальный no-subscription релиз (в этом случае — `ceph-squid`)."
related_files:
  - "PROXMOX-CEPH-OSD-DISK-PREP-2026-001"
  - "PROXMOX-POSTINSTALL-SCRIPT-2026-001"
schema_version: "1.0"
---

# Развёртывание OSD и пулов Ceph на pve01/pve02

## Предварительные условия
- [ ] Диски очищены и проверены (`PROXMOX-CEPH-OSD-DISK-PREP-2026-001`).
- [ ] Синхронизация времени в норме на обеих нодах.

## Шаг 1: установка пакетов Ceph — известная проблема с зависимостями

`Datacenter → Ceph → Install Ceph` завершилась ошибкой:
```
ceph-base : Depends: ceph-common (= 19.2.3-pve1) but 19.2.3-pve4 is to be installed
apt failed during ceph installation (25600)
```
**Причина:** рассинхронизация версий пакетов в кэше apt. **Решение:**
```bash
apt update
apt full-upgrade -y
```

**Вторая проблема, вскрывшаяся после апдейта:** битый enterprise-репозиторий:
```
Err: https://enterprise.proxmox.com/debian/ceph-tentacle trixie InRelease
401 Unauthorized
```
`ceph-tentacle` — некорректное/недоступное без подписки имя релиза.
Исправление (deb822-формат, PVE 9/trixie):
```bash
sed -i 's/pve-enterprise/pve-no-subscription/g' /etc/apt/sources.list.d/proxmox.sources
cat << 'EOF' > /etc/apt/sources.list.d/ceph.sources
Types: deb
URIs: http://download.proxmox.com/debian/ceph-squid
Suites: trixie
Components: no-subscription
Signed-By: /usr/share/keyrings/proxmox-archive-keyring.gpg
EOF
apt update
```
⚠️ Не создавать при этом дублирующий `.list`-файл рядом с уже настроенным
`.sources` — вызовет предупреждения `configured multiple times`. Проверка
чистого результата: `apt update` без ошибок 401 и без warning про дубли.

После исправления Ceph-релиз для установки — **squid** (Ceph 19.2, под PVE 9.2/Debian 13 trixie).

## Шаг 2: мониторы и менеджеры
`Ceph → Monitors → Create` и `Ceph → Managers → Create` — по одному на каждой ноде (`pve01`, `pve02`).

## Шаг 3: создание OSD

`Ceph → OSD → Create`, диск + `DB Disk: use OSD disk` (отдельный WAL/DB не нужен — оба диска SSD/NVMe):

| OSD | Нода | Диск | Device Class | Роль |
|---|---|---|---|---|
| osd.0 | pve01 | `/dev/nvme0n1` (~3.84 ТБ) | `nvme` | быстрый |
| osd.1 | pve01 | `/dev/sdb` (~7.68 ТБ) | `ssd` | ёмкий |
| osd.2 | pve02 | `/dev/nvme0n1` (~3.84 ТБ) | `nvme` | быстрый |
| osd.3 | pve02 | `/dev/sdb` (~7.68 ТБ) | `ssd` | ёмкий |

⚠️ В списке дисков также присутствуют `/dev/sda`/`/dev/sda3` (~479 ГБ,
системный) — не выбирать их под OSD.

## Шаг 4: создание пулов — обязательная коррекция GUI-умолчаний

**Проблема:** GUI по умолчанию предлагает `Size=3`/`Min Size=2` — для
кластера с 2 узлами это гарантированно даёт `active+undersized+degraded`
(некуда положить третью реплику).

**Верные параметры для обоих пользовательских пулов:**

| Пул | CRUSH Rule | Size | Min Size | Назначение |
|---|---|---|---|---|
| `ceph-fast` | `nvme-replicated` (строго на `nvme`-класс) | 2 | 1 | OLTP: 1С, терминальный сервер, AD |
| `ceph-bulk` | `ssd-replicated` (строго на `ssd`-класс) | 2 | 1 | Бэкапы, менее критичные ВМ |

Создание через GUI (`Ceph → Pools → Create`), сразу с `Size=2`. Если по
инерции создано с `Min Size=2` — довести до `1` через консоль:
```bash
ceph osd pool set ceph-fast min_size 1
ceph osd pool set ceph-bulk min_size 1
```

**Отдельно — системный пул `.mgr`:** создаётся автоматически при установке
Ceph с `Size=3` **независимо от пользовательских пулов** и тоже мешает
`HEALTH_OK` на 2 узлах:
```bash
ceph osd pool set .mgr min_size 1
ceph osd pool set .mgr size 2
```

## Проверка результата — подтверждённое финальное состояние
```bash
ceph -s
```
```
health: HEALTH_OK
osd: 4 osds: 4 up, 4 in
pools: .mgr (1, size 2/min 1), ceph-fast (2, size 2/min 1), ceph-bulk (3, size 2/min 1)
pgs: 256 active+clean
```
- [x] Оба RBD-хранилища (`ceph-fast`, `ceph-bulk`) добавлены в Proxmox на уровне Datacenter (Content: Disk image, Container).
- [x] QDevice подключён, кворум стабилен.

## Расширение в будущем (при добавлении 3-го/4-го узла с OSD)
1. Установить Ceph, создать OSD и монитор на новом узле.
2. Пересчитать `Size`/`Min Size` пулов под новое число узлов — например, при 3 узлах: `ceph osd pool set <pool> size 3` и `min_size 2`.
3. Количество PG менять вручную не нужно — `PG Autoscaler Mode: on` пересчитает сам.
4. CRUSH rules и сетевая конфигурация (Public/Cluster Network) не требуют изменений.

## ⛔ Don't repeat
- Не оставлять `Size=3`/`Min Size=2` по умолчанию на 2-узловом кластере — ни для пользовательских пулов, ни для системного `.mgr`.
- Не путать `.list` и `.sources` при правке репозиториев на PVE 9.
- Проверять, не подставился ли некорректный enterprise-релиз (`ceph-tentacle`) вместо `no-subscription`.

## Связанные документы
- «Подготовка дисков и архитектура OSD» — предшествующий шаг (очистка дисков, обоснование архитектуры)
- «Скрипт первичной настройки Proxmox VE (pstInstall)» — там же встречалась аналогичная проблема с `.list`/`.sources` на уровне пакетов Proxmox, здесь — то же самое на уровне Ceph

---
*Примечание при миграции (2026-09-11): документ построен на основе
финального резюме, которое уже присутствовало в конце исходного файла
(«Контекст для перехода в новый чат») — оно само по себе было точным и
проверенным итогом, использовано как основа таблиц выше. Помимо этого,
в тело перенесены обе реальные проблемы (конфликт версий пакетов,
enterprise-репозиторий `ceph-tentacle`) и обязательная коррекция
Size/Min Size, включая нюанс с системным пулом `.mgr`, который легко
упустить. Содержание не изменено, только структурировано.*
