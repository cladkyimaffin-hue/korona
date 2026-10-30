---
schema_version: "1.1"
status: "in_progress"
date_created: 2026-10-21
date_modified: 2026-10-29
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
# [R] Какую память получил запущенный процесс QEMU — PROXMOX-VM2002-AD-RAM-INCREASE-2026-001
# Интерактивно: после qm monitor <VMID> в приглашении qm> выполнить info balloon, затем quit.
# max_mem должен совпадать с memory из qm config; если нет — ВМ не перезапускали после смены memory.
# actual меньше max_mem означает, что балун ограничил память гостя (INFERRED). mem_swapped_in/out — счётчики гостя в байтах
qm monitor <VMID>
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
# [W] Применить новую память работающей ВМ (по порядку) — PROXMOX-VM2002-AD-RAM-INCREASE-2026-001
# Перезагрузка из гостя (Windows: Пуск, Перезагрузка) процесс QEMU не перезапускает: max_mem останется прежним.
# Hotplug памяти на ВМ с numa: 0 не включать (Linux-ВМ с таким сочетанием не загрузилась): сначала numa: 1, память кратна 512. Остановка контроллера домена прерывает его службы —
# сначала убедиться, что другие DC доступны. Откат — вернуть прежние memory и balloon и снова остановить и запустить ВМ.
# balloon равен memory — память ВМ балунингом не уменьшается (INFERRED)
qm set <VMID> --memory <MiB> --balloon <MiB>
qm shutdown <VMID>
qm status <VMID>
qm start <VMID>
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

```bash
# [R] Состояние кворума — PROXMOX-CLUSTER-QDEVICE-SETUP-2026-001, PROXMOX-QDEVICE-REPLACEMENT-2026-001
# Для двух узлов с QDevice ожидается Expected votes: 3 и флаг Qdevice в Flags.
# Команды pvecm qdevice status не существует: состояние смотреть через pvecm status и corosync-qdevice-tool -s
pvecm status
```

```bash
# [W] Создать кластер и добавить второй узел — PROXMOX-CLUSTER-QDEVICE-SETUP-2026-001
# Две команды на разных узлах: pvecm create — на первом, pvecm add — на втором (не подряд на одной машине).
# До настройки QDevice потеря любого из двух узлов блокирует кластер. Резервная копия конфигурации
# создаётся автоматически при добавлении узла (в источнике — каталог /var/lib/pve-cluster/backup/)
pvecm create <имя_кластера>
pvecm add <адрес_первого_узла>
```

```bash
# [W] Установить corosync-qnetd на отдельном хосте QDevice, не на узлах кластера (по порядку)
# PROXMOX-CLUSTER-QDEVICE-SETUP-2026-001, PROXMOX-QDEVICE-REPLACEMENT-2026-001
apt update && apt install -y corosync-qnetd
systemctl enable --now corosync-qnetd
systemctl status corosync-qnetd.service
```

```bash
# [W] Установить corosync-qdevice на обоих узлах Proxmox — PROXMOX-CLUSTER-QDEVICE-SETUP-2026-001
apt update && apt install corosync-qdevice -y
```

```bash
# [W] Имя хоста QDevice и запись в hosts (на хосте QDevice, от обычного пользователя с sudo; по порядку)
# PROXMOX-QDEVICE-REPLACEMENT-2026-001
# sudo echo ... >> /etc/hosts не работает: перенаправление выполняется от обычного пользователя —
# использовать | sudo tee -a. Имя хоста лучше задавать до pvecm qdevice setup (рекомендация, INFERRED)
sudo hostnamectl set-hostname <fqdn_qdevice>
echo "<адрес_qdevice> <fqdn_qdevice> <короткое_имя>" | sudo tee -a /etc/hosts
hostname -f
```

```bash
# [R] Открытый ключ root на узле, с которого выполняется pvecm qdevice setup — PROXMOX-QDEVICE-REPLACEMENT-2026-001
# Только открытый ключ (.pub). Копировать целой строкой, сохраняя пробелы между типом ключа,
# телом и комментарием: ключ вида ssh-rsaAAAA... сервер отвергает
cat /root/.ssh/id_rsa.pub
```

```bash
# [W] Права на хосте QDevice для входа root по ключу, после добавления ключа в /root/.ssh/authorized_keys
# PROXMOX-QDEVICE-REPLACEMENT-2026-001
# В Debian 13 вход root по паролю отключён (PermitRootLogin prohibit-password)
chmod 700 /root/.ssh
chmod 600 /root/.ssh/authorized_keys
```

```bash
# [R] Проверка входа root по ключу с узла на хост QDevice — PROXMOX-QDEVICE-REPLACEMENT-2026-001
# Должно вернуть имя хоста QDevice без запроса пароля. accept-new при первом подключении
# добавляет ключ хоста в known_hosts
ssh -o StrictHostKeyChecking=accept-new root@<адрес_qdevice> "hostname -f"
```

```bash
# [W] Подключить QDevice (с одного узла, по порядку) — PROXMOX-CLUSTER-QDEVICE-SETUP-2026-001, PROXMOX-QDEVICE-REPLACEMENT-2026-001
# Нужен вход root с этого узла на хост QDevice по SSH-ключу без пароля; TCP-порт 5403 должен быть
# доступен между узлами и хостом QDevice. pvecm add qdevice <IP> в PVE 9.2 не работает (400 too many arguments)
pvecm qdevice setup <адрес_qdevice>
pvecm status
```

```bash
# [W] Удалить QDevice: откат или первый шаг замены (по порядку) — PROXMOX-CLUSTER-QDEVICE-SETUP-2026-001, PROXMOX-QDEVICE-REPLACEMENT-2026-001
# После удаления Expected votes: 2 — кворум держится только на двух узлах, потеря любого узла
# в этом окне остановит кластер. Не выполнять, когда один из узлов недоступен.
# Удаление узла из кластера (pvecm delnode) — отдельная процедура, в справочник не вошла
pvecm qdevice remove
pvecm status
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

## 8. Zabbix

Токены и пароли здесь — только плейсхолдеры. Имена пользователей, токенов, адреса и
CTID брать из `AI-environment_facts-korona-proxmox.md`. Шаги в веб-интерфейсе Zabbix
(макросы, фильтры LLD, шаблоны) команд не содержат и сюда не входят.

```bash
# [R] Состояние служб стека Zabbix — внутри контейнера Zabbix (pct enter <CTID>)
# ZABBIX-STACK-INSTALL-2026-001
systemctl is-active zabbix-server zabbix-agent nginx php8.2-fpm mariadb
```

```bash
# [W] Установить пакеты стека Zabbix в контейнере — ZABBIX-STACK-INSTALL-2026-001
pct exec <CTID> -- bash -c "apt install -y zabbix-server-mysql zabbix-frontend-php zabbix-nginx-conf zabbix-sql-scripts zabbix-agent mariadb-server"
```

```bash
# [W] Включить nesting, если MariaDB не стартует в непривилегированном LXC (226/NAMESPACE) —
# ZABBIX-STACK-INSTALL-2026-001. Контейнер в privileged не переводить. Перезагрузка контейнера
# прерывает мониторинг на время старта
pct set <CTID> -features nesting=1
pct reboot <CTID>
systemctl status mariadb   # внутри контейнера, должен стать active
```

```bash
# [W] Создать БД и импортировать схему (по порядку, ОДНОКРАТНО) — ZABBIX-STACK-INSTALL-2026-001
# Импорт схемы не идемпотентен: повторный запуск даёт дубли ключей. <ПАРОЛЬ_БД> заменить на
# реальный надёжный пароль: не выполнять с плейсхолдером буквально
pct exec <CTID> -- bash -c "
mysql -e \"CREATE DATABASE IF NOT EXISTS zabbix CHARACTER SET utf8mb4 COLLATE utf8mb4_bin;\"
mysql -e \"CREATE USER IF NOT EXISTS 'zabbix'@'localhost' IDENTIFIED BY '<ПАРОЛЬ_БД>';\"
mysql -e \"GRANT ALL PRIVILEGES ON zabbix.* TO 'zabbix'@'localhost';\"
mysql -e \"FLUSH PRIVILEGES;\"
zcat /usr/share/zabbix-sql-scripts/mysql/server.sql.gz | mysql --default-character-set=utf8mb4 -uzabbix -p'<ПАРОЛЬ_БД>' zabbix
"
```

```bash
# [W] Настроить конфиги Zabbix, nginx и PHP-FPM, перезапустить и включить службы (по порядку)
# ZABBIX-STACK-INSTALL-2026-001. Перезапуск прерывает веб-интерфейс и сбор метрик
pct exec <CTID> -- bash -c "
sed -i 's/^# DBHost=localhost/DBHost=localhost/' /etc/zabbix/zabbix_server.conf
sed -i 's/^# DBName=zabbix/DBName=zabbix/' /etc/zabbix/zabbix_server.conf
sed -i 's/^# DBUser=zabbix/DBUser=zabbix/' /etc/zabbix/zabbix_server.conf
sed -i '/^DBUser=zabbix/a DBPassword=<ПАРОЛЬ_БД>' /etc/zabbix/zabbix_server.conf
sed -i 's|^#        listen|        listen|' /etc/zabbix/nginx.conf
sed -i 's|^#        server_name|        server_name|' /etc/zabbix/nginx.conf
sed -i 's|server_name example.com;|server_name <имя_сервера> <адрес_zabbix>;|' /etc/zabbix/nginx.conf
sed -i 's|^; php_value\[date.timezone\] = Europe/Riga|php_value[date.timezone] = Europe/Moscow|' /etc/zabbix/php-fpm.conf
systemctl restart zabbix-server zabbix-agent nginx php8.2-fpm
systemctl enable zabbix-server zabbix-agent nginx php8.2-fpm
"
```

```bash
# [W] Сменить пароль пользователя БД zabbix — ZABBIX-STACK-INSTALL-2026-001
# Рекомендовано в документе; на момент документа не выполнено. Окно обслуживания (по порядку):
# 1) в консоли mysql: ALTER USER 'zabbix'@'localhost' IDENTIFIED BY '<новый_пароль>';
# 2) поправить DBPassword= в /etc/zabbix/zabbix_server.conf
systemctl restart zabbix-server
```

```bash
# [R] Ошибки несовпадения имени хоста в журнале сервера Zabbix — ZABBIX-LXC-FALSE-ALERTS-2026-001
# Много повторов «host [X] not found» означает, что Hostname агента и Host name в Zabbix не совпадают
tail -n 100 /var/log/zabbix/zabbix_server.log | grep "not found"
```

```bash
# [W] Роль, пользователь и API-токен для мониторинга (по порядку) — ZABBIX-PVE-API-MONITORING-2026-001
# Перечень прав роли — как в документе-источнике. Токен создаётся с privsep=1: права пользователя
# он НЕ наследует (следующий блок). Секрет токена выводится один раз — сразу сохранить
pveum role add <роль> -privs "Sys.Audit,VM.Audit,Datastore.Audit,Sys.Modify,SDN.Audit"
pveum user add <пользователь>@pve
pveum acl modify / --users <пользователь>@pve --roles <роль>
pveum user token add <пользователь>@pve <имя_токена>
```

```bash
# [W] ACL на сам токен — ZABBIX-PVE-API-MONITORING-2026-001
# Без явного ACL токен получает 403, даже если у пользователя права есть. В документе: /nodes
# для данных узлов; для cluster/status нужны права на /
pveum acl modify <путь> --token '<пользователь>@pve!<имя_токена>' --role <роль>
```

```bash
# [R] Права пользователя и токена — ZABBIX-PVE-API-MONITORING-2026-001
# Команд pveum user show и pveum user list-permissions в этой версии Proxmox нет
pveum user permissions <пользователь>@pve --path <путь>
pveum user token list <пользователь>@pve
pveum user token permissions <пользователь>@pve <имя_токена>
```

```bash
# [R] Проверка API напрямую, в обход Zabbix — ZABBIX-PVE-API-MONITORING-2026-001
# Формат заголовка PVEAPIToken=USER@REALM!TOKENID=SECRET: перед секретом знак «=», не «:».
# Одинарные кавычки обязательны: восклицательный знак в двойных даёт history expansion в bash.
# Секрет подставить вручную; он попадает в историю оболочки — не сохранять его в файлах репозитория
curl -k -s -w "\nHTTP_CODE: %{http_code}\n" \
  -H 'Authorization: PVEAPIToken=<пользователь>@pve!<имя_токена>=<СЕКРЕТ>' \
  "https://<адрес_узла>:8006/api2/json/<путь_API>"
