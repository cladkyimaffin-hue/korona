---
document_id: "ZABBIX-AD-DFSR-MONITORING-2026-001"
title: "Мониторинг DFSR/SYSVOL и репликации AD в Zabbix на контроллерах DC и AD (krnn.ru)"
document_type: "setup"
status: "completed"
priority: "high"
date_created: 2026-10-31
date_modified: 2026-10-31
next_review: 2026-11-30
author: "cladkyimaffin-hue"
category: "08_Monitoring/Zabbix"
tags:
  - Zabbix
  - ActiveDirectory
  - AD-DS
  - krnn.ru
  - Replication
  - dfsr
  - sysvol
  - WindowsServer2025
  - Configuration
  - Setup
  - krnn
ai_summary: "Мониторинг в Zabbix 7.0.31 на узлах DC и AD (Windows Server 2025, Zabbix Agent 2): скрипт ad_dfsr_health.ps1 через UserParameter ad.dfsr.health отдаёт JSON, мастер-элемент раз в 5 минут, 8 зависимых элементов через JSONPath, на DC расчётный элемент расхождения SYSVOL между контроллерами, триггеры 1, 2, A, B, C на обоих узлах и D только на DC. Закрывает сбой из PROXMOX-AD-DFSR-SYSVOL-RECOVERY-2026-001 (DFSR State 5 и пустой SYSVOL семь месяцев никто не видел). Документ нужен, чтобы понять, что именно мониторится, с какими порогами, почему не добавлены события и счётчики NTDS и какие грабли встретились (серверный таймаут элемента перекрывает Timeout агента, ServerActive, тип мастер-элемента)."
dont_repeat:
  - "В Zabbix 7.0 таймаут проверки задаётся на элементе на стороне сервера (по умолчанию 3 с) и перекрывает Timeout в zabbix_agent2.conf. Скрипт на DC выполняется около 3,4 с, поэтому у мастер-элемента нужен Timeout = Override 30s; одной правки Timeout=30 в конфиге агента недостаточно (ошибка «Timeout occurred while gathering data» на DC, 2026-10-28)."
  - "Не создавать триггер раньше элемента, на который он ссылается: Zabbix отвечает «Incorrect item key» (так было с триггером D, пока не существовал ad.dfsr.sysvol_diff)."
  - "Элементы, которые могут вернуть -1 (скрипт пишет -1, когда часть данных не прочиталась), делать Numeric (float), а не unsigned. Исключение по факту: shares, sysvol_files, policy_dirs заведены как unsigned (value_type 3), они -1 не получают в норме."
  - "Не откатываться на zabbix_agent2.conf.bak_20261028: в нём прежний ServerActive=127.0.0.1 (активный режим не работает). Откат только на zabbix_agent2.conf.bak2_20261028."
  - "Hostname в zabbix_agent2.conf должен совпадать с именем узла в Zabbix буква в букву (DC, AD), иначе активные проверки не работают."
  - "Windows на контроллерах русская: для счётчиков использовать perf_counter_en, а не perf_counter."
  - "Не добавлять отдельный eventlog-элемент на события 4012, 2213, 2104 журнала «DFS Replication»: любое из них выводит DFSR из State 4, и триггер 1 срабатывает по состоянию; отдельный элемент дал бы второе уведомление о том же. Решение администратора 2026-10-29."
  - "Не считать число триггеров на DC равным пяти: триггер D (расхождение SYSVOL) существует только на DC, то есть 6 против 5 на AD. Фактический trigger.get по DC и AD через API не выполнялся (раздел 9)."
  - "Мастер-элемент на DC и на AD имеет разный тип (DC: Zabbix agent, пассивный, type 0; AD: Zabbix agent (active), type 7) по item.get 2026-10-29. В исходном плане подразумевался active на обоих; не «исправлять» молча (раздел 9)."
related_files:
  - "PROXMOX-AD-DFSR-SYSVOL-RECOVERY-2026-001"
  - "PROXMOX-AD-THIRD-DC-PROMOTION-2026-001"
  - "PROXMOX-VM2002-AD-RAM-INCREASE-2026-001"
  - "ZABBIX-STACK-INSTALL-2026-001"
  - "ZABBIX-API-CLI-ACCESS-2026-001"
