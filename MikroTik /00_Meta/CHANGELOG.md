---
schema_version: "1.0"
status: "active"
maintainer: "cladkyimaffin-hue"
---

# 📜 CHANGELOG.md — журнал изменений конвейера (домен MikroTik)

Формат записи и типы событий — см. `Proxmox/00_Meta/CHANGELOG.md`
(идентичный формат, независимый журнал).

---

- 2026-09-17 | bootstrap | Создан каркас `00_Meta/` для домена `MikroTik/` (`SCHEMA.md` — общий с Proxmox, `TAGS.md` с первичным набором тегов, `registry.csv` с заголовками, `CONFLICTS.md`, `TEMPLATES/` — скопированы из Proxmox без изменений), папки категорий `01_Interfaces`, `02_Firewall_NAT`, `03_VPN`, `04_Routing`, `05_Troubleshooting`, `99_Archive`, `00_Inbox/`. Основание: тот же конвейер, что уже работает для `Proxmox/`, расширен на второй домен репозитория по решению администратора — во избежание того, что при росте числа доменов пришлось бы пересматривать архитектуру заново | Claude (по запросу cladkyimaffin-hue)
- 2026-09-17 | schema-change | `AI-INSTRUCTIONS.md` перенесён из `Proxmox/AI-INSTRUCTIONS.md` в корень репозитория (`korona/AI-INSTRUCTIONS.md`) — стал общим для всех доменов; пути в разделах 1 и 8а обобщены до `<домен>/00_Meta/...`. Обновлена ссылка в `Proxmox/AI-README.md` | Claude (по запросу cladkyimaffin-hue)
