---
document_id: "PROXMOX-WEBGUI-DATACENTER-2026-001"
title: "Справочник по меню Datacenter в веб-интерфейсе Proxmox VE: общие пункты, HA, SDN"
document_type: "reference"
status: "completed"
priority: "info"
date_created: 2026-08-30
date_modified: 2026-09-11
next_review: 2026-12-01
author: "cladkyimaffin-hue"
category: "03_Network"
tags:
  - "ProxmoxVE"
  - "WebGUI"
  - "HA"
  - "SDN"
ai_summary: "Разбор пунктов меню Datacenter в веб-интерфейсе Proxmox VE (Search, Summary, Cluster, Ceph, Storage, Backup, Replication, Permissions/RBAC), подробно — HA (Groups, Fencing) и SDN (Zones, VNets, IPAM, Options), с примерами команд под кластер pve01+pve02+QDevice."
dont_repeat:
  - "Не предлагать самоподписанные сертификаты для production без предупреждения о рисках."
  - "Не предлагать EVPN-зону SDN для двух нод — VLAN-зона проще и надёжнее для этой конфигурации."
related_files:
  - "TBD: Создание Ceph №1.md (ещё не мигрирован)"
schema_version: "1.0"
---

# Справочник по меню Datacenter в веб-интерфейсе Proxmox VE

## Назначение
Общий разбор структуры меню **Datacenter** в веб-интерфейсе Proxmox VE 8.2.2,
и подробный разбор двух конкретных разделов — **HA** и **SDN** — под
реальную конфигурацию кластера (2 узла `pve01`+`pve02` + внешний Corosync
QDevice `Qdevice.krnn.ru`, `192.168.202.251` — подтверждено в
`AI-environment_facts-korona-proxmox.md`).

## Общие пункты меню Datacenter

| Пункт | Назначение |
|---|---|
| Search | Поиск по узлам, VM, CT, хранилищам, пулам — по имени и ID |
| Summary | Сводка: версия PVE, состав и состояние узлов |
| Notes | Свободные заметки администратора, видны всем с доступом к датацентру |
| Cluster | Создание кластера, join information, состояние quorum |
| Ceph | Управление Ceph из GUI: статус, установка пакетов, OSD/MON/MGR, пулы, CRUSH |
| Options | Общие параметры: клавиатура консолей, язык, bwlimit, тип консоли по умолчанию, MAC-префикс, max_workers |
| Storage | Хранилища на уровне датацентра: Directory, NFS, CIFS, iSCSI, LVM/LVM-Thin, ZFS over iSCSI, Ceph RBD/CephFS, PBS |
| Backup | Плановые vzdump-задания: режим (snapshot/suspend/stop), расписание, retention |
| Replication | Плановая репликация дисков VM на другой узел (в первую очередь для ZFS) |

### Ветка Permissions (RBAC)

| Пункт | Назначение |
|---|---|
| Users | Учётные записи; realm'ы `pve`, `pam`, а также LDAP/AD/OpenID после настройки |
| API Tokens | Токены для доступа к API от имени пользователя, свои права и срок действия |
| Two Factor | TOTP, WebAuthn (FIDO2/U2F), recovery-ключи; обязательность 2FA на уровне датацентра/realm'а |
| Groups | Группы пользователей — права выдаются группе, не каждому пользователю |
| Pools | Логическая группировка объектов (VM/CT/хранилища) для выдачи прав пакетом |
| Roles | Наборы привилегий: `Administrator`, `PVEAuditor`, `PVEVMAdmin`, `PVEVMUser`, `PVEDatastoreAdmin/User`, `PVESysAdmin`, `NoAccess` и др.; можно создавать свои |

## HA (Datacenter → HA)

HA-стек (`pve-ha-manager`) следит за помеченными ресурсами (VM/CT) и
перезапускает их на другом узле при падении исходного. Требует **quorum**
в corosync-кластере — для схемы «2 узла» это означает обязательный
**QDevice**.

Панель **Status** — список HA-ресурсов, их состояние, узел, состояние
HA-менеджеров, quorum.

### Groups
HA-группа — набор узлов с приоритетами и флагом `restricted`.

