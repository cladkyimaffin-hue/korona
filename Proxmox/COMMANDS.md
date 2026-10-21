---
schema_version: "1.1"
status: "in_progress"
date_created: 2026-10-21
date_modified: 2026-10-21
maintainer: "cladkyimaffin-hue"
file_type: "commands_reference"
confidence: "Команды перенесены из документов домена без изменения смысла; контекст, ожидаемый вывод и ограничения — в документе-источнике. Покрытие неполное: список источников и то, что не вошло, — в конце файла."
---

# COMMANDS.md — команды Proxmox

Справочник команд, к которым нужно возвращаться, отдельно от общих описаний.
Команды остаются и в своих документах (там контекст, ожидаемый вывод и
ограничения), здесь — быстрый доступ, сгруппированный по задачам.

## Как пользоваться

Каждый блок начинается со строки-комментария: `[класс] что делает — источник`.

Классы риска:

- **[R]** — только чтение. Безопасно выполнять для диагностики.
- **[W]** — меняет состояние (конфигурация, сервисы, ВМ). Перед выполнением
  проверить текущее состояние (`qm config`, `pct config`), знать откат.
- **[D]** — разрушающая или необратимая (данные, разделы, диски). Только по
  явному подтверждению администратора (метка `REQUIRES_APPROVAL`, см.
  `AI-INSTRUCTIONS.md`, раздел 3.3).

Правила:

- **Блок с несколькими командами — перечень, а не скрипт.** Выполнять нужные
  строки по одной. Только если в комментарии написано «по порядку», команды
  блока выполняются подряд.
- `<угловые скобки>` — плейсхолдер, подставить своё значение. Конкретные ID,
  имена и адреса брать из `AI-environment_facts-korona-proxmox.md` или из
  свежего вывода команд, не из этого файла.
- Секреты (пароли, токены, ключи) здесь не хранятся.
- Если не указано иное, команды выполняются на узле (`pve01` или `pve02`) под
  `root`. Блоки с PowerShell выполняются внутри Windows-гостя от администратора.
- Источник указан как `document_id` из `00_Meta/registry.csv`.

---

## 1. Инвентаризация: кластер, ВМ, LXC

```bash
# [R] Все ВМ и LXC кластера с узлом размещения (таблица может быть шире экрана — смотреть колонку node)
pvesh get /cluster/resources --type vm
```

```bash
# [R] Короткий вариант: id, node, name (проверено 2026-10-20)
pvesh get /cluster/resources --type vm --output-format json-pretty | grep -E '"(id|node|name)"'
```

```bash
# [R] LXC на текущем узле (видит только локальный узел)
pct list
```

```bash
# [R] Конфигурация ВМ / LXC и состояние ВМ — PROXMOX-VM-CLONE-2001-2026-001
qm config <VMID>
qm status <VMID>
pct config <CTID>
```

```bash
# [R] Связь с гостевым агентом и данные ОС гостя — PROXMOX-VM-MEMORY-BALLOON-2026-001
# (команды qm guest info на части версий Proxmox нет — использовать qm guest cmd)
qm guest cmd <VMID> ping
qm guest cmd <VMID> get-osinfo
qm guest cmd <VMID> get-host-name
```

```bash
# [R] Автозапуск и порядок старта — PROXMOX-AUTOSTART-STARTUP-ORDER-2026-001
# Пустой вывод grep означает, что параметр не задан (автозапуск выключен)
for vm in <VMID1> <VMID2>; do echo "VM $vm:"; qm config $vm | grep -E '^(onboot|startup):'; done
for ct in <CTID1> <CTID2>; do echo "CT $ct:"; pct config $ct | grep -E '^(onboot|startup):'; done
```

```bash
# [R] Какому VMID соответствует процесс kvm (по PID) — PROXMOX-CEPH-PUBLIC-NETWORK-1C-2026-001
ps -o pid,args -p <PID1>,<PID2> | grep -o -- '-id [0-9]*'
```

## 2. ВМ и LXC: изменение