```

```bash
# [W] Пересоздать токен (по порядку) — ZABBIX-PVE-API-MONITORING-2026-001
# Рекомендовано в документе, на момент документа не выполнено. Сначала проверить текущий токен
# прямым curl (блок выше) — пересоздание может не понадобиться. Роль в документе — PVEAuditor;
# расхождение с кастомной ролью мониторинга документ не объясняет
pveum user token add <пользователь>@pve <новое_имя_токена> --comment "<комментарий>"
pveum acl modify / --roles PVEAuditor --token '<пользователь>@pve!<новое_имя_токена>'
```

```bash
# [W] Отключить privsep у токена — ZABBIX-PVE-API-MONITORING-2026-001
# Обходной путь, менее безопасный: уравнивает права токена с правами пользователя целиком.
# Основным путём не считать — предпочитать явный ACL на токен
pveum user token modify <пользователь>@pve <имя_токена> --privsep 0
```

```bash
# [R] Реальная версия ОС узла перед выбором репозитория — ZABBIX-AGENT-PVE-NODES-2026-001
# Версию проверять, а не предполагать: репозиторий Zabbix для другого выпуска Debian даёт
# конфликт зависимостей
cat /etc/os-release
```

```bash
# [W] Поставить zabbix-agent из штатного репозитория Debian (по порядку) —
# ZABBIX-AGENT-PVE-NODES-2026-001. Сторонний репозиторий Zabbix для другого выпуска Debian
# не добавлять (конфликт libldap)
apt remove --purge -y zabbix-release
apt update
apt install -y zabbix-agent
```

```bash
# [R] Текущий формат строк Server и ServerActive в конфиге агента — ZABBIX-AGENT-PVE-NODES-2026-001
# Смотреть до замены: строка может быть закомментирована или иметь другое значение
grep -E "^Server=|^ServerActive=|^#\s*Server=|^#\s*ServerActive=" /etc/zabbix/zabbix_agentd.conf
```

```bash
# [W] Указать сервер Zabbix в конфиге агента (по порядку) — ZABBIX-AGENT-PVE-NODES-2026-001
# Результат проверять grep в последней строке, не по отсутствию ошибки у sed
sed -i 's/^#\?\s*Server=.*/Server=<адрес_zabbix>/' /etc/zabbix/zabbix_agentd.conf
sed -i 's/^#\?\s*ServerActive=.*/ServerActive=<адрес_zabbix>/' /etc/zabbix/zabbix_agentd.conf
systemctl restart zabbix-agent
systemctl enable zabbix-agent
grep -E "^Server=|^ServerActive=" /etc/zabbix/zabbix_agentd.conf
```

```bash
# [R] Проверка агента — ZABBIX-AGENT-PVE-NODES-2026-001
# Зелёный ZBX-индикатор подтверждает связь, но не то, что собираются полезные данные
zabbix_agentd -V
systemctl status zabbix-agent
grep "connected to" /var/log/zabbix/zabbix_agentd.log | tail -3
```

```bash
# [R] Память в LXC: free и /proc/meminfo против zabbix_get — ZABBIX-LXC-FALSE-ALERTS-2026-001
# vm.memory.size[*] в LXC возвращает память физического хоста, а не лимит контейнера
free -h
cat /proc/meminfo
zabbix_get -s 127.0.0.1 -k vm.memory.size[total]
```

```bash
# [W] Кастомные ключи памяти для LXC поверх /proc/meminfo (по порядку) — ZABBIX-LXC-FALSE-ALERTS-2026-001
# Унаследованные от шаблона элементы на vm.memory.size[*] отключать на уровне хоста в Zabbix
mkdir -p /etc/zabbix/zabbix_agentd.d
cat << 'EOF' > /etc/zabbix/zabbix_agentd.d/lxc_memory.conf
UserParameter=custom.linux.memory.pavailable,awk '/MemTotal/ {t=$2} /MemAvailable/ {a=$2} END {printf "%.2f", (a/t)*100}' /proc/meminfo
UserParameter=custom.linux.memory.pused,awk '/MemTotal/ {t=$2} /MemAvailable/ {a=$2} END {printf "%.2f", 100-(a/t)*100}' /proc/meminfo
EOF
systemctl restart zabbix-agent
zabbix_get -s 127.0.0.1 -k custom.linux.memory.pavailable
```

```bash
# [R] Загрузка: реальная нагрузка или шторм переключений контекста — ZABBIX-LXC-FALSE-ALERTS-2026-001
# Сотни тысяч переключений контекста (cs) в секунду при 100% idle — признак шторма
vmstat 1 5
```

```bash
# [W] Сбросить кэш конфигурации после правки имени хоста в Zabbix (по порядку) — ZABBIX-LXC-FALSE-ALERTS-2026-001
# После перезапуска ожидать разрыв сбора метрик на 5–15 секунд — это не новый инцидент
systemctl restart zabbix-server
tail -n 30 /var/log/zabbix/zabbix_server.log | grep "not found"
```

```bash
# [R] Состояние интерфейса — ZABBIX-LXC-FALSE-ALERTS-2026-001
# Чтение /sys/class/net/<интерфейс>/speed у интерфейса в состоянии DOWN даёт Invalid argument —
# это поведение ядра, а не агента
ip -details link show <интерфейс>
```

## 9. Диски под Ceph OSD

Порядок подготовки: проверить время, осмотреть диск, очистить, проверить результат.
Очистка диска — класс [D]. Создание самих OSD и пулов в источнике выполняется через
веб-интерфейс (Datacenter → Ceph → OSD / Pools) и сюда не входит.

```bash
# [R] Синхронизация времени перед созданием OSD — PROXMOX-CEPH-OSD-DISK-PREP-2026-001
# Критична для Ceph: рассинхронизация времени ломает кворум. Проверять на обоих узлах;
# ожидается малое смещение (в документе — меньше 1 мс)
chronyc tracking
```

```bash
# [R] Состояние дисков до создания OSD и после очистки — PROXMOX-CEPH-OSD-DISK-PREP-2026-001
# Именно lsblk -f: без -f не видны FSTYPE и UUID остаточных файловых систем, и грязный диск
# можно принять за чистый. После очистки ожидается пусто (без FSTYPE, UUID и MOUNTPOINTS)
lsblk -d -o NAME,SIZE,MODEL,TYPE,MOUNTPOINT
lsblk -f /dev/<диск1> /dev/<диск2>
```

```bash
# [D] REQUIRES_APPROVAL — очистить диск перед созданием OSD (по порядку) — PROXMOX-CEPH-OSD-DISK-PREP-2026-001
# Безвозвратно удаляет все данные на устройстве. Только по явному подтверждению администратора.
# Имя устройства брать из свежего вывода lsblk, не из документов; системный диск и любой диск
# с нужными данными не использовать. wipefs -a убирает сигнатуры файловых систем,
# sgdisk --zap-all — таблицу GPT, включая резервную копию GPT в конце диска
wipefs -a /dev/<диск>
sgdisk --zap-all /dev/<диск>
```

```bash
# [W] Установить gdisk (даёт sgdisk), если команды нет; partprobe — если ядро не сразу увидело
# изменения после очистки (варианты, не по порядку) — PROXMOX-CEPH-OSD-DISK-PREP-2026-001
apt install gdisk
partprobe
```

## 10. Active Directory: контроллер домена (PowerShell, внутри ВМ)

Домен, сайт и имена серверов — плейсхолдеры. Удаление осиротевшего объекта сервера в AD
после неудачной промоции (`Get-ADObject`, `Remove-ADObject`) в источнике описано без
полных команд и сюда не вошло: смотреть `PROXMOX-AD-THIRD-DC-PROMOTION-2026-001`.

```powershell
# [R] Остатки прерванной промоции перед повторным запуском — PROXMOX-AD-THIRD-DC-PROMOTION-2026-001
# Ожидается: False, пусто, пусто. Повторять Install-ADDSDomainController, не проверив и не очистив
# артефакты (файлы NTDS, DSA Database Epoch в реестре, осиротевший объект сервера в AD), нельзя
Test-Path C:\Windows\NTDS\ntds.dit
Get-ChildItem C:\Windows\NTDS -Force -ErrorAction SilentlyContinue
Get-ItemProperty 'HKLM:\System\CurrentControlSet\Services\NTDS\Parameters' -Name 'DSA Database Epoch' -ErrorAction SilentlyContinue
```

```powershell
# [W] Повысить сервер до контроллера домена — PROXMOX-AD-THIRD-DC-PROMOTION-2026-001
# Не прерывать (Ctrl+C / Ctrl+Z): команда может молчать 5–15 минут. Пароль DSRM вводится
# интерактивно, в команде и в файлах репозитория его нет
Install-ADDSDomainController `
  -DomainName "<домен>" `
  -Credential (Get-Credential) `
  -SiteName "<сайт>" `
  -InstallDns:$true `
  -NoGlobalCatalog:$false `
  -ReplicationSourceDC "<FQDN_работающего_DC>" `
  -DatabasePath "C:\Windows\NTDS" `
  -LogPath "C:\Windows\NTDS" `
  -SysvolPath "C:\Windows\SYSVOL" `
  -SafeModeAdministratorPassword (Read-Host -AsSecureString "Введите пароль DSRM") `
  -Confirm:$false
```

