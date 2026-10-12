---
document_id: "PROXMOX-AUTOSTART-STARTUP-ORDER-2026-001"
title: "Автозапуск и порядок старта ВМ и LXC на pve01"
document_type: "runbook"
status: "completed"
priority: "high"
date_created: 2026-10-12
date_modified: 2026-10-12
next_review: 2026-12-01
author: "cladkyimaffin-hue"
category: "05_VirtualMachines"
tags: [ProxmoxVE, Autostart, pve01, LXC, ActiveDirectory, RDS, 1C-ERP, Vaultwarden, Zabbix, Ceph, Configuration, Production]
ai_summary: "На узле pve01 включён автозапуск (onboot: 1) и задан порядок запуска (startup order/up) для ВМ 2002 AD, 2003 TC, 2001 Srv1c и LXC 600 passwd (Vaultwarden), 700 zabbix: AD, затем TC, Srv1c, passwd, zabbix. Исходно параметр onboot у всех пяти объектов отсутствовал (автозапуск был выключен). Конфигурация подтверждена выводом qm config и pct config; поведение при перезагрузке узла не проверялось."
dont_repeat:
  - "Пустой вывод qm config VMID | grep onboot означает, что автозапуск выключен: параметр не задан."
  - "Параметр up задаёт только паузу в секундах после запуска гостя; он не проверяет готовность служб внутри гостя (DNS и Kerberos в AD, SQL в Srv1c)."
  - "Не считать порядок запуска проверенным без перезагрузки узла: подтверждена только конфигурация."
related_files:
  - "PROXMOX-VM-CLONE-2001-2026-001"
  - "PROXMOX-AD-THIRD-DC-PROMOTION-2026-001"
  - "PROXMOX-RDS-2003-2026-001"
  - "PROXMOX-VAULTWARDEN-INSTALL-2026-001"
  - "ZABBIX-STACK-INSTALL-2026-001"
  - "PROXMOX-VM-MIGRATION-ISOLATION-2026-001"
schema_version: "1.0"
---

# Автозапуск и порядок старта ВМ и LXC на pve01

## Цель
Включить автоматический запуск ВМ и LXC-контейнеров при перезагрузке или включении узла `pve01` и задать порядок запуска с паузами.

## Предварительные условия
- Все пять объектов находятся на `pve01`: команды `qm config` и `pct config` выполнены на `pve01` и вернули их конфигурации (VERIFIED).
- Объекты по выводу команд: ВМ 2002 `AD`, ВМ 2003 `TC`, ВМ 2001 `Srv1c`, CT 600 `passwd` (Vaultwarden, см. `PROXMOX-VAULTWARDEN-INSTALL-2026-001`), CT 700 `zabbix`. Признака `template` у них нет.
- Дата выполнения команд в чате не зафиксирована (после 2026-10-07).

## Исходное состояние (VERIFIED)
У ВМ 2001, 2002, 2003 и CT 600, 700 в конфигурации не было параметра `onboot` (пустой вывод `grep`). В Proxmox VE отсутствие параметра равносильно `onboot: 0`: автозапуск выключен (стандартное поведение).

## Шаги
Все команды выполняются на `pve01` под `root`.

1. Включить автозапуск:
```bash
qm set 2001 -onboot 1
qm set 2002 -onboot 1
qm set 2003 -onboot 1
pct set 600 -onboot 1
pct set 700 -onboot 1
```
2. Задать порядок запуска:
```bash
qm set 2002 -startup order=1,up=120; qm set 2003 -startup order=2,up=60; qm set 2001 -startup order=3,up=120
pct set 600 -startup order=4,up=60; pct set 700 -startup order=5,up=0
```

| Порядок | Объект | Имя | `up`, с |
|---|---|---|---|
| 1 | ВМ 2002 | `AD` | 120 |
| 2 | ВМ 2003 | `TC` | 60 |
| 3 | ВМ 2001 | `Srv1c` | 120 |
| 4 | CT 600 | `passwd` | 60 |
| 5 | CT 700 | `zabbix` | 0 |

