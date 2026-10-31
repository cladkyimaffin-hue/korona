---
document_id: "ZABBIX-API-CLI-ACCESS-2026-001"
title: "Доступ к Zabbix API из командной строки: пользователи api-ro и api-rw, роли, группы, токены и порядок записи"
document_type: "runbook"
status: "completed"
priority: "medium"
date_created: 2026-10-31
date_modified: 2026-10-31
next_review: 2026-11-25
author: "cladkyimaffin-hue"
category: "08_Monitoring/Zabbix"
tags:
  - Zabbix
  - Security
  - Configuration
  - Automation
  - Bash
  - Debian12
  - Setup
ai_summary: "Как управлять Zabbix 7.0.31 из командной строки с самого сервера Zabbix (Debian 12): API по адресу http://localhost/api_jsonrpc.php (без /zabbix/), два контура: api-ro (чтение, только методы *.get) и api-rw (создание и изменение элементов и триггеров, экспорт конфигурации, без удаления), у каждого своя роль, группа пользователей, пользователь и токен в файле с правами 600 (/root/.zbx_ro_token, /root/.zbx_rw_token). Токены передаются заголовком через конвейер, не попадают в историю и чат. Документ нужен для воспроизведения настройки, проверки прав (editable, запрет host.update), порядка записи с резервной выгрузкой и ручным откатом, и чтобы не повторить ошибки: пустой host.get из-за Deny или ненажатой ссылки Add в Host permissions, неверный путь API. Открыто: токен api-rw-cli действует до 2026-11-28, права обеих групп выданы на все 8 групп узлов, судьба бессрочного токена zabbix в учётной записи администратора."
dont_repeat:
  - "Адрес API в этой установке: http://localhost/api_jsonrpc.php, без префикса /zabbix/. Запрос на /zabbix/api_jsonrpc.php даёт «File not found.» (ответ php-fpm за nginx)."
  - "В Host permissions группы пользователей выбранные группы узлов нужно добавить внутренней ссылкой Add под полем выбора до нажатия нижней кнопки формы. Без этого права не сохраняются, и host.get и hostgroup.get возвращают пустой список (так было с api-ro-group, 2026-10-29). Переключатель по умолчанию мог стоять на Deny: Deny приоритетнее любых других прав."
  - "Токен создавать в меню Users → API tokens, а не в User settings → API tokens: последнее создаёт токены только для своей учётной записи."
  - "Значение токена Zabbix показывает один раз. Не закрывать окно, пока токен не сохранён на сервере; иначе удалить токен и создать новый. Токен не вставлять в команду, чат, скрипт и документацию: ввод только через read -rsp."
  - "Метода удаления в роли api-rw нет намеренно (item.delete, trigger.delete): лишние объекты удаляются вручную в веб-интерфейсе. Откат API-записи через API невозможен."
  - "Права api-rw-group — Read-write на все 8 групп узлов (решение администратора 2026-10-29; в плане было только «Virtual machines» и «Databases»). Через токен api-rw-cli можно создавать и менять элементы и триггеры на любом узле, включая Zabbix server, pve01 и pve02."
  - "Строки ^[[200~ в терминале после вставки (bracketed paste) и обрезанные начала строк в присланных выводах — артефакт копирования, на результат не влияют."
related_files:
  - "ZABBIX-STACK-INSTALL-2026-001"
  - "ZABBIX-AD-DFSR-MONITORING-2026-001"
  - "ZABBIX-PVE-API-MONITORING-2026-001"
last_verified: 2026-10-29
schema_version: "1.1"
---

# Доступ к Zabbix API из командной строки: пользователи api-ro и api-rw, роли, группы, токены и порядок записи

## Краткий ответ

