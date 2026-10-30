---
schema_version: "1.0"
date_modified: 2026-10-29
status: "active"
maintainer: "cladkyimaffin-hue"
file_type: "navigation_index"
source_of_truth: "00_Meta/registry.csv"
---

# Индекс папки: Proxmox

## Назначение

Навигация по документам домена `Proxmox`. Машиночитаемый список документов —
`00_Meta/registry.csv`; формат метаданных — `00_Meta/SCHEMA.md`; допустимые теги —
`00_Meta/TAGS.md`.

Факты об инфраструктуре (адреса, версии, параметры ВМ, сети, интерфейсы) в этом
файле **не хранятся**: они находятся в `AI-environment_facts-korona-proxmox.md`. Так значения не
расходятся между файлами.

## Порядок работы ИИ

Подробный порядок — в `START-HERE.md` (раздел 4). Кратко:

1. Определить объект запроса (узел, ВМ, CTID, Ceph, сеть, интерфейс, пул) и его
   фактический идентификатор.
2. Найти документ в таблице «Документы» ниже или в `00_Meta/registry.csv`.
3. Прочитать YAML-поля документа (`ai_summary`, `dont_repeat`, `related_files`) и раздел
   Quick Answers, если он есть.
4. Для изменения системы прочитать документ целиком: команды, откат, типовые ошибки.
5. Перед опасной командой запросить текущий вывод диагностики; исторические
   команды автоматически не выполнять.
6. В ответе разделять факт, предположение, рекомендацию и действие, требующее
   подтверждения.

## Документы

### `01_Hardware`

| ID | Документ | Тип | Статус | Приоритет | Теги |
|---|---|---|---|---|---|
| `HARDWARE-HUAWEI-2288H-PORTMAP-2026-001` | [Комплектация и маппинг сетевых портов Huawei 2288H V5 — подключение Proxmox без оптики](./01_Hardware/%D0%9A%D0%BE%D0%BC%D0%BF%D0%BB%D0%B5%D0%BA%D1%82%D0%B0%D1%86%D0%B8%D1%8F%20%D0%B8%20%D0%BC%D0%B0%D0%BF%D0%BF%D0%B8%D0%BD%D0%B3%20%D0%BF%D0%BE%D1%80%D1%82%D0%BE%D0%B2%20Huawei%202288H%20V5.md) | `reference` | `completed` | `medium` | `Hardware`, `Huawei-2288H-V5`, `Intel-X722`, `Intel-X710`, `DAC-cable`, `ProxmoxVE` |
| `NETWORK-SWITCH-SELECTION-2026-001` | [Подбор коммутатора и оптических кабелей для 10GbE SFP+ (TP-Link TL-SX3008F)](./01_Hardware/%D0%9F%D0%BE%D0%B4%D0%B1%D0%BE%D1%80%20%D0%BA%D0%BE%D0%BC%D0%BC%D1%83%D1%82%D0%B0%D1%82%D0%BE%D1%80%D0%B0%20%D0%B8%20%D0%BE%D0%BF%D1%82%D0%B8%D0%BA%D0%B8.md) | `reference` | `completed` | `medium` | `Hardware`, `Huawei-2288H-V5`, `Intel-X722`, `Intel-X710`, `Switches`, `Optics`, `10GbE` |

### `02_Installation`

| ID | Документ | Тип | Статус | Приоритет | Теги |
|---|---|---|---|---|---|
| `PROXMOX-NODE-RENAME-2026-001` | [Смена hostname узла Proxmox VE до вступления в кластер](./02_Installation/%D0%A1%D0%BC%D0%B5%D0%BD%D0%B0%20hostname%20%D1%83%D0%B7%D0%BB%D0%B0%20Proxmox%20VE.md) | `setup` | `completed` | `high` | `ProxmoxVE`, `Configuration`, `Hostname` |
| `PROXMOX-POSTINSTALL-SCRIPT-2026-001` | [Скрипт первичной настройки Proxmox VE (pstInstall) — типовые ответы для одного узла без подписки](./02_Installation/%D0%A1%D0%BA%D1%80%D0%B8%D0%BF%D1%82%20%D0%BF%D0%B5%D1%80%D0%B2%D0%B8%D1%87%D0%BD%D0%BE%D0%B9%20%D0%BD%D0%B0%D1%81%D1%82%D1%80%D0%BE%D0%B9%D0%BA%D0%B8%20Proxmox%20VE%20pstInstall.md) | `setup` | `completed` | `medium` | `ProxmoxVE`, `Automation`, `Bash`, `Setup` |
| `PROXMOX-LXC-DEBIAN12-TEMPLATE-2026-001` | [Создание шаблона Debian 12 LXC в Proxmox VE и развёртывание клонов](./02_Installation/%D0%A8%D0%B0%D0%B1%D0%BB%D0%BE%D0%BD%20Debian%2012%20LXC%20%D0%B8%20%D0%BA%D0%BB%D0%BE%D0%BD%D0%B8%D1%80%D0%BE%D0%B2%D0%B0%D0%BD%D0%B8%D0%B5.md) | `setup` | `completed` | `medium` | `ProxmoxVE`, `LXC`, `Debian12`, `Template`, `Automation` |
| `PROXMOX-CLUSTER-QDEVICE-SETUP-2026-001` | [Создание кластера Proxmox VE (krnn) из pve01+pve02 и настройка внешнего Corosync QDevice](./02_Installation/%D0%A1%D0%BE%D0%B7%D0%B4%D0%B0%D0%BD%D0%B8%D0%B5%20%D0%BA%D0%BB%D0%B0%D1%81%D1%82%D0%B5%D1%80%D0%B0%20%D0%B8%20QDevice.md) | `setup` | `completed` | `critical` | `ProxmoxVE`, `Cluster`, `QDevice`, `Corosync`, `Quorum`, `pve01`, `pve02`, `krnn`, `Debian`, `HighAvailability` |
| `PROXMOX-QDEVICE-REPLACEMENT-2026-001` | [Замена Corosync QDevice в кластере krnn (192.168.202.251 → 192.168.200.84)](./02_Installation/%D0%97%D0%B0%D0%BC%D0%B5%D0%BD%D0%B0%20Corosync%20QDevice.md) | `runbook` | `completed` | `high` | `ProxmoxVE`, `Cluster`, `QDevice`, `Corosync`, `Quorum`, `corosync-qnetd`, `corosync-qdevice`, `Debian13`, `SSH`, `Hostname`, `krnn`, `pve01`, `pve02` |

### `03_Network`

| ID | Документ | Тип | Статус | Приоритет | Теги |
|---|---|---|---|---|---|
| `PROXMOX-WEBGUI-DATACENTER-2026-001` | [Справочник по меню Datacenter в веб-интерфейсе Proxmox VE: общие пункты, HA, SDN](./03_Network/%D0%A1%D0%BF%D1%80%D0%B0%D0%B2%D0%BE%D1%87%D0%BD%D0%B8%D0%BA%20%D0%BC%D0%B5%D0%BD%D1%8E%20Datacenter%20Proxmox%20VE.md) | `reference` | `completed` | `info` | `ProxmoxVE`, `WebGUI`, `HighAvailability`, `SDN` |
| `NETWORK-BOND0-CEPH-ACTIVEBACKUP-2026-001` | [Настройка bond0 (active-backup) для выделенной сети Ceph между pve01 и pve02](./03_Network/%D0%9D%D0%B0%D1%81%D1%82%D1%80%D0%BE%D0%B9%D0%BA%D0%B0%20bond0%20active-backup%20%D0%B4%D0%BB%D1%8F%20%D1%81%D0%B5%D1%82%D0%B8%20Ceph.md) | `setup` | `completed` | `high` | `ProxmoxVE`, `Networking`, `Bonding`, `bond0`, `HighAvailability` |
| `PROXMOX-NETWORK-TOPOLOGY-2026-001` | [Физическая топология сети кластера krnn (pve01, pve02, коммутация)](./03_Network/%D0%A4%D0%B8%D0%B7%D0%B8%D1%87%D0%B5%D1%81%D0%BA%D0%B0%D1%8F%20%D1%82%D0%BE%D0%BF%D0%BE%D0%BB%D0%BE%D0%B3%D0%B8%D1%8F%20%D1%81%D0%B5%D1%82%D0%B8%20pve01-pve02.md) | `reference` | `in_progress` | `high` | `ProxmoxVE`, `Networking`, `Switches`, `SFP+`, `10GbE`, `Architecture`, `pve01`, `pve02`, `nic0`, `bond0`, `Ceph` |