last_verified: 2026-10-29
schema_version: "1.1"
---

# Мониторинг DFSR/SYSVOL и репликации AD в Zabbix на контроллерах DC и AD (krnn.ru)

## Краткий ответ

- **Что работает (VERIFIED, `item.get` по API 2026-10-29):** на узлах Zabbix `DC` и `AD` один мастер-элемент `ad.dfsr.health` (JSON), 8 зависимых элементов `ad.dfsr.*`, на `DC` дополнительно расчётный `ad.dfsr.sysvol_diff`. Итого 10 элементов на `DC` и 9 на `AD`, все включены, ни один не в состоянии unsupported.
- **Триггеры (VERIFIED по спискам из веб-интерфейса 2026-10-28/29):** 1, 2, A, B, C на обоих контроллерах, D только на `DC`; на момент проверки все в состоянии OK.
- **Зачем:** сбой DFSR и пустой SYSVOL на `AD` семь месяцев никто не замечал, мониторинга не было (см. `PROXMOX-AD-DFSR-SYSVOL-RECOVERY-2026-001`).
- **Статус:** задача закрыта администратором 2026-10-29 («цель достигнута, останавливаемся»). Срабатывание триггеров на реальном или искусственном сбое **не проверялось** (UNKNOWN).
- **Сознательно не делали:** элементы журнала «DFS Replication», события «Directory Service», счётчики NTDS (раздел 7).
- **Где смотреть данные:** Monitoring → Latest data, фильтр Hosts `DC` и `AD`, Name `AD DFSR`.

## 1. Какие сценарии закрыты

| Сценарий | Чем закрыт | Важность |
|---|---|---|
| DFSR не в состоянии 4 (как при инциденте: State 5 на `DC`, State 2 на `AD`) | триггер 1 | High |
| Шары SYSVOL или NETLOGON не опубликованы, `SysvolReady` не 1 | триггер 2 | High |
| Ошибки репликации AD DS с партнёром | триггер A | Average |
| Нет успешной репликации AD DS более 2 часов | триггер B | Average |
| Скрипт или агент перестал отдавать данные | триггер C (nodata, 20 минут) | Average |
| Содержимое SYSVOL на `DC` и `AD` разошлось (число файлов и папок политик) | триггер D, только на `DC` | Average |

Эталонное состояние для порогов (VERIFIED, 2026-10-28): DFSR State 4 на обоих, шар 2, `SysvolReady` 1, в SYSVOL 24 файла и 11 папок в `Policies` (10 рабочих GPO и одна лишняя пустая), один партнёр входящей репликации, 0 ошибок. Справочник State: 0 Uninitialized, 1 Initialized, 2 Initial Sync, 3 Auto Recovery, 4 Normal, 5 In Error.

## 2. Узлы в Zabbix

- Узлы `DC` и `AD` созданы 2026-10-28 вручную в веб-интерфейсе (Data collection → Hosts → Create host): Host name точно `DC` и `AD`, шаблон «Windows by Zabbix agent active», интерфейс Agent на порту 10050. Адреса и версии — в `AI-environment_facts-korona-proxmox.md`.
- Группа узлов у обоих — «Virtual machines» (VERIFIED, `host.get` 2026-10-29: `DC` hostid 10687, `AD` hostid 10688). Группа «Windows servers» из исходного плана не создавалась.
- На 2026-10-28 в Zabbix было элементов: `AD` 34, `DC` 48 (скриншот). Разница, вероятно, из-за незавершённого обнаружения (LLD) на `AD` (INFERRED); повторно не сверялась (раздел 9).

## 3. Агент на DC и AD

Настройка выполнена 2026-10-28 на обоих контроллерах (PowerShell от администратора). Конфиг: `C:\Program Files\Zabbix Agent 2\zabbix_agent2.conf`.