- **Откуда:** команды выполняются на самом сервере Zabbix (Debian 12, Zabbix 7.0.31), запросы идут на `http://localhost/api_jsonrpc.php`. Сеть и firewall между машинами не нужны. Версия подтверждена ответом `apiinfo.version` (VERIFIED, 2026-10-29).
- **Два контура (VERIFIED):** `api-ro` читает (методы `*.get`), `api-rw` создаёт и меняет элементы и триггеры и выгружает конфигурацию (`configuration.export`), но ничего не удаляет.
- **Токены:** `/root/.zbx_ro_token` и `/root/.zbx_rw_token`, права `-rw-------`, 64 символа. В документе и чате значений нет.
- **Проверено боевой записью:** тестовый элемент создан через `item.create` под `api-rw-cli`, прочитан под `api-ro-cli`, удалён администратором вручную (2026-10-29).
- **Резервная выгрузка:** `/root/zbx-backup/hosts_SRV1C_DC_AD_2026-10-29.json` (118 608 байт, права 600, формат 7.0, узлы AD, DC, SRV1C).
- **Срок:** токен `api-rw-cli` действует до **2026-11-28**: продлить заранее (раздел 9).

## 1. Принципы

- У каждого контура своя роль, группа пользователей, пользователь и токен.
- Права минимальные: роль чтения разрешает только `*.get`, роль записи — создание и изменение элементов и триггеров без удаления.
- Токен хранится в файле с правами 600, вводится скрытым вводом и не попадает в историю команд, скрипты, чат и документы.
- У токена записи ограниченный срок.
- Любая запись — после резервной выгрузки и явного подтверждения администратора с указанием `hostid`.
- Сначала чтение, потом изменение.

## 2. Окружение (VERIFIED, 2026-10-29)

- ОС сервера Zabbix: Debian 12 (bookworm), `curl` установлен, `python3` установлен (`/usr/bin/python3`).
- `jq` был не установлен; установлен `apt-get install -y jq` (jq-1.6, пакет `1.6-2.1+deb12u2`).
- Путь API: `http://localhost/api_jsonrpc.php` (HTTP). `/zabbix/api_jsonrpc.php` отвечает «File not found.».
- Версия Zabbix: 7.0.31.

```bash
# [W] Установка jq (откат: apt-get remove -y jq)
apt-get install -y jq
jq --version

# [R] Доступность API, авторизация не нужна: ожидаем {"jsonrpc":"2.0","result":"7.0.31","id":1}
curl -s -X POST -H "Content-Type: application/json-rpc" \
  -d '{"jsonrpc":"2.0","method":"apiinfo.version","params":[],"id":1}' \
  http://localhost/api_jsonrpc.php
```

## 3. Что создано

| Объект | Имя | Параметры |
|---|---|---|
| Роль чтения | `api-ro` (roleid 5) | User type `User`, UI-элементы и действия сняты, API: Allow list `*.get`, `apiinfo.version` |
| Группа чтения | `api-ro-group` (usrgrpid 14) | Frontend access Internal, включена, Read на все 8 групп узлов |
| Пользователь чтения | `api-ro` (userid 3) | роль `api-ro`, группа `api-ro-group`, пароль случайный, в API не используется |
| Токен чтения | `api-ro-cli` | файл `/root/.zbx_ro_token`; срок в итоговом протоколе указан до 2026-11-28 (INFERRED для этого токена) |
| Роль записи | `api-rw` | User type `Admin`, API: `*.get`, `apiinfo.version`, `item.create`, `item.update`, `trigger.create`, `trigger.update`, `configuration.export` |
| Группа записи | `api-rw-group` | Read-write на все 8 групп узлов (отступление от плана, решение администратора) |
| Пользователь записи | `api-rw` | роль `api-rw`, группа `api-rw-group`, пароль случайный, в API не используется |
| Токен записи | `api-rw-cli` | файл `/root/.zbx_rw_token`, срок до **2026-11-28** |

Настройки внутри ролей на скриншотах списка не видны; их корректность подтверждена поведением: под `api-ro-cli` проходит `host.get` и отклоняется `host.update`, под `api-rw-cli` проходят `configuration.export` и `item.create`.

Группы узлов, видимые обоим пользователям (VERIFIED, `hostgroup.get`): Applications (19), Databases (20), Discovered hosts (5), Hypervisors (7), Linux servers (2), Proxmox VE (22), Virtual machines (6), Zabbix servers (4).

Узлы (VERIFIED, `host.get`, все включены):

| Узел | hostid | Группы |
|---|---|---|
| Zabbix server | 10084 | Zabbix servers |
| pve01 | 10683 | Proxmox VE |
| pve02 | 10685 | Proxmox VE |
| SRV1C | 10686 | Databases, Virtual machines |
| DC | 10687 | Virtual machines |
| AD | 10688 | Virtual machines |

