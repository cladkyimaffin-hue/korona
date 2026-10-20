---
schema_version: "1.1"
date_created: 2026-09-11
date_modified: 2026-10-20
status: "active"
maintainer: "cladkyimaffin-hue"
---

# 📐 SCHEMA.md — доменные дополнения (Proxmox)

Общее ядро схемы (обязательные 15 полей, опциональный блок, формат
`document_id`, принцип эволюции, история версий) находится в
[`../../SCHEMA.md`](../../SCHEMA.md). Этот файл содержит только то, что
зависит от домена `Proxmox/`. При противоречии приоритет у корневого файла
— расхождение записывается в `CONFLICTS.md`.

## category

Имя целевой папки домена: `01_Hardware`, `02_Installation`, `03_Network`,
`04_Storage_Ceph`, `05_VirtualMachines`, `06_Troubleshooting`, `07_Vaultwarden`,
`08_Monitoring`, `99_Archive`. Для Zabbix-документов допустима подпапка:
`08_Monitoring/Zabbix` (решение администратора 2026-10-15, см. `CONFLICTS.md`).
Актуальный список — в `AI-README.md`.

## Доменные значения опциональных полей

```yaml
node: ""       # pve01 | pve02
cluster: ""     # krnn
```

## Теги и реестр

Теги — только из `TAGS.md` этого домена, `document_id` проверяются по
`registry.csv` этого домена.