```powershell
# [R] Что делает процесс при «зависшей» промоции — из второй, отдельной сессии, не трогая окно
# PROXMOX-AD-THIRD-DC-PROMOTION-2026-001
# Процесс, нагружающий CPU, означает, что DCPromo не завершился (причина не обязательно QuickEdit)
Get-Process powershell
```

```powershell
# [D] REQUIRES_APPROVAL — принудительно завершить зависший процесс DCPromo — PROXMOX-AD-THIRD-DC-PROMOTION-2026-001
# Прерывает промоцию посреди работы; файлы C:\Windows\NTDS (ntds.dit, edb.log) могут остаться
# заблокированными движком ESE до перезагрузки сервера, дальше нужна очистка артефактов (проверка выше).
# Только по явному подтверждению администратора; PID брать из свежего вывода Get-Process
Stop-Process -Id <PID> -Force
Get-Process powershell
```

```powershell
# [W] Перезагрузить сервер, чтобы снять блокировку файлов NTDS после остановки процесса
# PROXMOX-AD-THIRD-DC-PROMOTION-2026-001
# Прерывает всю работу сервера
Restart-Computer -Force
```

```powershell
# [R] Репликация и здоровье AD после промоции — PROXMOX-AD-THIRD-DC-PROMOTION-2026-001
# Нормой в источнике считалось: 0 сбоев по партнёрам, ключевые тесты dcdiag PASS
repadmin /replsummary
repadmin /showrepl
Get-ADDomainController -Filter *
dcdiag /v /c
```

```powershell
# [R] Тесты, зависящие от SYSVOL — PROXMOX-AD-THIRD-DC-PROMOTION-2026-001
# Сразу после промоции Advertising и NetLogons могут не проходить, пока SYSVOL (DFSR) в состоянии
# Initializing (State=2): ждать завершения DFSR (State=4 и событие 4114), это не отдельная поломка
dcdiag /test:Advertising
dcdiag /test:NetLogons
```

```powershell
# [W] Ускорить начальную синхронизацию SYSVOL (DFSR) (по порядку) — PROXMOX-AD-THIRD-DC-PROMOTION-2026-001
Install-WindowsFeature RSAT-DFS-Mgmt-Con
dfsrdiag pollad
```

```powershell
# [R] Очередь репликации SYSVOL — PROXMOX-AD-THIRD-DC-PROMOTION-2026-001
# Конечное и убывающее число файлов (в источнике — 99) означает, что DFSR работает, а не завис
dfsrdiag backlog /rgname:"Domain System Volume" /rfname:"SYSVOL Share" /smem:<DC_источник> /rmem:<этот_DC>
```

## 11. RDS: терминальный сервер и лицензирование (PowerShell, внутри ВМ)

Блоки выполняются на сервере сеансов (TC) и на сервере лицензий (контроллер домена). Имена
серверов, домен и группы — плейсхолдеры. В командлетах RDS использовать полный FQDN, не
короткое имя. Роль RDS-Licensing и активация сервера лицензий не заменяют покупку RDS CAL;
срок льготного периода — в `PROXMOX-RDS-2003-2026-001`.

```powershell
# [W] Установить роль Session Host на сервере сеансов — PROXMOX-RDS-2003-2026-001
Install-WindowsFeature -Name RDS-RD-Server -IncludeManagementTools
Get-WindowsFeature -Name RDS-RD-Server
```

```powershell
# [W] Создать RDS Deployment и коллекцию сеансов (по порядку) — PROXMOX-RDS-2003-2026-001
# Connection Broker и Session Host — один сервер; только полный FQDN, не короткое имя
New-RDSessionDeployment -ConnectionBroker "<FQDN_TC>" -SessionHost "<FQDN_TC>"
Get-RDServer
New-RDSessionCollection -CollectionName "<коллекция>" -SessionHost "<FQDN_TC>" -ConnectionBroker "<FQDN_TC>"
Get-RDSessionCollection -ConnectionBroker "<FQDN_TC>"
```

```powershell
# [W] Разрешить RDP-подключение доменной группе — PROXMOX-RDS-2003-2026-001
# Grant-RDAccess в этой среде отсутствует — использовать Add-LocalGroupMember.
# Не выдавать доступ всем пользователям домена в production без отдельного подтверждения
# требований безопасности
Add-LocalGroupMember -Group "Remote Desktop Users" -Member "<ДОМЕН>\<группа>"
Get-LocalGroupMember -Group "Remote Desktop Users"
```

```powershell
# [W] Установить роль сервера лицензий — на контроллере домена, не на сервере сеансов
# PROXMOX-RDS-2003-2026-001
# Активация сервера лицензий — мастером в «Диспетчере лицензирования удалённых рабочих столов»
# (ярлык или полный путь: lsmgr.exe как команда может не находиться на Windows Server 2022/2025)
Install-WindowsFeature -Name RDS-Licensing -IncludeManagementTools
```

```powershell
# [W] Режим лицензирования и сервер лицензий — PROXMOX-RDS-2003-2026-001
# Параметры -LicensingMode и -LicenseServer есть у Set-RDSessionDeployment, а НЕ у
# Set-RDSessionCollectionConfiguration (тот вернёт «не удаётся найти параметр»)
Set-RDSessionDeployment -ConnectionBroker "<FQDN_TC>" -LicensingMode "PerUser" -LicenseServer "<FQDN_сервера_лицензий>"
Get-RDSessionDeployment -ConnectionBroker "<FQDN_TC>" | Select-Object LicensingMode, LicenseServer
```

```powershell
# [R] Что записано в реестре о лицензировании — PROXMOX-RDS-2003-2026-001
# LicensingMode: 4 означает Per User. Запись в реестре применяется только после перезапуска TermService
Get-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\Terminal Server\RCM\Licensing Core" | Select-Object LicenseServers, LicensingMode
```

```powershell
# [W] Перезапустить TermService, чтобы подхватить параметры лицензирования (по порядку)
# PROXMOX-RDS-2003-2026-001
# Служба кэширует эти значения при старте. Перезапуск службы удалённых рабочих столов разрывает
# текущие RDP-сеансы (замечание не из источника) — выполнять вне рабочего времени
Restart-Service -Name TermService -Force
Set-Service -Name TermService -StartupType Automatic
Get-Service -Name TermService | Select-Object Status, StartType
```

```powershell
# [W] Вернуть тип запуска TermService в ручной (откат только типа запуска) — PROXMOX-RDS-2003-2026-001
Set-Service -Name TermService -StartupType Manual
```

## 12. USB-ключ (HASP) в ВМ

```bash
# [R] Какое USB-устройство проброшено в ВМ и что есть на хосте — PROXMOX-VM2001-USB-HASP-2026-001
# Список USB в GUI Proxmox не считать достаточным: сверять Vendor:Device ID через lsusb.
# Встроенный KVM/IPMI-контроллер сервера Huawei 2288H V5 (12d1:0003) — служебное устройство,
# не ключ защиты
qm config <VMID> | grep usb
lsusb
```

```bash
# [W] Пробросить USB-устройство в ВМ по Vendor:Device ID — PROXMOX-VM2001-USB-HASP-2026-001
# ID брать из свежего вывода lsusb. Для работающей ВМ изменение применяется только после её
# перезагрузки. Откат — вернуть прежнее значение usb0; в источнике прежним был служебный
# KVM-контроллер, возвращать который в ВМ не нужно
qm set <VMID> --usb0 host=<VendorID>:<DeviceID>
qm config <VMID> | grep usb
```

## 13. Vaultwarden (LXC)

Контейнер, имена, адреса и пароли — плейсхолдеры. Хеш `ADMIN_TOKEN` и сам токен в репозиторий и
чаты не вносить. Без HTTPS страница входа Vaultwarden не заработает (браузеры блокируют Web
Crypto API на обычном HTTP), поэтому после установки нужен обратный прокси (Caddy, ниже).

```bash
# [W] Создать контейнер из шаблона LXC (по порядку) — PROXMOX-VAULTWARDEN-INSTALL-2026-001
# Только --full: по умолчанию клон шаблона получается linked. Production-контейнеры в этой
# инфраструктуре — на ceph-fast. --net0 в pct clone не принимается: сеть отдельной командой pct set
pct clone <TEMPLATE_CTID> <CTID> --hostname <имя> --storage ceph-fast --full
pct set <CTID> --net0 name=eth0,bridge=vmbr0,ip=<IP>/<маска>,gw=<шлюз>
pct start <CTID>
```