В учётной записи администратора существует бессрочный токен `zabbix` (создан 2026-10-26 11:17:43, статус Enabled, использовался: Never; скриншот User settings → API tokens, 2026-10-29). Им не пользовались; решение о его судьбе не принято (раздел 10).

## 4. Создание контура чтения (api-ro)

Веб-интерфейс Zabbix под учётной записью администратора.

1. **Роль:** Users → User roles → Create user role. Name `api-ro`, User type `User`, Access to UI elements — снять все галочки, Access to API — Enabled, режим Allow list, методы `*.get` и `apiinfo.version`, Access to actions — снять все галочки. Метод `configuration.export` под маску `*.get` не попадает.
2. **Группа:** Users → User groups → Create user group. Group name `api-ro-group`, Frontend access Internal, Enabled, Debug mode выключен. Вкладка Host permissions: Select, отметить нужные группы узлов, в переключателе справа выбрать **Read**, нажать внутреннюю ссылку **Add** под полем групп (над полем должны появиться строки с правом Read), и только затем нижнюю кнопку формы. Deny не использовать.
3. **Пользователь:** Users → Users → Create user. Username `api-ro`, Groups `api-ro-group`, пароль случайный не короче 16 символов (хранить в Vaultwarden, в чат не присылать), вкладка Permissions, Role `api-ro`.
4. **Токен:** Users → **API tokens** → Create API token. Name `api-ro-cli`, User `api-ro`, включить срок действия и задать дату, Enabled. Окно с токеном не закрывать до шага 5.
5. **Сохранение токена на сервере** (терминал на сервере Zabbix):

```bash
# [W] Создаёт файл с правами 600 и записывает токен скрытым вводом (на экране и в истории его не будет)
install -m 600 /dev/null /root/.zbx_ro_token
read -rsp 'Вставьте токен и нажмите Enter: ' T; echo
printf '%s' "$T" > /root/.zbx_ro_token; unset T
# [R] Ожидаем -rw------- root и размер 64
ls -l /root/.zbx_ro_token
wc -c /root/.zbx_ro_token
```

Откат: Users → API tokens → отметить `api-ro-cli` → Delete, на сервере `rm /root/.zbx_ro_token`; затем удалить пользователя, группу и роль в обратном порядке.

## 5. Контур записи (api-rw)

По той же схеме, что и контур чтения, со следующими отличиями:

- Роль `api-rw`: User type **Admin** (тип `User` не может создавать элементы и триггеры), API Allow list: `*.get`, `apiinfo.version`, `item.create`, `item.update`, `trigger.create`, `trigger.update`, `configuration.export`. Методов `*.delete`, `host.*`, `user.*` и настроек в списке нет намеренно.
- Группа `api-rw-group`: право **Read-write** на группы узлов, где разрешено менять объекты; ссылка Add обязательна. План был — только «Virtual machines» и «Databases», фактически выдано на все 8 групп.
- Пользователь `api-rw`: роль `api-rw`, группа `api-rw-group`.
- Токен `api-rw-cli`: срок 30 дней (до 2026-11-28), файл `/root/.zbx_rw_token`, ввод теми же командами, что в разделе 4, с заменой имени файла.

## 6. Проверка прав (только чтение)

