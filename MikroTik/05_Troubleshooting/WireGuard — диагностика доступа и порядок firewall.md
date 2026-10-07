---
document_id: TS-MIKROTIK-WIREGUARD-ACCESS-2026-001
title: WireGuard — диагностика доступа и порядок firewall
document_type: troubleshooting
status: completed
priority: high
date_created: 2026-10-07
date_modified: 2026-10-07
next_review: 2027-01-07
author: "cladkyimaffin-hue"
category: "05_Troubleshooting"
tags: ["RouterOS", "MikroTik", "VPN", "WireGuard", "Firewall", "Troubleshooting"]
ai_summary: "Решённые проблемы WireGuard: DNS/forward, input to router, Clash, порядок Firewall."
dont_repeat: ["Не повторять ошибку порядка firewall"]
related_files: ["VPN-MIKROTIK-WIREGUARD-SERVER-2026-001"]
schema_version: "1.0"
---

# WireGuard — диагностика доступа и порядок firewall

## Симптом 1: Handshake есть, интернета нет
**Причина:** Неверный DNS (нужен 192.168.200.2) и отсутствие forward в WAN.
**Решение:**
~~~routeros
/ip firewall filter add chain=forward action=accept in-interface=wg-korona out-interface=pppoe-out1 place-before=0 comment="Allow WireGuard to Internet"
~~~

## Симптом 2: Локальные сервисы не пингуются
**Причина:** Firewall блокирует input из wg-korona.
**Решение:**
~~~routeros
/ip firewall filter add chain=input action=accept in-interface=wg-korona comment="Allow WireGuard to Router"
~~~

## Симптом 3: Handshake не проходит (rx=0)
**Причина А:** Конфликт с Clash (FlClashX) на клиенте.
**Решение:** Закрыть Clash.

**Причина Б:** Ошибка порядка правил Firewall. Правило Allow WireGuard стояло ПОСЛЕ drop in-interface=pppoe-out1.
**Решение:** Переместить Allow WireGuard ПЕРЕД правилами drop.
~~~routeros
/ip firewall filter remove [find comment="Allow WireGuard"]
/ip firewall filter add chain=input action=accept protocol=udp in-interface=pppoe-out1 port=51820 place-before=<drop_rule_number> comment="Allow WireGuard"
~~~