```bash
# [W] Включить автозапуск и задать порядок — PROXMOX-AUTOSTART-STARTUP-ORDER-2026-001
# up — пауза в секундах после запуска гостя, не проверка готовности служб внутри него
qm set <VMID> -onboot 1
qm set <VMID> -startup order=<N>,up=<секунды>
pct set <CTID> -onboot 1
pct set <CTID> -startup order=<N>,up=<секунды>
```

```bash
# [W] Откат автозапуска и порядка (варианты, не по порядку) — PROXMOX-AUTOSTART-STARTUP-ORDER-2026-001
qm set <VMID> -delete startup
pct set <CTID> -delete startup
qm set <VMID> -onboot 0
pct set <CTID> -onboot 0
```

```bash
# [R] Проверить шаблон перед клонированием — PROXMOX-VM-CLONE-2001-2026-001
qm status <TEMPLATE_VMID>
qm config <TEMPLATE_VMID>
```

```bash
# [W] Полное клонирование (только --full; linked clone для production не использовать)
# PROXMOX-VM-CLONE-2001-2026-001
qm clone <TEMPLATE_VMID> <NEW_VMID> --name <имя> --full --storage ceph-fast
```

```bash
# [W] Увеличить диск. Увеличение необратимо (уменьшить диск средствами Proxmox нельзя)
# Флага --storage у qm resize НЕТ: команда с ним завершится ошибкой Unknown option
# PROXMOX-VM-CLONE-2001-2026-001
qm resize <VMID> scsi0 +<размер>G
```

```bash
# [W] Память (MiB) и ядра — PROXMOX-VM-CLONE-2001-2026-001
qm set <VMID> --memory <MiB>
qm set <VMID> --cores <N>
```

```bash
# [W] Запуск и остановка (варианты, не по порядку). stop — жёсткая остановка, предпочитать shutdown
# PROXMOX-VM-CLONE-2001-2026-001
qm start <VMID>
qm shutdown <VMID>
qm stop <VMID>
```

```bash
# [W] Отключить установочные ISO после завершения установки — PROXMOX-VM-CLONE-2001-2026-001
qm set <VMID> --delete ide0
qm set <VMID> --delete ide2
```

```bash
# [W] Включить cache=writeback для диска ВМ (по порядку) — PROXMOX-VM-CLONE-2001-2026-001
# Риск: при аварийном отключении узла возможна потеря несброшенных данных.
# Не переносить на другие ВМ «по аналогии». Вступает в силу только после stop/start ВМ.
# Взять текущую строку scsi0 из qm config и менять только нужные опции:
qm stop <VMID>
qm set <VMID> --scsi0 <storage>:<диск>,cache=writeback,discard=on,iothread=1,size=<размер>,ssd=1
qm start <VMID>
```

## 3. Ceph: состояние (только чтение)

```bash
# [R] Общее состояние: HEALTH, OSD up/in, PG — PROXMOX-CEPH-OSD-POOLS-DEPLOYMENT-2026-001
ceph -s
```

```bash
# [R] Топология и правила размещения — PROXMOX-CEPH-NIC0-DIRECT-LINK-2026-001
ceph osd tree
ceph osd crush rule dump
ceph osd pool ls detail
ceph mon dump
```

```bash
# [R] Настройки Ceph: что действует на самом деле — AI-environment_facts-korona-proxmox.md
# Локальный /etc/ceph/ceph.conf имеет приоритет над настройками монитора при старте демонов OSD
ceph config dump
ceph config get osd.<N> osd_memory_target
```

```bash
# [R] Адреса, которые слушают OSD (должны быть из cluster_network) — PROXMOX-CEPH-NIC0-DIRECT-LINK-2026-001
ss -tlnp | grep ceph-osd
```

```bash
# [R] Задержки OSD — AI-environment_facts-korona-proxmox.md
ceph osd perf
```