```bash
# [R] Узлы и их группы под токеном чтения
printf 'Authorization: Bearer %s\n' "$(cat /root/.zbx_ro_token)" | \
curl -s -X POST -H "Content-Type: application/json-rpc" -H @- \
  -d '{"jsonrpc":"2.0","method":"host.get","params":{"output":["hostid","host","status"],"selectHostGroups":["groupid","name"]},"id":1}' \
  http://localhost/api_jsonrpc.php | jq -c '.result[] | {hostid, host, status, groups: [.hostgroups[].name]}'

# [R] Кто такой пользователь, его роль и группы (при пустом host.get смотреть сюда)
printf 'Authorization: Bearer %s\n' "$(cat /root/.zbx_ro_token)" | \
curl -s -X POST -H "Content-Type: application/json-rpc" -H @- \
  -d '{"jsonrpc":"2.0","method":"user.get","params":{"output":["userid","username"],"selectRole":["roleid","name","type"],"selectUsrgrps":["usrgrpid","name","users_status","gui_access"]},"id":1}' \
  http://localhost/api_jsonrpc.php | jq .

# [R] Запрет записи: узла 99999999 нет, изменить нечего. Ожидаем «No permissions to call "host.update"»
printf 'Authorization: Bearer %s\n' "$(cat /root/.zbx_ro_token)" | \
curl -s -X POST -H "Content-Type: application/json-rpc" -H @- \
  -d '{"jsonrpc":"2.0","method":"host.update","params":{"hostid":"99999999","status":0},"id":1}' \
  http://localhost/api_jsonrpc.php | jq .

# [R] Что токен записи может ИЗМЕНЯТЬ (параметр editable оставляет только объекты с правом Read-write)
printf 'Authorization: Bearer %s\n' "$(cat /root/.zbx_rw_token)" | \
curl -s -X POST -H "Content-Type: application/json-rpc" -H @- \
  -d '{"jsonrpc":"2.0","method":"host.get","params":{"output":["hostid","host"],"editable":true},"id":1}' \
  http://localhost/api_jsonrpc.php | jq -c '.result[]'
```

Результаты 2026-10-29 (VERIFIED): под `api-ro-cli` видны все 6 узлов; `host.update` отклонён с `No permissions to call "host.update"` (метод заблокирован ролью, а не только правами на узлы); под `api-rw-cli` с `editable: true` вернулись все 8 групп и все 6 узлов, то есть право записи есть везде.

## 7. Порядок записи

1. **Резервная выгрузка** конфигурации нужных узлов до первой записи.
2. **Чтение текущего состояния** (`item.get`, `trigger.get`) токеном чтения.
3. **Запись** одним вызовом после подтверждения администратора. Элементы, способные вернуть -1, — Numeric (float); имена описательные, Description на русском; элемент создаётся раньше триггера.
4. **Проверка** чтением токеном `api-ro-cli`.
5. **Откат:** метода удаления в роли нет, лишние объекты удаляются вручную (Data collection → Hosts → узел → Items или Triggers). Если удалён не тот объект, состояние восстанавливается по резервной выгрузке.

```bash
# [W] Резервная выгрузка узлов SRV1C (10686), DC (10687), AD (10688) в файл с правами 600
install -d -m 700 /root/zbx-backup
printf 'Authorization: Bearer %s\n' "$(cat /root/.zbx_rw_token)" | \
curl -s -X POST -H "Content-Type: application/json-rpc" -H @- \
  -d '{"jsonrpc":"2.0","method":"configuration.export","params":{"options":{"hosts":["10686","10687","10688"]},"format":"json"},"id":1}' \
  http://localhost/api_jsonrpc.php | jq -r '.result // .error' > /root/zbx-backup/hosts_SRV1C_DC_AD_2026-10-29.json
chmod 600 /root/zbx-backup/hosts_SRV1C_DC_AD_2026-10-29.json
ls -l /root/zbx-backup/
# [R] Ожидаем ["7.0",["AD","DC","SRV1C"]] (порядок узлов может отличаться)
jq -c '[.zabbix_export.version, [.zabbix_export.hosts[].host]]' /root/zbx-backup/hosts_SRV1C_DC_AD_2026-10-29.json
```

Шаблоны, на которые ссылаются узлы, в выгрузку не входят: выгружаются сами узлы и их собственные объекты.

Проверочная запись 2026-10-29 (VERIFIED): выключенный элемент типа Zabbix trapper на `DC`, не опрашивает агента и не уходит в unsupported.

```bash
# [W] Создаёт один выключенный элемент на DC (10687). Откат: удалить вручную в веб-интерфейсе
printf 'Authorization: Bearer %s\n' "$(cat /root/.zbx_rw_token)" | \
curl -s -X POST -H "Content-Type: application/json-rpc" -H @- \
  -d '{"jsonrpc":"2.0","method":"item.create","params":{"hostid":"10687","name":"Тест записи через API (можно удалить)","key_":"api.test.write","type":2,"value_type":4,"status":1},"id":1}' \
  http://localhost/api_jsonrpc.php | jq -c .
```

