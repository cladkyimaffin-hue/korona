---
document_id: ZABBIX-PVE-API-MONITORING-2026-001
title: Мониторинг кластера Proxmox через API в Zabbix (шаблон Proxmox VE by HTTP)
  — ошибка 403 из-за Privilege Separation токена
document_type: setup
status: in_progress
priority: high
date_created: 2026-09-14
date_modified: '2026-09-29'
next_review: 2026-10-06
author: cladkyimaffin-hue
category: 08_Monitoring/Zabbix
tags:
- ProxmoxVE
- Zabbix
- krnn
- pve01
- pve02
ai_summary: 'Настройка мониторинга pve01/pve02 в Zabbix через Proxmox API (не через
  агент): создан пользователь zabbix_monitor@pve с кастомной ролью Zabbix_Monitor
  (Sys.Audit/VM.Audit/Datastore.Audit/Sys.Modify/SDN.Audit), API-токен zabbix_token,
  применён официальный шаблон «Proxmox VE by HTTP» к отдельным хостам на каждую ноду.
  Известная проблема: 403 Forbidden несмотря на верные права пользователя — причина
  в Privilege Separation (privsep=1) API-токенов Proxmox: токен имеет СОБСТВЕННЫЕ
  ACL, отдельные от ACL пользователя, и без явного ACL на токен доступа нет, даже
  если у пользователя он есть. Настроена фильтрация LLD discovery по макросу {$PVE.NODE.NAME},
  чтобы хост pve01 не подтягивал метрики pve02 и наоборот. Статус переведён обратно в in_progress: 2026-09-29 на том же токене zabbix_monitor@pve!zabbix_token обнаружена НОВАЯ, отдельная от privsep ошибка 401 Unauthorized — см. раздел «Известная проблема 3» ниже, не решена, требуется пересоздание токена.'
dont_repeat:
- Не считать наличие прав у пользователя (`pveum user permissions`) достаточным для
  API-токена — при privsep=1 (по умолчанию) токен имеет собственные, отдельные ACL;
  без явного `pveum acl modify <path> --token '<user>!<token>' --role <role>` токен
  не унаследует права пользователя.
- Отключение privsep (`--privsep 0`) — рабочий, но менее безопасный обходной путь;
  правильный способ — явный ACL на сам токен (Вариант B), а не уравнивание прав токена
  с правами пользователя целиком.
- 'Команда `pveum user show`/`pveum user list-permissions` не существует в этой версии
  Proxmox — правильная команда: `pveum user permissions <user>`.'
- Не назначать пользователю одновременно встроенную роль PVEAuditor и кастомную роль
  на один и тот же путь — дублирование усложняет диагностику; выбрать одну (в этой
  инфраструктуре — кастомная Zabbix_Monitor).
- Без фильтрации LLD discovery по макросу узла шаблон «Proxmox VE by HTTP», применённый
  к нескольким хостам, будет дублировать метрики всех нод на каждом хосте — обязательно
  настраивать Filters + LLD macro {$PVE.NODE.NAME} сразу при добавлении второго и
  последующих хостов.
- Секрет API-токена Proxmox показывается только один раз, в момент создания — если он
  не сохранён немедленно, восстановить его невозможно, только пересоздать токен целиком
  (см. «Известная проблема 3»).
- Выдача роли на корень (`/`) токену НЕ гарантирует устранение 401, если сам секрет
  токена в макросах Zabbix не совпадает с реальным — прежде чем менять права,
  проверяйте `curl` с текущим секретом напрямую, в обход Zabbix.
related_files:
- ZABBIX-STACK-INSTALL-2026-001
- PROXMOX-CLUSTER-QDEVICE-SETUP-2026-001
- ZABBIX-AGENT-PVE-NODES-2026-001
- ZABBIX-LXC-FALSE-ALERTS-2026-001
schema_version: '1.0'
---

# Мониторинг кластера Proxmox через API в Zabbix (шаблон Proxmox VE by HTTP) — ошибка 403 из-за Privilege Separation токена

## Что настраивается и зачем
Сбор метрик узлов Proxmox (`pve01`, `pve02`) в Zabbix через официальный
Proxmox API (HTTPS, порт 8006), без установки классического Zabbix Agent
на узлы — отдельным, дополняющим способом является Zabbix Agent
(`ZABBIX-AGENT-PVE-NODES-2026-001`).