### `04_Storage_Ceph`

| ID | Документ | Тип | Статус | Приоритет | Теги |
|---|---|---|---|---|---|
| `PROXMOX-CEPH-ARCHITECTURE-PLANNING-2026-001` | [Архитектурные решения: дисковая и сетевая топология для Ceph-кластера Proxmox](./04_Storage_Ceph/%D0%90%D1%80%D1%85%D0%B8%D1%82%D0%B5%D0%BA%D1%82%D1%83%D1%80%D0%BD%D1%8B%D0%B5%20%D1%80%D0%B5%D1%88%D0%B5%D0%BD%D0%B8%D1%8F%20Ceph-%D0%BA%D0%BB%D0%B0%D1%81%D1%82%D0%B5%D1%80%D0%B0.md) | `reference` | `completed` | `medium` | `ProxmoxVE`, `Ceph`, `Storage`, `Architecture`, `OSD` |
| `PROXMOX-CEPH-CONCEPTS-2NODE-2026-001` | [Ceph: производительность метаданных (WAL/DB), разные диски по объёму, связь с HA — применительно к схеме 2 узла + QDevice](./04_Storage_Ceph/Ceph%20%D1%82%D0%B5%D0%BE%D1%80%D0%B8%D1%8F%20WAL-DB%20%D1%80%D0%B0%D0%B7%D0%BD%D1%8B%D0%B5%20%D0%B4%D0%B8%D1%81%D0%BA%D0%B8%20%D0%B8%20HA.md) | `reference` | `completed` | `medium` | `ProxmoxVE`, `Ceph`, `Storage`, `OSD` |
| `PROXMOX-CEPH-OSD-DISK-PREP-2026-001` | [Подготовка дисков и утверждённая архитектура OSD для Ceph (2 узла: sdb + nvme0n1)](./04_Storage_Ceph/%D0%9F%D0%BE%D0%B4%D0%B3%D0%BE%D1%82%D0%BE%D0%B2%D0%BA%D0%B0%20%D0%B4%D0%B8%D1%81%D0%BA%D0%BE%D0%B2%20%D0%B8%20%D0%B0%D1%80%D1%85%D0%B8%D1%82%D0%B5%D0%BA%D1%82%D1%83%D1%80%D0%B0%20OSD.md) | `setup` | `completed` | `high` | `ProxmoxVE`, `Ceph`, `OSD`, `CRUSH`, `Storage`, `Planning` |
| `PROXMOX-CEPH-OSD-POOLS-DEPLOYMENT-2026-001` | [Развёртывание OSD и пулов Ceph на pve01/pve02 — до HEALTH_OK](./04_Storage_Ceph/%D0%A0%D0%B0%D0%B7%D0%B2%D1%91%D1%80%D1%82%D1%8B%D0%B2%D0%B0%D0%BD%D0%B8%D0%B5%20OSD%20%D0%B8%20%D0%BF%D1%83%D0%BB%D0%BE%D0%B2%20Ceph.md) | `setup` | `completed` | `critical` | `ProxmoxVE`, `Ceph`, `OSD`, `Storage`, `Setup`, `pve01`, `pve02` |
| `PROXMOX-CEPH-NIC0-DIRECT-LINK-2026-001` | [Миграция Ceph на прямой оптический канал nic0 и восстановление после сбоя](./04_Storage_Ceph/2026-09-30_ceph_nic0_direct_link_migration_and_recovery.md) | `troubleshooting` | `completed` | `high` | `ProxmoxVE`, `Ceph`, `Networking`, `nic0`, `MTU`, `10GbE`, `OSD`, `Configuration`, `Corosync`, `pve01`, `pve02`, `Troubleshooting` |

### `05_VirtualMachines`

| ID | Документ | Тип | Статус | Приоритет | Теги |
|---|---|---|---|---|---|
| `PROXMOX-WINSRV2022-TEMPLATE-2026-001` | [Создание шаблона Windows Server 2022 (VirtIO, UEFI+TPM, Sysprep) — итоговый ID 2000](./05_VirtualMachines/%D0%A8%D0%B0%D0%B1%D0%BB%D0%BE%D0%BD%20Windows%20Server%202022.md) | `setup` | `completed` | `high` | `ProxmoxVE`, `WindowsServer2022`, `Template`, `VirtIO`, `QEMUGuestAgent`, `Sysprep`, `UEFI`, `TPM` |
| `PROXMOX-VM-CLONE-2001-2026-001` | [Клонирование шаблона в производственную ВМ (пример: ВМ 2001, сервер 1С:ERP)](./05_VirtualMachines/%D0%9A%D0%BB%D0%BE%D0%BD%D0%B8%D1%80%D0%BE%D0%B2%D0%B0%D0%BD%D0%B8%D0%B5%20%D0%92%D0%9C%20%D0%BF%D0%BE%D0%B4%20%D1%80%D0%BE%D0%BB%D1%8C%201%D0%A1-ERP.md) | `runbook` | `completed` | `high` | `ProxmoxVE`, `WindowsServer2022`, `FullClone`, `1C`, `1C-ERP`, `Ceph`, `VirtIO`, `UEFI`, `TPM`, `QEMUGuestAgent`, `Production`, `Diagnostics` |
| `PROXMOX-AD-THIRD-DC-PROMOTION-2026-001` | [Добавление третьего контроллера домена (WIN-AD → AD, ВМ 2002) в домен krnn.ru — УСПЕШНО](./05_VirtualMachines/%D0%94%D0%BE%D0%B1%D0%B0%D0%B2%D0%BB%D0%B5%D0%BD%D0%B8%D0%B5%20%D1%82%D1%80%D0%B5%D1%82%D1%8C%D0%B5%D0%B3%D0%BE%20DC%20WIN-AD.md) | `runbook` | `completed` | `medium` | `ActiveDirectory`, `AD-DS`, `WindowsServer2022`, `WindowsServer2025`, `krnn.ru`, `ProxmoxVE`, `Replication`, `DNS`, `Troubleshooting`, `dfsr` |
| `PROXMOX-RDS-2003-2026-001` | [Настройка терминального сервера RDS на ВМ 2003 (TC.KRNN.RU) — функционален, лицензии CAL не куплены](./05_VirtualMachines/%D0%A2%D0%B5%D1%80%D0%BC%D0%B8%D0%BD%D0%B0%D0%BB%D1%8C%D0%BD%D1%8B%D0%B9%20%D1%81%D0%B5%D1%80%D0%B2%D0%B5%D1%80%20RDS%20%D0%92%D0%9C%202003.md) | `runbook` | `completed` | `high` | `WindowsServer2022`, `RDS`, `ActiveDirectory`, `krnn.ru`, `ProxmoxVE` |
| `PROXMOX-VM2001-USB-HASP-2026-001` | [Проброс USB-ключа HASP в ВМ 2001 (Srv1c) — путаница со встроенным KVM-контроллером](./05_VirtualMachines/%D0%9F%D1%80%D0%BE%D0%B1%D1%80%D0%BE%D1%81%20USB%20HASP%20%D0%B2%20%D0%92%D0%9C%202001.md) | `troubleshooting` | `completed` | `high` | `ProxmoxVE`, `USB-Passthrough`, `HASP`, `1C`, `pve01` |
| `PROXMOX-VM-MIGRATION-ISOLATION-2026-001` | [План миграции ВМ для изоляции 1С ERP](./05_VirtualMachines/%D0%9F%D0%BB%D0%B0%D0%BD%20%D0%BC%D0%B8%D0%B3%D1%80%D0%B0%D1%86%D0%B8%D0%B8%20%D0%92%D0%9C%20%D0%B4%D0%BB%D1%8F%20%D0%B8%D0%B7%D0%BE%D0%BB%D1%8F%D1%86%D0%B8%D0%B8%201%D0%A1%20ERP.md) | `runbook` | `archived` | `high` | `ProxmoxVE`, `Migration`, `1C`, `1C-ERP`, `pve01`, `pve02`, `Production`, `Troubleshooting` |
| `PROXMOX-AUTOSTART-STARTUP-ORDER-2026-001` | [Автозапуск и порядок старта ВМ и LXC на pve01](./05_VirtualMachines/%D0%90%D0%B2%D1%82%D0%BE%D0%B7%D0%B0%D0%BF%D1%83%D1%81%D0%BA%20%D0%B8%20%D0%BF%D0%BE%D1%80%D1%8F%D0%B4%D0%BE%D0%BA%20%D1%81%D1%82%D0%B0%D1%80%D1%82%D0%B0%20%D0%92%D0%9C%20%D0%B8%20LXC%20%D0%BD%D0%B0%20pve01.md) | `runbook` | `completed` | `high` | `ProxmoxVE`, `Autostart`, `pve01`, `LXC`, `ActiveDirectory`, `RDS`, `1C-ERP`, `Vaultwarden`, `Zabbix`, `Ceph`, `Configuration`, `Production` |

