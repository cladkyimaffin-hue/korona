---
# === БАЗОВАЯ ИНФОРМАЦИЯ ===
date_created: 2026-08-30
date_modified: 2026-09-05
author: cladkyimaffin-hue
status: "completed"
# === КОНТЕКСТ СИСТЕМЫ ===
target_system: "Proxmox VE 8.x/9.x Cluster (pve01: 192.168.202.121, pve02: 192.168.202.179 + QDevice: 192.168.202.251), Ceph, Huawei 2288H V5, LXC, Windows Server 2022"
environment: "production"
# === БЫСТРАЯ КЛАССИФИКАЦИЯ ===
category: "documentation"
severity: "info"
problem: |
  Необходимость структурированной документации по развертыванию, планированию и обслуживанию гиперконвергентного кластера Proxmox VE с Ceph, сетевой отказоустойчивостью (Bonding), обеспечением кворума через QDevice и стандартизацией развертывания LXC/Windows-шаблонов.
solution: |
  Создан комплексный набор Markdown-файлов с YAML-метаданными, описывающих аппаратную спецификацию, агрегацию каналов (LACP), планирование дисковой подсистемы Ceph (CRUSH Rules, Device Classes, PG), практическую установку OSD, создание шаблонов Debian 12 LXC и Windows Server 2022, и обеспечение кворума через QDevice.
root_cause: |
  Сложность архитектуры гиперконвергентного кластера требует четкой фиксации решений (отказ от локального RAID для дисков данных, использование LACP для 10G сетей, разделение разнородных дисков по CRUSH Rules, DAC-кабели вместо оптики, стандартизация LXC/Windows-шаблонов).
# === AI-СПЕЦИФИЧНЫЕ ПОЛЯ ===
ai_summary: |
  Папка содержит полную документацию по кластеру Proxmox VE на базе серверов Huawei 2288H V5. Включает спецификации железа, маппинг портов Intel X722/X710, настройку LACP-бондинга, планирование дисков Ceph (CRUSH Rules, Device Classes, PG), практическую установку OSD на pve01/pve02, создание шаблонов Debian 12 LXC и Windows Server 2022 (с VirtIO, QEMU Guest Agent, UEFI+TPM, Sysprep), инструкции по развертыванию Ceph, обеспечение кворума через QDevice на третьем хосте и пост-установочные скрипты.
key_takeaways:
  - "Для 7 ТБ дисков не используется локальный RAID1, каждый диск создается как отдельный OSD в Ceph."
  - "Разнородные диски (4 ТБ и 7 ТБ) требуют отдельных Device Classes и CRUSH Rules для предотвращения эффекта «деревянной бочки»."
  - "Сеть 10G для Ceph и VM агрегируется через bond0 (mode 4 / 802.3ad LACP) для отказоустойчивости."
  - "Кластер из 2 нод с данными критически требует QDevice на независимом третьем хосте для предотвращения split-brain."
  - "Шаблон LXC создается только из остановленного и очищенного контейнера; для экономии места при клонировании используется Linked Clone."
  - "Windows Server 2022 требует: Machine=q35, BIOS=OVMF, VirtIO SCSI, TPM v2.0, QEMU Guest Agent и финальный Sysprep перед шаблоном."
dont_repeat:
  - "Не предлагать использование оптических модулей 10GBASE-T (RJ45) в SFP+ портах Intel X722."
  - "Не предлагать создание локального зеркала (RAID1/ZFS mirror) из дисков данных."
  - "Не предлагать размещение полноценного Ceph Monitor на хосте QDevice."
  - "Не предлагать команду `pvecm add qdevice <IP>` (устарела), использовать `pvecm qdevice setup <IP>`."
  - "Не назначать IP-адреса на физические интерфейсы-слэйвы при настройке bond0."
  - "Не использовать один общий пул Ceph для дисков разного объема без CRUSH Rules."
  - "Не выносить WAL/DB на NVMe, если основные диски — SSD."
  - "Не предлагать `ceph-deploy` — в Proxmox VE 8.x/9.x используется `cephadm` orchestrator."
  - "Не создавать шаблон LXC из работающего контейнера или забывать менять hostname/IP после клонирования."
  - "Не использовать IDE/SATA для дисков Windows-ВМ — только VirtIO SCSI с подключенным virtio-win.iso."
  - "Не создавать шаблон Windows без выполнения Sysprep — это приведет к дублированию SID."
  - "Не использовать machine type i440fx для новых Windows-ВМ — только q35 с UEFI."