| Параметр | Значение | Примечание |
|---|---|---|
| `Server` | адрес сервера Zabbix | пассивные проверки |
| `ServerActive` | адрес сервера Zabbix | было `127.0.0.1` (по умолчанию): активный режим не работал, заменено 2026-10-28 |
| `Hostname` | `DC` / `AD` | совпадает с именем узла в Zabbix |
| `Timeout` | `30` (строка 284) | добавлено под скрипт; для элемента см. раздел 5 |
| `Include` | `C:\Program Files\Zabbix Agent 2\zabbix_agent2.d\` | сюда положен файл `ad_dfsr_health.conf` |

Резервные копии конфига: `zabbix_agent2.conf.bak_20261028` (до смены `ServerActive`; для отката поздних шагов не использовать) и `zabbix_agent2.conf.bak2_20261028` (после смены `ServerActive`, до `Timeout`).

```powershell
# [R] Проверка связи с сервером Zabbix для активных проверок (порт 10051); ожидаем TcpTestSucceeded : True
Test-NetConnection <адрес_сервера_Zabbix> -Port 10051

# [W] Резервная копия конфига перед правкой
Copy-Item "C:\Program Files\Zabbix Agent 2\zabbix_agent2.conf" "C:\Program Files\Zabbix Agent 2\zabbix_agent2.conf.bak2_20261028"

# [R] Проверка параметров после правки
Select-String -Path "C:\Program Files\Zabbix Agent 2\zabbix_agent2.conf" -Pattern '^(Server|ServerActive|Hostname|Timeout)='

# [W] Файл UserParameter (ASCII без BOM)
Set-Content -Path "C:\Program Files\Zabbix Agent 2\zabbix_agent2.d\ad_dfsr_health.conf" -Encoding ASCII -Value 'UserParameter=ad.dfsr.health,powershell -NoProfile -ExecutionPolicy Bypass -File "C:\Program Files\Zabbix Agent 2\scripts\ad_dfsr_health.ps1"'

# [W] Перезапуск агента (откат: вернуть .bak2_20261028 и удалить ad_dfsr_health.conf, затем снова перезапустить)
Restart-Service "Zabbix Agent 2"
Get-Service "Zabbix Agent 2"

# [R] Проверка ключа локально через агента: ожидаем JSON в ответе
& "C:\Program Files\Zabbix Agent 2\zabbix_agent2.exe" -c "C:\Program Files\Zabbix Agent 2\zabbix_agent2.conf" -t ad.dfsr.health
```

Результат 2026-10-28 (VERIFIED): `Timeout=30` стоит на обоих, файл `ad_dfsr_health.conf` на месте, служба Running, `zabbix_agent2 -t` возвращает JSON с эталонными значениями.

## 4. Скрипт сбора

Путь на обоих контроллерах: `C:\Program Files\Zabbix Agent 2\scripts\ad_dfsr_health.ps1`. Скрипт только читает данные и печатает одну строку JSON. Значение `-1` в поле означает, что часть данных не прочиталась (нет модуля ActiveDirectory, нет прав или WMI-класса).

```powershell
$ErrorActionPreference = 'SilentlyContinue'
$o = [ordered]@{}
$f = Get-CimInstance -Namespace root\microsoftdfs -ClassName DfsrReplicatedFolderInfo |
     Where-Object { $_.ReplicatedFolderName -eq 'SYSVOL Share' } | Select-Object -First 1