### `06_Troubleshooting`

| ID | Документ | Тип | Статус | Приоритет | Теги |
|---|---|---|---|---|---|
| `NETWORK-SFP-OPTICAL-MISMATCH-2026-001` | [Диагностика: оптические SFP-модули 1000BASE-SX вместо ожидаемых SFP+ RJ45 на Intel X710](./06_Troubleshooting/%D0%94%D0%B8%D0%B0%D0%B3%D0%BD%D0%BE%D1%81%D1%82%D0%B8%D0%BA%D0%B0%20SFP-%D0%BC%D0%BE%D0%B4%D1%83%D0%BB%D0%B5%D0%B9%20Intel%20X710.md) | `troubleshooting` | `completed` | `high` | `Troubleshooting`, `Intel-X710`, `SFP+`, `Optics`, `Switches`, `Diagnostics` |
| `LINUX-SSH-DEBIAN-ACCESS-2026-001` | [Чек-лист диагностики: доступ по SSH к Debian (неверный адрес, PermitRootLogin, статический IP)](./06_Troubleshooting/%D0%94%D0%B8%D0%B0%D0%B3%D0%BD%D0%BE%D1%81%D1%82%D0%B8%D0%BA%D0%B0%20SSH-%D0%B4%D0%BE%D1%81%D1%82%D1%83%D0%BF%D0%B0%20%D0%BA%20Debian.md) | `troubleshooting` | `completed` | `high` | `Troubleshooting`, `SSH`, `Debian`, `Security` |
| `LINUX-SSH-PAM-SYSTEMD-ZABBIX-2026-001` | [Устранение задержки SSH-входа в LXC (zabbix) из-за pam_systemd.so](./06_Troubleshooting/%D0%97%D0%B0%D0%B4%D0%B5%D1%80%D0%B6%D0%BA%D0%B0%20SSH%20%D0%B2%20LXC%20pam_systemd.md) | `troubleshooting` | `completed` | `medium` | `SSH`, `OpenSSH`, `PAM`, `pam_systemd`, `systemd-logind`, `LXC`, `Debian`, `NAMESPACE`, `Zabbix` |
| `PROXMOX-VM-MEMORY-BALLOON-2026-001` | [Некорректное отображение расхода RAM в Proxmox при использовании QEMU Guest Agent](./06_Troubleshooting/%D0%9D%D0%B5%D0%BA%D0%BE%D1%80%D1%80%D0%B5%D0%BA%D1%82%D0%BD%D1%8B%D0%B9%20%D1%80%D0%B0%D1%81%D1%85%D0%BE%D0%B4%20RAM%20QEMU%20Guest%20Agent.md) | `troubleshooting` | `completed` | `medium` | `ProxmoxVE`, `QEMUGuestAgent`, `VirtIO`, `BalloonService`, `WindowsServer2025`, `Diagnostics` |
| `PROXMOX-CEPH-BOND0-LATENCY-INVESTIGATION-2026-001` | [Исследование задержек записи Ceph через bond0 (165-204 мс) — НЕ ЗАВЕРШЕНО, реальная диагностика не начата](./06_Troubleshooting/%D0%A0%D0%B0%D1%81%D1%81%D0%BB%D0%B5%D0%B4%D0%BE%D0%B2%D0%B0%D0%BD%D0%B8%D0%B5%20%D0%B7%D0%B0%D0%B4%D0%B5%D1%80%D0%B6%D0%B5%D0%BA%20%D0%B7%D0%B0%D0%BF%D0%B8%D1%81%D0%B8%20Ceph.md) | `troubleshooting` | `in_progress` | `high` | `ProxmoxVE`, `Ceph`, `Networking`, `bond0`, `pve01`, `pve02`, `Troubleshooting` |
| `PROXMOX-CEPH-PUBLIC-NETWORK-1C-2026-001` | [Тормоза 1С (ВМ 2001 Srv1c): public_network и линк pve02 — ЧАСТИЧНО ПРОВЕРЕНО](./06_Troubleshooting/1c-slow-public-network-2026-10-15.md) | `troubleshooting` | `in_progress` | `high` | `ProxmoxVE`, `Ceph`, `OSD`, `Networking`, `Troubleshooting`, `Diagnostics`, `1C`, `pve01`, `pve02` |
| `PROXMOX-VM2002-AD-RAM-INCREASE-2026-001` | [Нехватка RAM на ВМ 2002 AD и увеличение до 8 ГБ](./06_Troubleshooting/%D0%9D%D0%B5%D1%85%D0%B2%D0%B0%D1%82%D0%BA%D0%B0%20RAM%20%D0%BD%D0%B0%20%D0%92%D0%9C%202002%20AD%20%D0%B8%20%D1%83%D0%B2%D0%B5%D0%BB%D0%B8%D1%87%D0%B5%D0%BD%D0%B8%D0%B5%20%D0%B4%D0%BE%208%20%D0%93%D0%91.md) | `troubleshooting` | `completed` | `medium` | `ProxmoxVE`, `WindowsServer2025`, `ActiveDirectory`, `BalloonService`, `MemoryManagement`, `QEMUGuestAgent`, `Diagnostics`, `Troubleshooting`, `Configuration`, `pve01` |
| `PROXMOX-AD-DFSR-SYSVOL-RECOVERY-2026-001` | [Восстановление репликации SYSVOL (DFSR) на контроллерах krnn.ru — DC в ошибке 4012, AD в Initial Sync](./06_Troubleshooting/%D0%92%D0%BE%D1%81%D1%81%D1%82%D0%B0%D0%BD%D0%BE%D0%B2%D0%BB%D0%B5%D0%BD%D0%B8%D0%B5%20%D1%80%D0%B5%D0%BF%D0%BB%D0%B8%D0%BA%D0%B0%D1%86%D0%B8%D0%B8%20SYSVOL%20DFSR%20%D0%BD%D0%B0%20%D0%BA%D0%BE%D0%BD%D1%82%D1%80%D0%BE%D0%BB%D0%BB%D0%B5%D1%80%D0%B0%D1%85%20%D0%B4%D0%BE%D0%BC%D0%B5%D0%BD%D0%B0.md) | `troubleshooting` | `completed` | `high` | `ActiveDirectory`, `AD-DS`, `WindowsServer2025`, `krnn.ru`, `Replication`, `dfsr`, `sysvol`, `DNS`, `Zabbix`, `Diagnostics`, `Troubleshooting`, `pve01` |

### `07_Vaultwarden`