assumptions:
  - "Серверы Huawei 2288H V5 работают в режиме HBA/JBOD для дисков данных."
  - "Коммутаторы поддерживают агрегацию каналов (LACP) и транкинг VLAN."
  - "Диски 7 ТБ видны в системе как /dev/sdX и не имеют активных LVM/ZFS подписей."
  - "ISO-образы Windows Server 2022 и virtio-win.iso загружены в хранилище Proxmox."
# === АРТЕФАКТЫ ===
commands: |
  # Проверка статуса кворума и QDevice
  pvecm status
  # Проверка здоровья Ceph
  ceph health
  ceph -s
  # Проверка дерева OSD
  ceph osd tree
  # Проверка статуса бондинга
  cat /proc/net/bonding/bond0
  # Применение настроек сети
  ifreload -a
  # Расчет PG и autoscale
  ceph osd pool autoscale-status
  # Очистка диска перед созданием OSD
  wipefs -a /dev/sdX
  # Создание OSD
  pveceph osd create /dev/sdX
  # Назначение Device Class
  ceph osd crush set-device-class ssd-7tb osd.0 osd.1
  # Управление LXC шаблонами
  pveam download local debian-12-standard_12.6-1_amd64.tar.zst
  pct set <vmid> -template 1
  # Создание Windows ВМ с VirtIO и TPM
  qm create 200 --name ws2022-template --machine q35 --bios ovmf \
    --scsihw virtio-scsi-single --tpmstate0 ceph-vm:version=v2.0 \
    --agent enabled=1
  # Конвертация ВМ в шаблон
  qm template 200
  # Клонирование шаблона
  qm clone 200 201 --full
config_snippets:
  ceph_pool_config: |
    Size: 2 (для 2 нод с данными)
    Min Size: 1
    Autoscale: on
  bond_config_snippet: |
    auto bond0
    iface bond0 inet static
        bond-slaves eno1 eno2
        bond-mode 802.3ad
        bond-miimon 100
  crush_rule_example: |
    ceph osd crush rule create-replicated rule-7tb default host ssd-7tb
    ceph osd pool create ceph-vm-bulk 128 128 replicated rule-7tb
  lxc_features: |
    features: nesting=1,keyctl=1
  windows_vm_hardware: |
    BIOS: OVMF (UEFI)
    Machine: q35
    CPU: host
    SCSI Controller: VirtIO SCSI Single
    Disk: SCSI, iothread=1, discard=on, ssd=1
    Network: VirtIO (paravirtualized)
    TPM: v2.0 (swtpm)
    QEMU Agent: enabled=1
urls:
  - "https://github.com/cladkyimaffin-hue/korona/tree/7e61d0c471c64f881b35a5f2d02881fd6535af07/Proxmox"
  - "https://pve.proxmox.com/wiki/Ceph_Server"
  - "https://pve.proxmox.com/wiki/Linux_Container"
  - "https://pve.proxmox.com/wiki/Windows_Virtual_Machines"
# === СВЯЗИ ===
related_files:
  - "hardware-spec.md"
  - "pve01+pve02+Qdevice.md"
  - "Создание Ceph №1.md"
  - "Настройка Ceph Планирование Дисков OSD.md"
  - "Установка Ceph OSD НА на pve02 pve01.md"
  - "Proxmox установка Debian 12 LXC создание шаблона развертывание из шаблона.md"
  - "Настройка ВМ Windows Server 2022 шаблона.md"
  - "Настройка сети bond0.md"
  - "Установка Proxmox VE на 3 сервера (зеркало 2×480 ГБ + 2×7 ТБ), создание кластера, настройка Ceph, распределение сетей, рекомендации по дискам и сети.md"
depends_on: []
superseded_by: ""
tags:
  - "ProxmoxVE"
  - "Ceph"
  - "QDevice"
  - "Huawei-2288H-V5"
  - "Networking"
  - "HighAvailability"
  - "OSD"
  - "CRUSH"
  - "LXC"
  - "WindowsServer2022"
  - "VirtIO"
# === ВРЕМЕННОЙ КОНТЕКСТ ===
last_incident: 2026-09-05
next_review: 2026-12-01
valid_until: 2027-01-01
# === ОТВЕТСТВЕННОСТЬ ===
reviewer: "cladkyimaffin-hue"
approval_status: "approved"
---
# Индекс папки: Proxmox (Кластер, Ceph, Сеть, LXC и Windows)

