---
document_id: "NETWORK-MIKROTIK-TOPOLOGY-2026-001"
title: "Топология и адресация MikroTik CRS326-24G-2S+: интерфейсы, bridge, routing, link flapping ether9"
document_type: "reference"
status: "completed"
priority: "medium"
date_created: 2026-09-19
date_modified: 2026-09-19
next_review: 2026-12-19
author: "cladkyimaffin-hue"
category: "01_Interfaces"
tags:
  - "RouterOS"
  - "MikroTik"
  - "Interfaces"
  - "PPPoE"
  - "WAN"
  - "Bridge"
  - "Routing"
  - "Audit"
ai_summary: "Топология MikroTik CRS326-24G-2S+: WAN pppoe-out1 на sfp-sfpplus2, два bridge (bridge_localnet 192.168.200.0/22 — основная LAN, bridge_video 192.168.1.0/24 — видео), маршрутизация простая (только default + connected, без policy routing). Обнаружена реальная физическая проблема: ether9 постоянно флаппает между 10M и 1G (лог подтверждён), кандидат на замену патч-корда/порта."
dont_repeat:
  - "Не считать основную LAN подсетью /24 — фактически /22 (192.168.200.0/22), расхождение с изначальным предположением подтверждено аудитом."
  - "Не игнорировать частый link flapping как безобидную аномалию лога — у ether9 это стабильно воспроизводится (10M↔1G каждые ~10-15 секунд в зафиксированных интервалах) и указывает на физическую проблему (патч-корд/порт/устройство на другом конце), а не на разовый сбой."
related_files:
  - "NETWORK-MIKROTIK-FIREWALL-NAT-CLEANUP-2026-001"
schema_version: "1.0"
---

# Топология и адресация MikroTik CRS326-24G-2S+

## Устройство
CRS326-24G-2S+, RouterOS 7.23.1 (stable).

## Интерфейсы и адресация

| Компонент | Значение |
|---|---|
| WAN (физический) | `sfp-sfpplus2` |
| WAN (логический) | `pppoe-out1`, публичный IP `89.109.14.221/32` (dynamic), шлюз провайдера `79.126.0.1` |
| `bridge_localnet` | `192.168.200.1/22` — основная LAN |
| `bridge_video` | `192.168.1.1/24` — дополнительная LAN «Video» |

## Bridge-порты

| Bridge | Активные порты | Неактивные порты |
|---|---|---|
| `bridge_localnet` | ether2–ether15 | ether1, ether16–ether20 |
| `bridge_video` | ether22, ether24 | ether21, ether23 |

В составе `bridge_localnet` также числится `eoip-tunnel1` (EoIP-туннель,
disabled) — не используется, кандидат на удаление, если не появится
причина его сохранить.

## Маршрутизация

| Тип | Сеть назначения | Шлюз | Distance |
|---|---|---|---|
| Dynamic | `0.0.0.0/0` | `pppoe-out1` | 1 |
| Connected | `79.126.0.1/32` | `pppoe-out1` | 0 |
| Connected | `192.168.200.0/22` | `bridge_localnet` | 0 |
| Connected | `192.168.1.0/24` | `bridge_video` | 0 |

Простая и корректная схема: только default route + connected. **Policy
routing отсутствует** (`/ip firewall mangle print` — пусто, подтверждено
аудитом).

## ⚠️ Известная проблема: link flapping на ether9

**Симптом** (подтверждено логом `/log print`):
```
2026-09-18 10:41:27 interface,info ether9 link down
2026-09-18 10:41:29 interface,info ether9 link up (speed 10M, full duplex)
2026-09-18 10:41:43 interface,info ether9 link down
2026-09-18 10:41:48 interface,info ether9 link up (speed 1G, full duplex)
2026-09-18 12:42:07 interface,info ether9 link down
2026-09-18 12:42:09 interface,info ether9 link up (speed 10M, full duplex)
```
Порт `ether9` (в составе `bridge_localnet`) постоянно переключается между
скоростями 10M и 1G с падением линка — воспроизводится многократно за
сутки, не разовый инцидент.

**Вероятная причина (не проверено на месте):** повреждённый/некачественный
патч-корд, проблема на порту устройства на другом конце, либо
неисправность самого порта коммутатора.

**Рекомендуемая диагностика (не выполнена в рамках этого аудита):**
1. Проверить/заменить патч-корд на `ether9`.
2. Проверить порт и кабель на устройстве, подключённом к `ether9`.
3. При сохранении проблемы — попробовать другой физический порт коммутатора.

## ⛔ Don't repeat
См. `dont_repeat` во фронтматтере.

## Связанные документы
- «Аудит Firewall и NAT» — та же сессия аудита, другой аспект конфигурации

---
*Примечание: обработано из файла «Аудит конфигурации MikroTik» (полный
read-only аудит, 2026-09-19). Ни одно исправление из этого документа не
применено на устройстве — это констатация текущего состояния и
рекомендация, не протокол выполненных действий.*