Результат: `itemids: ["53009"]`; чтение под `api-ro-cli` вернуло `type: "2"`, `value_type: "4"`, `status: "1"`, `state: "0"`. Администратор удалил элемент вручную 2026-10-29 (со слов администратора; проверочный запрос после удаления в источниках не приведён).

## 8. Типичные ошибки

| Симптом | Причина | Что делать |
|---|---|---|
| `File not found.` | неверный путь API | использовать `/api_jsonrpc.php` без `/zabbix/` |
| `host.get` и `hostgroup.get` возвращают `[]` | у группы пользователей не сохранились права на группы узлов (выбран Deny или не нажата ссылка Add) | Users → User groups → группа → Host permissions: Read, ссылка Add, затем Update |
| `Not authorized` или `Session terminated` | токен отключён, просрочен или сохранён неверно | проверить Enabled и срок в Users → API tokens, размер файла 64 байта |
| `No permissions to call "..."` | метод не входит в Allow list роли | для записи — проверить роль `api-rw`; для чтения это ожидаемо при записи под `api-ro` |
| `No permissions to referred object or it does not exist!` | нет права записи на группу узла либо объекта нет | проверить `editable: true`, права `api-rw-group` |
| `wc -c` показывает не 64 | вставлен лишний текст или не весь токен | удалить токен и создать новый; содержимое файла в чат не присылать |
| Окно с токеном закрыто до сохранения | значение повторно не показывается | удалить токен и создать новый |

## 9. Эксплуатация и риски

- **Срок токенов:** `api-rw-cli` до 2026-11-28; внести в календарь. Продление: создать новый токен, заменить файл, удалить старый токен. Срок `api-ro-cli` в источниках явно не подтверждён.
- **Утечка:** удалить токен (Users → API tokens → Delete), на сервере `rm` файла токена.
- **Широкие права:** `api-ro-group` и `api-rw-group` выданы на все 8 групп. Через токен записи можно менять элементы и триггеры на `pve01`, `pve02` и `Zabbix server`. Защита: роль без удаления и без методов узлов, пользователей и настроек, срок токена, подтверждение каждой записи. Рекомендация (не принята): сузить права до «Virtual machines» и «Databases».
- **Файлы токенов** лежат в `/root` сервера Zabbix: доступ у всех, кто имеет root на этом контейнере или узле Proxmox.
- **Резервные выгрузки** в `/root/zbx-backup/` хранить с правами 600 и удалять, когда они не нужны.

## 10. Открытые вопросы (UNKNOWN)

- Судьба бессрочного токена `zabbix` в учётной записи администратора: нужен ли, оставить, отключить или удалить.
- Сужение прав `api-ro-group` и `api-rw-group` (раздел 9).
- Дата окончания токена `api-ro-cli`.
- Сверка `trigger.get` по `DC` и `AD` с веб-интерфейсом (в `ZABBIX-AD-DFSR-MONITORING-2026-001` состав триггеров взят из веб-интерфейса, не из API).
- Триггеры MSSQL на `SRV1C` (шаг 3.3 прежнего плана): через API или веб, не выполнялось; перед записью нужно прочитать элементы `SRV1C` (`item.get`, hostid 10686).

## 11. Связанные документы

- `ZABBIX-AD-DFSR-MONITORING-2026-001` — мониторинг, элементы которого прочитаны через этот API.
- `ZABBIX-STACK-INSTALL-2026-001` — установка сервера Zabbix (в нём открыты вопросы по паролям).
- `ZABBIX-PVE-API-MONITORING-2026-001` — другой API: Proxmox API и токен `PVEAPIToken` для шаблона Proxmox VE by HTTP (не путать с токенами Zabbix API).

## Источник

Чат «cmd на zabbix» (2026-10-29; `user_input`, `command_output`; сырая копия в `Proxmox/` не помещена) и инструкция администратора `Chat-Qwen/Zabbix/Инструкции/API ключи в zabix user group rule.md` (добавлена в репозиторий 2026-10-30): документ сверен с ней и с выводами команд. Значения токенов и пароли в источниках отсутствуют и сюда не переносились. Скриншоты ролей и групп в источнике не позволяют прочитать все настройки внутри ролей; они подтверждены поведением API (раздел 3).
