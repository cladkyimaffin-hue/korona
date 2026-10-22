---
schema_version: "1.1"
status: "in_progress"
date_created: 2026-10-21
date_modified: 2026-10-22
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

---

## Покрытие

Команды перенесены из документов:

- `PROXMOX-AUTOSTART-STARTUP-ORDER-2026-001`
- `PROXMOX-VM-CLONE-2001-2026-001`
- `PROXMOX-VM-MEMORY-BALLOON-2026-001`
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

Команды `pvesh get /cluster/resources` и `qm guest cmd <VMID> get-host-name`
проверены администратором 2026-10-20 (отдельного документа-источника нет).

**Ещё не вошли** (будут добавлены следующими правками): AD, RDS, USB HASP,
Vaultwarden, шаблоны (Windows Server, LXC), диагностика SSH и `pam_systemd`, `bond0`.
До их добавления искать команды
в самих документах по `INDEX.md`.

## Как дополнять

1. Команду, к которой стоит возвращаться, добавляют в документ-источник и здесь.
2. Формат блока: первая строка-комментарий `[класс] что делает — document_id`.
3. Класс выбирать по самому опасному шагу блока. Сомневаетесь между [W] и [D] — ставьте [D].
4. Секретов нет: токены, пароли и ключи заменять плейсхолдерами.
5. После правки обновить `date_modified` и список покрытия.
