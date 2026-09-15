---
document_id: "PROXMOX-CLUSTER-QDEVICE-SETUP-2026-001"
title: "Создание кластера Proxmox VE (krnn) из pve01+pve02 и настройка внешнего Corosync QDevice"
document_type: "setup"
status: "completed"
priority: "critical"
date_created: 2026-08-30
date_modified: 2026-09-02
next_review: 2026-12-01
author: "cladkyimaffin-hue"
category: "02_Installation"
tags:
  - "ProxmoxVE"
  - "Cluster"
  - "QDevice"
  - "Corosync"
  - "Quorum"
  - "pve01"
  - "pve02"
  - "krnn"
  - "Debian"
  - "HighAvailability"
ai_summary: "Создание кластера Proxmox VE krnn из pve01 (192.168.202.121) и pve02 (192.168.202.179), настройка внешнего Corosync QDevice на отдельном хосте Qdevice (Debian 13, 192.168.202.251) — необходим для сохранения кворума при потере любого одного из двух узлов. QDevice НЕ является Ceph-монитором и не хранит данные Ceph, даёт голос только уровню Corosync/Proxmox. Известная проблема: команда pvecm add qdevice <IP> в PVE 9.2 даёт ошибку 400 too many arguments — правильная команда для этой версии: pvecm qdevice setup <IP>."
dont_repeat:
  - "Не использовать команду `pvecm add qdevice 192.168.202.251` — в PVE 9.2 она завершается ошибкой `400 too many arguments`. Правильная команда: `pvecm qdevice setup <IP>`."
  - "Не считать QDevice настроенным только по факту установки пакетов — обязательно проверять `pvecm status`: должен появиться флаг `Qdevice` и `Expected votes: 3`."
  - "Не размещать QDevice на pve01 или pve02 — обязательно независимый третий хост, иначе смысл дополнительного голоса кворума теряется."
  - "Не эксплуатировать двухузловой production-кластер без QDevice (или иного третьего голоса) — потеря любого одного узла блокирует кворум и операции управления/HA."
related_files:
  - "PROXMOX-NODE-RENAME-2026-001"
  - "PROXMOX-POSTINSTALL-SCRIPT-2026-001"
  - "PROXMOX-WEBGUI-DATACENTER-2026-001"
schema_version: "1.0"
---

# Создание кластера Proxmox VE и настройка QDevice

## Что настраивается и зачем
Объединение `pve01` и `pve02` в кластер `krnn`, плюс внешний источник
третьего голоса кворума (Corosync QDevice) — без него потеря любого из
двух узлов останавливает управление кластером и HA (кворум 2 из 2
недостижим при живом только одном узле).

## Предварительные условия
- [ ] Оба узла доступны по сети, hostname уже настроены (`PROXMOX-NODE-RENAME-2026-001`).
- [ ] Есть третий независимый хост для QDevice — **не** pve01/pve02 (в этой инфраструктуре — отдельный Debian 13, `Qdevice`, `192.168.202.251`).

## Шаги

**1. Создать кластер на первом узле (`pve01`):**
```bash
pvecm create krnn
```

**2. Добавить второй узел (`pve02`):**
```bash
pvecm add 192.168.202.121
```
На этом этапе `Expected votes: 2`, `Quorum: 2` — потеря любого узла уже
блокирует кластер, QDevice ещё не настроен.

**3. Установить `corosync-qnetd` на отдельном хосте QDevice:**
```bash
apt update && apt install -y corosync-qnetd
systemctl enable --now corosync-qnetd
systemctl status corosync-qnetd.service
```

**4. Установить `corosync-qdevice` на обоих узлах Proxmox:**
```bash
apt update && apt install corosync-qdevice -y
```

**5. Настроить QDevice** (выполняется на одном из узлов Proxmox):
```bash
pvecm qdevice setup 192.168.202.251
```
⚠️ **Не** `pvecm add qdevice 192.168.202.251` — в PVE 9.2 эта форма команды
даёт `400 too many arguments`. Правильная форма для этой версии —
`pvecm qdevice setup <IP>`.

**6. Проверить результат:**
```bash
pvecm status
```

## Итоговая конфигурация (подтверждено)

| Узел | Роль | IP |
|---|---|---|
| pve01 | узел кластера | 192.168.202.121 |
| pve02 | узел кластера | 192.168.202.179 |
| Qdevice | внешний источник кворума (Debian 13) | 192.168.202.251 |

| Параметр | До QDevice | После QDevice |
|---|---|---|
| Expected votes | 2 | **3** |
| Quorum | 2 | 2 |
| Flags | Quorate | **Quorate Qdevice** |

QDevice даёт **только** голос уровня Corosync/Proxmox — он не является
Ceph-монитором и не хранит данные Ceph (см. также
`PROXMOX-CEPH-CONCEPTS-2NODE-2026-001`), и **не заменяет fencing** —
это два независимых механизма отказоустойчивости, оба нужны отдельно
(fencing — через watchdog, см. `PROXMOX-WEBGUI-DATACENTER-2026-001`,
раздел HA).

**Сетевое требование:** TCP-порт **5403** должен быть доступен между
узлами Proxmox и хостом QDevice — это порт `corosync-qnetd`.

## Проверка результата — подтверждено
- [x] `pvecm status` — оба узла в кластере `krnn`.
- [x] `Expected votes: 3`, флаг `Qdevice` присутствует.
- [x] `systemctl status corosync-qnetd` на хосте QDevice — `active (running)`.
- [x] Резервная копия конфигурации создана автоматически при добавлении pve02: `/var/lib/pve-cluster/backup/config-1786452293.sql.gz`.

## Откат
```bash
pvecm qdevice remove
pvecm status
```
Удаление узла из кластера — отдельная процедура (`pvecm delnode`),
выполнять только после проверки состояния кластера, наличия кворума и
свежей резервной копии конфигурации.

**Когда откатывать:** QDevice не подключается или показывает некорректное
состояние; после настройки отсутствует флаг `Qdevice`; нарушена связь
между узлами и QDevice; изменение вызывает ошибки Corosync.

## ⛔ Don't repeat
См. `dont_repeat` во фронтматтере — главное: команда `pvecm qdevice setup`,
не `pvecm add qdevice`.

## Связанные документы
- «Смена hostname узла Proxmox VE» — предшествующий шаг
- «Справочник меню Datacenter Proxmox VE» — про HA/Fencing, использующие этот кворум

---
*Примечание при миграции (2026-09-11): этот файл был одним из четырёх с
задвоенным `document_id: "DOC-2026-08-30-001"`. Определён как основной,
реально выполненный документ этой группы (в отличие от «Добавить
qdevice.md» — обобщённого черновика с плейсхолдером IP на ту же тему,
перенесённого в `99_Archive/` как дубликат). Объёмный фронтматтер (20 секций)
сжат до ядра `SCHEMA.md` v1.0, содержание перенесено в тело без изменений
по сути.*
