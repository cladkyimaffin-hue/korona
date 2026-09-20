---
schema_version: "1.0"
date_created: 2026-09-17
status: "active"
maintainer: "cladkyimaffin-hue"
---

# 🏷️ Реестр тегов (TAGS.md) — домен MikroTik

Единственный источник допустимых тегов для поля `tags` в документах
домена `MikroTik/`. Независим от `Proxmox/00_Meta/TAGS.md` — теги между
доменами не переиспользуются автоматически, у каждого домена свой список
(см. `../../AI-INSTRUCTIONS.md`, раздел 8а).

Правило добавления нового тега — как в Proxmox: проверить, нет ли уже
тега с тем же смыслом в другом написании, добавить в подходящую группу,
записать в `CHANGELOG.md`.

## Группы тегов (первичный набор, дополняется по ходу разбора)

### Устройство и платформа
`RouterOS` · `MikroTik`

### Сеть — интерфейсы и адресация
`Interfaces` · `PPPoE` · `WAN` · `LAN` · `VLAN` · `Bridge`

### Firewall / NAT
`Firewall` · `NAT` · `SrcNAT` · `DstNAT` · `Filter-Rules`

### VPN
`VPN` · `IPsec` · `L2TP` · `WireGuard`

### Маршрутизация
`Routing` · `Static-Route`

### Эксплуатация / процесс
`Audit` · `Security` · `Troubleshooting` · `Configuration` · `Backup`