```bash
# [R] Где лежат данные образа диска ВМ и какая у него задержка — PROXMOX-CEPH-PUBLIC-NETWORK-1C-2026-001
# <имя_объекта> взять из block_name_prefix в выводе rbd info
qm config <VMID> | grep scsi0
rbd ls -p ceph-fast
rbd info ceph-fast/<имя_образа>
ceph osd map ceph-fast <имя_объекта>
rbd perf image iostat ceph-fast
```

## 4. Ceph: изменение

```bash
# [W] Параметры пула. На 2-узловом кластере GUI-умолчания Size=3/Min Size=2 дают degraded,
# нужны size 2 / min_size 1 (в том числе для системного пула .mgr).
# min_size 1 снижает защиту данных — принято осознанно для 2 узлов
# PROXMOX-CEPH-OSD-POOLS-DEPLOYMENT-2026-001
ceph osd pool set <пул> size 2
ceph osd pool set <пул> min_size 1
```

```bash
# [W] Подсеть кластерной сети Ceph в мониторе — PROXMOX-CEPH-NIC0-DIRECT-LINK-2026-001
# Значения — подсетью, не адресом узла с маской. Локальный ceph.conf может переопределить
ceph config set mon cluster_network <подсеть/маска>
```

```bash
# [W] Перезапуск OSD после сбоя (по порядку; ceph orch в этом кластере не настроен)
# Перезапуск вызывает peering и влияет на доступность — только в окне работ
# PROXMOX-CEPH-NIC0-DIRECT-LINK-2026-001
systemctl reset-failed ceph-osd@<N>
systemctl restart ceph-osd.target
```

```bash
# [W] Репозитории для установки Ceph на PVE 9 / trixie, формат .sources, не .list (по порядку)
# PROXMOX-CEPH-OSD-POOLS-DEPLOYMENT-2026-001
apt update
apt full-upgrade -y
sed -i 's/pve-enterprise/pve-no-subscription/g' /etc/apt/sources.list.d/proxmox.sources
cat << 'EOF' > /etc/apt/sources.list.d/ceph.sources
Types: deb
URIs: http://download.proxmox.com/debian/ceph-squid
Suites: trixie
Components: no-subscription
Signed-By: /usr/share/keyrings/proxmox-archive-keyring.gpg
EOF
apt update
```

## 5. Сеть и интерфейсы

```bash
# [R] Состояние и скорость всех физических интерфейсов — NETWORK-SFP-OPTICAL-MISMATCH-2026-001
for iface in $(ls /sys/class/net/ | grep -v '^lo$'); do
    echo "=== Интерфейс: $iface ==="
    ip link show "$iface" | grep -oP 'state \K\w+'
    ethtool "$iface" 2>/dev/null | grep -E "Speed:|Link detected:"
done
```

```bash
# [R] Скорость конкретного порта. Скорость моста vmbr0 по ethtool линком НЕ является —
# проверять физический порт (nic2) и bridge link — PROXMOX-CEPH-PUBLIC-NETWORK-1C-2026-001
ethtool <интерфейс> | grep -E "Speed|Link"
bridge link
```

```bash
# [R] Драйвер и реальный тип установленного модуля (SFP/SFP+) — NETWORK-SFP-OPTICAL-MISMATCH-2026-001
# Тип модуля подтверждать только так, не со слов
ethtool -i <интерфейс> 2>/dev/null | grep -E 'driver:|bus-info:'
ethtool -m <интерфейс> 2>/dev/null | head -20
```

```bash
# [R] История линка и ошибки карты — NETWORK-SFP-OPTICAL-MISMATCH-2026-001
# Link detected: no сам по себе — не диагноз, сверять с dmesg
dmesg | grep -iE '<интерфейс1>|<интерфейс2>|i40e|link' | tail -30
```

```bash
# [R] Счётчики ошибок порта на самом узле (без доступа к коммутатору)
# PROXMOX-CEPH-BOND0-LATENCY-INVESTIGATION-2026-001
ethtool -S <интерфейс> | grep -iE 'error|drop|crc|miss|over|fifo'
```

