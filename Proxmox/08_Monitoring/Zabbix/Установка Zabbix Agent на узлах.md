---
document_id: "ZABBIX-AGENT-PVE-NODES-2026-001"
title: "Установка Zabbix Agent на pve01/pve02 — репозиторий Zabbix для bookworm несовместим, узлы на Debian 13 (trixie)"
document_type: "setup"
status: "completed"
priority: "medium"
date_created: 2026-09-15
date_modified: 2026-09-15
next_review: 2026-12-01
author: "cladkyimaffin-hue"
category: "08_Monitoring/Zabbix"
tags:
  - "ProxmoxVE"
  - "Zabbix"
  - "Debian"
  - "pve01"
  - "pve02"
ai_summary: "Установка классического Zabbix Agent (не через API) на узлы pve01/pve02, дополняющая мониторинг через Proxmox API (ZABBIX-PVE-API-MONITORING-2026-001) детальными метриками ОС (шаблон Linux by Zabbix agent). Известная проблема: официальный репозиторий Zabbix для Debian 12 (bookworm) несовместим — сами узлы Proxmox VE 9 работают на Debian 13 (trixie), пакет требует libldap-2.5-0, которого нет в trixie (там libldap2). Решение: удалить репозиторий Zabbix (zabbix-release) и поставить agent из штатного репозитория Debian 13 (версия 7.0.22, совместима с сервером 7.0.30 LTS). Подтверждено на обеих нодах: агент активен, ZBX-индикатор зелёный."
dont_repeat:
  - "Не добавлять сторонний репозиторий Zabbix (repo.zabbix.com) для установки zabbix-agent на сами узлы Proxmox VE 9 — они на Debian 13 (trixie), а типовые инструкции/репозитории Zabbix рассчитаны на bookworm (Debian 12) и дают конфликт зависимостей (libldap-2.5-0 vs libldap2). Ставить agent из штатного репозитория Debian 13 — версия там достаточно свежая (7.0.x) и совместима с сервером."
  - "Перед выбором репозитория пакета — проверять реальную версию ОС узла (`cat /etc/os-release`), не полагаться на предположение «Proxmox = Debian 12» по умолчанию."
  - "Не использовать sed-паттерн, рассчитанный на один конкретный формат строки (`^Server=127\\.0\\.0\\.1$`) — реальный файл конфигурации может иметь строку закомментированной, с другим значением по умолчанию или в другом регистре; писать замену так, чтобы она сработала независимо от текущего состояния строки, и всегда проверять результат через `grep`, а не считать применённым по факту отсутствия ошибки у sed."
  - "Не путать зелёный статус ZBX-индикатора хоста с тем, что мониторинг уже даёт полезные данные — проверять реальные последние значения элементов, не только сам факт связи."
related_files:
  - "ZABBIX-STACK-INSTALL-2026-001"
  - "ZABBIX-PVE-API-MONITORING-2026-001"
  - "PROXMOX-CEPH-OSD-POOLS-DEPLOYMENT-2026-001"
schema_version: "1.0"
---

# Установка Zabbix Agent на pve01/pve02

## Что настраивается и зачем
Классический Zabbix Agent на самих узлах Proxmox (`pve01`, `pve02`) —
дополняет мониторинг через Proxmox API (`ZABBIX-PVE-API-MONITORING-2026-001`)
детальными метриками уровня ОС (шаблон **Linux by Zabbix agent**): диски,
процессы, детальная загрузка, логи — то, что Proxmox API не отдаёт.

## ⚠️ Известная проблема: репозиторий Zabbix для bookworm несовместим с узлами (Debian 13)

**Симптом:**
```
zabbix-agent : Depends: libldap-2.5-0 (>= 2.5.4) but it is not installable
```

**Корневая причина:** узлы Proxmox VE 9 в этом кластере работают на
**Debian 13 (trixie)**, подтверждено `/etc/os-release`:
```
PRETTY_NAME="Debian GNU/Linux 13 (trixie)"
```
Типовая инструкция «добавить репозиторий repo.zabbix.com» подставляет
репозиторий для **bookworm (Debian 12)** — пакет там собран под
`libldap-2.5-0`, которого в trixie уже нет (заменён на `libldap2`).

**Решение — не использовать сторонний репозиторий Zabbix вообще, ставить из штатного репозитория Debian 13:**
```bash
apt remove --purge -y zabbix-release
apt update
apt install -y zabbix-agent
```
Версия из репозитория Debian 13 — **7.0.22**, полностью совместима с
Zabbix Server **7.0.30 LTS**.

## Настройка конфигурации агента

```bash
grep -E "^Server=|^ServerActive=|^#\s*Server=|^#\s*ServerActive=" /etc/zabbix/zabbix_agentd.conf
```
Проверить реальный текущий формат строк **перед** заменой — не
предполагать заранее, что там ровно `Server=127.0.0.1` без комментария.

```bash
sed -i 's/^#\?\s*Server=.*/Server=192.168.200.223/' /etc/zabbix/zabbix_agentd.conf
sed -i 's/^#\?\s*ServerActive=.*/ServerActive=192.168.200.223/' /etc/zabbix/zabbix_agentd.conf
systemctl restart zabbix-agent
systemctl enable zabbix-agent
grep -E "^Server=|^ServerActive=" /etc/zabbix/zabbix_agentd.conf
```
⚠️ В этой сессии первая (более узкая) версия `sed`-паттерна не сработала —
агент продолжал подключаться к `127.0.0.1`, реальная строка в файле не
совпадала с предполагаемым форматом. Паттерн `^#\?\s*Server=.*` выше —
уже исправленный, покрывающий и закомментированный, и раскомментированный
варианты в одной замене.

**Повторить те же шаги на `pve02`.**

## Проверка результата — подтверждено на обеих нодах
```bash
zabbix_agentd -V                                              # 7.0.22
systemctl status zabbix-agent                                  # active (running)
grep "connected to" /var/log/zabbix/zabbix_agentd.log | tail -3  # connected to 192.168.200.223:10051
```
- [x] `pve01` и `pve02` — агент активен, версия 7.0.22.
- [x] `Server=192.168.200.223` / `ServerActive=192.168.200.223` — без дублей строк.
- [x] В веб-интерфейсе Zabbix к хостам `Proxmox pve01`/`Proxmox pve02` добавлен интерфейс «Агент» (порт 10050) + шаблон `Linux by Zabbix agent`, индикатор `ZBX` зелёный.
- [ ] Реальные последние значения элементов (не только факт связи) — отдельно не проверялись в этой сессии; зелёный индикатор подтверждает связь, не факт полезности собираемых данных.

## ⛔ Don't repeat
См. `dont_repeat` во фронтматтере.

## Не сделано в рамках этой сессии (открыто, следующий шаг)
Мониторинг самих ВМ **2001** (`Srv1c`, 1С) и **2003** (`TC`, RDS)
изнутри — решено пойти по **Варианту Б** (Zabbix Agent прямо внутри ВМ,
не только через API), но установка не начата.

## Связанные документы
- «Установка стека Zabbix» — сам сервер
- «Мониторинг Proxmox через API» — дополняющий, уже настроенный способ сбора метрик тех же узлов

---
*Примечание: загружено администратором напрямую как экспорт переписки.
Содержание не изменено, убрана диалоговая рамка и повторяющиеся
протокольные преамбулы.*
