---
document_id: "ZABBIX-STACK-INSTALL-2026-001"
title: "Установка стека Zabbix 7.0 LTS (LXC 700) — MariaDB, Nginx, PHP-FPM"
document_type: "setup"
status: "completed"
priority: "high"
date_created: 2026-09-14
date_modified: 2026-09-14
next_review: 2026-10-01
author: "cladkyimaffin-hue"
category: "08_Monitoring/Zabbix"
tags:
  - "ProxmoxVE"
  - "Zabbix"
  - "LXC"
  - "Debian12"
  - "MariaDB"
  - "Security"
ai_summary: "Установка Zabbix Server 7.0.30 LTS + MariaDB 10.11 + Nginx 1.22.1 + PHP-FPM 8.2 в LXC 700 (клон шаблона 1000, 192.168.200.223/22). Известная проблема: MariaDB не запускалась в непривилегированном LXC (226/NAMESPACE, тот же класс ошибки, что и systemd-logind в других контейнерах) — решено включением features:nesting=1 на контейнере. ⚠️ Открытая проблема безопасности: пароль пользователя БД zabbix буквально равен строке из четырёх звёздочек «****» (не placeholder — реальный рабочий пароль), пароль веб-панели Admin остался дефолтным «zabbix» — ни то, ни другое не сменено на момент документа."
dont_repeat:
  - "Никогда не выполнять команду с плейсхолдером **** буквально, не подставив реальное значение — в этой сессии так была создана рабочая, но крайне слабая, буквальная строка-пароль."
  - "MariaDB (как и systemd-logind, см. LINUX-SSH-PAM-SYSTEMD-ZABBIX-2026-001) может не запускаться в непривилегированном LXC с ошибкой 226/NAMESPACE — первым делом проверять `features: nesting` в конфигурации контейнера, не сразу переводить контейнер в privileged (это менее безопасно и обычно не нужно)."
  - "Не считать импорт схемы Zabbix (`server.sql.gz` → mysql) идемпотентным — повторный запуск даёт ошибки дублирования ключей; выполнять только один раз."
  - "Не оставлять пароль БД/веб-панели дефолтным или тривиальным на сервисе, который затем получит доступ к API управления кластером Proxmox (см. ZABBIX-PVE-API-MONITORING-2026-001) — компрометация Zabbix в этом случае means компрометация мониторингового доступа ко всему кластеру."
related_files:
  - "PROXMOX-LXC-DEBIAN12-TEMPLATE-2026-001"
  - "LINUX-SSH-PAM-SYSTEMD-ZABBIX-2026-001"
  - "ZABBIX-PVE-API-MONITORING-2026-001"
  - "ZABBIX-AGENT-PVE-NODES-2026-001"
schema_version: "1.0"
---

# ⚠️ Установка стека Zabbix — открыта проблема безопасности (пароли)

**Перед использованием этого сервера в production-режиме мониторинга** —
сначала закрыть пункт «Открытые проблемы безопасности» ниже. На момент
этого документа два пароля остаются дефолтными/тривиальными.

## Что настраивается и зачем
Централизованный мониторинг кластера Proxmox (узлы, ВМ, LXC) и, в
перспективе, самих сервисов (1С, RDS) — Zabbix Server 7.0 LTS в
LXC-контейнере 700, развёрнутом из общего шаблона Debian 12 (`PROXMOX-LXC-DEBIAN12-TEMPLATE-2026-001`).

## Итоговая конфигурация
| Параметр | Значение |
|---|---|
| Контейнер | LXC 700, клон шаблона 1000, `192.168.200.223/22` |
| Zabbix | 7.0.30 LTS |
| СУБД | MariaDB 10.11, БД `zabbix`, пользователь `zabbix` |
| Веб | Nginx 1.22.1 + PHP-FPM 8.2, `http://192.168.200.223/` |
| Часовой пояс | Europe/Moscow |

## Шаги

**1. Установить пакеты:**
```bash
pct exec 700 -- bash -c "apt install -y zabbix-server-mysql zabbix-frontend-php zabbix-nginx-conf zabbix-sql-scripts zabbix-agent mariadb-server"
```

## ⚠️ Известная проблема: MariaDB не запускается в непривилегированном LXC

**Симптом:**
```
mariadb.service - MariaDB 10.11.18 database server
Main process exited, code=exited, status=226/NAMESPACE
Failed to set up mount namespacing: /run/systemd/unit-root/proc: Permission denied
```
Это тот же класс ошибки (`226/NAMESPACE`), что и у `systemd-logind` в
контейнере zabbix ранее (см. `LINUX-SSH-PAM-SYSTEMD-ZABBIX-2026-001`) —
ограничение mount namespace в непривилегированном LXC, только на этот раз
затронута сама СУБД, а не PAM-модуль SSH.

**Решение — включить `nesting` на уровне контейнера (не переводить в privileged):**
```bash
pct set 700 -features nesting=1
pct reboot 700
systemctl status mariadb   # должен стать active
```
`nesting=1` в непривилегированном контейнере не повышает его привилегии
до root на хосте — только разрешает вложенные операции с namespaces,
нужные systemd-юнитам с усиленной изоляцией.

