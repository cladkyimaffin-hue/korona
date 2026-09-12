---
document_id: "NETWORK-BOND0-CEPH-ACTIVEBACKUP-2026-001"
title: "Настройка bond0 (active-backup) для выделенной сети Ceph между pve01 и pve02"
document_type: "setup"
status: "completed"
priority: "high"
date_created: 2026-09-02
date_modified: 2026-09-11
next_review: 2026-12-01
author: "cladkyimaffin-hue"
category: "03_Network"
tags:
  - "ProxmoxVE"
  - "Networking"
  - "Bonding"
  - "bond0"
  - "HighAvailability"
ai_summary: "Создание bond0 (режим active-backup, mode 1) из портов nic4+nic5 на узлах pve01 и pve02, выделенная подсеть 10.10.10.0/24 для трафика Ceph, независимая от management-сети 192.168.202.0/22."
dont_repeat:
  - "Не назначать IP-адреса напрямую на nic4/nic5 — только на bond0, слейвы остаются `inet manual`."
  - "Не предлагать режим 802.3ad (LACP) для этой конфигурации без отдельной настройки агрегации портов на коммутаторе TP-Link SX3008F — на момент внедрения выбран active-backup именно потому, что не требует изменений на коммутаторе (см. раздел «Почему active-backup, а не LACP» ниже)."
related_files:
  - "NETWORK-SFP-OPTICAL-MISMATCH-2026-001"
schema_version: "1.0"
---

# Настройка bond0 (active-backup) для выделенной сети Ceph между pve01 и pve02

## Что настраивается и зачем
Отдельная от management сеть для трафика Ceph, с отказоустойчивостью на
уровне сетевого линка — агрегация двух портов (`nic4`+`nic5`) в один
логический интерфейс `bond0` на каждом из двух узлов кластера.

## Предварительные условия
- [ ] Линк на `nic4` и `nic5` активен на обоих узлах: `ethtool nic4 | grep "Link detected"` → `yes`. (Физическая диагностика модулей — см. `NETWORK-SFP-OPTICAL-MISMATCH-2026-001`, итог — 1 Гбит/с на оптических модулях 1000BASE-SX.)
- [ ] `nic4` и `nic5` объявлены в `/etc/network/interfaces` как `inet manual` (не входят в другой bridge/bond).

## Почему active-backup, а не LACP
Изначально рассматривался режим `802.3ad` (LACP, mode 4) — он требует
настройки агрегации портов (LAG) на коммутаторе TP-Link SX3008F.
Решение принято в пользу **active-backup (mode 1)**: работает без каких-либо
изменений на коммутаторе, один порт активен, второй в резерве. Переход на
LACP остаётся технически возможным в будущем при необходимости увеличить
пропускную способность, но потребует настройки коммутатора и краткого
простоя сетевого стека на узле.

## Шаги

**1. Проверить линк на обоих узлах:**
```bash
ethtool nic4 | grep "Link detected"
ethtool nic5 | grep "Link detected"
```

**2. Создать конфигурацию bond0 (на pve01):**
```bash
cat >> /etc/network/interfaces << 'EOF'

auto bond0
iface bond0 inet static
    address 10.10.10.1/24
    bond-slaves nic4 nic5
    bond-mode active-backup
    bond-miimon 100
    bond-primary nic4
EOF
```

**3. Применить конфигурацию (без перезагрузки):**
```bash
ifreload -a
```

**4. Повторить шаги 2-3 на pve02** с адресом `10.10.10.2/24` вместо `10.10.10.1/24`.

**5. Проверить результат на каждом узле:**
```bash
ip addr show bond0
cat /proc/net/bonding/bond0
```

**6. Проверить связность между узлами:**
```bash
# на pve01
ping -c 4 10.10.10.2
# на pve02
ping -c 4 10.10.10.1
```

## Итоговая конфигурация (подтверждено выполнением)

| Узел | bond0 IP | Slave-интерфейсы | Режим | Primary |
|---|---|---|---|---|
| pve01 | 10.10.10.1/24 | nic4, nic5 | active-backup (mode 1) | nic4 |
| pve02 | 10.10.10.2/24 | nic4, nic5 | active-backup (mode 1) | nic4 |

Management-сеть (`vmbr0`, отдельно от bond0): `pve01` — `192.168.202.121/22`,
`pve02` — `192.168.202.179/22`, gateway `192.168.200.1`.

`/etc/network/interfaces` (фрагмент, идентичен на обоих узлах с поправкой на IP):
```
auto nic4
iface nic4 inet manual

auto nic5
iface nic5 inet manual

auto bond0
iface bond0 inet static
    address 10.10.10.1/24
    bond-slaves nic4 nic5
    bond-mode active-backup
    bond-miimon 100
    bond-primary nic4
```

## Проверка результата
Подтверждено фактическим выполнением на обоих узлах:
- [x] `bond0` в состоянии `UP` на обеих нодах.
- [x] `Bonding Mode: fault-tolerance (active-backup)`, `MII Status: up` на обоих slave.
- [x] `Link Failure Count: 0`.
- [x] `ping` между `10.10.10.1` и `10.10.10.2` проходит.

## ⛔ Don't repeat
- Не назначать IP на `nic4`/`nic5` напрямую — только на `bond0`.
- Не предполагать, что LACP можно включить без правок на коммутаторе.

## Связанные документы
- «Диагностика SFP-модулей Intel X710» — почему nic4/nic5 работают на 1 Гбит/с, а не на 10

---
*Примечание при миграции (2026-09-11): выделено в отдельный документ из
«Настройка сети bond0.md» (диагностика SFP вынесена в отдельный документ
`NETWORK-SFP-OPTICAL-MISMATCH-2026-001`). Также при миграции разрешено
противоречие, зафиксированное в `00_Meta/CONFLICTS.md`: исходный
фронтматтер файла (написан в начале работы) утверждал план — режим
802.3ad/LACP; тело файла и `AI-environment_facts-korona-proxmox.md`
подтверждают, что фактически реализован и работает active-backup.
Администратор подтвердил резолюцию: active-backup — источник истины,
LACP отражён здесь только как рассмотренная и явно отклонённая на
момент внедрения альтернатива, не как основной тег/факт документа.*
