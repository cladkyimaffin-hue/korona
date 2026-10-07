---
schema_version: "1.0"
date_modified: 2026-09-29
status: "active"
maintainer: "cladkyimaffin-hue"
file_type: "navigation_index"
source_of_truth: "00_Meta/registry.csv"
---

# Индекс папки: MikroTik

## Назначение

Человекочитаемая навигация по документам домена `MikroTik`. Машиночитаемый
источник списка документов — `00_Meta/registry.csv`; метаданные документов
проверяются по `00_Meta/SCHEMA.md`, допустимые теги — по `00_Meta/TAGS.md`.

## Документы


### `00_Inbox`

| ID | Документ | Тип | Статус | Приоритет | Теги |
|---|---|---|---|---|---|
| `INBOX-MIKROTIK-WIREGUARD-RAW-2026-001` | [Raw WireGuard MikroTik Setup 2026-10-07](./00_Inbox/Raw-WireGuard-MikroTik-Setup-2026-10-07.md) | `reference` | `completed` | `high` | `RouterOS`, `MikroTik`, `VPN`, `WireGuard` |

### `01_Interfaces`

| ID | Документ | Тип | Статус | Приоритет | Теги |
|---|---|---|---|---|---|
| `NETWORK-MIKROTIK-TOPOLOGY-2026-001` | [Топология и адресация MikroTik CRS326-24G-2S+: интерфейсы, bridge, routing, link flapping ether9](./01_Interfaces/%D0%A2%D0%BE%D0%BF%D0%BE%D0%BB%D0%BE%D0%B3%D0%B8%D1%8F%20%D0%B8%20%D0%B0%D0%B4%D1%80%D0%B5%D1%81%D0%B0%D1%86%D0%B8%D1%8F%20MikroTik.md) | `reference` | `completed` | `medium` | `RouterOS`, `MikroTik`, `Interfaces`, `PPPoE`, `WAN`, `Bridge`, `Routing`, `Audit` |

### `02_Firewall_NAT`

| ID | Документ | Тип | Статус | Приоритет | Теги |
|---|---|---|---|---|---|
| `NETWORK-MIKROTIK-FIREWALL-NAT-CLEANUP-2026-001` | [Аудит Firewall и NAT MikroTik: 7 мёртвых правил Filter, 5 мёртвых правил NAT (legacy 192.168.199.x)](./02_Firewall_NAT/%D0%90%D1%83%D0%B4%D0%B8%D1%82%20Firewall%20%D0%B8%20NAT%20%E2%80%94%20%D0%BC%D1%91%D1%80%D1%82%D0%B2%D1%8B%D0%B5%20%D0%BF%D1%80%D0%B0%D0%B2%D0%B8%D0%BB%D0%B0.md) | `reference` | `completed` | `high` | `RouterOS`, `MikroTik`, `Firewall`, `NAT`, `Filter-Rules`, `Audit` |
| `NETWORK-MIKROTIK-REMOTE-ACCESS-PROCEDURE-2026-001` | [Процедура настройки проброса портов (NAT) для удалённого доступа — чек-лист и реестр портов](./02_Firewall_NAT/%D0%9F%D1%80%D0%BE%D1%86%D0%B5%D0%B4%D1%83%D1%80%D0%B0%20%D0%BF%D1%80%D0%BE%D0%B1%D1%80%D0%BE%D1%81%D0%B0%20%D0%BF%D0%BE%D1%80%D1%82%D0%BE%D0%B2%20NAT.md) | `reference` | `completed` | `medium` | `RouterOS`, `MikroTik`, `NAT`, `Configuration` |

### `03_VPN`

| ID | Документ | Тип | Статус | Приоритет | Теги |
|---|---|---|---|---|---|
| `NETWORK-MIKROTIK-VPN-PROFILE-BROKEN-2026-001` | [VPN-профиль MikroTik ссылается на нерабочую подсеть — пользователи получают недействительные адреса](./03_VPN/VPN-%D0%BF%D1%80%D0%BE%D1%84%D0%B8%D0%BB%D1%8C%20%D1%81%D1%81%D1%8B%D0%BB%D0%B0%D0%B5%D1%82%D1%81%D1%8F%20%D0%BD%D0%B0%20%D0%BD%D0%B5%D1%80%D0%B0%D0%B1%D0%BE%D1%87%D1%83%D1%8E%20%D0%BF%D0%BE%D0%B4%D1%81%D0%B5%D1%82%D1%8C.md) | `troubleshooting` | `completed` | `critical` | `RouterOS`, `MikroTik`, `VPN`, `Audit`, `Troubleshooting` |