```bash
# [R] Задержка между узлами по сети репликации — PROXMOX-CEPH-BOND0-LATENCY-INVESTIGATION-2026-001
# Сеть bond0 (10.10.10.0/24) сейчас не используется (bond0 DOWN) — подставить актуальную сеть
ping -c 100 -i 0.2 <адрес_второго_узла>
```

```bash
# [R] Проверка Jumbo Frames (MTU 9000) между узлами — PROXMOX-CEPH-NIC0-DIRECT-LINK-2026-001
# Без потерь означает, что MTU 9000 проходит на обоих концах
ping -M do -s 8972 -c 3 <адрес_второго_узла>
```

```bash
# [R] MTU и сохранённая конфигурация интерфейса — PROXMOX-CEPH-NIC0-DIRECT-LINK-2026-001
ip -d link show <интерфейс> | grep mtu
grep -A4 "iface <интерфейс>" /etc/network/interfaces
```

```bash
# [R] Соединения Ceph и QEMU (кто с кем и по каким портам) — PROXMOX-CEPH-PUBLIC-NETWORK-1C-2026-001
ss -tnp
ss -tulnp | grep ceph-osd
```

```bash
# [W] MTU в runtime (после перезагрузки теряется, если не сохранён в /etc/network/interfaces).
# Менять на обоих концах канала до перезапуска сервисов Ceph
# PROXMOX-CEPH-NIC0-DIRECT-LINK-2026-001
ip link set <интерфейс> mtu 9000
```

```bash
# [W] Поднять интерфейс / применить /etc/network/interfaces без перезагрузки (варианты, не по порядку)
# ifreload -a применяет конфигурацию всех интерфейсов: при ошибке в файле можно потерять
# связь с узлом — иметь консоль/IPMI. PROXMOX-CEPH-NIC0-DIRECT-LINK-2026-001
ifup <интерфейс>
ifreload -a
```

## 6. Кворум кластера (corosync)

```bash
# [R] Состояние QDevice и доступность его порта — PROXMOX-CEPH-PUBLIC-NETWORK-1C-2026-001
corosync-qdevice-tool -s
nc -vz <адрес_qdevice> 5403
journalctl -u corosync-qdevice --since "-1 day"
```

## 7. Windows-гость (PowerShell, внутри ВМ)

```powershell
# [R] QEMU Guest Agent и драйвер VirtIO Balloon — PROXMOX-VM-MEMORY-BALLOON-2026-001
Get-Service -Name QEMU-GA
Get-PnpDevice | Where-Object {$_.Class -eq "System" -or $_.FriendlyName -like "*Balloon*"} | Format-Table Status, Class, FriendlyName, DeviceID
Get-Service -Name "*balloon*"
```

```powershell
# [R] Реальное использование RAM внутри гостя (не путать с Memory usage в Proxmox)
# PROXMOX-VM-MEMORY-BALLOON-2026-001
Get-CimInstance Win32_OperatingSystem | Select-Object TotalVisibleMemorySize, FreePhysicalMemory | ForEach-Object {
  [PSCustomObject]@{
    'Total RAM (GB)' = [math]::Round($_.TotalVisibleMemorySize / 1MB, 2)
    'Used RAM (GB)'  = [math]::Round(($_.TotalVisibleMemorySize - $_.FreePhysicalMemory) / 1MB, 2)
    'Usage %'        = [math]::Round(($_.TotalVisibleMemorySize - $_.FreePhysicalMemory) / $_.TotalVisibleMemorySize * 100, 2)
  }
}
```

```powershell
# [R] Найти диск с ISO virtio-win и путь к blnsvr.exe (путь зависит от версии и архитектуры Windows,
# общий путь не использовать) — PROXMOX-VM-MEMORY-BALLOON-2026-001
Get-WmiObject Win32_CDROMDrive | Select-Object Drive, VolumeName
Get-ChildItem -Path <буква_диска>:\ -Recurse -Filter 'blnsvr.exe' -ErrorAction SilentlyContinue | Select-Object FullName
```

