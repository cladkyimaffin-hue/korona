---
document_id: "ZABBIX-LXC-FALSE-ALERTS-2026-001"
title: "Ложные алерты Zabbix для собственного LXC-хоста Zabbix (память, Load Average, интерфейсы DOWN)"
document_type: "troubleshooting"
status: "in_progress"
priority: "medium"
date_created: 2026-09-29
date_modified: 2026-09-29
next_review: 2026-10-06
author: "cladkyimaffin-hue"
category: "08_Monitoring"
tags:
  - "Zabbix"
  - "LXC"
  - "Debian12"
  - "MemoryManagement"
  - "Diagnostics"
  - "Troubleshooting"
  - "ProxmoxVE"
  - "pve02"
  - "Hostname"
  - "Bash"
ai_summary: "Три независимых ложных срабатывания мониторинга на собственном LXC-хосте Zabbix (CTID 700, узел pve02): (1) память — sysinfo() в LXC возвращает RAM физического хоста, а не лимит контейнера, решено кастомным UserParameter поверх /proc/meminfo; (2) Load Average — шторм переключений контекста из-за рассинхрона Hostname агента и имени хоста в БД Zabbix, решено синхронизацией имени и перезапуском zabbix-server; (3) сетевые интерфейсы nic0/nic1/nic3 в состоянии DOWN — чтение /sys/class/net/*/speed для них возвращает ядру ошибку, элементы данных отключены. Релевантно для любого LXC-хоста под управлением Zabbix, не только для самого сервера мониторинга."
dont_repeat:
  - "Не доверять стандартным ключам Zabbix vm.memory.size[*] в LXC — sysinfo() не изолирован cgroups и возвращает параметры физического хоста, а не лимиты контейнера. Использовать /proc/meminfo напрямую через UserParameter."
  - "Не оставлять несовпадение между Hostname в конфиге zabbix-agent и полем Host name хоста в Zabbix — вызывает бесконечные попытки опроса, лог 'host [X] not found' и шторм переключений контекста (не путать с реальной нагрузкой CPU)."
  - "Не мониторить speed сетевых интерфейсов в состоянии DOWN без фильтрации — чтение /sys/class/net/<iface>/speed для них возвращает ядру Invalid argument."
  - "Не использовать двойные кавычки в bash для строк с восклицательным знаком (например, в PVEAPIToken user!tokenid) — вызывает history expansion (bash: event not found). Использовать одинарные кавычки."
  - "После перезапуска zabbix-agent/zabbix-server ожидать кратковременный (5–15 сек) разрыв сбора метрик — не считать это новым инцидентом."
related_files:
  - "ZABBIX-STACK-INSTALL-2026-001"
  - "ZABBIX-PVE-API-MONITORING-2026-001"
  - "LINUX-SSH-PAM-SYSTEMD-ZABBIX-2026-001"
schema_version: "1.0"
---

# Ложные алерты Zabbix для собственного LXC-хоста Zabbix (память, Load Average, интерфейсы DOWN)

## Сущности и окружение
| Объект | Роль | Идентификаторы | Примечания |
| :--- | :--- | :--- | :--- |
| Zabbix Server (LXC) | Собственный хост Zabbix, за которым следит сам Zabbix | CTID `700`, Debian 12, Zabbix Server 7.0 LTS, 4 ГБ RAM, 2 vCPU | IP по `AI-environment_facts-korona-proxmox.md`: `192.168.200.223/22`. В источнике этой сессии фигурирует другой адрес — см. «Конфликт» ниже |
| `pve02` | Узел Proxmox, на котором расположен LXC 700 | `192.168.202.179/22` | Совпадает с `AI-environment_facts` — расхождений нет |
| `nic0`, `nic1`, `nic3` | Сетевые интерфейсы на `pve02` | физические PCI-устройства, состояние `DOWN` | Не путать с `bond0`/`nic4`/`nic5` (сеть Ceph) — это отдельные, неиспользуемые порты |

⚠️ **Конфликт с `AI-environment_facts-korona-proxmox.md` (не разрешён, см. `CONFLICTS.md`):** источник этой сессии указывает IP LXC-хоста Zabbix как `192.168.202.121` («из вывода `ss`»), но `AI-environment_facts` и соседний документ `ZABBIX-PVE-API-MONITORING-2026-001` подтверждают, что `192.168.202.121` — это адрес узла `pve01`, а не LXC-контейнера с Zabbix. Ниже используется адрес из авторитетного источника (`192.168.200.223`) там, где адрес требуется по существу; исходная цифра из чата сохранена только в таблице выше как задокументированное расхождение.

## Симптомы
1. Хронический алерт «Linux: высокая загрузка памяти (>90%)» на хосте Zabbix Server, при том что `free -h` показывал ~3.6 ГБ свободных из 4 ГБ.
2. Load Average ~4.5–7.0 при 2 vCPU и 100% CPU idle, без процессов в состояниях `R`/`D`.
3. Ошибки «Cannot read from file» для элементов данных `Interface nic0/nic1/nic3: Speed`.

## Отвергнутые гипотезы
- **Load Average вызван реальной нагрузкой процессов** → отвергнуто: `vmstat` показал 100% CPU idle, нет процессов в состояниях `R`/`D`.
- **Ошибка чтения `speed` интерфейсов — проблема прав/агента** → отвергнуто: интерфейсы физически в состоянии `DOWN`, ядро возвращает `Invalid argument` независимо от прав на файл.