| `VPN-MIKROTIK-WIREGUARD-SERVER-2026-001` | [WireGuard — сервер wg-korona](./03_VPN/WireGuard%20%E2%80%94%20%D1%81%D0%B5%D1%80%D0%B2%D0%B5%D1%80%20wg-korona.md) | `reference` | `completed` | `high` | `RouterOS`, `MikroTik`, `VPN`, `WireGuard`, `Firewall`, `NAT` |
| `VPN-MIKROTIK-WIREGUARD-ADD-USER-2026-001` | [WireGuard — добавление нового пользователя](./03_VPN/WireGuard%20%E2%80%94%20%D0%B4%D0%BE%D0%B1%D0%B0%D0%B2%D0%BB%D0%B5%D0%BD%D0%B8%D0%B5%20%D0%BD%D0%BE%D0%B2%D0%BE%D0%B3%D0%BE%20%D0%BF%D0%BE%D0%BB%D1%8C%D0%B7%D0%BE%D0%B2%D0%B0%D1%82%D0%B5%D0%BB%D1%8F.md) | `setup` | `completed` | `medium` | `RouterOS`, `MikroTik`, `VPN`, `WireGuard`, `Configuration` |

### `05_Troubleshooting`

| ID | Документ | Тип | Статус | Приоритет | Теги |
|---|---|---|---|---|---|
| `MikroTik-CRITICAL-SECURITY-PLAN-2026-001` | [Критические уязвимости MikroTik — приоритизированный план устранения (ничего ещё не применено)](./05_Troubleshooting/%D0%9A%D1%80%D0%B8%D1%82%D0%B8%D1%87%D0%B5%D1%81%D0%BA%D0%B8%D0%B5%20%D1%83%D1%8F%D0%B7%D0%B2%D0%B8%D0%BC%D0%BE%D1%81%D1%82%D0%B8%20%E2%80%94%20%D0%BF%D0%BB%D0%B0%D0%BD%20%D1%83%D1%81%D1%82%D1%80%D0%B0%D0%BD%D0%B5%D0%BD%D0%B8%D1%8F.md) | `troubleshooting` | `in_progress` | `critical` | `RouterOS`, `MikroTik`, `Security`, `Audit`, `Troubleshooting` |

| `TS-MIKROTIK-WIREGUARD-ACCESS-2026-001` | [WireGuard — диагностика доступа и порядок firewall](./05_Troubleshooting/WireGuard%20%E2%80%94%20%D0%B4%D0%B8%D0%B0%D0%B3%D0%BD%D0%BE%D1%81%D1%82%D0%B8%D0%BA%D0%B0%20%D0%B4%D0%BE%D1%81%D1%82%D1%83%D0%BF%D0%B0%20%D0%B8%20%D0%BF%D0%BE%D1%80%D1%8F%D0%B4%D0%BE%D0%BA%20firewall.md) | `troubleshooting` | `completed` | `high` | `RouterOS`, `MikroTik`, `VPN`, `WireGuard`, `Firewall`, `Troubleshooting` |

### `06_Wireless`

| ID | Документ | Тип | Статус | Приоритет | Теги |
|---|---|---|---|---|---|
| `MIKROTIK-WIFI-SSID-RSK-2026-001` | [Добавление дополнительного SSID (RSK) на точках доступа MikroTik (Т2, Т1-Т6)](./06_Wireless/%D0%94%D0%BE%D0%BF%D0%BE%D0%BB%D0%BD%D0%B8%D1%82%D0%B5%D0%BB%D1%8C%D0%BD%D1%8B%D0%B9%20SSID%20Mikrotik%20%D0%A2%D0%94%20%D0%A22.md) | `setup` | `in_progress` | `medium` | `RouterOS`, `MikroTik`, `Wi-Fi`, `SSID`, `cAP_ac`, `Configuration` |
| `MIKROTIK-WIFI-SSID-2026-001` | [перенастройка мастер Wi-Fi SSID на MikroTik cAP ac (T7)](./06_Wireless/%D0%BF%D0%B5%D1%80%D0%B5%D0%BD%D0%B0%D1%81%D1%82%D1%80%D0%BE%D0%B9%D0%BA%D0%B0%20%D0%BC%D0%B0%D1%81%D1%82%D0%B5%D1%80%20Wi-Fi%20SSID%20%D0%BD%D0%B0%20MikroTik%20cAP%20ac%20%28T7).md) | `troubleshooting` | `in_progress` | `medium` | `RouterOS`, `MikroTik`, `Interfaces`, `Bridge`, `Wi-Fi`, `Troubleshooting`, `Configuration` |

## Быстрые маршруты

- **Топология, WAN/LAN и маршрутизация:** `01_Interfaces/`.
- **Firewall и NAT:** `02_Firewall_NAT/`.
- **VPN:** `03_VPN/`.
- **Маршрутизация:** `04_Routing/`.
- **Инциденты и план исправлений:** `05_Troubleshooting/`.
- **Wi-Fi и SSID:** `06_Wireless/`.
- **Исторические исходники:** `99_Archive/`.