| ID | Документ | Тип | Статус | Приоритет | Теги |
|---|---|---|---|---|---|
| `PROXMOX-VAULTWARDEN-INSTALL-2026-001` | [Установка Vaultwarden (сервер паролей) в LXC Debian 12 — CT 600 (passwd)](./07_Vaultwarden/%D0%A3%D1%81%D1%82%D0%B0%D0%BD%D0%BE%D0%B2%D0%BA%D0%B0%20Vaultwarden%20CT600.md) | `setup` | `completed` | `medium` | `Vaultwarden`, `LXC`, `Debian12`, `ProxmoxVE` |
| `PROXMOX-VAULTWARDEN-HTTPS-CADDY-2026-001` | [Настройка HTTPS для Vaultwarden через Caddy (reverse proxy, самоподписанный сертификат)](./07_Vaultwarden/HTTPS%20%D0%B4%D0%BB%D1%8F%20Vaultwarden%20%D1%87%D0%B5%D1%80%D0%B5%D0%B7%20Caddy.md) | `setup` | `completed` | `medium` | `Vaultwarden`, `ProxmoxVE`, `LXC`, `Debian12` |
| `PROXMOX-VAULTWARDEN-ADMIN-TOKEN-2026-001` | [Vaultwarden: «Invalid admin token» из-за лишнего экранирования $$ в EnvironmentFile, ошибка смены мастер-пароля](./07_Vaultwarden/ADMIN_TOKEN%20%D0%B8%20%D1%81%D0%BC%D0%B5%D0%BD%D0%B0%20%D0%BC%D0%B0%D1%81%D1%82%D0%B5%D1%80-%D0%BF%D0%B0%D1%80%D0%BE%D0%BB%D1%8F.md) | `troubleshooting` | `completed` | `medium` | `Vaultwarden`, `Troubleshooting`, `ProxmoxVE` |
| `PROXMOX-VAULTWARDEN-USERS-2026-001` | [Настройка пользователей Vaultwarden (приглашения) и ошибка Bitwarden-расширения в Chrome — НЕ ЗАВЕРШЕНО](./07_Vaultwarden/%D0%9D%D0%B0%D1%81%D1%82%D1%80%D0%BE%D0%B9%D0%BA%D0%B0%20%D0%BF%D0%BE%D0%BB%D1%8C%D0%B7%D0%BE%D0%B2%D0%B0%D1%82%D0%B5%D0%BB%D0%B5%D0%B9%20%D0%B8%20%D0%BE%D1%88%D0%B8%D0%B1%D0%BA%D0%B0%20Chrome.md) | `troubleshooting` | `in_progress` | `medium` | `Vaultwarden`, `Troubleshooting`, `ProxmoxVE` |

### `08_Monitoring/Zabbix`

| ID | Документ | Тип | Статус | Приоритет | Теги |
|---|---|---|---|---|---|
| `ZABBIX-STACK-INSTALL-2026-001` | [Установка стека Zabbix 7.0 LTS (LXC 700) — MariaDB, Nginx, PHP-FPM](./08_Monitoring/Zabbix/%D0%A3%D1%81%D1%82%D0%B0%D0%BD%D0%BE%D0%B2%D0%BA%D0%B0%20%D1%81%D1%82%D0%B5%D0%BA%D0%B0%20Zabbix.md) | `setup` | `completed` | `high` | `ProxmoxVE`, `Zabbix`, `LXC`, `Debian12`, `MariaDB`, `Security` |
| `ZABBIX-PVE-API-MONITORING-2026-001` | [Мониторинг кластера Proxmox через API в Zabbix (шаблон Proxmox VE by HTTP) — ошибка 403 из-за Privilege Separation токена (решено), ошибка 401 (решено)](./08_Monitoring/Zabbix/%D0%9C%D0%BE%D0%BD%D0%B8%D1%82%D0%BE%D1%80%D0%B8%D0%BD%D0%B3%20Proxmox%20%D1%87%D0%B5%D1%80%D0%B5%D0%B7%20API.md) | `setup` | `completed` | `high` | `ProxmoxVE`, `Zabbix`, `krnn`, `pve01`, `pve02` |
| `ZABBIX-AGENT-PVE-NODES-2026-001` | [Установка Zabbix Agent на pve01/pve02 — репозиторий Zabbix для bookworm несовместим, узлы на Debian 13 (trixie)](./08_Monitoring/Zabbix/%D0%A3%D1%81%D1%82%D0%B0%D0%BD%D0%BE%D0%B2%D0%BA%D0%B0%20Zabbix%20Agent%20%D0%BD%D0%B0%20%D1%83%D0%B7%D0%BB%D0%B0%D1%85.md) | `setup` | `completed` | `medium` | `ProxmoxVE`, `Zabbix`, `Debian`, `pve01`, `pve02` |
| `ZABBIX-LXC-FALSE-ALERTS-2026-001` | [Ложные алерты Zabbix для собственного LXC-хоста Zabbix (память, Load Average, интерфейсы DOWN)](./08_Monitoring/Zabbix/%D0%9B%D0%BE%D0%B6%D0%BD%D1%8B%D0%B5%20%D0%B0%D0%BB%D0%B5%D1%80%D1%82%D1%8B%20Zabbix%20%D0%B4%D0%BB%D1%8F%20LXC-%D1%85%D0%BE%D1%81%D1%82%D0%B0%20Zabbix%20%28%D0%BF%D0%B0%D0%BC%D1%8F%D1%82%D1%8C%20Load%20Average%20%D0%B8%D0%BD%D1%82%D0%B5%D1%80%D1%84%D0%B5%D0%B9%D1%81%D1%8B%29.md) | `troubleshooting` | `in_progress` | `medium` | `Zabbix`, `LXC`, `Debian12`, `MemoryManagement`, `Diagnostics`, `Troubleshooting`, `ProxmoxVE`, `pve02`, `Hostname`, `Bash` |

### `99_Archive`

| ID | Документ | Тип | Статус | Приоритет | Теги |
|---|---|---|---|---|---|
| `ARCHIVE-QDEVICE-DRAFT-2026-001` | [\[АРХИВ — ДУБЛИКАТ\] Настройка Corosync QDevice — обобщённый черновик](./99_Archive/%D0%94%D0%BE%D0%B1%D0%B0%D0%B2%D0%B8%D1%82%D1%8C%20qdevice%20%28%D0%B0%D1%80%D1%85%D0%B8%D0%B2-%D0%B4%D1%83%D0%B1%D0%BB%D0%B8%D0%BA%D0%B0%D1%82%29.md) | `reference` | `archived` | `info` | `ProxmoxVE`, `QDevice`, `Corosync` |
| `ARCHIVE-HARDWARE-SPEC-DRAFT-2026-001` | [\[АРХИВ — УСТАРЕЛО\] Сводная спецификация оборудования — черновик на сценарий 3 серверов](./99_Archive/hardware-spec%20%28%D0%B0%D1%80%D1%85%D0%B8%D0%B2-%D1%83%D1%81%D1%82%D0%B0%D1%80%D0%B5%D0%BB%D0%BE%29.md) | `reference` | `archived` | `info` | `Hardware`, `Huawei-2288H-V5` |

## ⚡ Quick Answers

Ответы ниже краткие и не добавляют адресов, версий и параметров ВМ: актуальные значения —
в `AI-environment_facts-korona-proxmox.md`.