## Диагностика

### 1. Память
```bash
free -h
cat /proc/meminfo
zabbix_get -s 127.0.0.1 -k vm.memory.size[total]
```
`free -h`/`/proc/meminfo` показывали ожидаемые ~4 ГБ лимита контейнера,
а `zabbix_get -k vm.memory.size[total]` возвращал ~250 ГБ — память
физического хоста Proxmox.

### 2. Load Average
```bash
vmstat 1 5
# > 200 000 переключений контекста (cs) в секунду
tail -n 100 /var/log/zabbix/zabbix_server.log | grep "not found"
# host [pve02] not found — тысячи повторов
```
Две независимые причины: (а) `Hostname` в конфиге агента не совпадал с
полем `Host name` хоста в БД Zabbix, что вызывало бесконечный retry и
шторм переключений контекста; (б) LXC видит все 36 ядер физического
хоста при расчёте нормализованной нагрузки на ядро, хотя реально
выделено только 2 vCPU — известный артефакт виртуализации LXC, а не
баг конфигурации.

### 3. Интерфейсы
```bash
ip -details link show nic0
```
Интерфейсы `nic0`, `nic1`, `nic3` в состоянии `DOWN`. Чтение
`/sys/class/net/<iface>/speed` для интерфейса в состоянии `DOWN`
возвращает ядру `Invalid argument` — это поведение ядра, не
Zabbix-агента.

## Корневая причина
1. **Память:** ключ `vm.memory.size[*]` использует системный вызов
   `sysinfo()`, который не изолирован cgroups в LXC и отдаёт параметры
   физического хоста, а не лимиты контейнера.
2. **Load Average:** рассинхронизация `Hostname` агента и `Host name`
   в Zabbix (retry-шторм) — независимо усугублена артефактом LXC
   (контейнер видит 36 ядер хоста вместо 2 выделенных vCPU).
3. **Интерфейсы:** попытка мониторить `speed` для интерфейсов, которые
   физически не подняты (`DOWN`) — не ошибка конфигурации, а
   несоответствие того, что мониторится, тому, что реально
   используется.

## Решение

### Память — кастомный UserParameter поверх /proc/meminfo
```bash
mkdir -p /etc/zabbix/zabbix_agentd.d
cat << 'EOF' > /etc/zabbix/zabbix_agentd.d/lxc_memory.conf
UserParameter=custom.linux.memory.pavailable,awk '/MemTotal/ {t=$2} /MemAvailable/ {a=$2} END {printf "%.2f", (a/t)*100}' /proc/meminfo
UserParameter=custom.linux.memory.pused,awk '/MemTotal/ {t=$2} /MemAvailable/ {a=$2} END {printf "%.2f", 100-(a/t)*100}' /proc/meminfo
EOF
systemctl restart zabbix-agent
zabbix_get -s 127.0.0.1 -k custom.linux.memory.pavailable
```
Элемент данных и триггер созданы на уровне хоста; унаследованные от
шаблона элементы, использующие `vm.memory.size[*]`, отключены на
уровне хоста (напрямую переопределить унаследованный от шаблона
элемент нельзя).

### Load Average — синхронизация имени хоста
1. В веб-интерфейсе Zabbix: **Host name** хоста приведён к `pve02`,
   совпадающему с `Hostname` в конфиге агента.
2. Сброс кэша конфигурации:
   ```bash
   systemctl restart zabbix-server
   tail -n 30 /var/log/zabbix/zabbix_server.log | grep "not found"
   ```
3. Рекомендовано (не входит в объём этой сессии) отдельно отключить
   или скорректировать триггер Load Average именно для LXC-хостов —
   артефакт «36 ядер вместо 2 vCPU» сохраняется независимо от
   синхронизации имени.

### Интерфейсы — отключение нерелевантных элементов
Элементы данных `Interface nic0/nic1/nic3: Speed` отключены в
веб-интерфейсе Zabbix на уровне хоста `pve02`.

## Проверка результата
- [x] `custom.linux.memory.pavailable` возвращает ~90%, триггер в состоянии OK.
- [x] В `/var/log/zabbix/zabbix_server.log` больше нет `host [pve02] not found`.
- [x] `vmstat 1 3` показывает нормальный `cs` (тысячи, а не сотни тысяч в секунду).
- [x] В **Monitoring → Latest data** для `pve02` нет активных ошибок «Cannot read from file» по `nic0`/`nic1`/`nic3`.
- [ ] Триггер Load Average для LXC-хостов — решение об отключении/корректировке не подтверждено администратором.
- [ ] IP-адрес LXC-хоста Zabbix в этом документе и в `AI-environment_facts` — конфликт не разрешён (см. выше и `CONFLICTS.md`).

## ⛔ Don't repeat
См. `dont_repeat` во фронтматтере.

## Связанные документы
- `ZABBIX-STACK-INSTALL-2026-001` — установка самого LXC-хоста Zabbix (CTID 700), на котором наблюдались эти алерты.
- `ZABBIX-PVE-API-MONITORING-2026-001` — мониторинг узлов кластера через API; там же зафиксирован отдельный, но связанный инцидент с 401 после смены роли токена (см. обновление этого документа от 2026-09-29).
- `LINUX-SSH-PAM-SYSTEMD-ZABBIX-2026-001` — другая, ранее решённая проблема на этом же LXC-хосте (задержка SSH-входа).
