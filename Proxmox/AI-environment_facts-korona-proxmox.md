### ASSISTANT
Вот пересобранный и актуализированный файл `AI-environment_facts-korona-proxmox.md` на основе изучения всех новых данных из директории `Proxmox` репозитория `cladkyimaffin-hue/korona` (commit `20ea62a25ec90acdc0661180b4d7a6761de224dd`). 

В документ добавлены подтверждённые факты о ВМ 2001 (1С), ВМ 2003 (Терминальный сервер), LXC-шаблонах, уточнения по Ceph и новые типичные ошибки ИИ, зафиксированные в логах.

```markdown
# environment_facts — извлечено из репозитория korona/Proxmox

**Источник:** https://github.com/cladkyimaffin-hue/korona/tree/20ea62a25ec90acdc0661180b4d7a6761de224dd/Proxmox  
**Дата анализа:** 2026-09-11  
**Статус:** Все значения ниже подтверждены текстом файлов репозитория (INDEX.md, runbook-и, логи). Там, где данные противоречивы, неполны или помечены как «уточнить» — указано явно, чтобы ИИ не выдавал их как факт.

```yaml
environment_facts:

  proxmox:
    version: "Proxmox VE 9.2.9"                       # подтверждено в pve01+pve02+Qdevice.md и INDEX.md
    cluster_name: "krnn"
    nodes:
      - name: pve01
        mgmt_ip: "192.168.202.121/22"
        ceph_cluster_ip: "10.10.10.1/24 (bond0)"
      - name: pve02
        mgmt_ip: "192.168.202.179/22"
        ceph_cluster_ip: "10.10.10.2/24 (bond0)"
    cluster_topology: "2 полноценных узла (pve01, pve02) + внешний Corosync QDevice. НЕ трёхнодовый кластер (третий сервер Huawei есть в наличии, но в кластер не введён)."
    qdevice:
      hostname: "Qdevice.krnn.ru"
      ip: "192.168.202.251"
      os: "Debian GNU/Linux 13 (trixie)"
      setup_command_note: "В PVE 9.2 используется `pvecm qdevice setup 192.168.202.251`. Команда `pvecm add qdevice ...` НЕ работает (ошибка 400 too many arguments) — не предлагать её."
    hardware:
      server_model: "Huawei FusionServer 2288H V5 (3 одинаковых сервера в наличии, активно используются 2)"
      system_disks: "2× 480 GB SSD (зеркало под ОС Proxmox, storage local-lvm)"
      per_node_data_disks_actual: "1× NVMe ~3.5/3.84 ТБ (для ceph-fast) + 1× SSD ~7/7.68 ТБ (для ceph-bulk). Фактическая конфигурация подтверждена в 'Установка Ceph OSD НА на pve02 pve01.md' и 'INDEX.md'. Ранние упоминания 'HDD 7 ТБ' устарели."
      cpu_ram_per_node: "НЕ подтверждено на уровне хоста (в hardware-spec.md помечено как [УТОЧНИТЬ]). Известно только, что ресурсы выделяются динамически (например, ВМ 2001 имеет 24 vCPU / 160 GiB RAM)."
      network_cards: "Intel X722 (LOM, 2×10GbE SFP+ + 2×1GbE RJ45), Intel X710 (PCIe SLOT3, 2×10GbE SFP+)"
      transceivers: "Intel FTLX8571D3BCVIT1 (10GBASE-SR, оптические модули LC, НЕ RJ45)"

  network:
    management_subnet: "192.168.200.0/22 (охватывает диапазон .200.x–.203.x)"
    management_gateway: "192.168.200.1"
    ceph_cluster_network:
      subnet: "10.10.10.0/24"
      interface: "bond0"
      bond_mode: "active-backup (mode 1) — НЕ LACP/802.3ad. Реализован active-backup, т.к. не требует настройки коммутатора."
      slaves: "nic4 + nic5 (имена интерфейсов могут отличаться, проверять через `ip addr` перед конфигурацией)"
    proxmox_web_ui_bridge: "vmbr0 (управление/VM-трафик, привязан к nic2 на pve01)"
    known_ip_reservations:
      "192.168.200.1": "gateway"
      "192.168.200.2": "DC.krnn.ru"
      "192.168.200.10": "ANDQ.krnn.ru"
      "192.168.200.225": "AD.krnn.ru (бывш. WIN-AD, также сервер лицензирования RDS)"
      "192.168.202.121": "pve01"
      "192.168.202.179": "pve02"
      "192.168.202.251": "Qdevice.krnn.ru"
      "192.168.203.93": "zabbix (LXC, финальный ID уточняется, ранее фигурировал как 201 или 700)"

  storage:
    pools:
      - name: "local-lvm"
        type: "LVM-thin, локальный"
        purpose: "ISO-образы, системные разделы узлов. НЕ использовать для production-дисков ВМ/CT по умолчанию."
      - name: "ceph-fast"
        backing_disks: "NVMe (device class: nvme)"
        crush_rule: "nvme-replicated"
        size_min_size: "Size=2, Min.Size=1"
        pg: 128
        purpose: "Критичные к задержкам workloads: 1С, терминальный сервер, Active Directory, БД. Используется как storage ПО УМОЛЧАНИЮ для production ВМ/CT и шаблонов."
      - name: "ceph-bulk"
        backing_disks: "SSD 7/7.68 ТБ (device class: ssd)"
        crush_rule: "ssd-replicated"
        size_min_size: "Size=2, Min.Size=1"
        pg: 128
        purpose: "Бэкапы, архивы, менее критичные ВМ. Не использовать для активных БД."
    clone_policy: "Proxmox по умолчанию создаёт LINKED clone (зависимый от базового диска шаблона). Чтобы получить независимый клон — ВСЕГДА добавлять флаг `--full` к `pct clone` / `qm clone`."
    known_gotchas:
      - "pct create для LXC использует `--rootfs <storage>:<size>`, НЕ `--disk` (--disk для LXC не существует и вызывает ошибку)."
      - "pct clone НЕ поддерживает параметр `--net0` — сетевые настройки задаются отдельно через `pct set` после клонирования."
      - "qm resize НЕ поддерживает параметр `--storage`. Правильный синтаксис: `qm resize <vmid> <disk> +<size>` (например, `qm resize 2001 scsi0 +924G`)."
      - "В Proxmox нет команды для изменения ID существующего контейнера/ВМ напрямую. Единственный штатный способ — vzdump + restore с новым ID."

  vm_ct_numbering_convention:
    templates:
      - id: 1000
        name: "debian12-pattern" (пользователь пытался переименовать в "debian12-template" через `pct set 1000 --name debian12-template`)
        type: "LXC"
        storage: "ceph-fast"
        note: "Это LXC-контейнер, управляется через `pct`, а не `qm`."
      - id: 2000
        name: "win2022-template"
        type: "QEMU/KVM"
        storage: "ceph-fast"
        specs: "q35, BIOS=OVMF(UEFI), CPU=host, SCSI=VirtIO SCSI Single, Network=VirtIO, TPM v2.0 (swtpm), диск ~100 ГБ, прошёл Sysprep /generalize перед конвертацией в шаблон."
    known_working_instances:
      - id: 2001
        name: "win-1c-app-01"
        role: "сервер приложений 1С:ERP"
        source_template: 2000
        clone_type: "Full Clone (--full)"
        storage: "ceph-fast"
        resources: "24 vCPU (1 socket × 24 cores), 163840 MiB (160 GiB) RAM, диск увеличен со 100 ГБ до 1 ТБ через `qm resize 2001 scsi0 +924G`"
      - id: 2003
        name: "TC" (FQDN: TC.KRNN.RU)
        role: "терминальный сервер RDS (Remote Desktop Services)"
        source_template: 2000
        clone_type: "Full Clone"
        resources: "4 vCPU, 48.15 GiB RAM, 500 GiB диск"
        rds_status: "RDS Session Host и Connection Broker настроены. Коллекция 'Terminal'. Роль RDS Licensing установлена на AD.krnn.ru, но RDS CAL НЕ приобретены. Сервер работает в 120-дневном льготном периоде (grace period)."
      - id: 700 (или 201 в ранних логах)
        name: "zabbix-lxc"
        type: "LXC"
        role: "мониторинг (Zabbix)"
        source_template: 1000
        resources: "2 CPU, 4096 MiB RAM, 100 GiB rootfs на ceph-fast"
    convention_summary: "Шаблоны — круглые номера (1000 для LXC, 2000 для Windows-ВМ). Рабочие Windows-машины — в диапазоне 2001–2003+. Рабочие LXC — произвольные ID. Перед работой с конкретным ID всегда выполняй `pct list` / `qm list` для сверки."

  active_directory:
    domain_fqdn: "krnn.ru"
    netbios: "KRNN"
    os_locale: "ru-RU — группы AD называются на русском (например, «Пользователи домена», а не «Domain Users»). Проверять точное имя через `whoami /user` и `net group` перед использованием в командах."
    domain_controllers:
      - hostname: "ANDQ.krnn.ru"
        ip: "192.168.200.10"
      - hostname: "DC.krnn.ru"
        ip: "192.168.200.2"
      - hostname: "AD.krnn.ru"
        ip: "192.168.200.225"
        note: "Ранее назывался WIN-AD. На нём размещена роль RDS Licensing. Активирован, но клиентские лицензии (RDS CAL) пока не установлены."
    rds_terminal_server:
      hostname: "TC.KRNN.RU (VM 2003)"
      collection_name: "Terminal"
      access_group: "Локальная группа 'Remote Desktop Users' содержит доменную группу 'KRNN\\Пользователи домена'."
      licensing_mode_registry_value: 4  # Per User
      licensing_server: "AD.krnn.ru"
      status: "RDS CAL не приобретены — сервер работает в льготном 120-дневном периоде. НЕ считать лицензирование завершённым."

  common_ai_mistakes_already_seen_in_this_repo:
    - "Использование короткого имени сервера (`$env:COMPUTERNAME`) вместо FQDN в `New-RDSessionDeployment` — требуется полное доменное имя (TC.KRNN.RU)."
    - "Придуманный несуществующий cmdlet `Grant-RDAccess`."
    - "Придуманный параметр `-UserGroups` для `Set-RDSessionCollectionConfiguration` (такого параметра нет)."
    - "Вызов `Get-ADDomain`/`Get-ADGroup` на рядовом сервере (TC) без установленного модуля ActiveDirectory PowerShell."
    - "Использование `lsmgr.exe` — устарело (Windows Server 2008 R2), в Windows Server 2022 не существует."
    - "Использование `--disk` вместо `--rootfs` в `pct create` для LXC."
    - "Использование `pct clone` или `qm clone` без флага `--full` там, где нужен независимый клон (по умолчанию создаётся linked clone, который блокирует удаление исходного шаблона)."
    - "Использование `qm resize` с параметром `--storage` (этот параметр не поддерживается, правильный синтаксис: `qm resize <vmid> <disk> +<size>`)."
    - "Указание `local-lvm` как storage по умолчанию для production ВМ/CT — в этой инфраструктуре production по умолчанию размещается на `ceph-fast`."
