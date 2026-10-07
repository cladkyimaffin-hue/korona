---
document_id: VPN-MIKROTIK-WIREGUARD-ADD-USER-2026-001
title: WireGuard — добавление нового пользователя
document_type: setup
status: completed
priority: medium
date_created: 2026-10-07
date_modified: 2026-10-07
next_review: 2027-01-07
author: "cladkyimaffin-hue"
category: "03_VPN"
tags: ["RouterOS", "MikroTik", "VPN", "WireGuard", "Configuration"]
ai_summary: "СОП добавления нового клиента WireGuard."
dont_repeat: []
related_files: ["VPN-MIKROTIK-WIREGUARD-SERVER-2026-001"]
schema_version: "1.0"
---

# WireGuard — добавление нового пользователя

## Шаг 1. Генерация ключей на клиенте
1. Откройте WireGuard. 2. Add empty tunnel. 3. Скопируйте PublicKey.

## Шаг 2. Добавление пира на MikroTik
~~~routeros
/interface wireguard peers add \
  interface=wg-korona \
  public-key=<PUBLIC_KEY> \
  allowed-address=10.200.0.X/32 \
  comment=User-Name
~~~

## Шаг 3. Конфиг на клиенте
~~~ini
[Interface]
PrivateKey = <PRIVATE_KEY>
Address = 10.200.0.X/32
DNS = 192.168.200.2

[Peer]
PublicKey = SawamFfjuVXF/zk86QU3ss2qyW2KX5jTfjzIDg4Ammw=
AllowedIPs = 0.0.0.0/0
Endpoint = 89.109.14.221:51820
PersistentKeepalive = 25
~~~