| Вопрос | Краткий ответ | Документ |
|---|---|---|
| Какой состав кластера? | Две ноды (`pve01`, `pve02`) плюс внешний QDevice на Debian. Адреса — в env facts. | [02_Installation/Создание кластера и QDevice.md](./02_Installation/%D0%A1%D0%BE%D0%B7%D0%B4%D0%B0%D0%BD%D0%B8%D0%B5%20%D0%BA%D0%BB%D0%B0%D1%81%D1%82%D0%B5%D1%80%D0%B0%20%D0%B8%20QDevice.md) |
| Зачем нужен QDevice? | Он даёт дополнительный голос кворума Proxmox для двухнодовой конфигурации. | [02_Installation/Создание кластера и QDevice.md](./02_Installation/%D0%A1%D0%BE%D0%B7%D0%B4%D0%B0%D0%BD%D0%B8%D0%B5%20%D0%BA%D0%BB%D0%B0%D1%81%D1%82%D0%B5%D1%80%D0%B0%20%D0%B8%20QDevice.md) |
| Как заменить QDevice на другой хост? | `pvecm qdevice remove`, подготовка нового хоста с `corosync-qnetd`, затем `pvecm qdevice setup <IP>` с pve01; нужен вход root по SSH-ключу на новый хост. | [02_Installation/Замена Corosync QDevice.md](./02_Installation/%D0%97%D0%B0%D0%BC%D0%B5%D0%BD%D0%B0%20Corosync%20QDevice.md) |
| Нужно ли создавать Ceph MON на QDevice? | Нет. QDevice не является полноценной Ceph-нодой. | [04_Storage_Ceph/Ceph теория WAL-DB разные диски и HA.md](./04_Storage_Ceph/Ceph%20%D1%82%D0%B5%D0%BE%D1%80%D0%B8%D1%8F%20WAL-DB%20%D1%80%D0%B0%D0%B7%D0%BD%D1%8B%D0%B5%20%D0%B4%D0%B8%D1%81%D0%BA%D0%B8%20%D0%B8%20HA.md) |
| Где создавать OSD? | Только на узлах с физическими дисками: `pve01` и `pve02`. | [04_Storage_Ceph/Развёртывание OSD и пулов Ceph.md](./04_Storage_Ceph/%D0%A0%D0%B0%D0%B7%D0%B2%D1%91%D1%80%D1%82%D1%8B%D0%B2%D0%B0%D0%BD%D0%B8%D0%B5%20OSD%20%D0%B8%20%D0%BF%D1%83%D0%BB%D0%BE%D0%B2%20Ceph.md) |
| Сколько OSD в текущей схеме? | По два OSD на каждой ноде, всего четыре. | [04_Storage_Ceph/Подготовка дисков и архитектура OSD.md](./04_Storage_Ceph/%D0%9F%D0%BE%D0%B4%D0%B3%D0%BE%D1%82%D0%BE%D0%B2%D0%BA%D0%B0%20%D0%B4%D0%B8%D1%81%D0%BA%D0%BE%D0%B2%20%D0%B8%20%D0%B0%D1%80%D1%85%D0%B8%D1%82%D0%B5%D0%BA%D1%82%D1%83%D1%80%D0%B0%20OSD.md) |
| Что хранится на NVMe OSD? | Быстрые ВМ: 1С, RDS и Active Directory. | [04_Storage_Ceph/Развёртывание OSD и пулов Ceph.md](./04_Storage_Ceph/%D0%A0%D0%B0%D0%B7%D0%B2%D1%91%D1%80%D1%82%D1%8B%D0%B2%D0%B0%D0%BD%D0%B8%D0%B5%20OSD%20%D0%B8%20%D0%BF%D1%83%D0%BB%D0%BE%D0%B2%20Ceph.md) |
| Что хранится на SSD sdb OSD? | Бэкапы и менее чувствительные к задержкам ВМ. | [04_Storage_Ceph/Ceph теория WAL-DB разные диски и HA.md](./04_Storage_Ceph/Ceph%20%D1%82%D0%B5%D0%BE%D1%80%D0%B8%D1%8F%20WAL-DB%20%D1%80%D0%B0%D0%B7%D0%BD%D1%8B%D0%B5%20%D0%B4%D0%B8%D1%81%D0%BA%D0%B8%20%D0%B8%20HA.md) |
| Объединяется ли RAM через Ceph? | Нет. RAM всегда локальна для ноды, где запущена ВМ. | [04_Storage_Ceph/Ceph теория WAL-DB разные диски и HA.md](./04_Storage_Ceph/Ceph%20%D1%82%D0%B5%D0%BE%D1%80%D0%B8%D1%8F%20WAL-DB%20%D1%80%D0%B0%D0%B7%D0%BD%D1%8B%D0%B5%20%D0%B4%D0%B8%D1%81%D0%BA%D0%B8%20%D0%B8%20HA.md) |
| Что делает Ceph? | Даёт общее распределённое хранилище и репликацию дисков ВМ. | [04_Storage_Ceph/Ceph теория WAL-DB разные диски и HA.md](./04_Storage_Ceph/Ceph%20%D1%82%D0%B5%D0%BE%D1%80%D0%B8%D1%8F%20WAL-DB%20%D1%80%D0%B0%D0%B7%D0%BD%D1%8B%D0%B5%20%D0%B4%D0%B8%D1%81%D0%BA%D0%B8%20%D0%B8%20HA.md) |
| Что делает HA? | Автоматически перезапускает ВМ на другой ноде после отказа. | [04_Storage_Ceph/Ceph теория WAL-DB разные диски и HA.md](./04_Storage_Ceph/Ceph%20%D1%82%D0%B5%D0%BE%D1%80%D0%B8%D1%8F%20WAL-DB%20%D1%80%D0%B0%D0%B7%D0%BD%D1%8B%D0%B5%20%D0%B4%D0%B8%D1%81%D0%BA%D0%B8%20%D0%B8%20HA.md) |
| Можно ли использовать Ceph без HA? | Да. Ceph и HA независимы, но HA требует общего доступного хранилища. | [04_Storage_Ceph/Ceph теория WAL-DB разные диски и HA.md](./04_Storage_Ceph/Ceph%20%D1%82%D0%B5%D0%BE%D1%80%D0%B8%D1%8F%20WAL-DB%20%D1%80%D0%B0%D0%B7%D0%BD%D1%8B%D0%B5%20%D0%B4%D0%B8%D1%81%D0%BA%D0%B8%20%D0%B8%20HA.md) |
| Когда включать HA? | После готовности кворума, Ceph, пулов, сети и проверки свободной RAM. | [03_Network/Справочник меню Datacenter Proxmox VE.md](./03_Network/%D0%A1%D0%BF%D1%80%D0%B0%D0%B2%D0%BE%D1%87%D0%BD%D0%B8%D0%BA%20%D0%BC%D0%B5%D0%BD%D1%8E%20Datacenter%20Proxmox%20VE.md) |
| Какие сети и интерфейсы у кластера? | Адреса и актуальное состояние — в env facts; физическая схема (`nic0` — прямой канал, `nic2` — public_network через коммутаторы) — в документе о топологии. | [03_Network/Физическая топология сети pve01-pve02.md](./03_Network/%D0%A4%D0%B8%D0%B7%D0%B8%D1%87%D0%B5%D1%81%D0%BA%D0%B0%D1%8F%20%D1%82%D0%BE%D0%BF%D0%BE%D0%BB%D0%BE%D0%B3%D0%B8%D1%8F%20%D1%81%D0%B5%D1%82%D0%B8%20pve01-pve02.md) |
| Почему клиентский трафик ВМ может быть медленным? | Скорость public_network проверена и описана в env facts; причина тормозов 1С не доказана. | [06_Troubleshooting/1c-slow-public-network-2026-10-15.md](./06_Troubleshooting/1c-slow-public-network-2026-10-15.md) |
| Что проверить, если OSD не стартуют после смены `cluster_network`? | Локальный `/etc/ceph/ceph.conf`: его `cluster_network` / `public_network` имеют приоритет над монитором; значения задавать подсетью, не закомментированными и не адресом с маской. | [04_Storage_Ceph/2026-09-30_ceph_nic0_direct_link_migration_and_recovery.md](./04_Storage_Ceph/2026-09-30_ceph_nic0_direct_link_migration_and_recovery.md) |
| Какой режим bond0? | `active-backup`: один активный линк, второй резервный. Сейчас Ceph не использует `bond0` — актуальное состояние в env facts. | [03_Network/Настройка bond0 active-backup для сети Ceph.md](./03_Network/%D0%9D%D0%B0%D1%81%D1%82%D1%80%D0%BE%D0%B9%D0%BA%D0%B0%20bond0%20active-backup%20%D0%B4%D0%BB%D1%8F%20%D1%81%D0%B5%D1%82%D0%B8%20Ceph.md) |
| Даёт ли active-backup сумму скоростей? | Нет. Для агрегации нужна 802.3ad/LACP и настройка коммутатора. | [03_Network/Настройка bond0 active-backup для сети Ceph.md](./03_Network/%D0%9D%D0%B0%D1%81%D1%82%D1%80%D0%BE%D0%B9%D0%BA%D0%B0%20bond0%20active-backup%20%D0%B4%D0%BB%D1%8F%20%D1%81%D0%B5%D1%82%D0%B8%20Ceph.md) |
| Где настраивается IP bond? | На `bond0`, а не на `nic4` и `nic5`. | [03_Network/Настройка bond0 active-backup для сети Ceph.md](./03_Network/%D0%9D%D0%B0%D1%81%D1%82%D1%80%D0%BE%D0%B9%D0%BA%D0%B0%20bond0%20active-backup%20%D0%B4%D0%BB%D1%8F%20%D1%81%D0%B5%D1%82%D0%B8%20Ceph.md) |
| Как проверить Ceph? | `ceph -s`, `ceph osd tree`, `ceph df`, `ceph osd pool ls detail` — готовые блоки в `COMMANDS.md` (разделы 3 и 19); норма: `HEALTH_OK`, все OSD `up`/`in`, PG `active+clean`. При `HEALTH_WARN` и для заполнения по OSD обычно смотрят ещё `ceph health detail` и `ceph osd df` (стандартные команды Ceph, в документах репозитория не описаны). | [COMMANDS.md](./COMMANDS.md) |
| Какое нормальное состояние PG? | `active+clean`. | [04_Storage_Ceph/Развёртывание OSD и пулов Ceph.md](./04_Storage_Ceph/%D0%A0%D0%B0%D0%B7%D0%B2%D1%91%D1%80%D1%82%D1%8B%D0%B2%D0%B0%D0%BD%D0%B8%D0%B5%20OSD%20%D0%B8%20%D0%BF%D1%83%D0%BB%D0%BE%D0%B2%20Ceph.md) |
| Почему Ceph показывает HEALTH_WARN после создания OSD? | Нужно проверить размер реплик пула и состояние PG; пул с Size=3 не подходит для двух узлов с OSD. | [04_Storage_Ceph/Ceph теория WAL-DB разные диски и HA.md](./04_Storage_Ceph/Ceph%20%D1%82%D0%B5%D0%BE%D1%80%D0%B8%D1%8F%20WAL-DB%20%D1%80%D0%B0%D0%B7%D0%BD%D1%8B%D0%B5%20%D0%B4%D0%B8%D1%81%D0%BA%D0%B8%20%D0%B8%20HA.md) |
| Какой размер реплики использовать для двух узлов? | Обычно `Size=2`; Min Size выбирается с учётом требуемой доступности и риска работы без полной репликации. | [04_Storage_Ceph/Подготовка дисков и архитектура OSD.md](./04_Storage_Ceph/%D0%9F%D0%BE%D0%B4%D0%B3%D0%BE%D1%82%D0%BE%D0%B2%D0%BA%D0%B0%20%D0%B4%D0%B8%D1%81%D0%BA%D0%BE%D0%B2%20%D0%B8%20%D0%B0%D1%80%D1%85%D0%B8%D1%82%D0%B5%D0%BA%D1%82%D1%83%D1%80%D0%B0%20OSD.md) |
| Как подготовить новый OSD? | Идентифицировать диск, проверить отсутствие данных, очистить сигнатуры и только потом создать OSD. | [04_Storage_Ceph/Развёртывание OSD и пулов Ceph.md](./04_Storage_Ceph/%D0%A0%D0%B0%D0%B7%D0%B2%D1%91%D1%80%D1%82%D1%8B%D0%B2%D0%B0%D0%BD%D0%B8%D0%B5%20OSD%20%D0%B8%20%D0%BF%D1%83%D0%BB%D0%BE%D0%B2%20Ceph.md) |
| Какой диск нельзя использовать для OSD? | Системный диск и любой диск с нужными данными. | [01_Hardware/Комплектация и маппинг портов Huawei 2288H V5.md](./01_Hardware/%D0%9A%D0%BE%D0%BC%D0%BF%D0%BB%D0%B5%D0%BA%D1%82%D0%B0%D1%86%D0%B8%D1%8F%20%D0%B8%20%D0%BC%D0%B0%D0%BF%D0%BF%D0%B8%D0%BD%D0%B3%20%D0%BF%D0%BE%D1%80%D1%82%D0%BE%D0%B2%20Huawei%202288H%20V5.md) |
| Как создана VM 2001? | Full Clone из шаблона 2000 на `ceph-fast`. Актуальные параметры ВМ — в env facts. | [05_VirtualMachines/Клонирование ВМ под роль 1С-ERP.md](./05_VirtualMachines/%D0%9A%D0%BB%D0%BE%D0%BD%D0%B8%D1%80%D0%BE%D0%B2%D0%B0%D0%BD%D0%B8%D0%B5%20%D0%92%D0%9C%20%D0%BF%D0%BE%D0%B4%20%D1%80%D0%BE%D0%BB%D1%8C%201%D0%A1-ERP.md) |
| Зависит ли VM 2001 от VM 2000? | Нет, после Full Clone диск независим. | [05_VirtualMachines/Клонирование ВМ под роль 1С-ERP.md](./05_VirtualMachines/%D0%9A%D0%BB%D0%BE%D0%BD%D0%B8%D1%80%D0%BE%D0%B2%D0%B0%D0%BD%D0%B8%D0%B5%20%D0%92%D0%9C%20%D0%BF%D0%BE%D0%B4%20%D1%80%D0%BE%D0%BB%D1%8C%201%D0%A1-ERP.md) |
| Можно ли удалить шаблон 2000? | Да, после проверки Full Clone, запуска VM 2001 и резервной копии. | [05_VirtualMachines/Клонирование ВМ под роль 1С-ERP.md](./05_VirtualMachines/%D0%9A%D0%BB%D0%BE%D0%BD%D0%B8%D1%80%D0%BE%D0%B2%D0%B0%D0%BD%D0%B8%D0%B5%20%D0%92%D0%9C%20%D0%BF%D0%BE%D0%B4%20%D1%80%D0%BE%D0%BB%D1%8C%201%D0%A1-ERP.md) |
| Как увеличить диск Windows? | Сначала `qm resize`, затем отдельно расширить раздел внутри Windows. | [05_VirtualMachines/Клонирование ВМ под роль 1С-ERP.md](./05_VirtualMachines/%D0%9A%D0%BB%D0%BE%D0%BD%D0%B8%D1%80%D0%BE%D0%B2%D0%B0%D0%BD%D0%B8%D0%B5%20%D0%92%D0%9C%20%D0%BF%D0%BE%D0%B4%20%D1%80%D0%BE%D0%BB%D1%8C%201%D0%A1-ERP.md) |
| Почему Windows не расширяет C:? | Recovery-раздел находится сразу после C:. | [05_VirtualMachines/Клонирование ВМ под роль 1С-ERP.md](./05_VirtualMachines/%D0%9A%D0%BB%D0%BE%D0%BD%D0%B8%D1%80%D0%BE%D0%B2%D0%B0%D0%BD%D0%B8%D0%B5%20%D0%92%D0%9C%20%D0%BF%D0%BE%D0%B4%20%D1%80%D0%BE%D0%BB%D1%8C%201%D0%A1-ERP.md) |
| Какой шаблон Windows используется? | Windows Server 2022 с q35, UEFI, TPM 2.0, VirtIO и QEMU Guest Agent. | [05_VirtualMachines/Шаблон Windows Server 2022.md](./05_VirtualMachines/%D0%A8%D0%B0%D0%B1%D0%BB%D0%BE%D0%BD%20Windows%20Server%202022.md) |
| Зачем нужен Sysprep? | Для обобщения Windows перед клонированием и предотвращения конфликтов идентификаторов. | [05_VirtualMachines/Шаблон Windows Server 2022.md](./05_VirtualMachines/%D0%A8%D0%B0%D0%B1%D0%BB%D0%BE%D0%BD%20Windows%20Server%202022.md) |
| Как создать Debian LXC-шаблон? | Создать контейнер, настроить и очистить его, остановить, перевести в template и клонировать. | [02_Installation/Шаблон Debian 12 LXC и клонирование.md](./02_Installation/%D0%A8%D0%B0%D0%B1%D0%BB%D0%BE%D0%BD%20Debian%2012%20LXC%20%D0%B8%20%D0%BA%D0%BB%D0%BE%D0%BD%D0%B8%D1%80%D0%BE%D0%B2%D0%B0%D0%BD%D0%B8%D0%B5.md) |
| Почему не работает SSH root? | Проверить PermitRootLogin, ключи, права `.ssh`, службу SSH и firewall. | [06_Troubleshooting/Диагностика SSH-доступа к Debian.md](./06_Troubleshooting/%D0%94%D0%B8%D0%B0%D0%B3%D0%BD%D0%BE%D1%81%D1%82%D0%B8%D0%BA%D0%B0%20SSH-%D0%B4%D0%BE%D1%81%D1%82%D1%83%D0%BF%D0%B0%20%D0%BA%20Debian.md) |
| Как исправить Enterprise repository без подписки? | Отключить Enterprise и оставить корректный no-subscription-источник для текущей версии PVE. | [02_Installation/Скрипт первичной настройки Proxmox VE pstInstall.md](./02_Installation/%D0%A1%D0%BA%D1%80%D0%B8%D0%BF%D1%82%20%D0%BF%D0%B5%D1%80%D0%B2%D0%B8%D1%87%D0%BD%D0%BE%D0%B9%20%D0%BD%D0%B0%D1%81%D1%82%D1%80%D0%BE%D0%B9%D0%BA%D0%B8%20Proxmox%20VE%20pstInstall.md) |
| Где искать сведения о железе? | В документе о комплектации и маппинге портов Huawei 2288H V5. | [01_Hardware/Комплектация и маппинг портов Huawei 2288H V5.md](./01_Hardware/%D0%9A%D0%BE%D0%BC%D0%BF%D0%BB%D0%B5%D0%BA%D1%82%D0%B0%D1%86%D0%B8%D1%8F%20%D0%B8%20%D0%BC%D0%B0%D0%BF%D0%BF%D0%B8%D0%BD%D0%B3%20%D0%BF%D0%BE%D1%80%D1%82%D0%BE%D0%B2%20Huawei%202288H%20V5.md) |
| Почему Zabbix показывает ложную загрузку памяти >90% на своём же LXC-хосте? | `sysinfo()` в LXC не изолирован cgroups и возвращает RAM физического хоста, а не лимит контейнера — использовать кастомный ключ поверх `/proc/meminfo`. | [08_Monitoring/Zabbix/Ложные алерты Zabbix для LXC-хоста Zabbix (память Load Average интерфейсы).md](./08_Monitoring/Zabbix/%D0%9B%D0%BE%D0%B6%D0%BD%D1%8B%D0%B5%20%D0%B0%D0%BB%D0%B5%D1%80%D1%82%D1%8B%20Zabbix%20%D0%B4%D0%BB%D1%8F%20LXC-%D1%85%D0%BE%D1%81%D1%82%D0%B0%20Zabbix%20%28%D0%BF%D0%B0%D0%BC%D1%8F%D1%82%D1%8C%20Load%20Average%20%D0%B8%D0%BD%D1%82%D0%B5%D1%80%D1%84%D0%B5%D0%B9%D1%81%D1%8B%29.md) |
| Почему Load Average завышен на LXC-хосте Zabbix при 100% CPU idle? | Рассинхрон «Hostname» агента и имени хоста в Zabbix (retry-шторм) плюс артефакт LXC: контейнер видит все ядра физического хоста. | [08_Monitoring/Zabbix/Ложные алерты Zabbix для LXC-хоста Zabbix (память Load Average интерфейсы).md](./08_Monitoring/Zabbix/%D0%9B%D0%BE%D0%B6%D0%BD%D1%8B%D0%B5%20%D0%B0%D0%BB%D0%B5%D1%80%D1%82%D1%8B%20Zabbix%20%D0%B4%D0%BB%D1%8F%20LXC-%D1%85%D0%BE%D1%81%D1%82%D0%B0%20Zabbix%20%28%D0%BF%D0%B0%D0%BC%D1%8F%D1%82%D1%8C%20Load%20Average%20%D0%B8%D0%BD%D1%82%D0%B5%D1%80%D1%84%D0%B5%D0%B9%D1%81%D1%8B%29.md) |
| Мониторинг Proxmox через Zabbix даёт 403 Forbidden, хотя у пользователя есть права — что делать? | Причина — Privilege Separation (`privsep=1`): у API-токена собственные ACL, права пользователя он не наследует. Нужен явный ACL на сам токен (`pveum acl modify <путь> --token '<пользователь>!<токен>' --role <роль>`), при этом права токена не шире прав пользователя на том же пути; подробности в документе. | [08_Monitoring/Zabbix/Мониторинг Proxmox через API.md](./08_Monitoring/Zabbix/%D0%9C%D0%BE%D0%BD%D0%B8%D1%82%D0%BE%D1%80%D0%B8%D0%BD%D0%B3%20Proxmox%20%D1%87%D0%B5%D1%80%D0%B5%D0%B7%20API.md) |
| Мониторинг Proxmox через Zabbix даёт 401 Unauthorized — что делать? | 401 — сбой аутентификации, а не нехватка прав (она даёт 403). Прямым `curl` проверить формат заголовка `PVEAPIToken=USER@REALM!TOKENID=SECRET` (знак `=` перед секретом), затем ID и секрет токена в макросах Zabbix. Если `curl` отвечает 403 `Permission check failed (/, Sys.Audit)`, права нужно выдать и пользователю, и токену на `/` (при `privsep=1` права токена ограничены правами пользователя). Секрет показывается один раз при создании. Подробности — в документе. | [08_Monitoring/Zabbix/Мониторинг Proxmox через API.md](./08_Monitoring/Zabbix/%D0%9C%D0%BE%D0%BD%D0%B8%D1%82%D0%BE%D1%80%D0%B8%D0%BD%D0%B3%20Proxmox%20%D1%87%D0%B5%D1%80%D0%B5%D0%B7%20API.md) |
| Какой тип кабеля нужен для 10GBASE-SR? | LC duplex, 2 волокна, многомодовый OM3/OM4, 50/125. | [01_Hardware/Подбор коммутатора и оптики.md](./01_Hardware/%D0%9F%D0%BE%D0%B4%D0%B1%D0%BE%D1%80%20%D0%BA%D0%BE%D0%BC%D0%BC%D1%83%D1%82%D0%B0%D1%82%D0%BE%D1%80%D0%B0%20%D0%B8%20%D0%BE%D0%BF%D1%82%D0%B8%D0%BA%D0%B8.md) |
| Планируется ли миграция ВМ с pve01 на pve02? | Нет: план отменён администратором 2026-10-28, миграция не выполнялась. Прежняя идея — оставить на pve01 только ВМ 1С ERP; причина жалоб на скорость 1С не подтверждена замерами (INFERRED). Документ сохранён как историческая запись. | [05_VirtualMachines/План миграции ВМ для изоляции 1С ERP.md](./05_VirtualMachines/%D0%9F%D0%BB%D0%B0%D0%BD%20%D0%BC%D0%B8%D0%B3%D1%80%D0%B0%D1%86%D0%B8%D0%B8%20%D0%92%D0%9C%20%D0%B4%D0%BB%D1%8F%20%D0%B8%D0%B7%D0%BE%D0%BB%D1%8F%D1%86%D0%B8%D0%B8%201%D0%A1%20ERP.md) |
| Включён ли автозапуск ВМ и LXC при перезагрузке pve01 и в каком порядке они стартуют? | Да, `onboot` включён у ВМ 2001–2003 и CT 600, 700. Порядок и открытые вопросы — в документе; перезагрузкой узла не проверялось. | [05_VirtualMachines/Автозапуск и порядок старта ВМ и LXC на pve01.md](./05_VirtualMachines/%D0%90%D0%B2%D1%82%D0%BE%D0%B7%D0%B0%D0%BF%D1%83%D1%81%D0%BA%20%D0%B8%20%D0%BF%D0%BE%D1%80%D1%8F%D0%B4%D0%BE%D0%BA%20%D1%81%D1%82%D0%B0%D1%80%D1%82%D0%B0%20%D0%92%D0%9C%20%D0%B8%20LXC%20%D0%BD%D0%B0%20pve01.md) |
| Почему в `qm config` у ВМ уже новый объём RAM, а в Windows прежний? | Перезагрузка из гостя не перезапускает процесс QEMU: новая `memory` применяется после полной остановки и запуска ВМ. Проверять `max_mem` в `info balloon`, а не только `qm config`. Hotplug памяти включать только при `numa: 1`: при `numa: 0` ВМ не загрузилась. | [06_Troubleshooting/Нехватка RAM на ВМ 2002 AD и увеличение до 8 ГБ.md](./06_Troubleshooting/%D0%9D%D0%B5%D1%85%D0%B2%D0%B0%D1%82%D0%BA%D0%B0%20RAM%20%D0%BD%D0%B0%20%D0%92%D0%9C%202002%20AD%20%D0%B8%20%D1%83%D0%B2%D0%B5%D0%BB%D0%B8%D1%87%D0%B5%D0%BD%D0%B8%D0%B5%20%D0%B4%D0%BE%208%20%D0%93%D0%91.md) |
| На контроллере домена пустой SYSVOL, не публикуются шары SYSVOL и NETLOGON, DFSR в State 2 — что проверять? | Сначала State DFSR на обоих контроллерах. Если у партнёра-источника State 5 и событие 4012 (offline дольше `MaxOfflineTimeInDays`), начальная синхронизация не завершится. Порядок: резервная копия SYSVOL и GPO, временно поднять лимит на источнике, перезапустить DFSR, дождаться State 4 на приёмнике, вернуть лимит на 60. D2/D4 не применять, пока источник в ошибке. Сбой питания причиной не был. | [06_Troubleshooting/Восстановление репликации SYSVOL DFSR на контроллерах домена.md](./06_Troubleshooting/%D0%92%D0%BE%D1%81%D1%81%D1%82%D0%B0%D0%BD%D0%BE%D0%B2%D0%BB%D0%B5%D0%BD%D0%B8%D0%B5%20%D1%80%D0%B5%D0%BF%D0%BB%D0%B8%D0%BA%D0%B0%D1%86%D0%B8%D0%B8%20SYSVOL%20DFSR%20%D0%BD%D0%B0%20%D0%BA%D0%BE%D0%BD%D1%82%D1%80%D0%BE%D0%BB%D0%BB%D0%B5%D1%80%D0%B0%D1%85%20%D0%B4%D0%BE%D0%BC%D0%B5%D0%BD%D0%B0.md) |
| Является ли ANDQ контроллером домена? | Нет: демотирован 2026-10-23, в домене два контроллера (`DC` и `AD`). Подробности — в разделе Active Directory env facts. | [AI-environment_facts-korona-proxmox.md](./AI-environment_facts-korona-proxmox.md) |

