---
document_id: PROXMOX-CEPH-PUBLIC-NETWORK-1C-2026-001
title: Тормоза 1С (ВМ 2001 Srv1c): public_network и линк pve02 — ЧАСТИЧНО ПРОВЕРЕНО
document_type: troubleshooting
status: in_progress
priority: high
date_created: 2026-10-15
date_modified: 2026-10-15
next_review: 2026-11-15
author: cladkyimaffin-hue
category: 06_Troubleshooting
tags:
  - ProxmoxVE
  - Ceph
  - OSD
  - Networking
  - Troubleshooting
  - Diagnostics
  - 1C
  - pve01
  - pve02
ai_summary: Диагностика жалоб на тормоза 1С на ВМ 2001 (Srv1c). Гипотеза — клиентский трафик Ceph от ВМ на pve01 к OSD на pve02 идёт через public_network (vmbr0), где физический порт pve02 работает на 1 Гбит/с. Часть фактов подтверждена командами, часть остаётся гипотезой.
dont_repeat:
  - Не считать скорость vmbr0 по ethtool на мосту — он показывает значение по умолчанию; проверять физический порт (nic2) и bridge link.
  - Не считать 1 Гбит/с причиной тормозов без замера задержки и пропускной способности с ВМ.
  - Не менять сеть public_network на рабочем кластере без оценки риска для кворума Ceph (2 монитора).
vm_id: "2001"
related_files:
  - PROXMOX-CEPH-BOND0-LATENCY-INVESTIGATION-2026-001
  - PROXMOX-VM-MIGRATION-ISOLATION-2026-001
  - PROXMOX-VM-CLONE-2001-2026-001
  - PROXMOX-CEPH-NIC0-DIRECT-LINK-2026-001
schema_version: "1.0"
---

# Тормоза 1С (ВМ 2001 Srv1c): public_network и линк pve02 — ЧАСТИЧНО ПРОВЕРЕНО

## Симптом (со слов администратора)
- Тормоза 1С на ВМ 2001 (Srv1c).
- Диски Srv1c на Ceph; по словам администратора, соединения с OSD на pve02 идут через 192.168.202.179.

## Проверено командами (VERIFIED)
- pve02, физический порт nic2: Speed 1000Mb/s, UP.
- pve02, nic0: Speed 10000Mb/s, 10.10.11.2/24 (cluster network).
- pve01, ss: процессы kvm (PID 60904, 61183, 61372) имеют ESTAB-соединения с 192.168.202.179 на порты 6800/6802/6804/6806 (OSD).
- pve02, ss: ceph-osd имеют ESTAB-соединения с 192.168.202.121.
- `/etc/pve/qemu-server/2001.conf` содержит `name: Srv1c`.

## Гипотезы (INFERRED)
- vmbr0 на pve02 работает через nic2 (1 Гбит/с). Не проверено: `bridge link`.
- Клиентский трафик от ВМ к OSD идёт по public_network (vmbr0), а не по cluster network (nic0).
- Узкое место 1 Гбит/с может влиять на задержки 1С. Нужен замер.

## Не известно (UNKNOWN)
- Скорость физического порта, на который натянут vmbr0 на pve01. Значение 10000Mb/s, полученное по ethtool на мосту, не считается подтверждением.
- Какие OSD (и на каком узле) держат данные Srv1c: `ceph osd map` не выполнялся.
- Фактическая пропускная способность и задержка Srv1c к OSD.

## Конфликт (CONFLICT)
- Документы репозитория: vmbr0 на обоих узлах через nic2 1 GbE. Схема администратора: vmbr0 pve01 — 10 Гбит/с. См. CONFLICTS.md.

## Следующие шаги
1. pve01: `bridge link` и `ethtool <член моста>` — определить физический порт vmbr0.
2. Оба узла: `bridge link`, `ethtool nic2`.
3. Кластер: `ceph osd map` для пулов ВМ 2001 — где лежат объекты Srv1c.
4. Замер задержки и пропускной способности с Srv1c во время обычной работы (только чтение).
5. Разобрать SYN-SENT у corosync-qdevice на pve02 (192.168.200.84:5403) — наблюдение без объяснения.

## Связанные документы
- PROXMOX-CEPH-BOND0-LATENCY-INVESTIGATION-2026-001 — другая сеть (bond0, 10.10.10.0/24), но тот же класс задержек Ceph.
- PROXMOX-VM-MIGRATION-ISOLATION-2026-001 — план миграции ВМ (зависит от результатов этого документа).
- PROXMOX-VM-CLONE-2001-2026-001 — ВМ 2001, в нём открыт вопрос о зависаниях 1С.
