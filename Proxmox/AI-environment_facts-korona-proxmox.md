# environment_facts — извлечено из репозитория korona/Proxmox

Источник: https://github.com/cladkyimaffin-hue/korona/tree/e18954451262bb578748bd7e19625a3eeb094de5/Proxmox
Дата анализа: 2026-09-08. Все значения ниже подтверждены текстом файлов репозитория (не домыслены). Там, где данные противоречивы, неполны или помечены в источнике как «уточнить» — указано явно, чтобы ИИ не выдавал их как факт.

```yaml
environment_facts:

  proxmox:
    version: "Proxmox VE 9.2"                       # подтверждено в pve01+pve02+Qdevice.md (команда pvecm qdevice setup — специфична для 9.2)
    cluster_name: "krnn"
    nodes:
      - name: pve01
        mgmt_ip: "192.168.202.121/22"
        ceph_cluster_ip: "10.10.10.1/24 (bond0)"
      - name: pve02
        mgmt_ip: "192.168.202.179/22"
        ceph_cluster_ip: "10.10.10.2/24 (bond0)"
    cluster_topology: "2 полноценных узла (pve01, pve02) + внешний Corosync QDevice — НЕ трёхнодовый кластер, несмотря на то что в одном из файлов обсуждалась установка на 3 сервера (это отдельный/плановый документ, фактически реализовано 2+QDevice)."
    qdevice:
      hostname: "Qdevice.krnn.ru"
      ip: "192.168.202.251"
      os: "Debian GNU/Linux 13"
      setup_command_note: "В PVE 9.2 используется `pvecm qdevice setup 192.168.202.251`. Команда `pvecm add qdevice 192.168.202.251` НЕ работает (ошибка 400 too many arguments) — не предлагать её."
    hardware:
      server_model: "Huawei FusionServer 2288H V5 (3 одинаковых сервера в наличии, но в кластере активно используются только pve01/pve02)"
      system_disks: "2× 480 GB SSD (зеркало под ОС Proxmox, storage local-lvm)"
      per_node_data_disks_actual: "1× NVMe ~3.5/3.84 ТБ + 1× SSD ~7/7.68 ТБ (фактическая конфигурация; в ранних плановых документах ошибочно фигурировали 'HDD 7 ТБ' — это устарело, реальность подтверждена в 'Установка Ceph OSD НА на pve02 pve01.md')"
      cpu_ram_per_node: "НЕ подтверждено (в hardware-spec.md помечено как [УТОЧНИТЬ]). Известно только вскользь: на одной из нод упоминалось '36 ядер и 240 ГБ RAM' — не считать это подтверждённой спецификацией всех узлов без проверки."
      network_cards: "Intel X722 (LOM, 2×10GbE SFP+ + 2×1GbE RJ45), Intel X710 (PCIe SLOT3, 2×10GbE SFP+)"
      transceivers: "Intel FTLX8571D3BCVIT1, 10GBASE-SR"

  network:
    management_subnet: "192.168.200.0/22 (охватывает диапазон .200.x–.203.x)"
    management_gateway: "192.168.200.1"
    ceph_cluster_network:
      subnet: "10.10.10.0/24"
      interface: "bond0"
      bond_mode: "active-backup (mode 1) — НЕ LACP/802.3ad, несмотря на то что в планировании обсуждался LACP; по факту реализован active-backup, т.к. не требует настройки коммутатора"
      slaves: "nic4 + nic5 (или eno1/eno2 в зависимости от ноды — проверять фактическое имя интерфейса перед командами)"
    proxmox_web_ui_bridge: "vmbr0 (управление/VM-трафик, привязан к nic2 на pve01)"
    known_ip_reservations:
      "192.168.200.1": "gateway"
      "192.168.200.2": "DC.krnn.ru"
      "192.168.200.10": "ANDQ.krnn.ru"
      "192.168.200.225": "AD.krnn.ru (бывш. WIN-AD)"
      "192.168.202.121": "pve01"
      "192.168.202.179": "pve02"
      "192.168.202.251": "Qdevice.krnn.ru"
      "192.168.203.93": "zabbix (LXC CT 201)"

  storage:
    pools:
      - name: "local-lvm"
        type: "LVM-thin, локальный"
        purpose: "ISO-образы, системные разделы узлов; НЕ использовать для production-дисков ВМ/CT по умолчанию — в этой инфраструктуре production располагается на Ceph"
      - name: "ceph-fast"
        backing_disks: "NVMe (device class: nvme)"
        crush_rule: "nvme-replicated"
        size_min_size: "Size=2, Min.Size=1"
        pg: 128
        purpose: "Критичные к задержкам workloads: 1С, терминальный сервер, Active Directory, БД (например Zabbix). Используется как storage ПО УМОЛЧАНИЮ для production ВМ/CT, включая шаблоны (шаблон 1000 debian12-pattern физически лежит на ceph-fast)."
      - name: "ceph-bulk"
        backing_disks: "SSD 7/7.68 ТБ (device class: ssd)"
        crush_rule: "ssd-replicated"
        size_min_size: "Size=2, Min.Size=1"
        pg: 128
        purpose: "Бэкапы, архивы, менее критичные ВМ. Не использовать для активных БД/систем, где важна задержка."
    clone_policy: "Proxmox по умолчанию создаёт LINKED clone (зависимый от базового диска шаблона), а не Full Clone. В репозитории уже был инцидент: контейнер 500 был создан как linked clone от шаблона 200 и заблокировал удаление шаблона ('base volume ... is still in use by linked clone'). Чтобы получить независимый клон — ВСЕГДА добавлять флаг --full к pct clone / qm clone, если пользователь явно не просил linked clone."
    known_gotchas:
      - "pct create для LXC использует --rootfs <storage>:<size>, НЕ --disk (--disk для LXC не существует и вызывает ошибку)."
      - "pct clone НЕ поддерживает параметр --net0 — сетевые настройки задаются отдельно через pct set после клонирования."
      - "В Proxmox нет команды для изменения ID существующего контейнера/ВМ напрямую. Единственный штатный способ дать ресурсу новый ID — сделать резервную копию (vzdump) и восстановить (pct restore / qm restore) с нужным ID."

  vm_ct_numbering_convention:
    templates:
      - id: 1000
        name: "debian12-pattern"
        type: "LXC"
        storage: "ceph-fast"
        note: "Официальное название — debian12-pattern, а не 'debian12-template' (это расхождение уже встречалось в реальном диалоге с пользователем — не путать)."
      - id: 2000
        name: "win2022-template"
        type: "QEMU/KVM"
        storage: "ceph-fast (предположительно, как и клоны от него; явно не переуказано, но клоны 2001/2003 на ceph-fast)"
        specs: "q35, BIOS=OVMF(UEFI), CPU=host, SCSI=VirtIO SCSI Single, Network=VirtIO, TPM v2.0 (swtpm), диск 100 ГБ, прошёл Sysprep /generalize перед конвертацией в шаблон."
    known_working_instances:
      - id: 2001
        name: "Srv1c"
        role: "сервер приложений 1С:ERP"
        source_template: 2000
        clone_type: "Full Clone"
        storage: "ceph-fast"
        resources: "24 vCPU, 160 ГиБ RAM, диск увеличен со 100 ГБ до 1 ТБ"
      - id: 2003
        name: "TC (TC.KRNN.RU)"
        role: "терминальный сервер RDS"
        source_template: 2000
        resources: "4 vCPU, ~48 ГБ RAM, 500 ГБ диск"
      - id: 700
        name: "zabbix"
        type: "LXC"
        role: "мониторинг (Zabbix)"
        source_template: 1000
      - id: 201
        name: "zabbix"
        type: "LXC"
        note: "промежуточный/более ранний контейнер до итоговой ревизии нумерации — при работе с текущей инфраструктурой ориентироваться на актуальный CT 700, а не на 201, если не указано иное."
    convention_summary: "Шаблоны — круглые номера (1000 для LXC, 2000 для Windows-ВМ). Рабочие Windows-машины — в диапазоне 2001–2003+. Рабочие LXC — произвольные ID (700 и т.д.), процесс формирования ID исторически проходил через несколько промежуточных номеров (100→2000, 200→500→501→1000) — не считать промежуточные ID финальными без проверки текущего `pct list` / `qm list`."

  active_directory:
    domain_fqdn: "krnn.ru"
    netbios: "KRNN"
    os_locale: "ru — группы AD называются на русском (например «Пользователи домена», а не «Domain Users»); проверять точное имя через `whoami /user` и `net group` перед использованием в командах, не считать англоязычное имя фактом по умолчанию."
    domain_controllers:
      - hostname: "ANDQ.krnn.ru"
        ip: "192.168.200.10"
      - hostname: "DC.krnn.ru"
        ip: "192.168.200.2"
      - hostname: "AD.krnn.ru"
        ip: "192.168.200.225"
        note: "Ранее назывался WIN-AD, переименован в AD. На нём размещена роль RDS Licensing (сервер лицензий), активирован в режиме 120-дневного grace period, RDS CAL пока не куплены."
    rds_terminal_server:
      hostname: "TC.KRNN.RU (VM 2003)"
      collection_name: "Terminal"
      access_group: "Remote Desktop Users (локальная) ← KRNN\\Пользователи домена (доменная)"
      licensing_mode_registry_value: 4  # Per User
      licensing_server: "AD.krnn.ru"
      status: "RDS CAL не приобретены — сервер работает в льготном 120-дневном периоде; НЕ считать лицензирование завершённым."

  common_ai_mistakes_already_seen_in_this_repo:
    - "Использование короткого имени сервера ($env:COMPUTERNAME) вместо FQDN в New-RDSessionDeployment — требуется FQDN."
    - "Придуманный несуществующий cmdlet Grant-RDAccess."
    - "Придуманный параметр -UserGroups для Set-RDSessionCollectionConfiguration (такого параметра нет)."
    - "Вызов Get-ADDomain/Get-ADGroup на рядовом сервере без установленного модуля ActiveDirectory PowerShell."
    - "Команда lsmgr.exe — устарела (Windows Server 2008 R2), в Windows Server 2022 не существует."
    - "Использование --disk вместо --rootfs в pct create для LXC."
    - "Использование pct clone без --full там, где нужен независимый клон (по умолчанию создаётся linked clone)."
    - "Указание local-lvm как storage по умолчанию для production ВМ/CT — в этой инфраструктуре production по умолчанию на ceph-fast."
```

## Как этим пользоваться

Вставляй актуальный блок `environment_facts` (или ссылку на этот файл) в начало любой новой рабочей сессии по этой инфраструктуре — до того, как просить у ИИ конкретные команды. Перед каждой командой, трогающей storage/сеть/ID/AD-группы, сверяйся именно с этими значениями, а не с общими знаниями о Proxmox/Windows Server по умолчанию.

**Не подтверждено репозиторием (не считать фактом, спрашивать/проверять):**
- точная модель и количество CPU, объём и тип RAM хостов pve01/pve02 (в исходниках помечено «уточнить»);
- финальная модель коммутатора;
- используется ли третий сервер как полноценный узел кластера (в наличии есть, в кластер по факту не введён);
- актуальный список ВСЕХ ID контейнеров/ВМ — нумерация в истории репозитория несколько раз менялась, перед работой с конкретным ID лучше выполнить `pct list` / `qm list` для сверки с текущим состоянием.