```bash
# [W] Передать .deb-пакеты Vaultwarden и Web-Vault в контейнер и установить (по порядку)
# PROXMOX-VAULTWARDEN-INSTALL-2026-001
# apt-репозиторий и прямая загрузка пакетов с vaultwarden-deb.pages.dev с сервера недоступны (блокировка
# HTTPS к Cloudflare Pages на уровне шлюза). Обход: скачать пакеты на локальном ПК, переименовать в .iso
# (веб-интерфейс Proxmox фильтрует загрузку по расширению), загрузить через local → ISO Images → Upload.
# Версии должны быть совместимы: для Vaultwarden 1.37.2 источник называет рабочим Web-Vault v2025.12.2,
# а не v2026.7.0
pct push <CTID> /var/lib/vz/template/iso/<vaultwarden>.deb.iso /tmp/vaultwarden.deb
pct push <CTID> /var/lib/vz/template/iso/<vaultwarden-web-vault>.deb.iso /tmp/vaultwarden-web-vault.deb
pct exec <CTID> -- dpkg -i /tmp/vaultwarden-web-vault.deb /tmp/vaultwarden.deb
pct exec <CTID> -- apt --fix-broken install -y
```

```bash
# [W] Путь к Web-Vault и адрес прослушивания (по порядку) — PROXMOX-VAULTWARDEN-INSTALL-2026-001
# Пакет ставит Web-Vault в /usr/share/vaultwarden/web-vault, а не в /var/lib/vaultwarden
pct exec <CTID> -- bash -c "echo -e '\nROCKET_ADDRESS=0.0.0.0\nWEB_VAULT_FOLDER=/usr/share/vaultwarden/web-vault' >> /etc/vaultwarden.env"
pct exec <CTID> -- systemctl restart vaultwarden
```

```bash
# [R] Получить Argon2id-хеш для ADMIN_TOKEN — PROXMOX-VAULTWARDEN-INSTALL-2026-001
# Текстовый ADMIN_TOKEN Vaultwarden не принимает, нужен хеш Argon2id. Команда vaultwarden hash
# предпочтительнее ручной связки openssl + argon2 (она в источнике описана). Пароль вводится
# интерактивно; хеш вписать в /etc/vaultwarden.env как ADMIN_TOKEN=<хеш> — подробности про $ в следующем блоке
pct exec <CTID> -- vaultwarden hash
```

```bash
# [W] Исправить удвоенные $ в ADMIN_TOKEN (по порядку) — PROXMOX-VAULTWARDEN-ADMIN-TOKEN-2026-001
# /etc/vaultwarden.env подключён как EnvironmentFile=, он читает файл буквально: значение — одинарные $,
# без кавычек и без удвоения $$ (удвоение относится к Environment= в .service-файле и ломает токен).
# Вывод grep содержит хеш токена — не копировать в документы и чаты
sed -i '/^ADMIN_TOKEN=/ s/\$\$/\$/g' /etc/vaultwarden.env
grep '^ADMIN_TOKEN=' /etc/vaultwarden.env
systemctl restart vaultwarden
```

```bash
# [R] Что реально получил процесс Vaultwarden — PROXMOX-VAULTWARDEN-ADMIN-TOKEN-2026-001
# Однозначная проверка вместо догадок: config.json имеет приоритет над EnvironmentFile; в выводе
# systemctl show пустое Environment= для EnvironmentFile ожидаемо. Вывод последней команды содержит
# хеш токена — не копировать в документы и чаты
grep -i "admin_token" /var/lib/vaultwarden/data/config.json
systemctl show vaultwarden --property=Environment
cat /proc/<PID>/environ | tr '\0' '\n' | grep -i admin_token
```

```bash
# [R] Состояние Vaultwarden — PROXMOX-VAULTWARDEN-INSTALL-2026-001
# Ожидается: Active: active (running), Rocket has launched, HTTP/1.1 200 OK, без строк ERROR
pct exec <CTID> -- systemctl status vaultwarden --no-pager -l | grep -E 'Active:|Rocket has launched|ERROR'
pct exec <CTID> -- curl -s -I http://127.0.0.1:8000
```

```bash
# [D] REQUIRES_APPROVAL — откат Web-Vault при ошибке смены мастер-пароля (по порядку) — PROXMOX-VAULTWARDEN-ADMIN-TOKEN-2026-001
# Ошибка 422 / «missing field newMasterPasswordHash»: новая версия Web-Vault несовместима с версией
# Vaultwarden. Сначала смотреть логи на конкретный код ошибки, не переходить к деструктивному сбросу
# пароля. rm -rf удаляет Web-Vault; без установки нужной версии (команда в источнике не приведена)
# веб-интерфейс не заработает — .deb нужной версии должен быть под рукой
systemctl stop vaultwarden
rm -rf /usr/share/vaultwarden/web-vault
# установить Web-Vault нужной версии (в источнике — v2025.12.2)
systemctl start vaultwarden
```

```bash
# [W] Установить Caddy из официального репозитория (по порядку) — PROXMOX-VAULTWARDEN-HTTPS-CADDY-2026-001
# Команда добавления репозитория Caddy stable в источнике не приведена — подставить по документации Caddy
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https curl
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
# добавить репозиторий Caddy stable, затем:
sudo apt update && sudo apt install -y caddy
```

```caddy
# [W] /etc/caddy/Caddyfile — обратный прокси с TLS на внутренний Vaultwarden — PROXMOX-VAULTWARDEN-HTTPS-CADDY-2026-001
# tls internal: сертификат от внутреннего CA Caddy (нет публичного домена и DNS) — осознанный выбор,
# а не временное решение; браузер предупреждает о недоверенном сертификате, пока корневой
# сертификат не установлен на клиенте
<адрес_vaultwarden>, <имя_vaultwarden> {
    tls internal

    reverse_proxy 127.0.0.1:8000 {
        header_up Host {host}
        header_up X-Real-IP {remote_host}
        header_up X-Forwarded-For {remote_host}
        header_up X-Forwarded-Proto {scheme}
    }
}
```

```bash
# [W] Применить конфигурацию Caddy (варианты, не по порядку) — PROXMOX-VAULTWARDEN-HTTPS-CADDY-2026-001
sudo systemctl restart caddy    # при первой установке
sudo systemctl reload caddy     # при последующих правках Caddyfile — без разрыва соединений
```

```bash
# [R] Проверка HTTPS — PROXMOX-VAULTWARDEN-HTTPS-CADDY-2026-001
# Ожидается: TLS 1.3, HTTP/2 200, server: Rocket, via: 1.1 Caddy. -k отключает проверку сертификата.
# subject: [NONE] в выводе — особенность curl для сертификатов только с SAN, не ошибка
curl -kvI https://<адрес_vaultwarden>
```

```bash
# [D] REQUIRES_APPROVAL — удалить Caddy (откат) (по порядку) — PROXMOX-VAULTWARDEN-HTTPS-CADDY-2026-001
# Обратный прокси перестанет работать: веб-интерфейс Vaultwarden по HTTPS станет недоступен
sudo apt remove --purge caddy
sudo rm /etc/apt/sources.list.d/caddy-stable.list
```

```bash
# [R] Корневой сертификат Caddy для установки на клиентские машины — PROXMOX-VAULTWARDEN-USERS-2026-001
# Нужен именно корневой (root.crt), не промежуточный: промежуточный действует около 12 часов,
# и доверие быстро истечёт. Скопировать вывод целиком (BEGIN/END CERTIFICATE) в файл на клиенте
cat /var/lib/caddy/.local/share/caddy/pki/authorities/local/root.crt
```

```bash
# [R] Срок действия сертификата, который отдаёт сервер — PROXMOX-VAULTWARDEN-USERS-2026-001
echo | openssl s_client -connect <адрес_vaultwarden>:443 2>/dev/null | openssl x509 -noout -dates
```

## 14. Шаблоны: Windows Server 2022 и Debian 12 LXC

Имена, ID, образы и адреса — плейсхолдеры. Для ВМ и для контейнеров используются разные
команды: `qm` управляет ВМ (KVM/QEMU), `pct` — контейнерами (LXC); путь конфигурации
(`qemu-server/` или `lxc/`) однозначно показывает тип объекта.

```bash
# [W] Создать базовую ВМ под шаблон Windows Server 2022 — PROXMOX-WINSRV2022-TEMPLATE-2026-001
# Параметры обязательны: machine=q35 (не i440fx), bios=ovmf (UEFI), scsihw=virtio-scsi-single
# (не IDE/SATA), сеть virtio (не E1000/Realtek). Виртуальный TPM обязателен: без него установка
# Windows Server 2022 не пройдёт. На этапе выбора диска подключить драйвер VirtIO SCSI с virtio-win.iso
qm create <VMID> --name "<имя_шаблона>" --memory 4096 --cores 4 --cpu host \
  --machine q35 --bios ovmf --ostype win11 \
  --scsihw virtio-scsi-single \
  --scsi0 ceph-fast:100,iothread=1,discard=on,ssd=1 \
  --ide2 local:iso/<ISO_Windows>,media=cdrom \
  --ide3 local:iso/<ISO_virtio-win>,media=cdrom \
  --net0 virtio,bridge=vmbr0 \
  --boot order=ide2 \
  --tpmstate0 ceph-fast:version=v2.0
```

```bash
# [W] Включить QEMU Guest Agent после установки драйверов — PROXMOX-WINSRV2022-TEMPLATE-2026-001
# Внутри гостя убедиться, что служба QEMU Guest Agent запущена
qm set <VMID> --agent enabled=1,fstrim_cloned_disks=1
```

```powershell
# [W] Включить RDP внутри гостя (по умолчанию выключен) — PROXMOX-WINSRV2022-TEMPLATE-2026-001
Set-ItemProperty -Path 'HKLM:\System\CurrentControlSet\Control\Terminal Server' -Name "fDenyTSConnections" -Value 0
Enable-NetFirewallRule -DisplayGroup "Remote Desktop"
```

