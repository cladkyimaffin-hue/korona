---
document_id: VPN-MIKROTIK-WIREGUARD-SERVER-2026-001
title: WireGuard — сервер wg-korona
document_type: reference
status: completed
priority: high
date_created: 2026-10-07
date_modified: 2026-10-07
next_review: 2027-01-07
author: "cladkyimaffin-hue"
category: "03_VPN"
tags: ["RouterOS", "MikroTik", "VPN", "WireGuard", "Firewall", "NAT"]
ai_summary: "Конфигурация WireGuard-сервера (wg-korona) на MikroTik CRS326."
dont_repeat: ["Не дублировать публичный ключ сервера"]
related_files: ["VPN-MIKROTIK-WIREGUARD-ADD-USER-2026-001", "TS-MIKROTIK-WIREGUARD-ACCESS-2026-001"]
schema_version: "1.0"
---

# WireGuard — сервер wg-korona

## Параметры сервера

| Параметр | Значение |
|---|---|
| Интерфейс | wg-korona |
| Listen Port | 51820/UDP |
| Server IP | 10.200.0.1/24 |
| Public IP | 89.109.14.221 |
| Client DNS | 192.168.200.2 |

## Публичный ключ сервера
~~~text
SawamFfjuVXF/zk86QU3ss2qyW2KX5jTfjzIDg4Ammw=
~~~

## Текущие пиры
| Comment | Public Key | IP |
|---|---|---|
| Windows Client 1 | 8T2yORO2GMhWOMhiteVwBWqQgRZUXcKkIIaakHUZFnE= | 10.200.0.2/32 |
| Bazrov-Home | bSq/JE/Pciia8UH17GhwNRvh7hFnrbDtZjPzopfozBI= | 10.200.0.3/32 |

## Firewall Rules
### 1. Chain Input
~~~routeros
/ip firewall filter add chain=input action=accept protocol=udp in-interface=pppoe-out1 port=51820 place-before=<DROP_RULES> comment="Allow WireGuard"
/ip firewall filter add chain=input action=accept in-interface=wg-korona comment="Allow WireGuard to Router"
~~~

### 2. Chain Forward
~~~routeros
/ip firewall filter add chain=forward action=accept in-interface=wg-korona out-interface=bridge_localnet comment="Allow WireGuard to LAN"
/ip firewall filter add chain=forward action=accept in-interface=wg-korona out-interface=pppoe-out1 place-before=0 comment="Allow WireGuard to Internet"
~~~

### 3. Chain SrcNAT
~~~routeros
/ip firewall nat add chain=srcnat action=masquerade src-address=10.200.0.0/24 out-interface=pppoe-out1 comment="WireGuard NAT"
~~~
