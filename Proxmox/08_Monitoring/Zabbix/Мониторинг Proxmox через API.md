---
document_id: ZABBIX-PVE-API-MONITORING-2026-001
title: Мониторинг кластера Proxmox через API в Zabbix (шаблон Proxmox VE by HTTP)
  — ошибка 403 из-за Privilege Separation токена (решено), ошибка 401 (решено)
document_type: setup
status: completed
priority: high
date_created: 2026-09-14
date_modified: '2026-10-25'
next_review: 2026-12-01
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
  чтобы хост pve01 не подтягивал метрики pve02 и наоборот. 2026-09-29 на том же токене
  zabbix_monitor@pve!zabbix_token обнаружена отдельная ошибка 401 Unauthorized; на
  2026-10-25 она не воспроизводится: пользователю выдана роль PVEAuditor на /, прямой
  запрос к API возвращает HTTP 200, Zabbix собирает данные — см. раздел «Известная
  проблема 3».'
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
- При privsep=1 права токена ограничены правами пользователя: ACL токена на `/` не
  действует, пока у самого пользователя нет прав на `/` (подтверждено 2026-10-25 по
  `pveum user token permissions`). Прежде чем пересоздавать токен, проверить `curl` с
  текущим секретом напрямую, в обход Zabbix.
- Заголовок API-токена Proxmox VE имеет вид `PVEAPIToken=USER@REALM!TOKENID=SECRET`
  (знак `=` перед секретом, не `:`; формат с `=` подтверждён `curl` 2026-10-25, HTTP 200);
  ошибка 401 означает сбой аутентификации (формат заголовка, ID или секрет токена), а
  нехватка прав даёт 403.
related_files:
- ZABBIX-STACK-INSTALL-2026-001
- PROXMOX-CLUSTER-QDEVICE-SETUP-2026-001
- ZABBIX-AGENT-PVE-NODES-2026-001
- ZABBIX-LXC-FALSE-ALERTS-2026-001
schema_version: '1.0'
---

# Мониторинг кластера Proxmox через API в Zabbix (шаблон Proxmox VE by HTTP) — ошибка 403 из-за Privilege Separation токена (решено), ошибка 401 (решено)

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

## ✅ Известная проблема 3: 401 Unauthorized (2026-09-29, решено 2026-10-25)

**Симптом (2026-09-29):** зависимый элемент `proxmox.node.online[pve02]` не
получал данные, мастер-элемент (HTTP agent) возвращал ошибку. Прямой `curl` к
`https://192.168.202.179:8006/api2/json/cluster/status` с текущим токеном
возвращал `HTTP 401`. Права токена на тот момент: `privsep=1` и права только на
`/nodes`, тогда как для `cluster/status` требуются права на `/`. Первая попытка
(`pveum acl modify / --roles PVEAuditor --token 'zabbix_monitor@pve!zabbix_token'`)
401 не устранила.

**Диагностика 2026-10-25 (pve01):**
```bash
pveum user token list zabbix_monitor@pve
pveum user token permissions zabbix_monitor@pve zabbix_token
pveum acl list
```
Состояние до правки: токен `zabbix_token` — `privsep=1`, без срока действия. ACL:
`PVEAuditor` на `/` у токена; `Zabbix_Monitor` на `/nodes` у пользователя и у токена.
Эффективные права токена (`pveum user token permissions`) при этом перечисляли только
`/nodes`. Прямой `curl` с форматом заголовка `=` вернул `HTTP 403`,
`Permission check failed (/, Sys.Audit)`.

**Причина:** при `privsep=1` права токена ограничены правами пользователя. ACL токена
`PVEAuditor` на `/` не действовал, потому что у пользователя `zabbix_monitor@pve` на `/`
прав не было — только `Zabbix_Monitor` на `/nodes` (в шаге 2 выше роль назначается
на `/`; фактический ACL пользователя на 2026-10-25 был на `/nodes`).

**Решение (выполнено 2026-10-25):**
```bash
pveum acl modify / --users zabbix_monitor@pve --roles PVEAuditor
pveum user token permissions zabbix_monitor@pve zabbix_token
```
После этого права токена включают `/` и дочерние пути (`/access`, `/pool`, `/sdn`,
`/storage`, `/vms`) с правами только на чтение (`Sys.Audit`, `VM.Audit`,
`Datastore.Audit`, `SDN.Audit`, `Pool.Audit`, `Mapping.Audit`,
`VM.GuestAgent.Audit`); на `/nodes` по-прежнему действует `Zabbix_Monitor`.

**Роли в итоге:** `Zabbix_Monitor` на `/nodes` (пользователь и токен), `PVEAuditor` на
`/` (токен и пользователь) — две роли на разных путях, а не одна, как в исходной
настройке. Роль `Zabbix_Monitor` включает `Sys.Modify`, для мониторинга только на
чтение это избыточно; изменение роли не выполнялось.

**Проверка:**
- Прямой запрос `cluster/status` с текущим токеном и форматом `=` вернул `HTTP 200`:
  кластер `krnn`, `quorate: 1`, два узла online.
- В Zabbix на хосте `Proxmox pve02` элементы `Node [pve02]: ...` получают значения
  (`Status` = `Online (1)`, CPU, память, диск, сеть, uptime), ошибок 401 и 403 нет.

**Не установлено:** что именно вызывало 401 в `curl` и в Zabbix 2026-09-29 — разделитель
`:` вместо `=` в заголовке, макросы в Zabbix или нехватка прав: исходный источник не
сохранил точную команду и состояние макросов. На 2026-10-25 401 не воспроизводится.

**Остаточные ошибки на хосте `Proxmox pve02` (6 элементов из 339 в состоянии Not
supported), с токеном не связаны:**
- Disk read/write ВМ 2000 (шаблон) и 2004 (PRINT): `cannot extract value from json by
  path "$.data.diskwrite"` — обе ВМ остановлены, API не отдаёт для них счётчики диска
  (вывод по симптомам, отдельно не проверялся).
- Speed `nic4` и `nic5`: `Value of type "double" is not suitable for value type
  "Numeric (unsigned)". Value "-1000000"` — у портов нет линка (`bond0` не
  используется), скорость отрицательная (вывод по симптомам, отдельно не проверялся).

## Проверка результата — подтверждено
- [x] `curl` с токеном возвращает полный JSON статуса ноды.
- [x] Zabbix собирает метрики (~23 элемента на ноду): CPU, memory, disk, network, uptime, версия PVE.
- [x] pve01 показывает только свои метрики, pve02 — только свои (фильтрация подтверждена).
- [x] Отказоустойчивость: падение мониторинга одной ноды не останавливает мониторинг другой (раздельные хосты).
- [x] Данные с `pve02` поступают (2026-10-25): `Node [pve02]: Status` = `Online (1)`, CPU, Memory, Uptime обновляются; ранее не собирался `proxmox.node.online[pve02]` из-за 401.
- [ ] Фильтрация по узлу для ВМ: 2026-10-25 среди элементов хоста `Proxmox pve02` в состоянии Not supported есть ВМ с тегом `node: pve01`; фильтр по `{$PVE.NODE.NAME}` для discovery ВМ не проверялся.
- [ ] ICMP ping для хостов — не настроен (опционально, шаблон HTTP его не требует).
- [ ] Мониторинг самих ВМ/CT (2001, 2003) и уведомления/дашборды — не в рамках этой сессии.

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