$o.dfsr_state = if ($f) { [int]$f.State } else { -1 }
$o.shares = @(Get-CimInstance -ClassName Win32_Share | Where-Object { $_.Name -in 'SYSVOL','NETLOGON' }).Count
$sr = (Get-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Services\Netlogon\Parameters').SysvolReady
$o.sysvol_ready = if ($null -ne $sr) { [int]$sr } else { -1 }
$o.sysvol_files = @(Get-ChildItem 'C:\Windows\SYSVOL\domain' -Recurse -File -Force).Count
$o.policy_dirs  = @(Get-ChildItem 'C:\Windows\SYSVOL\domain\Policies' -Directory -Force).Count
try { $m = @(Get-ADReplicationPartnerMetadata -Target $env:COMPUTERNAME -Scope Server -PartnerType Inbound -ErrorAction Stop) } catch { $m = $null }
if ($null -eq $m) { $o.repl_partners = -1; $o.repl_failed = -1; $o.repl_max_age_min = -1 }
else {
  $o.repl_partners = $m.Count
  $o.repl_failed = @($m | Where-Object { $_.LastReplicationResult -ne 0 }).Count
  $old = ($m | Sort-Object LastReplicationSuccess | Select-Object -First 1).LastReplicationSuccess
  $o.repl_max_age_min = if ($old) { [int]((Get-Date) - $old).TotalMinutes } else { -1 }
}
$o | ConvertTo-Json -Compress
```

Время выполнения (VERIFIED, `Measure-Command`, 2026-10-28): `DC` 3,36 с, `AD` 1,65 с. Часть времени уходит на холодный старт PowerShell и загрузку модуля AD. Результат на обоих: `dfsr_state` 4, `shares` 2, `sysvol_ready` 1, `sysvol_files` 24, `policy_dirs` 11, `repl_partners` 1, `repl_failed` 0, `-1` нет.

## 5. Элементы данных

### Мастер-элемент (на DC и на AD)

- Имя: «AD DFSR: сводка состояния SYSVOL и репликации AD (JSON, мастер-элемент)».
- Ключ `ad.dfsr.health`, Type of information `Text`, интервал 5m, History 7d, тег `component: ad-dfsr`.
- **Timeout = Override 30s** на обоих (VERIFIED скриншотом для `AD` 2026-10-29; для `DC` выставлено 2026-10-28 и устранило ошибку «Timeout occurred while gathering data»).
- Тип (VERIFIED, `item.get` 2026-10-29): на `DC` `type: 0` (Zabbix agent, пассивный), на `AD` `type: 7` (Zabbix agent (active)). Первоначально на `AD` после копирования с `DC` тоже был пассивный тип; администратор сменил его на active 2026-10-29, Timeout Override 30s при этом сохранился, данные пошли в течение минут.

### Зависимые элементы (на DC и на AD)

Тип Dependent item, мастер — `ad.dfsr.health` того же узла, предобработка JSONPath `$.<поле>` (для состояния поле `dfsr_state`), History 31d, Trends 365d (по умолчанию). Описание у каждого на русском: короткое пояснение, затем значения, норма и последствия отклонения. Имена с общим префиксом «AD DFSR:».

| Ключ | Что показывает (норма) | Type of information | itemid `DC` / `AD` |
|---|---|---|---|
| `ad.dfsr.state` | состояние DFSR папки SYSVOL (4) | Numeric (float) | 52992 / 53000 |
| `ad.dfsr.shares` | сколько из шар SYSVOL и NETLOGON опубликовано (2) | Numeric (unsigned) | 52993 / 53001 |
| `ad.dfsr.sysvol_ready` | признак `SysvolReady` в Netlogon (1) | Numeric (float) | 52994 / 53002 |
| `ad.dfsr.sysvol_files` | число файлов в `C:\Windows\SYSVOL\domain` (эталон 24) | Numeric (unsigned) | 52995 / 53003 |
| `ad.dfsr.policy_dirs` | число папок GPO в `SYSVOL\Policies` (эталон 11) | Numeric (unsigned) | 52996 / 53004 |
| `ad.dfsr.repl_partners` | число партнёров входящей репликации AD (эталон 1) | Numeric (float) | 52997 / 53005 |
| `ad.dfsr.repl_failed` | партнёры с ошибкой последней репликации (0) | Numeric (float) | 52998 / 53006 |
| `ad.dfsr.repl_max_age_min` | минут с последней успешной репликации AD (единицы минут; наблюдали 1–14) | Numeric (float) | 52999 / 53007 |

itemid взяты из `item.get` 2026-10-29 и меняются при пересоздании элемента (в этом случае не полагаться на них).

### Расчётный элемент (только на DC)

- Имя: «AD DFSR: расхождение SYSVOL между DC и AD (файлы + папки политик, 0 = совпадают)».
- Тип Calculated (type 15), ключ `ad.dfsr.sysvol_diff`, интервал 5m, unsigned, itemid 53008; значение 0 подтверждено в Latest data 2026-10-28.

```text
abs(last(/DC/ad.dfsr.sysvol_files)-last(/AD/ad.dfsr.sysvol_files))+abs(last(/DC/ad.dfsr.policy_dirs)-last(/AD/ad.dfsr.policy_dirs))
```

## 6. Триггеры

Выражения показаны для `DC`; на `AD` триггеры 1, 2, A, B, C скопированы (Triggers → Copy), Zabbix подставил `/AD/` вместо `/DC/` (VERIFIED по списку 2026-10-29). Интервал элементов 5 минут, поэтому `#3` означает около 15 минут, `#2` около 10.

| № | Важность | Имя | Выражение | Operational data |
|---|---|---|---|---|
| 1 | High | AD DFSR: папка SYSVOL не в нормальном состоянии на {HOST.NAME} более 15 минут | `count(/DC/ad.dfsr.state,#3,"ne",4)=3` | Состояние DFSR: {ITEM.LASTVALUE1} (норма 4) |
| 2 | High | AD DFSR: SYSVOL или NETLOGON не опубликованы на {HOST.NAME} более 10 минут | `count(/DC/ad.dfsr.shares,#2,"lt",2)=2 or count(/DC/ad.dfsr.sysvol_ready,#2,"ne",1)=2` | Опубликовано шар: {ITEM.LASTVALUE1} (норма 2), SysvolReady: {ITEM.LASTVALUE2} (норма 1) |
| A | Average | AD DFSR: ошибки репликации AD с партнёром на {HOST.NAME} более 15 минут | `count(/DC/ad.dfsr.repl_failed,#3,"ne",0)=3` | Партнёров с ошибкой: {ITEM.LASTVALUE1} (норма 0) |
| B | Average | AD DFSR: нет успешной репликации AD более 2 часов на {HOST.NAME} | `count(/DC/ad.dfsr.repl_max_age_min,#3,"gt",120)=3` | Минут с последней успешной репликации: {ITEM.LASTVALUE1} (норма до 15–60) |
| C | Average | AD DFSR: нет данных мониторинга DFSR и репликации от {HOST.NAME} более 20 минут | `nodata(/DC/ad.dfsr.health,20m)=1` | не задано |
| D (только DC) | Average | AD DFSR: содержимое SYSVOL на DC и AD различается более 15 минут | `count(/DC/ad.dfsr.sysvol_diff,#3,"ne",0)=3` | Расхождение (файлы + папки политик): {ITEM.LASTVALUE1} (норма 0) |

У каждого триггера есть Description на русском (последствия и что проверить). Порог B (120 минут) выбран с запасом: наблюдаемые значения `repl_max_age_min` были 1–14 минут; уточнять по накопленной истории, а не заранее.

Теги: `component: ad-dfsr` на `AD` есть только у триггеров 1 и 2; у A, B, C на `AD` тега нет. Администратор 2026-10-29 решил теги не добавлять («теги игнорируем»): на срабатывание это не влияет, только на фильтрацию по тегу. Есть ли тег у A, B, C на `DC`, не проверялось (UNKNOWN).

## 7. Что решено не делать

Решение администратора 2026-10-29 («чтобы не было перебора ради перебора»):

- **Элемент `eventlog` по событиям 4012, 2213, 2104** журнала «DFS Replication»: любое из них выводит DFSR из State 4, и триггер 1 сработает по состоянию. Журнал на обоих узлах существует и включён (`Get-WinEvent -ListLog`: `DC` 6790 записей, `AD` 276). Свежих тревожных событий после исправления нет; события 5008 на `AD` последний раз 13.10.
- **События «Directory Service»** (1925, 1311, 2042, 2087, 2088, 1722) и **счётчики NTDS** (например, `perf_counter_en["\NTDS\DRA Pending Replication Synchronizations"]`): эффект уже виден в `repl_failed` и `repl_max_age_min`.
- **Элемент по 5014** не вводился в план: событие шумное (код 9033 при перезапуске службы DFSR норма).
- **Value map для состояния DFSR, теги у зависимых элементов:** косметика.
- **Проверка триггеров на искусственном сбое:** сбой не создавали; настоящей проверкой считается естественное событие.

Необязательная проверка, не выполненная: правило обнаружения «Service discovery» на `DC` (шаблон «Windows by Zabbix agent active» обычно сам контролирует службы с автозапуском: NTDS, DFSR, Netlogon, DNS, kdc, W32Time). Если правило есть и включено, отдельные элементы служб не нужны.

## 8. Правила оформления (приняты администратором)

- Имя элемента или триггера — описательная строка с общим префиксом «AD DFSR: …».
- Description на русском: короткое пояснение, затем что означает каждое значение, норма, последствия и что проверить; английские названия состояний не использовать.
- Сначала элемент, потом триггер, который на него ссылается.
- Элементы, способные вернуть -1, — Numeric (float).
- Оповещения по ОС (диски, CPU) берутся из шаблона «Windows by Zabbix agent active», в этом документе не дублируются.

## 9. Открытые вопросы (UNKNOWN)

- Срабатывание триггеров на реальном событии не показано; пороги B и D по истории не пересматривались.
- Фактический состав триггеров через `trigger.get` не сверялся (запланировано в `ZABBIX-API-CLI-ACCESS-2026-001`): в протоколе 2026-10-29 фигурировало «5 триггеров на DC и 5 на AD», тогда как триггер D существует на `DC`, то есть там их 6.
- Почему мастер-элемент на `DC` пассивный (type 0), хотя в плане и в шаге создания указан active (INFERRED: на `DC` тип не менялся после создания или был изменён позже; не проверялось). Работает в обоих режимах.
- Разница 34 против 48 элементов (LLD) на `AD` и `DC` на 2026-10-28, повторная сверка не проводилась.
- Теги `component: ad-dfsr` у триггеров A, B, C на `DC`.
- Проверка «Service discovery» на `DC`.

## 10. Откат

- **Zabbix:** удалить триггеры, затем элементы (зависимые, затем мастер, на `DC` ещё расчётный) вручную: Data collection → Hosts → узел → Triggers / Items. Роль `api-rw` из `ZABBIX-API-CLI-ACCESS-2026-001` удалять через API не позволяет, это сделано намеренно. Резервная выгрузка узлов `SRV1C`, `DC`, `AD` от 2026-10-29 лежит на сервере Zabbix в `/root/zbx-backup/` (содержит состояние уже с этим мониторингом, не «до»).
- **Агент:** удалить `ad_dfsr_health.conf` и `scripts\ad_dfsr_health.ps1`, вернуть `zabbix_agent2.conf.bak2_20261028`, перезапустить службу.

## 11. Связанные документы

- `PROXMOX-AD-DFSR-SYSVOL-RECOVERY-2026-001` — инцидент, из-за которого заведён мониторинг; его раздел 9 писался до передачи состава мониторинга и ссылается на «UNKNOWN».
- `ZABBIX-API-CLI-ACCESS-2026-001` — доступ к Zabbix API из командной строки, через который 2026-10-29 прочитаны элементы этого мониторинга.
- `ZABBIX-STACK-INSTALL-2026-001` — сервер Zabbix.
- `PROXMOX-AD-THIRD-DC-PROMOTION-2026-001`, `PROXMOX-VM2002-AD-RAM-INCREASE-2026-001` — контроллер `AD` (ВМ 2002).

## Источник

Три экспорта чатов (`user_input`, `command_output`): «Мониторинг AD DC и SYSVOL в Zabbix №1» (2026-10-28), «№2» (2026-10-28/29) и «cmd на zabbix» (2026-10-29, чтение элементов через `item.get`, `host.get`). Сырые копии в `Proxmox/` не помещены. Выводы PowerShell, скриншоты списков элементов и триггеров и значения Latest data предоставлены администратором. Фактическое состояние элементов на 2026-10-29 подтверждено ответами API (`item.get`), состав триггеров — по спискам из веб-интерфейса, не по API. Справочник State и событий DFSR — общие знания о DFSR, без ссылки на документацию Microsoft (INFERRED).