```powershell
# [R] Диагностика RDP, если не помогло — PROXMOX-WINSRV2022-TEMPLATE-2026-001
# В ipconfig: реальный IP или APIPA 169.254.x.x (DHCP не сработал)
ipconfig
Get-NetFirewallRule -DisplayGroup "Remote Desktop"
```

```powershell
# [D] REQUIRES_APPROVAL — Sysprep перед превращением ВМ в шаблон — PROXMOX-WINSRV2022-TEMPLATE-2026-001
# Только для ВМ, которая готовится стать шаблоном: обобщение меняет идентичность системы (SID),
# на рабочей ВМ не запускать. Это исполняемый файл, не командлет PowerShell: вызывать по полному пути.
# В окне: «Переход в OOBE»; галочка «Подготовка к использованию» (Generalize) ОБЯЗАТЕЛЬНА (без неё SID
# не обобщается, клоны конфликтуют в AD); завершение — «Завершение работы», не «Перезагрузка»
# (перезагрузка запускает OOBE и портит шаблон)
& 'C:\Windows\System32\Sysprep\sysprep.exe'
```

```bash
# [W] Остановить ВМ, превратить в шаблон и клонировать (по порядку) — PROXMOX-WINSRV2022-TEMPLATE-2026-001
# --full 1 обязателен: без него получается linked clone, зависящий от диска исходного шаблона,
# и исходный шаблон потом нельзя удалить (base volume ... is still in use by linked clone)
qm stop <VMID>
qm template <VMID>
qm clone <VMID> <NEW_VMID> --name "<имя>" --full 1
```

```bash
# [R] Шаблон это или клон, и какого типа — PROXMOX-WINSRV2022-TEMPLATE-2026-001
# template: 1 — шаблон: его нельзя запускать, только клонировать. Проверять тип клона перед
# удалением исходного шаблона
qm config <VMID> | grep -E "(template|clone)"
```

```bash
# [D] REQUIRES_APPROVAL — удалить ВМ вместе с неиспользуемыми дисками — PROXMOX-WINSRV2022-TEMPLATE-2026-001
# Безвозвратно. В источнике: ошибочно созданный linked clone удалялся и пересоздавался как full clone,
# и только после этого удалялся исходный шаблон. Исходный шаблон не удалять, пока клон не проверен
# как full clone (блок выше)
qm destroy <VMID> --destroy-unreferenced-disks --purge
```

```bash
# [R] Шаблон Debian 12 для LXC на месте — PROXMOX-LXC-DEBIAN12-TEMPLATE-2026-001
ls /var/lib/vz/template/cache/
```

```bash
# [W] Создать контейнер-заготовку под шаблон Debian 12 — PROXMOX-LXC-DEBIAN12-TEMPLATE-2026-001
# Корневой диск — только --rootfs, не --disk (иначе Unknown option: disk)
pct create <CTID> local:vztmpl/<образ_debian12>.tar.zst \
  --rootfs ceph-fast:100 \
  --memory 4096 --cores 2 \
  --net0 name=eth0,bridge=vmbr0 \
  --hostname <имя> --unprivileged 1
```

```bash
# [W] Автозапуск eth0 внутри контейнера (по порядку) — PROXMOX-LXC-DEBIAN12-TEMPLATE-2026-001
# В образе /etc/network/interfaces содержит только lo: eth0 после перезагрузки сам не поднимается
pct exec <CTID> -- bash -c "echo -e '\nauto eth0\niface eth0 inet dhcp' >> /etc/network/interfaces"
pct reboot <CTID>
pct exec <CTID> -- ip -4 addr show eth0
```

```bash
# [W] Временный статический IP для проверки перед шаблонированием — PROXMOX-LXC-DEBIAN12-TEMPLATE-2026-001
pct set <CTID> --net0 name=eth0,bridge=vmbr0,ip=<IP>/<маска>,gw=<шлюз>
```

```bash
# [W] Подготовить контейнер и создать шаблон (по порядку) — PROXMOX-LXC-DEBIAN12-TEMPLATE-2026-001
# Контейнер должен быть остановлен. Статический IP и gateway убрать из net0: иначе все клоны получат
# один и тот же адрес. pct template необратим в рамках этого ID: контейнер после этого предназначен
# только для клонирования
pct shutdown <CTID>
pct set <CTID> --net0 name=eth0,bridge=vmbr0
pct config <CTID> | grep net0
pct template <CTID>
```

```bash
# [W] Клонировать контейнер из шаблона и задать сеть отдельной командой (по порядку)
# PROXMOX-LXC-DEBIAN12-TEMPLATE-2026-001
# --net0 в pct clone не принимается (Unknown option: net0): сначала клон без сетевых параметров,
# затем pct set. Для production-контейнеров добавлять --full и --storage ceph-fast, иначе клон
# шаблона будет linked (PROXMOX-VAULTWARDEN-INSTALL-2026-001). Успешный pct clone не подтверждает
# рабочую сеть клона — проверять отдельно
pct clone <TEMPLATE_CTID> <NEW_CTID> --hostname <новое_имя>
pct set <NEW_CTID> --net0 name=eth0,bridge=vmbr0,ip=<IP>/<маска>,gw=<шлюз>
pct start <NEW_CTID>
```

```bash
# [W] Сменить имя или описание контейнера, не трогая ID — PROXMOX-LXC-DEBIAN12-TEMPLATE-2026-001
# Прямой команды смены VMID в Proxmox нет
pct set <CTID> --hostname <имя> --description "<описание>"
```

```bash
# [W] Сменить VMID: резервная копия, затем восстановление с новым ID — PROXMOX-LXC-DEBIAN12-TEMPLATE-2026-001
# Это единственный поддерживаемый способ (в том числе для дисков на Ceph RBD). Восстановление
# выполняется через GUI или pct restore / qmrestore (в источнике без параметров)
vzdump <старый_id> --mode snapshot --storage local
```

```bash
# [W] Свежий клон: SSH «доступ запрещён» — зайти с узла и разрешить root по паролю — PROXMOX-LXC-DEBIAN12-TEMPLATE-2026-001
# Debian по умолчанию не пускает root по паролю (PermitRootLogin prohibit-password). Это ослабляет
# защиту SSH; оставлять ли так — отдельное решение (замечание не из источника)
pct start <CTID>
pct enter <CTID>
sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config && systemctl restart ssh
```

```bash
# [W] apt возвращает 404 на пакетах — обновить устаревший кэш списков в образе шаблона
# PROXMOX-LXC-DEBIAN12-TEMPLATE-2026-001
apt-get update
```

```bash
# [W] SSH зависает на новом клоне из-за обратного DNS: прописать UseDNS no с узла
# PROXMOX-LXC-DEBIAN12-TEMPLATE-2026-001
# Не путать с зависанием из-за pam_systemd (другая причина, LINUX-SSH-PAM-SYSTEMD-ZABBIX-2026-001)
pct exec <CTID> -- bash -c "echo 'UseDNS no' >> /etc/ssh/sshd_config && systemctl restart ssh"
```

## 15. SSH на Debian и в LXC: доступ, статический IP, pam_systemd

Адреса, интерфейсы и имена — плейсхолдеры. Блоки общие, не привязаны к конкретному узлу.

```bash
# [R] Какой адрес у хоста — LINUX-SSH-DEBIAN-ACCESS-2026-001
# Брать значение после inet, а не brd: адрес X.X.X.255 при маске /24 — broadcast, не хост
# (на него SSH даёт «Cannot assign requested address»)
hostname -I
ip -br addr
```

```bash
# [R] Если SSH всё равно не подключается — LINUX-SSH-DEBIAN-ACCESS-2026-001
# Также проверить, что клиент в той же подсети. Для ВМ в VirtualBox/VMware адаптер должен быть
# в режиме Bridge/Host-only (при NAT нужен проброс порта 22)
sudo systemctl status ssh
ss -tln | grep :22
sudo ufw status
sudo iptables -L -n
```

```bash
# [W] «Access denied» под root, вариант 1: разрешить вход root по паролю (по порядку)
# LINUX-SSH-DEBIAN-ACCESS-2026-001
# Годится для лаборатории. По умолчанию в Debian PermitRootLogin prohibit-password: root пускает только
# по ключу. В sshd_config поставить PermitRootLogin yes и PasswordAuthentication yes. Не отключать
# PasswordAuthentication до подтверждённого входа по ключу. Менять порт SSH — только вместе с правилами брандмауэра
sudo passwd root                    # если у root ещё нет пароля
sudo nano /etc/ssh/sshd_config
sudo systemctl restart ssh
```

```bash
# [W] «Access denied» под root, вариант 2: вход root только по ключу (правильнее для production)
# LINUX-SSH-DEBIAN-ACCESS-2026-001
# Права обязательны: 700 на ~/.ssh и 600 на authorized_keys. Вместо примера подставить свой открытый ключ
# целиком. tee без -a перезаписывает файл: существующие ключи будут потеряны (замечание не из источника)
sudo mkdir -p /root/.ssh && sudo chmod 700 /root/.ssh
echo "<открытый_ключ>" | sudo tee /root/.ssh/authorized_keys
sudo chmod 600 /root/.ssh/authorized_keys
```

```bash
# [R] Применилась ли настройка и почему отказ — LINUX-SSH-DEBIAN-ACCESS-2026-001
# sshd -T должен показать permitrootlogin yes; если остался prohibit-password — в конфиге есть
# дублирующая строка выше по файлу (первая имеет приоритет)
sudo sshd -T | grep -i permitroot
ssh -v root@<хост>
sudo journalctl -u ssh -n 20
```

```bash
# [R] Текущие параметры сети перед переводом с DHCP на статический IP — LINUX-SSH-DEBIAN-ACCESS-2026-001
# default via ... в выводе ip route — шлюз
ip -br addr
ip route
```