```

## Как этим пользоваться

1. **Вставляй актуальный блок `environment_facts`** в начало любой новой рабочей сессии по этой инфраструктуре — до того, как просить у ИИ конкретные команды.
2. **Перед каждой командой**, трогающей storage, сеть, ID или AD-группы, сверяйся именно с этими значениями, а не с общими знаниями о Proxmox/Windows Server по умолчанию.
3. **Строго соблюдай правило одного шага**: предлагай только одну маленькую команду за раз, жди подтверждения пользователя («ок», «готово» или вывод команды) и веди обновлённый «Протокол» в конце каждого ответа.

### ⚠️ Не подтверждено репозиторием (НЕ считать фактом, спрашивать/проверять):
- Точная модель и количество CPU, объём и тип RAM физических хостов pve01/pve02 (в `hardware-spec.md` помечено «[УТОЧНИТЬ]»).
- Финальная модель закупленного коммутатора (требуется минимум 4× 10G SFP+ порта).
- Режим работы дискового контроллера (критично подтверждение режима HBA/JBOD/IT для Ceph).
- Актуальный полный список ВСЕХ ID контейнеров/ВМ — нумерация в истории репозитория несколько раз менялась (например, Zabbix фигурировал как 201 и 700). Перед работой с конкретным ID всегда выполняй `pct list` / `qm list`.
- Дата окончания 120-дневного льготного периода RDS на сервере TC.

---

### Основные изменения по сравнению с предыдущей версией:
1. **Уточнена версия Proxmox**: 9.2.9 (вместо общей 9.2).
2. **Добавлены факты о ВМ 2001 (1С)**: полный клон, 24 vCPU, 160 GiB RAM, диск расширен до 1 ТБ через `qm resize` (без `--storage`).
3. **Добавлены факты о ВМ 2003 (ТС)**: 4 vCPU, ~48 GiB RAM, 500 GiB диск. RDS Licensing на AD.krnn.ru, но CAL не куплены (grace period).
4. **Уточнён LXC шаблон 1000**: это именно LXC (`pct`), а не QEMU (`qm`). Пользователь пытался переименовать его в `debian12-template`.
5. **Добавлена новая ошибка ИИ**: использование `qm resize` с несуществующим параметром `--storage`.
6. **Уточнены диски**: явно зафиксировано, что 7 ТБ — это SSD (не HDD), подтверждено в логах установки Ceph OSD.