## Шаги: пользователь, роль и токен в Proxmox

**1. Создать кастомную роль с правами только на чтение (+минимум для метрик):**
```bash
pveum role add Zabbix_Monitor -privs "Sys.Audit,VM.Audit,Datastore.Audit,Sys.Modify,SDN.Audit"
```

**2. Создать пользователя и назначить роль на корень (`/`):**
```bash
pveum user add zabbix_monitor@pve
pveum acl modify / --users zabbix_monitor@pve --roles Zabbix_Monitor
```
⚠️ Не назначать вместе с этим ещё и встроенную `PVEAuditor` на тот же
путь — дублирование, только затрудняет диагностику прав позже.

**3. Создать API-токен:**
```bash
pveum user token add zabbix_monitor@pve zabbix_token
```
Токен создаётся с `privsep=1` (Privilege Separation) по умолчанию.

## ⚠️ Известная проблема: 403 Forbidden несмотря на верные права пользователя

**Симптом:** в Zabbix большинство элементов данных пустые, в логах —
`403 Forbidden` при обращении к `/nodes/pve01` и т.п., хотя:
```bash
pveum user permissions zabbix_monitor@pve --path /nodes/pve01
```
показывает нужные права.

**Корневая причина:** при `privsep=1` API-токен имеет **собственные,
отдельные от пользователя ACL**. Права пользователя не наследуются
токеном автоматически — без явного ACL именно на токен доступа нет,
даже если у пользователя он есть.

**Решение (Вариант B — рекомендован, безопаснее отключения privsep):**
```bash
pveum acl modify /nodes --token 'zabbix_monitor@pve!zabbix_token' --role Zabbix_Monitor
```
**Проверка:**
```bash
pveum user token permissions zabbix_monitor@pve zabbix_token
curl -k -H "Authorization: PVEAPIToken=zabbix_monitor@pve!zabbix_token=<секрет>" https://192.168.202.121:8006/api2/json/nodes/pve01/status
```
Ожидаемо: полный JSON со `status`, `uptime`, `memory`, `cpu`.

**Альтернатива (менее безопасно, не рекомендуется как основной путь):**
```bash
pveum user token modify zabbix_monitor@pve zabbix_token --privsep 0
```
Уравнивает права токена с правами пользователя целиком — проще, но шире,
чем нужно.

**Побочная находка:** команда `pveum user show`/`pveum user
list-permissions` в этой версии Proxmox не существует — правильная
команда `pveum user permissions <user>`.

## Шаги: хосты и шаблон в Zabbix

**4. Создать отдельный хост на каждую ноду** (не один хост на весь
кластер — отказоустойчивость мониторинга: падение одной ноды не рвёт
мониторинг другой):
- `Proxmox pve01` → macros: URL API, `{$PVE.NODE.NAME}=pve01`, токен.
- `Proxmox pve02` → аналогично, `{$PVE.NODE.NAME}=pve02`.
- Шаблон: **Proxmox VE by HTTP** (официальный, Zabbix 7.0).

## Известная проблема 2: discovery подтягивает метрики ВСЕХ нод на каждый хост

**Симптом:** хост `Proxmox pve01` в Zabbix показывает элементы не только
для `pve01`, но и для `pve02` — дублирование данных.

**Решение — фильтрация LLD discovery по имени ноды:**
1. Найти LLD-макрос с именем ноды в discovery rule шаблона: `{#NODE.NAME}` (JSONPath `$.node`).
2. В **Filters** discovery rule добавить: Label Macro `{#NODE.NAME}`, Regular expression `^{$PVE.NODE.NAME}$`.
3. В каждом хосте задать `{$PVE.NODE.NAME}` = имя соответствующей ноды (`pve01`/`pve02`).
4. Удалить уже созданные «чужие» элементы — они не исчезнут сами, только новые discovery-проходы будут отфильтрованы.

⚠️ Фильтр в discovery rule шаблона общий для всех хостов, использующих
этот шаблон — если появится хост без `{$PVE.NODE.NAME}`, discovery для
него перестанет находить ноды вообще.

## ⚠️ Известная проблема 3: 401 Unauthorized (2026-09-29, не решена)

**Симптом:** зависимый элемент `proxmox.node.online[pve02]` не получает
данные, мастер-элемент (HTTP agent) возвращает ошибку. Прямой `curl` к
`https://192.168.202.179:8006/api2/json/cluster/status` с текущим токеном
возвращает `HTTP 401`.