```powershell
# [W] Установить QEMU Guest Agent с ISO virtio-win — PROXMOX-VM-MEMORY-BALLOON-2026-001
Start-Process msiexec.exe -ArgumentList '/i <буква_диска>:\guest-agent\qemu-ga-x86_64.msi /qn /norestart' -Wait
```

```powershell
# [W] Создать и запустить службу BalloonService с найденным путём (по порядку)
# PROXMOX-VM-MEMORY-BALLOON-2026-001
sc.exe create BalloonService binPath= "<найденный_путь>\blnsvr.exe" start= auto
Start-Service -Name BalloonService
```

```powershell
# [W] Удалить службу BalloonService (например, чтобы пересоздать с верным путём).
# Отдельная команда — не выполнять сразу после создания — PROXMOX-VM-MEMORY-BALLOON-2026-001
sc.exe delete BalloonService
```

```powershell
# [R] Структура дисков и разделов. Номера разделов не копировать из документов —
# каждый раз смотреть заново — PROXMOX-VM-CLONE-2001-2026-001
Get-Disk | Format-Table Number, FriendlyName, Size, PartitionStyle
Get-Partition | Format-Table DiskNumber, PartitionNumber, DriveLetter, Size, Type
```

```powershell
# [D] Удалить раздел (в примере — Recovery-раздел между C: и свободным местом).
# Только после Get-Disk/Get-Partition, проверки номера и резервной копии; решение администратора
# PROXMOX-VM-CLONE-2001-2026-001
Remove-Partition -DiskNumber <N> -PartitionNumber <M> -Confirm:$false
```

```powershell
# [W] Расширить C: на всё свободное место (после удаления раздела между C: и свободным местом)
# PROXMOX-VM-CLONE-2001-2026-001
Resize-Partition -DriveLetter C -Size (Get-PartitionSupportedSize -DriveLetter C).SizeMax
```

```powershell
# [R] Тест диска изнутри гостя (создаёт нагрузку на диск; многопоточный, в отличие от AIDA64
# с queue depth=1, который занижает результат) — PROXMOX-VM-CLONE-2001-2026-001
winsat disk -drive C
```

---

## Покрытие версии 1

Команды перенесены из документов:

- `PROXMOX-AUTOSTART-STARTUP-ORDER-2026-001`
- `PROXMOX-VM-CLONE-2001-2026-001`
- `PROXMOX-VM-MEMORY-BALLOON-2026-001`
- `PROXMOX-CEPH-OSD-POOLS-DEPLOYMENT-2026-001`
- `PROXMOX-CEPH-NIC0-DIRECT-LINK-2026-001`
- `PROXMOX-CEPH-PUBLIC-NETWORK-1C-2026-001`
- `PROXMOX-CEPH-BOND0-LATENCY-INVESTIGATION-2026-001`
- `NETWORK-SFP-OPTICAL-MISMATCH-2026-001`

Команды `pvesh get /cluster/resources` и `qm guest cmd <VMID> get-host-name`
проверены администратором 2026-10-20 (отдельного документа-источника нет).

**Ещё не вошли** (будут добавлены следующими правками): Zabbix (`ZABBIX-*`, в том
числе `pveum` и токены — только плейсхолдеры), подготовка и очистка дисков под
OSD (`PROXMOX-CEPH-OSD-DISK-PREP-2026-001`, там класс [D]: `wipefs`, `sgdisk`),
QDevice, AD, RDS, USB HASP, Vaultwarden, шаблоны (Windows Server, LXC),
диагностика SSH и `pam_systemd`, `bond0`. До их добавления искать команды
в самих документах по `INDEX.md`.

## Как дополнять

1. Команду, к которой стоит возвращаться, добавляют в документ-источник и здесь.
2. Формат блока: первая строка-комментарий `[класс] что делает — document_id`.
3. Класс выбирать по самому опасному шагу блока. Сомневаетесь между [W] и [D] — ставьте [D].
4. Секретов нет: токены, пароли и ключи заменять плейсхолдерами.
5. После правки обновить `date_modified` и список покрытия.