`order` — приоритет запуска (меньшее число стартует раньше; гости с одинаковым `order` стартуют параллельно). `up` — пауза в секундах после запуска гостя перед запуском следующего. Параметр `down` не задан. Значения `up` предложены ассистентом как типичные и согласованы администратором; по реальному времени запуска служб не подбирались.

3. Проверка:
```bash
for vm in 2001 2002 2003; do echo "VM $vm:"; qm config $vm | grep -E '^(onboot|startup):'; done
for ct in 600 700; do echo "CT $ct:"; pct config $ct | grep -E '^(onboot|startup):'; done
```

## Откат
- Порядок запуска: `qm set <VMID> -delete startup`, `pct set <CTID> -delete startup`.
- Автозапуск: `qm set <VMID> -onboot 0`, `pct set <CTID> -onboot 0`.

## Проверка результата
- [x] `onboot: 1` у ВМ 2001, 2002, 2003 и CT 600, 700 (вывод `qm config` и `pct config`).
- [x] `startup: order=2,up=60` у ВМ 2003; `order=1,up=120` у ВМ 2002; `order=3,up=120` у ВМ 2001; `order=4,up=60` у CT 600; `order=5,up=0` у CT 700.
- [ ] Порядок и паузы при перезагрузке узла (не проверялось).

## Факты и статус
- **VERIFIED (вывод команд):** `onboot` и `startup` заданы у всех пяти объектов, значения как в таблице.
- **INFERRED:** при следующем старте узла порядок и паузы будут применены штатно; перезагрузкой не подтверждено. `up` — пауза после запуска гостя, а не проверка готовности служб внутри него.
- **INFERRED:** порядок запуска действует в пределах одного узла; после переноса ВМ на `pve02` (`PROXMOX-VM-MIGRATION-ISOLATION-2026-001`) порядок нужно будет задать для `pve02` отдельно.
- **INFERRED:** диски ВМ размещены на Ceph (`ceph-fast`), а в Ceph два монитора; при загрузке узла автозапуск зависит от готовности Ceph. Поведение при разных сценариях (второй узел включён или выключен) не проверялось.
- **UNKNOWN:** реальное время запуска AD, TC и SQL-сервера в `Srv1c`; достаточность пауз 120 / 60 / 120 / 60 / 0 с; время корректной остановки гостей (параметр `down` не задан).

## Открытые вопросы
1. Проверка перезагрузкой `pve01` в плановое окно: порядок, паузы, готовность AD (DNS, Kerberos), SQL, Vaultwarden, Zabbix.
2. Время остановки `Srv1c` (SQL Server) и `AD` при перезагрузке узла: нужен ли параметр `down`.
3. Пересмотр порядка запуска после возможной миграции ВМ на `pve02`.
4. Имя ВМ 2001 в Proxmox — `Srv1c`, в документации — `win-1c-app-01` (см. `00_Meta/CONFLICTS.md`).

## ⛔ Don't repeat
- Пустой вывод `qm config <VMID> | grep onboot` означает, что автозапуск выключен: параметр не задан.
- `up` задаёт только паузу в секундах после запуска гостя; он не проверяет готовность служб внутри гостя.
- Не считать порядок запуска проверенным без перезагрузки узла: подтверждена только конфигурация.

## Связанные документы
- `PROXMOX-VM-CLONE-2001-2026-001` — создание ВМ 2001 (сервер 1С:ERP).
- `PROXMOX-AD-THIRD-DC-PROMOTION-2026-001` — ВМ 2002 (`AD`, третий контроллер домена).
- `PROXMOX-RDS-2003-2026-001` — ВМ 2003 (`TC`, терминальный сервер RDS).
- `PROXMOX-VAULTWARDEN-INSTALL-2026-001` — CT 600 (Vaultwarden).
- `ZABBIX-STACK-INSTALL-2026-001` — CT 700 (Zabbix).
- `PROXMOX-VM-MIGRATION-ISOLATION-2026-001` — план переноса ВМ между узлами.

## NEEDS HUMAN VERIFICATION
1. Проверить перезагрузкой `pve01` (в плановое окно), что порядок и паузы работают и службы AD, SQL, Vaultwarden и Zabbix поднимаются после запуска.
2. Решить, нужен ли параметр `down` для `Srv1c` и `AD`.