**Описание:** Документация, логи и пошаговые инструкции по развертыванию и обслуживанию кластера Proxmox VE на базе серверов Huawei 2288H V5. Охватывает аппаратную спецификацию, агрегацию сетевых каналов (LACP), планирование дисковой подсистемы Ceph (CRUSH Rules, Device Classes, PG), практическую установку OSD на pve01/pve02, создание и развертывание шаблонов Debian 12 LXC и Windows Server 2022 (с VirtIO, UEFI+TPM, QEMU Guest Agent, Sysprep), настройку гиперконвергентного хранилища Ceph, обеспечение кворума через QDevice, пост-установочную автоматизацию и конфигурацию HA/SDN.

---
## ⚡ Quick Answers (Быстрые ответы)
> **Как ИИ использует эту секцию:** При получении типичного вопроса ИИ мгновенно находит ответ здесь, не читая полные файлы. Это экономит токены и ускоряет ответ.
| Вопрос | Краткий ответ | Файл |
|--------|---------------|------|
| Как подключить 10G без оптики? | Использовать пассивные DAC-кабели (SFP+ to SFP+), модули 10GBASE-T не подходят для Intel X722. | [Полная комплектация сервера...](./Полная%20комплектация%20сервера,%20идентификация%20сетевых%20карт,%20расположение%20портов%20и%20рекомендации%20по%20установке%20Proxmox%20без%20оптики.md) |
| Как настроить отказоустойчивую сеть 10G? | Использовать bonding (mode 4 / 802.3ad LACP) в `/etc/network/interfaces` с настройкой агрегации на коммутаторе. | [Настройка сети bond0.md](./Настройка%20сети%20bond0.md) |
| Зачем нужен QDevice и как добавить? | Обеспечивает третий голос для кворума. Добавляется командой `pvecm qdevice setup <IP>` на независимом хосте. | [Добавить qdevice.md](./Добавить%20qdevice.md) |
| Как настроить диски 2x480 ГБ и 2x7 ТБ? | 480 ГБ в зеркало под ОС, 7 ТБ диски добавляются как отдельные независимые OSD в Ceph (без локального RAID). | [Установка Proxmox VE на 3 сервера...](./Установка%20Proxmox%20VE%20на%203%20сервера%20(зеркало%202×480%20ГБ%20+%202×7%20ТБ),%20создание%20кластера,%20настройка%20Ceph,%20распределение%20сетей,%20рекомендации%20по%20дискам%20и%20сети.md) |
| Как планировать OSD для разнородных дисков (4 ТБ и 7 ТБ)? | Создавать отдельные Device Classes и CRUSH Rules для каждого типа дисков, чтобы избежать эффекта «деревянной бочки». | [Настройка Ceph Планирование Дисков OSD.md](./Настройка%20Ceph%20Планирование%20Дисков%20OSD.md) |
| Как установить OSD на pve01 и pve02? | Очистить диск `wipefs -a /dev/sdX`, создать OSD через `pveceph osd create /dev/sdX`, назначить Device Class, дождаться `active+clean`. | [Установка Ceph OSD НА на pve02 pve01.md](./Установка%20Ceph%20OSD%20НА%20на%20pve02%20pve01.md) |
| Как создать и развернуть шаблон Debian 12 LXC? | Очистить контейнер (`apt clean`), остановить (`pct stop`), конвертировать (`pct set <vmid> -template 1`), клонировать через GUI или `pct clone`. | [Proxmox установка Debian 12 LXC создание шаблона развертывание из шаблона.md](./Proxmox%20установка%20Debian%2012%20LXC%20создание%20шаблона%20развертывание%20из%20шаблона.md) |
| Как создать шаблон Windows Server 2022? | Создать ВМ с q35+OVMF+VirtIO SCSI+TPM v2.0, установить VirtIO-драйверы и QEMU Guest Agent, оптимизировать ОС, выполнить `sysprep /generalize /oobe /shutdown`, конвертировать через `qm template`. | [Настройка ВМ Windows Server 2022 шаблона.md](./Настройка%20ВМ%20Windows%20Server%202022%20шаблона.md) |
| Как рассчитать количество PG для пула? | Формула: `PG = (OSD_count × 100) / replica_count`, округление до ближайшей степени двойки. Или использовать autoscale. | [Настройка Ceph Планирование Дисков OSD.md](./Настройка%20Ceph%20Планирование%20Дисков%20OSD.md) |
| Объединяется ли RAM в Ceph? | Нет, Ceph объединяет только дисковое пространство. RAM остается локальной для каждой ноды. | [Установка Proxmox VE на 3 сервера...](./Установка%20Proxmox%20VE%20на%203%20сервера%20(зеркало%202×480%20ГБ%20+%202×7%20ТБ),%20создание%20кластера,%20настройка%20Ceph,%20распределение%20сетей,%20рекомендации%20по%20дискам%20и%20сети.md) |
| Не работает SSH после установки? | Проверить `PermitRootLogin prohibit-password` в `sshd_config` и права `700` на `~/.ssh`. | [Проблемы с доступом по SSH на Debian.md](./Проблемы%20с%20доступом%20по%20SSH%20на%20Debian.md) |
---
## 🌳 Decision Tree (Дерево решений)
> **Как ИИ использует эту секцию:** При диагностике проблемы ИИ следует по дереву, чтобы найти нужный файл и порядок действий. Это структурирует процесс поиска решения.