```bash
ha-manager groupadd grp-main pve01,pve02 --priority 1,2 --restricted 0
```
`--priority 1,2` — предпочтительный узел `pve01`, запасной `pve02`;
`--restricted 0` — ресурс предпочитает группу, но не заперт в ней.

С `restricted 1` ресурс работает только на указанном узле и не поднимется
на другом при его падении — применяется, когда VM привязана к локальным
ресурсам узла.

```bash
ha-manager add vm:100 --state started --group grp-main
```

⚠️ Failover реально сработает, только если диски VM доступны на втором
узле — общее хранилище (в этом кластере — **Ceph**, пулы `ceph-fast`/
`ceph-bulk`) либо репликация дисков.

### Fencing
Механизм изоляции «умершего» узла (защита от split-brain) — в Proxmox VE
через **watchdog**.

```bash
wdctl
```
Пример вывода для аппаратного watchdog: `Device: /dev/watchdog`,
`Identity: iTCO_wdt`, `Timeout: 10 seconds`. Если не настроен —
`modprobe iTCO_wdt` + запись в `/etc/modules` (программный fallback —
`softdog`, для production рекомендуется аппаратный).

### Почему оба элемента критичны для «2 узла + QDevice»
- **QDevice даёт quorum**: голоса `pve01` (1) + `pve02` (1) + QDevice (1) = 3, quorum ≥ 2. При потере одного узла оставшийся сохраняет quorum → HA может действовать. Без QDevice потеря одного из двух узлов = потеря quorum = HA парализован.
- **Fencing (watchdog)** даёт гарантию, что «пропавший» узел не продолжает работать с теми же VM параллельно.

## SDN (Datacenter → SDN)

Слой абстракции над сетями: описываются «зоны» и «виртуальные сети»
(vnet), Proxmox создаёт нужные интерфейсы на узлах после `pvesdn apply`.
Конфигурация — в `/etc/pve/sdn/` (`zones.cfg`, `vnets.cfg`, `ipam.cfg`,
`controllers.cfg`, `dns.cfg`).

### Zones

| Тип | Суть | Когда применять |
|---|---|---|
| `simple` | Обычный Linux-bridge на узле, без тегов | Локальные сети узла |
| `vlan` | VLAN-aware bridge, VNets получают VLAN-теги, L2 тянется между узлами если свич транкует VLAN | Классическая VLAN-сегментация |
| `evpn` | VXLAN + EVPN (BGP control plane), L2 растягивается без multicast, нужен controller и VRF | Растянутые L2 без VLAN на свиче |

Для конфигурации из двух узлов типовой сценарий — `vlan`-зона:
```bash
pvesdn create zone vlan vz-vlan --bridge vmbr0
```
Условие: `vmbr0` должен быть vlan-aware, порт свича — trunk с нужными VLAN.

### VNets
Виртуальный L2-сегмент внутри зоны — к нему подключается NIC VM/CT
(`bridge=vnetXXX` в конфиге VM).

```bash
pvesdn create vnet prod --zone vz-vlan --tag 10 --alias production
pvesdn apply
```
`pvesdn apply` (или кнопка Apply в GUI) обязателен — без него интерфейсы
на узлах не создаются.

### IPAM
Управление IP-адресацией подсетей vnet. Бэкенды: `pve` (встроенный, без
внешней настройки), `phpIPAM`, `Netbox` (внешние, по URL + токен).

### Options
Глобальные параметры подсистемы SDN. Точный набор полей версиозависим —
сверяться с актуальной вкладкой в GUI.

## Связанные документы
- «Создание Ceph №1.md» — используется как shared storage для HA failover (ещё не мигрирован)

---
*Примечание при миграции (2026-09-11): убрана нумерация «Шаг 1/2/3» и
диалоговая рамка USER/ASSISTANT, содержание сведено в единый справочник.
Плейсхолдеры узлов `pve1`/`pve2` из исходного текста заменены на
подтверждённые реальные имена `pve01`/`pve02` (см.
`AI-environment_facts-korona-proxmox.md`) — это не изменение факта, а
подстановка уже известного значения вместо условного примера. Открытый
в исходнике вопрос «это corosync qdevice на третьей машине?» — да,
подтверждено: `Qdevice.krnn.ru`, `192.168.202.251`, тот же источник.*