**Диагностика:**
```bash
pveum user token list zabbix_monitor@pve
pveum user token permissions zabbix_monitor@pve zabbix_token
```
Токен `zabbix_token` (тот же, что использован выше для устранения 403)
на момент проверки имел `privsep=1` и права только на `/nodes`, тогда как
для `cluster/status` требуются права на `/`.

**Что уже сделано (не помогло полностью):**
```bash
pveum acl modify / --roles PVEAuditor --token 'zabbix_monitor@pve!zabbix_token'
```
⚠️ Обратите внимание: здесь использована встроенная роль `PVEAuditor`,
а не кастомная `Zabbix_Monitor`, описанная выше в этом же документе —
это расхождение с изначально задокументированной настройкой **не
объяснено источником этой правки** и требует проверки при следующей
работе с этим токеном: применяется ли сейчас `Zabbix_Monitor`,
`PVEAuditor`, или обе роли на разных путях.

После выдачи прав на `/` ошибка 401 **сохранилась**, что указывает не
на нехватку прав, а на несовпадение секрета токена в макросах Zabbix
с реальным секретом (секрет отображается только один раз при создании
токена и мог быть утерян или введён с ошибкой).

**Решение (рекомендовано, не выполнено):**
```bash
# Пересоздание токена (секрет будет выведен в консоль один раз)
pveum user token add zabbix_monitor@pve zabbix_token_new --comment "Zabbix monitoring replacement"
pveum acl modify / --roles PVEAuditor --token 'zabbix_monitor@pve!zabbix_token_new'
```
```bash
# Проверка напрямую, в обход Zabbix, ДО обновления макросов
# ВАЖНО: одинарные кавычки — восклицательный знак в токене иначе триггерит history expansion в bash
curl -k -s -w "\nHTTP_CODE: %{http_code}\n" \
  -H 'Authorization: PVEAPIToken=zabbix_monitor@pve!zabbix_token_new:<НОВЫЙ_СЕКРЕТ>' \
  "https://192.168.202.179:8006/api2/json/cluster/status"
```
Затем обновить в Zabbix, на уровне хоста `pve02`:
- `{$PVE.TOKEN.ID}` = `zabbix_monitor@pve!zabbix_token_new`
- `{$PVE.TOKEN.SECRET}` = `<секрет, скопированный при создании>`

**Статус:** требуется выполнение и подтверждение — элемент
`proxmox.node.online[pve02]` не собирает данные до пересоздания токена.

## Проверка результата — подтверждено
- [x] `curl` с токеном возвращает полный JSON статуса ноды.
- [x] Zabbix собирает метрики (~23 элемента на ноду): CPU, memory, disk, network, uptime, версия PVE.
- [x] pve01 показывает только свои метрики, pve02 — только свои (фильтрация подтверждена).
- [x] Отказоустойчивость: падение мониторинга одной ноды не останавливает мониторинг другой (раздельные хосты).
- [ ] ICMP ping для хостов — не настроен (опционально, шаблон HTTP его не требует).
- [ ] Мониторинг самих ВМ/CT (2001, 2003) и уведомления/дашборды — не в рамках этой сессии.
- [ ] `proxmox.node.online[pve02]` — не собирает данные из-за 401, требуется пересоздание токена (см. «Известная проблема 3»).

## ⛔ Don't repeat
См. `dont_repeat` во фронтматтере — главное: Privilege Separation
токенов и обязательная фильтрация discovery при нескольких хостах на
одном шаблоне.

## На будущее (упомянуто, не факт на сейчас)
При добавлении третьего узла (`pve03`, если/когда кластер вырастет) —
ACL уже покрывает `/nodes` целиком, потребуется только: создать хост в
Zabbix и задать `{$PVE.NODE.NAME}=pve03`.

## Связанные документы
- «Установка стека Zabbix» — сам сервер, на котором это настроено
- «Создание кластера и QDevice» — топология кластера, который мониторится
- Документ по Zabbix Agent на pve01/pve02 — дополняющий способ сбора метрик

---
*Примечание: загружено администратором напрямую как экспорт переписки.
Содержание не изменено, убрана диалоговая рамка и повторяющиеся
протокольные преамбулы.*