**2. Создать БД и импортировать схему:**
```bash
pct exec 700 -- bash -c "
mysql -e \"CREATE DATABASE IF NOT EXISTS zabbix CHARACTER SET utf8mb4 COLLATE utf8mb4_bin;\"
mysql -e \"CREATE USER IF NOT EXISTS 'zabbix'@'localhost' IDENTIFIED BY '<РЕАЛЬНЫЙ_ПАРОЛЬ>';\"
mysql -e \"GRANT ALL PRIVILEGES ON zabbix.* TO 'zabbix'@'localhost';\"
mysql -e \"FLUSH PRIVILEGES;\"
zcat /usr/share/zabbix-sql-scripts/mysql/server.sql.gz | mysql --default-character-set=utf8mb4 -uzabbix -p'<РЕАЛЬНЫЙ_ПАРОЛЬ>' zabbix
"
```
⚠️ Не запускать импорт схемы повторно — не идемпотентно, задваивает ключи.
Подтверждённый результат: 203 таблицы.

**3. Настроить конфиги и запустить службы:**
```bash
pct exec 700 -- bash -c "
sed -i 's/^# DBHost=localhost/DBHost=localhost/' /etc/zabbix/zabbix_server.conf
sed -i 's/^# DBName=zabbix/DBName=zabbix/' /etc/zabbix/zabbix_server.conf
sed -i 's/^# DBUser=zabbix/DBUser=zabbix/' /etc/zabbix/zabbix_server.conf
sed -i '/^DBUser=zabbix/a DBPassword=<РЕАЛЬНЫЙ_ПАРОЛЬ>' /etc/zabbix/zabbix_server.conf
sed -i 's|^#        listen|        listen|' /etc/zabbix/nginx.conf
sed -i 's|^#        server_name|        server_name|' /etc/zabbix/nginx.conf
sed -i 's|server_name example.com;|server_name zabbix.krnn.ru 192.168.200.223;|' /etc/zabbix/nginx.conf
sed -i 's|^; php_value\[date.timezone\] = Europe/Riga|php_value[date.timezone] = Europe/Moscow|' /etc/zabbix/php-fpm.conf
systemctl restart zabbix-server zabbix-agent nginx php8.2-fpm
systemctl enable zabbix-server zabbix-agent nginx php8.2-fpm
"
```

**4. Пройти мастер установки в браузере** (`http://192.168.200.223/`) —
подключение к БД, часовой пояс, вход под `Admin`/`zabbix` (дефолтный).

## ⚠️ Открытые проблемы безопасности (не устранены на момент документа)

1. **Пароль пользователя БД `zabbix` в MariaDB — буквально `****`**
   (четыре символа звёздочки, не замаскированный реальный пароль).
   Причина: администратор выполнил команду создания пользователя с
   плейсхолдером `****` из примера, не подставив реальное значение —
   MariaDB создала пользователя именно с таким паролем, и вся
   последующая настройка (config, restart) была подогнана под него же,
   чтобы сервис вообще заработал.
2. **Пароль веб-панели `Admin` — дефолтный `zabbix`**, смена не выполнена
   в рамках этой сессии.

**Как исправить (не выполнено, требует отдельного окна обслуживания):**
```sql
ALTER USER 'zabbix'@'localhost' IDENTIFIED BY '<новый_надёжный_пароль>';
```
+ синхронно поправить `DBPassword=` в `/etc/zabbix/zabbix_server.conf` и
`systemctl restart zabbix-server`; пароль `Admin` сменить через
веб-интерфейс (`Users → Admin → Change password`).

## ⛔ Don't repeat
См. `dont_repeat` во фронтматтере.

## Проверка результата — подтверждено
- [x] `systemctl is-active zabbix-server zabbix-agent nginx php8.2-fpm mariadb` → все `active`.
- [x] Импорт схемы — 203 таблицы.
- [x] Веб-интерфейс доступен, мастер установки пройден, вход выполнен.
- [ ] Пароль БД `zabbix` заменён на надёжный — **не выполнено**.
- [ ] Пароль `Admin` заменён — **не выполнено**.

## Связанные документы
- «Создание шаблона Debian 12 LXC и клонирование» — исходный шаблон 1000
- «Устранение задержки SSH-входа в LXC (zabbix)» — тот же контейнер, другая по симптому, но того же класса (226/NAMESPACE) проблема
- Документы по настройке мониторинга Proxmox через API и Zabbix Agent — следующие шаги этой же темы

---
*Примечание: загружено администратором напрямую как экспорт переписки.
Обработано по протоколу конвейера — категория `08_Monitoring/Zabbix`
(новая, согласована с администратором как «зонтичная» папка для будущих
инструментов мониторинга: Grafana, Prometheus и т.д., без плоского
смешения всего в одну папку). Содержание не изменено, убрана диалоговая
рамка и повторяющиеся протокольные преамбулы.*