```bash
# [W] Статический IP через /etc/network/interfaces — LINUX-SSH-DEBIAN-ACCESS-2026-001
# Текущая SSH-сессия при применении отвалится: переподключаться на новый адрес, иметь консоль.
# Адрес брать вне диапазона DHCP роутера, не .0 и не .255. Вместо строк allow-hotplug / iface ... dhcp:
#   auto <интерфейс>
#   iface <интерфейс> inet static
#       address <IP>/<маска>
#       gateway <шлюз>
#       dns-nameservers <DNS1> <DNS2>
sudo nano /etc/network/interfaces
sudo systemctl restart networking    # или: ifdown <интерфейс> && ifup <интерфейс>
```

```bash
# [W] Статический IP через NetworkManager (по порядку) — LINUX-SSH-DEBIAN-ACCESS-2026-001
# В nmtui: Edit a connection, IPv4 CONFIGURATION: Automatic заменить на Manual, затем Addresses, Gateway, DNS
sudo nmtui
sudo nmcli con up <имя_соединения>
```

```bash
# [R] Проверка после смены адреса — LINUX-SSH-DEBIAN-ACCESS-2026-001
# Если пропал DNS (пакет resolvconf установлен не всегда), прописать его вручную в /etc/resolv.conf
ip -br addr
ping -c 3 <шлюз>
ping -c 3 <имя_внешнего_хоста>
```

```bash
# [R] Диагностика задержки SSH после успешной аутентификации в LXC — LINUX-SSH-PAM-SYSTEMD-ZABBIX-2026-001
# Сначала исключить UseDNS и GSSAPI (если пауза уже после аутентификации, дело не в них) и
# убедиться, что неинтерактивная команда быстрая. -o StrictHostKeyChecking=no отключает проверку
# ключа хоста — только в доверенной сети
grep -E "^(UseDNS|GSSAPIAuthentication|GSSAPICleanupCredentials|UsePAM)" /etc/ssh/sshd_config
ssh -v root@<адрес>      # где пауза: после «Entering interactive session»?
ssh -o StrictHostKeyChecking=no root@<адрес> "echo NON_INTERACTIVE_TEST && date"
ls -la /etc/update-motd.d/; tail -30 /root/.bashrc; cat /root/.profile
```

```bash
# [R] Ключевой шаг: состояние systemd-logind внутри контейнера — LINUX-SSH-PAM-SYSTEMD-ZABBIX-2026-001
# Признак: failed, status=226/NAMESPACE; в журнале «Failed to set up mount namespacing ... Permission denied»;
# в common-session строка «session optional pam_systemd.so»
systemctl status systemd-logind --no-pager -l
journalctl -u systemd-logind --no-pager -n 20
cat /etc/pam.d/common-session
```

```bash
# [W] Закомментировать pam_systemd.so (команда идемпотентна) — LINUX-SSH-PAM-SYSTEMD-ZABBIX-2026-001
# Только для LXC с подтверждённой ошибкой 226/NAMESPACE у systemd-logind. Не переносить на ВМ и
# физические серверы и не применять массово без подтверждения той же причины. Устраняет симптом,
# не причину. Правку может перезаписать pam-auth-update: проверять файл после обновлений пакетов
sed -i 's/^\([[:space:]]*session[[:space:]]\+optional[[:space:]]\+pam_systemd\.so\)/# \1/' /etc/pam.d/common-session
```

```bash
# [R] Проверка результата — LINUX-SSH-PAM-SYSTEMD-ZABBIX-2026-001
# Строка должна быть закомментирована; вход без минутной задержки, неинтерактивная команда по-прежнему быстрая
grep -n "pam_systemd" /etc/pam.d/common-session
time ssh root@<адрес>
time ssh root@<адрес> "echo OK && date"
```

```bash
# [W] Откат: раскомментировать pam_systemd.so — LINUX-SSH-PAM-SYSTEMD-ZABBIX-2026-001
# Не откатывать, пока systemd-logind падает с 226/NAMESPACE: задержка вернётся сразу
sed -i 's/^#[[:space:]]*\(session[[:space:]]\+optional[[:space:]]\+pam_systemd\.so\)/\1/' /etc/pam.d/common-session
```

## 16. bond0 (active-backup)

Адреса и имена интерфейсов — плейсхолдеры. По другим документам Ceph сейчас bond0 не использует,
а сам он в состоянии DOWN: актуальное состояние — в `AI-environment_facts-korona-proxmox.md`.
Блоки описывают, как bond0 создавался. IP назначается только на bond0, слейвы остаются `inet manual`.
Режим 802.3ad (LACP) без настройки агрегации портов на коммутаторе не включать.

```bash
# [R] Линк на слейвах bond0 до настройки (на обоих узлах) — NETWORK-BOND0-CEPH-ACTIVEBACKUP-2026-001
# Ожидается yes. Слейвы должны быть объявлены в /etc/network/interfaces как inet manual
# и не входить в другой bridge или bond
ethtool <интерфейс1> | grep "Link detected"
ethtool <интерфейс2> | grep "Link detected"
```

```bash
# [W] Создать bond0 active-backup и применить (по порядку, на каждом узле со своим адресом)
# NETWORK-BOND0-CEPH-ACTIVEBACKUP-2026-001
# active-backup не требует правок на коммутаторе: один порт активен, второй в резерве.
# ifreload -a применяет конфигурацию всех интерфейсов: при ошибке в файле можно потерять связь с узлом
cat >> /etc/network/interfaces << 'EOF'

auto bond0
iface bond0 inet static
    address <IP>/<маска>
    bond-slaves <интерфейс1> <интерфейс2>
    bond-mode active-backup
    bond-miimon 100
    bond-primary <интерфейс1>
EOF
ifreload -a
```

```bash
# [R] Проверка bond0 — NETWORK-BOND0-CEPH-ACTIVEBACKUP-2026-001
# Ожидается: bond0 UP, Bonding Mode fault-tolerance (active-backup), MII Status up на обоих
# слейвах, Link Failure Count 0
ip addr show bond0
cat /proc/net/bonding/bond0
```

## 17. Первичная настройка узла: имя и репозитории

Процедуры выполняются на свежем узле до вступления в кластер. Переименование узла, уже входящего
в кластер, требует правки `corosync.conf` при остановленном кластере: в `PROXMOX-NODE-RENAME-2026-001`
этот порядок не описан, сверяться с документацией Proxmox «Renaming a Node». Диалоги скрипта
пост-установки (whiptail) — не команды, рекомендованные ответы — в `PROXMOX-POSTINSTALL-SCRIPT-2026-001`.

```bash
# [R] Состоит ли узел в кластере — PROXMOX-NODE-RENAME-2026-001
# Переименование по этой процедуре применимо только к узлу вне активного кластера
pvecm status
```

```bash
# [W] Сменить имя узла до вступления в кластер (по порядку) — PROXMOX-NODE-RENAME-2026-001
# В окне обслуживания: перезагрузка остановит работающие ВМ. Не менять имя только через
# /etc/hostname или hostnamectl без правки /etc/hosts: рассинхронизация и ошибки SSL.
# Сначала вручную поправить /etc/hosts: строка с IP узла — сначала FQDN, затем короткое имя;
# имя узла не должно указывать на 127.0.0.1:
#   127.0.0.1 localhost.localdomain localhost
#   <IP_узла> <fqdn_узла> <имя_узла>
echo "<имя_узла>" > /etc/hostname
reboot
```

```bash
# [R] Каталоги конфигураций узлов после перезагрузки — PROXMOX-NODE-RENAME-2026-001
# После смены имени список ВМ в веб-интерфейсе пуст: конфигурации лежат в каталоге со старым именем
ls /etc/pve/nodes/
```

```bash
# [W] Перенести конфигурации в каталог с новым именем, если каталог нового имени ещё не создан
# PROXMOX-NODE-RENAME-2026-001
mv /etc/pve/nodes/<старое_имя> /etc/pve/nodes/<новое_имя>
```

```bash
# [D] REQUIRES_APPROVAL — слить каталог старого имени в уже созданный каталог нового и удалить старый (по порядку)
# PROXMOX-NODE-RENAME-2026-001
# Только если каталог нового имени уже существует (пустой). rm -rf безвозвратно удаляет каталог
# конфигураций со старым именем: перед ним проверить ls, что cp -a отработал и конфигурации ВМ на месте
cp -a /etc/pve/nodes/<старое_имя>/. /etc/pve/nodes/<новое_имя>/
rm -rf /etc/pve/nodes/<старое_имя>
```

```bash
# [W] Перезапустить службы после переноса конфигураций (или ещё раз reboot) — PROXMOX-NODE-RENAME-2026-001
# Самоподписанный сертификат останется со старым именем — не критично; при необходимости
# перегенерировать в Node → Certificates
systemctl restart pvedaemon pveproxy pvestatd pvescheduler
```

```bash
# [W] Обновить систему после диалогов скрипта первичной настройки (по порядку) — PROXMOX-POSTINSTALL-SCRIPT-2026-001
# reboot перезагружает узел: окно обслуживания. После — apt update без ошибок 401/NO_PUBKEY
apt update
apt full-upgrade -y
reboot
```

```bash
# [R] Формат репозиториев на узле — PROXMOX-POSTINSTALL-SCRIPT-2026-001
# На PVE 9 / Debian trixie репозитории хранятся в формате deb822 (.sources), не .list: команды под
# .list завершатся ошибкой «sed: can't read ...: No such file or directory». Сначала проверять формат
ls -l /etc/apt/sources.list.d/
```

```bash
# [W] Отключить enterprise-репозитории в формате deb822 (.sources) — PROXMOX-POSTINSTALL-SCRIPT-2026-001
# Если строка Enabled: есть — заменяется на «Enabled: no», если нет — добавляется в начало файла.
# Цикл трогает и ceph.sources: если этот файл уже заменён на репозиторий Ceph no-subscription
# (раздел 4), цикл отключит рабочий репозиторий — замечание не из источника
for f in /etc/apt/sources.list.d/pve-enterprise.sources /etc/apt/sources.list.d/ceph.sources; do
  [ -f "$f" ] && { grep -q '^Enabled:' "$f" && sed -i 's/^Enabled:.*/Enabled: no/' "$f" || sed -i '1i Enabled: no' "$f"; }
done
```

