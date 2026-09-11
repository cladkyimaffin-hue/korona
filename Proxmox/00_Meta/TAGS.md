---
schema_version: "1.0"
date_created: 2026-09-11
status: "active"
maintainer: "cladkyimaffin-hue"
---

# 🏷️ Реестр тегов (TAGS.md)

Единственный источник допустимых тегов для поля `tags` в документах домена `Proxmox/`.
Конвейер и ИИ обязаны брать теги **только отсюда**. Если нужного тега нет —
сначала добавить его сюда (в нужную группу, без дублей по смыслу), потом
использовать в документе.

Формат тега: `PascalCase` без пробелов для составных понятий, либо оригинальное
имя технологии как оно пишется официально (`bond0`, `pve01`). Кириллица — только
если термина без окончательного устоявшегося английского эквивалента нет
(таких в реестре нет, все переведены для единообразия поиска).

## Причина: миграция с разнобоя написаний

При разборе архива тег писался по-разному в разных файлах. Ниже — таблица
"старое написание → канонический тег", используется на Этапе 1 при переносе
старых файлов, чтобы не плодить дубли смысла.

| Было (варианты в архиве) | Стало (канонический тег) |
|---|---|
| Proxmox, ProxmoxVE, Proxmox VE, proxmox | `ProxmoxVE` |
| Huawei 2288H V5, Huawei-2288H-V5 | `Huawei-2288H-V5` |
| Intel X722, Intel-X722 | `Intel-X722` |
| Intel X710, Intel-X710 | `Intel-X710` |
| 10G, 10G SFP+, 10GbE | `10GbE` (отдельно от `SFP+`, это разные факты — скорость и тип разъёма) |
| Windows Server 2022, WindowsServer2022 | `WindowsServer2022` |
| Windows Server 2025 | `WindowsServer2025` |
| QEMU Guest Agent, QEMUGuestAgent | `QEMUGuestAgent` |
| Active Directory, active-directory | `ActiveDirectory` |
| high-availability, HighAvailability, HA | `HighAvailability` |
| troubleshooting, Troubleshooting | `Troubleshooting` (используется как тег; `document_type` дублирует это же на уровне типа документа — оставляем оба, у них разная роль: тип документа vs тема) |
| диагностика | `Diagnostics` |
| управление памятью | `MemoryManagement` |
| оптика | `Optics` |
| коммутаторы | `Switches` |
| терминальный сервер, Remote Desktop Services | `RDS` (RDS Session Host / RDS Licensing / RDS CAL — слишком детально для тега, это уже содержание документа, не тег) |
| виртуальная машина | — (удалено: слишком общий тег, не несёт поисковой ценности; вместо этого — конкретный `VM-XXXX`) |
| репликация | `Replication` |

## Группы тегов

### Кластер и виртуализация
`ProxmoxVE` · `Cluster` · `krnn` · `pve01` · `pve02` · `QDevice` · `Corosync` · `Quorum` · `HighAvailability` · `corosync-qnetd` · `corosync-qdevice`

### Хранилище (Ceph)
`Ceph` · `Ceph-Squid` · `OSD` · `CRUSH` · `Pools` · `ceph-fast` · `ceph-bulk` · `Storage` · `WAL-DB`

### Сеть
`Networking` · `Bonding` · `LACP` · `bond0` · `SDN` · `WebGUI` · `10GbE` · `SFP+` · `DAC-cable` · `Optics` · `Switches`

### Оборудование
`Hardware` · `Huawei-2288H-V5` · `Intel-X722` · `Intel-X710`

### Виртуальные машины и шаблоны
`Template` · `FullClone` · `VirtIO` · `Sysprep` · `UEFI` · `TPM` · `QEMUGuestAgent` · `BalloonService`

### Windows / AD / службы
`WindowsServer2022` · `WindowsServer2025` · `ActiveDirectory` · `AD-DS` · `krnn.ru` · `Replication` · `DNS` · `RDS` · `dc-promotion` · `dfsr` · `sysvol`

### Linux / LXC / SSH
`LXC` · `Debian` · `Debian12` · `Debian13` · `SSH` · `OpenSSH` · `PAM` · `pam_systemd` · `systemd-logind` · `NAMESPACE`

### Приложения
`1C` · `1C-ERP` · `Vaultwarden`

### Эксплуатация / процесс
`Automation` · `Bash` · `Configuration` · `Hostname` · `Setup` · `Architecture` · `Security` · `Production` · `MemoryManagement` · `Diagnostics` · `Troubleshooting`

### Мониторинг
`zabbix`

## Правило добавления нового тега

1. Проверить, нет ли уже тега с тем же смыслом в другом написании (сверить с таблицей миграции выше).
2. Добавить в соответствующую группу (или создать новую группу, если ни одна не подходит).
3. Записать в `CHANGELOG.md`: дата, какой тег добавлен и почему.

