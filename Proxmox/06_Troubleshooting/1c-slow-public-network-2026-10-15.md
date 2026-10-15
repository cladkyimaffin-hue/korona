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
ai_summary: Диагностика жалоб на тормоза 1С на ВМ 2001 (Srv1c). Клиентский трафик Ceph от ВМ идёт через public_network (vmbr0), который на обоих узлах работает через nic2 на 1 Гбит/с. Причина тормозов не доказана: нужны замеры задержки и карта OSD.
dont_repeat:
  - Не считать скорость моста (vmbr0) по ethtool — он показывает значение по умолчанию; проверять физический порт через bridge link и ethtool.
  - Не считать 1 Гбит/с причиной тормозов без замера задержки и пропускной способности с ВМ.
  - Не менять сеть public_network на рабочем кластере без плана отката и доступа через консоль или IPMI (кворум Ceph на 2 мониторах).
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
- Диски Srv1c на Ceph; по словам администратора, часть соединений с OSD на pve02 идёт через 192.168.202.179.

## Проверено командами (VERIFIED)
- pve01: `bridge link` — `nic2` в `vmbr0` (state forwarding). `ethtool nic2`: Speed 1000Mb/s, Link detected: yes.
- pve02: `bridge link` — `nic2` в `vmbr0`. `ethtool nic2`: Speed 1000Mb/s, Link detected: yes.
- pve01: `nic1` и `nic3` без линка (Speed Unknown), на pve02 то же самое. Свободного подключённого 10G-порта для public_network нет.
- pve01: интерфейсы ВМ 2001 (`tap2001i0` → `fwbr2001i0` → `fwpr2001p0`) подключены к `vmbr0`, то есть трафик ВМ уходит через `nic2` (1 Гбит/с).
- pve01: `nic0` 10000Mb/s, MTU 9000, выделенный линк cluster network (10.10.11.0/24), в `vmbr0` не входит.
- pve01, ss: процессы kvm (PID 60904, 61183, 61372) имеют ESTAB-соединения с 192.168.202.179 на порты 6800/6802/6804/6806 (OSD).
- pve02, ss: ceph-osd имеют ESTAB-соединения с 192.168.202.121.
- `/etc/pve/qemu-server/2001.conf` содержит `name: Srv1c`.

## Опровергнуто
- Гипотеза «pve01 работает на 10G на public_network» опровергнута: скорость 10000Mb/s, которую показывал `ethtool vmbr0`, относилась к виртуальному интерфейсу моста.

## Гипотезы (INFERRED)
- Симметричный линк 1 Гбит/с на public_network ограничивает пропускную способность клиентского трафика Ceph на обоих узлах (теоретический потолок ~110–120 МБ/с на весь трафик узла, не измерен).
- Тормоза 1С связаны с задержками клиентского трафика Ceph. Не подтверждено.

## Не известно (UNKNOWN)
- Какие OSD (и на каком узле) держат данные Srv1c: `ceph osd map` не выполнялся.
- Фактическая задержка и пропускная способность Srv1c к OSD.
- Причина SYN-SENT у corosync-qdevice на pve02 (к 192.168.200.84:5403).

## Конфликт (решён)
- Схема администратора (2026-10-12) показывала vmbr0 pve01 — 10 Гбит/с. Документы репозитория показывали nic2 1 GbE на обоих узлах. Командами подтверждено: 1 GbE на обоих узлах. См. CONFLICTS.md (RESOLVED).

## Следующие шаги
1. Выполнить `ceph osd map` для пулов ВМ 2001 — проверить, какие OSD держат данные Srv1c.
2. Замерить задержку и пропускную способность Srv1c к OSD во время обычной работы (только чтение).
3. Разобрать SYN-SENT у corosync-qdevice на pve02.
4. Если нужен 10G для public_network: проверить, какой порт и кабель можно подключить (nic1 или nic3, тип разъёма и порт коммутатора), и только после этого планировать изменение сети с откатом.
5. Решение по миграции ВМ (PROXMOX-VM-MIGRATION-ISOLATION-2026-001) принимать после шагов 1–2.

## Связанные документы
- PROXMOX-CEPH-BOND0-LATENCY-INVESTIGATION-2026-001 — другая сеть (bond0, 10.10.10.0/24), но похожий класс симптомов.
- PROXMOX-VM-MIGRATION-ISOLATION-2026-001 — план миграции ВМ, зависит от результатов этого документа.
- PROXMOX-VM-CLONE-2001-2026-001 — ВМ 2001, в нём открыт вопрос о зависаниях 1С.