```bash
# [W] Отключить enterprise-репозиторий в старом формате .list — PROXMOX-POSTINSTALL-SCRIPT-2026-001
# Только если репозитории действительно в формате .list (проверка выше)
sed -i 's/^deb/#deb/' /etc/apt/sources.list.d/pve-enterprise.list
```

```bash
# [R] Включён ли no-subscription — PROXMOX-POSTINSTALL-SCRIPT-2026-001
grep -ri 'no-subscription' /etc/apt/sources.list.d/
```

```bash
# [R] Диагностика ошибок apt update (код 100) — PROXMOX-POSTINSTALL-SCRIPT-2026-001
# Could not get lock / Waiting for cache lock: фоновый apt-daily ещё работает, обычно освобождается
# за 1–10 минут. Не убивать процесс и не удалять lock-файлы. Temporary failure resolving — сеть или DNS
ps -p <pid> -o pid,etime,cmd
ping -c3 download.proxmox.com
cat /etc/resolv.conf
```

```bash
# [W] NO_PUBKEY: добавить ключ Proxmox — PROXMOX-POSTINSTALL-SCRIPT-2026-001
# <кодовое_имя> — bookworm или trixie по версии Debian узла (cat /etc/os-release).
# Скачивать только с официального домена proxmox.com
wget https://enterprise.proxmox.com/debian/proxmox-release-<кодовое_имя>.gpg -O /etc/apt/trusted.gpg.d/proxmox-release-<кодовое_имя>.gpg
```

```bash
# [R] Corosync на одиночном узле — PROXMOX-POSTINSTALL-SCRIPT-2026-001
# Состояние зависит от ответа в диалоге скрипта: отключён, если выбрано «yes» на шаге про Corosync
systemctl status corosync
```

## 18. Миграция ВМ между узлами (план)

План на момент `PROXMOX-VM-MIGRATION-ISOLATION-2026-001` не выполнялся: миграция не начата, причина
жалоб на скорость 1С по замерам не установлена. Блоки [R] — проверки до миграции. ВМ 1С ERP на другой
узел без явного запроса администратора не переносить.

```bash
# [R] Память узла — PROXMOX-VM-MIGRATION-ISOLATION-2026-001
# Выполнять на каждом узле отдельно и подписывать вывод узлом: во вставках из источника подписи
# были перепутаны
free -h
```

```bash
# [R] Список ВМ и их ресурсы (vCPU, RAM, диски) — PROXMOX-VM-MIGRATION-ISOLATION-2026-001
qm list
qm config <VMID>
```

```bash
# [R] Процессор и NUMA на узле — PROXMOX-VM-MIGRATION-ISOLATION-2026-001
# Сравнить сумму vCPU всех запущенных ВМ с числом потоков хоста
lscpu
numactl -H
```

```bash
# [R] Ресурсы HA, которых затронет перенос — PROXMOX-VM-MIGRATION-ISOLATION-2026-001
ha-manager status
```

```bash
# [R] Канал под public_network Ceph (vmbr0) — PROXMOX-VM-MIGRATION-ISOLATION-2026-001
# ВМ на втором узле обращаются к OSD на первом по этой сети. Скорость моста по ethtool линком не
# является: смотреть физический порт
ip -br link
ethtool <интерфейс> | grep -i speed
```

```bash
# [R] Замеры во время жалобы на скорость — PROXMOX-VM-MIGRATION-ISOLATION-2026-001
# Без замеров во время жалоб причина не считается установленной. ceph osd perf выполнять несколько раз
# подряд. Внутри ВМ 1С: очереди дисков и CPU, активные запросы SQL (команды в источнике не приведены)
top
mpstat
ceph -s
ceph osd perf
```

```bash
# [R] Свободное место в пулах Ceph перед миграцией — PROXMOX-VM-MIGRATION-ISOLATION-2026-001
ceph df
```

```bash
# [W] Мигрировать ВМ на другой узел — PROXMOX-VM-MIGRATION-ISOLATION-2026-001
# Только после проверок выше и решения по замерам: по одной ВМ, в нерабочее время, начиная с наименее
# критичной. Не выполнять при нехватке места в пуле Ceph и RAM на целевом узле, а также для ВМ с
# локальным хранилищем (local, local-lvm): сначала перенести диски на Ceph. Для ВМ на общем
# хранилище переносится только состояние памяти
qm migrate <VMID> <целевой_узел>
```

```bash
# [W] Увеличить osd_memory_target для NVMe-OSD — PROXMOX-VM-MIGRATION-ISOLATION-2026-001
# Предложение из документа, не выполнялось; польза не подтверждена (INFERRED: ceph osd perf на
# простое показал 0 мс, замеров под нагрузкой нет). По умолчанию 4 ГБ (4294967296), здесь 8 ГБ на
# демон — выполнять только осознанно
ceph config set osd.<N> osd_memory_target 8589934592
```

## 19. Ceph: инициализация и общие проверки

Из `PROXMOX-CEPH-ARCHITECTURE-PLANNING-2026-001`: документ плановый, а не протокол выполненных
команд, порядок действий в нём — обобщённая шпаргалка. Установка пакетов Ceph, MON/MGR, OSD и
RBD-хранилище в источнике делаются через веб-интерфейс (Node → Ceph, Datacenter → Storage → Add → RBD).

```bash
# [R] Какая сеть реально используется кластером — PROXMOX-CEPH-ARCHITECTURE-PLANNING-2026-001
# Смотреть строки ring0_addr
cat /etc/pve/corosync.conf
```

```bash
# [W] Инициализировать Ceph с указанием сети — PROXMOX-CEPH-ARCHITECTURE-PLANNING-2026-001
# Команда из плановой шпаргалки: public и cluster network — внутренняя 10G подсеть. Фактический порядок
# развёртывания в этом кластере — в PROXMOX-CEPH-OSD-POOLS-DEPLOYMENT-2026-001, а cluster_network
# позже переносился на прямой канал (PROXMOX-CEPH-NIC0-DIRECT-LINK-2026-001)
pveceph init --network <подсеть/маска>
```

```bash
# [R] Общие проверки Ceph после развёртывания — PROXMOX-CEPH-ARCHITECTURE-PLANNING-2026-001
# Ожидается: HEALTH_OK, все OSD up/in
ceph -s
ceph osd tree
ceph df
pveceph status
```

## 20. HA: watchdog (fencing)

Fencing в Proxmox VE работает через watchdog (`PROXMOX-WEBGUI-DATACENTER-2026-001`). Команды
`ha-manager groupadd ... --group` и `ha-manager add ... --group` из того же документа в справочник не
вошли: документ написан для Proxmox VE 8.2.2, а в PVE 9 группы HA заменены правилами (по сообщениям
сотрудников Proxmox на форуме, с документацией версии не сверялось) — настраивать HA через веб-интерфейс
или `ha-manager rules` после сверки с документацией своей версии. Команды `pvesdn create ...` не вошли:
в обсуждениях SDN из командной строки настраивают через `pvesh create cluster/sdn/...` и применяют
`pvesh set cluster/sdn`; ни один из вариантов на этом кластере не проверялся.

```bash
# [R] Есть ли watchdog — PROXMOX-WEBGUI-DATACENTER-2026-001
# Пример вывода для аппаратного watchdog в источнике: Device /dev/watchdog, Identity iTCO_wdt,
# Timeout 10 seconds
wdctl
```

```bash
# [W] Загрузить аппаратный watchdog, если не настроен — PROXMOX-WEBGUI-DATACENTER-2026-001
# Программный fallback — softdog, для production рекомендуется аппаратный. Чтобы модуль загружался после
# перезагрузки, добавить его имя в /etc/modules (команда в источнике не приведена)
modprobe iTCO_wdt
```

## 21. Active Directory: SYSVOL и репликация DFSR (PowerShell, внутри ВМ)

Имена контроллеров и домен — плейсхолдеры: `<DC_источник>` — контроллер, с которого `SYSVOL`
реплицируется (в источнике — `DC`), `<DC_приёмник>` — контроллер, который его получает
(в источнике — `AD`). Блоки выполняются на указанном контроллере от администратора. Порядок
при простое SYSVOL: сначала привести в порядок источник, потом приёмник. Резервную копию делать
до первого изменения. Классы и состояние событий — в `PROXMOX-AD-DFSR-SYSVOL-RECOVERY-2026-001`.

```powershell
# [R] State папки SYSVOL на контроллере — PROXMOX-AD-DFSR-SYSVOL-RECOVERY-2026-001
# Выполнять на КАЖДОМ контроллере, не только на проблемном: причина часто на партнёре.
# Коды: 0 Uninitialized, 1 Initialized, 2 Initial Sync, 3 Auto Recovery, 4 Normal, 5 In Error.
# Initial Sync (2), не уходящий за час-два, при State 5 на партнёре означает, что источник остановлен
Get-CimInstance -Namespace root\microsoftdfs -ClassName DfsrReplicatedFolderInfo | Select ReplicatedFolderName, State
```

```powershell
# [R] События DFSR за последние часы — PROXMOX-AD-DFSR-SYSVOL-RECOVERY-2026-001
# 4012 — сервер отключён от партнёров дольше MaxOfflineTimeInDays, репликация остановлена;
# 4604 — начальная синхронизация завершена; 5008 — не удалось подключиться к партнёру;
# 2212/2218/2214 — аварийное завершение и штатное восстановление базы после сбоя питания
Get-WinEvent -FilterHashtable @{LogName='DFS Replication'; Id=4012,4102,4104,4112,4114,4602,4604,5004,5008,5014; StartTime=(Get-Date).AddHours(-2)} -ErrorAction SilentlyContinue |
  Select TimeCreated, Id, @{n='Msg';e={($_.Message -split "`r?`n")[0]}} | Format-Table -Wrap
```

