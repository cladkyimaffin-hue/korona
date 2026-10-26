---
document_id: PROXMOX-NETWORK-TOPOLOGY-2026-001
title: Физическая топология сети кластера krnn (pve01, pve02, коммутация)
document_type: reference
status: in_progress
priority: high
date_created: 2026-10-15
date_modified: 2026-10-26
next_review: 2026-11-15
author: cladkyimaffin-hue
category: 03_Network
tags:
  - ProxmoxVE
  - Networking
  - Switches
  - SFP+
  - 10GbE
  - Architecture
  - pve01
  - pve02
  - nic0
  - bond0
  - Ceph
ai_summary: Физическая схема сети кластера krnn — какой порт куда подключён на pve01 и pve02, какой линк для public_network, cluster_network и bond0, и какие коммутаторы стоят между узлами. Для вопросов про физические линки, порты и скорость.
dont_repeat:
  - Скорость vmbr0 по ethtool не отражает физический линк; проверять nic2 через ethtool и bridge link
  - Схема администратора — источник для подключений, но не для скоростей; скорости брать из вывода команд
  - Учётные данные веб-интерфейсов коммутаторов и MikroTik в репозиторий не записывать (хранить в Vaultwarden)
  - Подробная диагностика тормозов 1С — в PROXMOX-CEPH-PUBLIC-NETWORK-1C-2026-001, здесь не дублировать
related_files:
  - PROXMOX-CEPH-PUBLIC-NETWORK-1C-2026-001
  - PROXMOX-CEPH-NIC0-DIRECT-LINK-2026-001
  - NETWORK-BOND0-CEPH-ACTIVEBACKUP-2026-001
  - NETWORK-SWITCH-SELECTION-2026-001
  - PROXMOX-CEPH-BOND0-LATENCY-INVESTIGATION-2026-001
  - PROXMOX-VM-MIGRATION-ISOLATION-2026-001
schema_version: "1.0"
---

# Физическая топология сети кластера krnn (pve01, pve02, коммутация)

## Источник и статус

- Источник: схема сети от администратора (2026-10-12, рисунок в чате) и выводы `ip -br a`, `ethtool`, `ss` с pve01 и pve02 от 2026-10-15.
- Подтверждённое командами — VERIFIED. Известное только по схеме — SCHEMA. Неизвестное — UNKNOWN.

## Узлы и линки

### pve01
- `nic0` — SFP+ прямой линк к pve02, cluster_network `10.10.11.1/24`, MTU 9000. VERIFIED: 10000Mb/s.
- `nic2` (Lom3) — единственный физический порт `vmbr0` (public_network) `192.168.202.121/22`. VERIFIED: 1000Mb/s. SCHEMA: MAC `…38:6F` (полный не указан).
- `nic4`, `nic5` — в `bond0` (`10.10.10.1/24`), без линка, `bond0` DOWN. VERIFIED 2026-10-15.
- `nic1`, `nic3` — без линка. VERIFIED 2026-10-15.

### pve02
- `nic0` — SFP+ прямой линк к pve01, cluster_network `10.10.11.2/24`. VERIFIED: 10000Mb/s.
- `nic2` (Lom3) — `vmbr0` (public_network) `192.168.202.179/22`. VERIFIED: 1000Mb/s. SCHEMA: MAC `…38:35` (полный не указан).
- `nic4`, `nic5` — в `bond0` (`10.10.10.2/24`), без линка, `bond0` DOWN. VERIFIED 2026-10-15.
- `nic1`, `nic3` — без линка. VERIFIED 2026-10-15.
- `/etc/network/interfaces`: у `nic2` нет строки `auto` (у pve01 есть `auto nic2`); `nic2` при этом в состоянии UP на 1000Mb/s, поднимается, вероятно, через `bridge-ports nic2` (INFERRED). Различие между узлами — VERIFIED (вывод `cat /etc/network/interfaces` в чате #5; дата вывода в чате не указана).

## Public network (клиентский трафик, 1 Гбит/с)

- `nic2` pve01 и `nic2` pve02 подключены к коммутатору **D-link** (SCHEMA). Какой порт D-link занят каждым узлом, на схеме не подписано — UNKNOWN.
- От D-link линк к **MikroTik CRS112-8P-4S** (`192.168.200.3`, SCHEMA). Порт MikroTik — UNKNOWN.
- MikroTik связан с **TP-Link Omada SX3008F** (10GbE SFP+, SCHEMA): два линка от портов MikroTik `11` и `12` к SFP+-порту `sfp8` TP-Link. Адрес веб-интерфейса TP-Link на схеме — `192.168.202.202`.
- Скорость пути public_network — 1 Гбит/с по `nic2` на обоих узлах (VERIFIED). Ограничение задаёт физический порт `nic2` (Lom3), а не мост `vmbr0`.

## Cluster network (Ceph, 10 Гбит/с)

- Прямой оптический линк `nic0` ↔ `nic0` без коммутатора. Подробности настройки — `PROXMOX-CEPH-NIC0-DIRECT-LINK-2026-001`.

## bond0 (nic4 + nic5, 10.10.10.0/24)

- На схеме подписан «SFP+ Cluster Network», от `nic4`/`nic5` идут пунктирные линии. Фактически оба порта на обоих узлах без линка (VERIFIED), `bond0` не используется для трафика Ceph (см. `AI-environment_facts-korona-proxmox.md`).
- Подпись на схеме либо устарела, либо относится к плану. Конечная точка пунктира по схеме не определяется — UNKNOWN. См. `00_Meta/CONFLICTS.md`.

## Открытые вопросы

1. Какие порты D-link и MikroTik заняты линками `nic2` pve01 и pve02.
2. Назначение пунктира от `nic4`/`nic5` и актуальность подписи «SFP+ Cluster Network».
3. Назначение идентификаторов `E01: F457E945A7` и `E02: F457E945B2` с блока MikroTik (UNKNOWN).
4. Полные MAC-адреса `nic2` на обоих узлах.
5. На схеме `vmbr0` pve01 подписан как 10 Гбит/с. Командами опровергнуто (см. `CONFLICTS.md`, RESOLVED).

## Намеренно не включено

Учётные данные веб-интерфейсов TP-Link и MikroTik, указанные на схеме. Репозиторий публичный, такие данные в него не записываются. Хранить в Vaultwarden.