- **Нужна отказоустойчивость или агрегация каналов 10G?** 
  → Настрой LACP (mode 4) на Proxmox и коммутаторе → Смотри [Настройка сети bond0.md](./Настройка%20сети%20bond0.md).
- **Проблема с кворумом кластера или split-brain?** 
  → Проверь статус `pvecm status` → Если QDevice отсутствует или offline, следуй инструкциям в [Добавить qdevice.md](./Добавить%20qdevice.md) или [pve01+pve02+Qdevice.md](./pve01+pve02+Qdevice.md).
- **Нужно спланировать OSD для дисков разного объема?** 
  → Раздели диски по Device Classes → Создай CRUSH Rules → Смотри [Настройка Ceph Планирование Дисков OSD.md](./Настройка%20Ceph%20Планирование%20Дисков%20OSD.md).
- **Нужно физически установить OSD на нодах?** 
  → Очисти диски `wipefs` → Создай OSD через `pveceph osd create` → Назначь Device Class → Смотри [Установка Ceph OSD НА на pve02 pve01.md](./Установка%20Ceph%20OSD%20НА%20на%20pve02%20pve01.md).
- **Нужно быстро развернуть стандартизированный Linux-контейнер?** 
  → Загрузи образ через `pveam` → Настрой и очисти базовый LXC → Конвертируй в шаблон → Клонируй → Смотри [Proxmox установка Debian 12 LXC создание шаблона развертывание из шаблона.md](./Proxmox%20установка%20Debian%2012%20LXC%20создание%20шаблона%20развертывание%20из%20шаблона.md).
- **Нужно развернуть новую Windows Server 2022 ВМ?** 
  → Используй шаблон WS2022 (q35+OVMF+VirtIO+TPM+Guest Agent) → Клонируй через `qm clone` → Смотри [Настройка ВМ Windows Server 2022 шаблона.md](./Настройка%20ВМ%20Windows%20Server%202022%20шаблона.md).
- **Нужно добавить новый диск в Ceph или пул перешел в `HEALTH_WARN`?** 
  → Убедись, что контроллер в режиме HBA/JBOD → Проверь утилизацию OSD → Следуй шагам в [Создание Ceph №1.md](./Создание%20Ceph%20№1.md) или [Установка Proxmox VE на 3 сервера...](./Установка%20Proxmox%20VE%20на%203%20сервера%20(зеркало%202×480%20ГБ%20+%202×7%20ТБ),%20создание%20кластера,%20настройка%20Ceph,%20распределение%20сетей,%20рекомендации%20по%20дискам%20и%20сети.md).
- **Не работает сеть 10G или не определяются порты?** 
  → Проверь тип кабеля (DAC, а не 10GBASE-T) и маппинг портов LOM/SLOT → Смотри [Полная комплектация сервера...](./Полная%20комплектация%20сервера,%20идентификация%20сетевых%20карт,%20расположение%20портов%20и%20рекомендации%20по%20установке%20Proxmox%20без%20оптики.md) или [Железа серверов подборка коммутаторов.md](./Железа%20серверов%20подборка%20коммутаторов.md).
- **Нужно настроить отказоустойчивость ВМ (HA) или сети (SDN)?** 
  → Убедись, что диски ВМ лежат на Ceph → Настрой HA-группы и SDN через [web меню.md](./web%20меню.md).
- **Сервер только что установлен, с чего начать?** 
  → Запусти [Скрипт pstInstal после установки Proxmox.md](./Скрипт%20pstInstal%20после%20установки%20Proxmox.md), затем [Поменять имя устройства на pve01.md](./Поменять%20имя%20устройства%20на%20pve01.md).