## Дерево решений

Дерево построено по категориям и документам из `00_Meta/registry.csv`.

### 1. Кворум и кластер Proxmox

```text
Проблема с quorum / split-brain / добавлением ноды?
  ├─ Да → читать 02_Installation/Создание кластера и QDevice.md
  ├─ Нужно добавить QDevice?
  │    └─ читать 02_Installation/Создание кластера и QDevice.md
  ├─ Нужно заменить QDevice на другой хост?
  │    └─ читать 02_Installation/Замена Corosync QDevice.md
  └─ Нужно понять Corosync?
       └─ читать 02_Installation/Создание кластера и QDevice.md
```

### 2. Физические линки, порты и коммутаторы

```text
Проблема с public_network, портами, скоростью линка или коммутаторами?
  ├─ Да → читать 03_Network/Физическая топология сети pve01-pve02.md
  ├─ Тормоза 1С или медленный клиентский трафик Ceph?
  │    └─ читать 06_Troubleshooting/1c-slow-public-network-2026-10-15.md
  ├─ Оптические модули / SFP не работают?
  │    └─ читать 06_Troubleshooting/Диагностика SFP-модулей Intel X710.md
  └─ Нужна настройка bond0 или cluster network?
       └─ читать 03_Network/Настройка bond0 active-backup для сети Ceph.md
```