```powershell
# [R] Опубликованы ли шары и готов ли SYSVOL — PROXMOX-AD-DFSR-SYSVOL-RECOVERY-2026-001
# Нет шар SYSVOL и NETLOGON и SysvolReady = 0 — контроллер не «объявляет» себя (Advertising, NetLogons в dcdiag)
net share
reg query HKLM\SYSTEM\CurrentControlSet\Services\Netlogon\Parameters /v SysvolReady
```

```powershell
# [R] Подписки SYSVOL в AD — PROXMOX-AD-DFSR-SYSVOL-RECOVERY-2026-001
# Проверять именно подписки (msDFSR-Subscription), а не родительский объект группы «Domain System Volume»:
# отсутствие msDFSR-Enabled, GUID и Flags у родителя не признак повреждения конфигурации
Get-ADObject -LDAPFilter "(objectClass=msDFSR-Subscription)" -SearchBase "OU=Domain Controllers,<DN_домена>" -Properties msDFSR-Enabled |
  Format-Table distinguishedName, msDFSR-Enabled -AutoSize
```

```powershell
# [R] Текущий лимит offline (по умолчанию 60) — PROXMOX-AD-DFSR-SYSVOL-RECOVERY-2026-001
Get-CimInstance -Namespace root\microsoftdfs -ClassName DfsrMachineConfig | Select MaxOfflineTimeInDays
```

```powershell
# [R] Репликация AD и тесты, зависящие от SYSVOL — PROXMOX-AD-DFSR-SYSVOL-RECOVERY-2026-001
repadmin /replsummary
dcdiag /test:sysvolcheck /test:advertising /test:netlogons /test:dfsrevent
```

```powershell
# [R] Доступность порта DFSR на партнёре — PROXMOX-AD-DFSR-SYSVOL-RECOVERY-2026-001
# TCP 5722 закрыт у сервера, у которого DFSR остановлен (4012) или который больше не контроллер домена
Test-NetConnection <DC_партнёр> -Port 5722
```

```powershell
# [W] Резервная копия SYSVOL и GPO на источнике (по порядку, до любых изменений) — PROXMOX-AD-DFSR-SYSVOL-RECOVERY-2026-001
# GPO бэкапить по одной в try/catch: Backup-GPO -All останавливается на первой политике без файлов
# в SYSVOL. Копию держать не только на этом же сервере и не только на этом же Proxmox
New-Item -ItemType Directory -Path C:\Backup\SYSVOL_<DC_источник> -Force | Out-Null
robocopy C:\Windows\SYSVOL\domain C:\Backup\SYSVOL_<DC_источник> /E /COPYALL /DCOPY:DAT /R:1 /W:1
New-Item -ItemType Directory -Path C:\Backup\GPO_<DC_источник> -Force | Out-Null
foreach ($g in Get-GPO -All) {
  try { Backup-GPO -Guid $g.Id -Path C:\Backup\GPO_<DC_источник> -ErrorAction Stop | Out-Null; "OK   $($g.DisplayName)" }
  catch { "FAIL $($g.DisplayName) [$($g.Id)] : $($_.Exception.Message)" }
}
robocopy C:\Backup \\<DC_приёмник>\C$\Backup_from_<DC_источник> /E /COPYALL /DCOPY:DAT /R:1 /W:1
```

```powershell
# [W] Временно поднять MaxOfflineTimeInDays на источнике и перезапустить DFSR (по порядку)
# PROXMOX-AD-DFSR-SYSVOL-RECOVERY-2026-001
# Только когда на источнике событие 4012 и State 5. Выводит сервер из ошибки, но отключает защиту от
# репликации устаревших данных: после State 4 вернуть 60 (блок ниже), насовсем не оставлять.
# wmic в Windows Server 2025 может отсутствовать — использовать CIM. Откат: тем же вызовом поставить 60
Get-CimInstance -Namespace root\microsoftdfs -ClassName DfsrMachineConfig | Set-CimInstance -Property @{MaxOfflineTimeInDays=365}
Get-CimInstance -Namespace root\microsoftdfs -ClassName DfsrMachineConfig | Select MaxOfflineTimeInDays
Restart-Service DFSR
Start-Sleep 60
Get-CimInstance -Namespace root\microsoftdfs -ClassName DfsrReplicatedFolderInfo | Select ReplicatedFolderName, State
```

```powershell
# [W] Ускорить опрос конфигурации на приёмнике (по необходимости) — PROXMOX-AD-DFSR-SYSVOL-RECOVERY-2026-001
# dfsrdiag входит в RSAT-DFS-Mgmt-Con (раздел 10). Обычно приёмник сам завершает синхронизацию за 5–10
# минут после выхода источника из ошибки; D2/D4 для этого не нужны
dfsrdiag pollad
```

```powershell
# [R] Сравнить содержимое SYSVOL на двух контроллерах по хэшам — PROXMOX-AD-DFSR-SYSVOL-RECOVERY-2026-001
# Пустой вывод — идентично. Имя функции не делать «H»: это встроенный алиас Get-History
function Get-SysvolHash($s){ $r="\\$s\SYSVOL\<домен>"; Get-ChildItem $r -Recurse -File -Force -ErrorAction SilentlyContinue | Get-FileHash | ForEach-Object { "{0}  {1}" -f $_.Hash, $_.Path.Substring($r.Length) } }
Compare-Object (Get-SysvolHash <DC_приёмник>) (Get-SysvolHash <DC_источник>)
```

```powershell
# [W] Вернуть лимит offline после State 4 на обоих контроллерах — PROXMOX-AD-DFSR-SYSVOL-RECOVERY-2026-001
# Откат: поставить 365 той же командой
Get-CimInstance -Namespace root\microsoftdfs -ClassName DfsrMachineConfig | Set-CimInstance -Property @{MaxOfflineTimeInDays=60}
Restart-Service DFSR
```

```powershell
# [W] Порядок DNS-серверов на контроллере: себя первым — PROXMOX-AD-DFSR-SYSVOL-RECOVERY-2026-001
# Применено на AD 2026-10-27; «себя первым» — общая практика для DC (INFERRED). Имя интерфейса —
# из Get-DnsClientServerAddress. Откат: прежний список адресов. Демотированный сервер в списке
# оставлять не нужно, но решение по нему отложено
Get-DnsClientServerAddress -AddressFamily IPv4
Set-DnsClientServerAddress -InterfaceAlias "<интерфейс>" -ServerAddresses ("127.0.0.1","<DNS2>","<DNS3>")
ipconfig /registerdns
```

---

## Покрытие

Команды перенесены из документов:

- `PROXMOX-AUTOSTART-STARTUP-ORDER-2026-001`
- `PROXMOX-VM-CLONE-2001-2026-001`
- `PROXMOX-VM-MEMORY-BALLOON-2026-001`
- `PROXMOX-VM2002-AD-RAM-INCREASE-2026-001`
- `PROXMOX-CEPH-OSD-POOLS-DEPLOYMENT-2026-001`
- `PROXMOX-CEPH-NIC0-DIRECT-LINK-2026-001`
- `PROXMOX-CEPH-PUBLIC-NETWORK-1C-2026-001`
- `PROXMOX-CEPH-BOND0-LATENCY-INVESTIGATION-2026-001`
- `NETWORK-SFP-OPTICAL-MISMATCH-2026-001`
- `ZABBIX-STACK-INSTALL-2026-001`
- `ZABBIX-PVE-API-MONITORING-2026-001`
- `ZABBIX-AGENT-PVE-NODES-2026-001`
- `ZABBIX-LXC-FALSE-ALERTS-2026-001`
- `PROXMOX-CEPH-OSD-DISK-PREP-2026-001`
- `PROXMOX-CLUSTER-QDEVICE-SETUP-2026-001`
- `PROXMOX-QDEVICE-REPLACEMENT-2026-001`
- `PROXMOX-AD-THIRD-DC-PROMOTION-2026-001`
- `PROXMOX-AD-DFSR-SYSVOL-RECOVERY-2026-001`
- `PROXMOX-RDS-2003-2026-001`
- `PROXMOX-VM2001-USB-HASP-2026-001`
- `PROXMOX-VAULTWARDEN-INSTALL-2026-001`
- `PROXMOX-VAULTWARDEN-HTTPS-CADDY-2026-001`
- `PROXMOX-VAULTWARDEN-ADMIN-TOKEN-2026-001`
- `PROXMOX-VAULTWARDEN-USERS-2026-001`
- `PROXMOX-WINSRV2022-TEMPLATE-2026-001`
- `PROXMOX-LXC-DEBIAN12-TEMPLATE-2026-001`
- `LINUX-SSH-DEBIAN-ACCESS-2026-001`
- `LINUX-SSH-PAM-SYSTEMD-ZABBIX-2026-001`
- `NETWORK-BOND0-CEPH-ACTIVEBACKUP-2026-001`
- `PROXMOX-NODE-RENAME-2026-001`
- `PROXMOX-POSTINSTALL-SCRIPT-2026-001`
- `PROXMOX-VM-MIGRATION-ISOLATION-2026-001`
- `PROXMOX-CEPH-ARCHITECTURE-PLANNING-2026-001`
- `PROXMOX-WEBGUI-DATACENTER-2026-001`

Команды `pvesh get /cluster/resources` и `qm guest cmd <VMID> get-host-name`
проверены администратором 2026-10-20 (отдельного документа-источника нет).

**Просмотрены, команд для переноса нет** (справочные документы):
`PROXMOX-CEPH-CONCEPTS-2NODE-2026-001`, `HARDWARE-HUAWEI-2288H-PORTMAP-2026-001`,
`PROXMOX-NETWORK-TOPOLOGY-2026-001`, `NETWORK-SWITCH-SELECTION-2026-001`.

**Не разбирались:** архивные документы (`ARCHIVE-*`).

## Как дополнять

1. Команду, к которой стоит возвращаться, добавляют в документ-источник и здесь.
2. Формат блока: первая строка-комментарий `[класс] что делает — document_id`.
3. Класс выбирать по самому опасному шагу блока. Сомневаетесь между [W] и [D] — ставьте [D].
4. Секретов нет: токены, пароли и ключи заменять плейсхолдерами.
5. После правки обновить `date_modified` и список покрытия.