### 3. Ceph

```text
Вопрос про Ceph?
  ├─ Архитектура, WAL/DB, связь с HA
  │    └─ 04_Storage_Ceph/Ceph теория WAL-DB разные диски и HA.md
  ├─ Подготовка дисков, создание OSD и пулов
  │    └─ 04_Storage_Ceph/Подготовка дисков и архитектура OSD.md
  │    └─ 04_Storage_Ceph/Развёртывание OSD и пулов Ceph.md
  ├─ Смена cluster_network, OSD не стартуют
  │    └─ 04_Storage_Ceph/2026-09-30_ceph_nic0_direct_link_migration_and_recovery.md
  └─ Задержки записи (исследование не завершено)
       └─ 06_Troubleshooting/Расследование задержек записи Ceph.md
```

### 4. ВМ и шаблоны Windows

```text
Вопрос про ВМ?
  ├─ Шаблон Windows Server 2022
  │    └─ 05_VirtualMachines/Шаблон Windows Server 2022.md
  ├─ Клонирование, диск, Recovery-раздел
  │    └─ 05_VirtualMachines/Клонирование ВМ под роль 1С-ERP.md
  ├─ Active Directory, третий DC
  │    └─ 05_VirtualMachines/Добавление третьего DC WIN-AD.md
  ├─ SYSVOL пустой или не публикуется, DFSR в State 2 или 5, событие 4012
  │    └─ 06_Troubleshooting/Восстановление репликации SYSVOL DFSR на контроллерах домена.md
  ├─ Терминальный сервер RDS
  │    └─ 05_VirtualMachines/Терминальный сервер RDS ВМ 2003.md
  ├─ USB-ключ HASP
  │    └─ 05_VirtualMachines/Проброс USB HASP в ВМ 2001.md
  ├─ Автозапуск и порядок старта
  │    └─ 05_VirtualMachines/Автозапуск и порядок старта ВМ и LXC на pve01.md
  ├─ Миграция и изоляция 1С (план отменён 2026-10-28, архивный документ)
  │    └─ 05_VirtualMachines/План миграции ВМ для изоляции 1С ERP.md
  ├─ Некорректный расход RAM, Guest Agent
  │    └─ 06_Troubleshooting/Некорректный расход RAM QEMU Guest Agent.md
  └─ Нехватка RAM на ВМ, новая memory не применяется
       └─ 06_Troubleshooting/Нехватка RAM на ВМ 2002 AD и увеличение до 8 ГБ.md
```

### 5. LXC, SSH, Vaultwarden

```text
Вопрос про LXC, SSH или парольный сервер?
  ├─ Создать Debian LXC-шаблон
  │    └─ 02_Installation/Шаблон Debian 12 LXC и клонирование.md
  ├─ SSH не работает
  │    └─ 06_Troubleshooting/Диагностика SSH-доступа к Debian.md
  ├─ SSH входит медленно в LXC
  │    └─ 06_Troubleshooting/Задержка SSH в LXC pam_systemd.md
  └─ Vaultwarden
       └─ документы в 07_Vaultwarden/ (см. таблицу «Документы»)
```

### 6. Мониторинг

```text
Вопрос про Zabbix?
  └─ документы в 08_Monitoring/Zabbix/ (см. таблицу «Документы»)
```
