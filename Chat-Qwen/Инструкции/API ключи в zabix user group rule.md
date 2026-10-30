# Инструкция: доступ к API Zabbix из командной строки

Пользователи, группы и API-токены. Zabbix 7.0.31, сервер 192.168.200.223, дата составления 29.10.2026.

## 1. Назначение и принципы

Документ описывает, как создать пользователей, группы и API-токены для управления Zabbix из командной строки без веб-интерфейса. Схема состоит из двух контуров: чтение (пользователь `api-ro`) и запись (пользователь `api-rw`).

Принципы, на которых построена схема:

- у каждого контура своя роль, своя группа пользователей, свой пользователь и свой токен;
- права минимальные: роль чтения разрешает только методы `*.get`, роль записи разрешает создание и изменение элементов и триггеров, но не удаление;
- токен хранится на сервере в файле с правами 600, вводится скрытым вводом и не попадает в историю команд, скрипты и переписку;
- у токена записи ограниченный срок действия;
- каждая запись выполняется после резервной копии конфигурации и явного подтверждения администратора.

## 2. Подготовка

Команды выполняются в терминале на сервере Zabbix (Debian 12). Адрес API: `http://localhost/api_jsonrpc.php`, без префикса `/zabbix/`. Нужны `curl` и `jq`:

```bash
apt-get install -y jq
jq --version
```

Проверка доступности API (не требует авторизации):

```bash
curl -s -X POST -H "Content-Type: application/json-rpc" \
  -d '{"jsonrpc":"2.0","method":"apiinfo.version","params":[],"id":1}' \
  http://localhost/api_jsonrpc.php
```

Ожидаемый ответ: `{"jsonrpc":"2.0","result":"7.0.31","id":1}`.

## 3. Контур чтения (api-ro)

### 3.1. Роль

Users → User roles → Create user role.

- Name: `api-ro`
- User type: `User`
- Access to UI elements: снять все галочки
- Access to API: Enabled, режим Allow list, методы `*.get` и `apiinfo.version`
- Access to actions: снять все галочки
<img width="1122" height="848" alt="image" src="https://github.com/user-attachments/assets/940866dd-0296-4df8-9140-ec5d5c7140bd" />

### 3.2. Группа пользователей

Users → User groups → Create user group.

- Group name: `api-ro-group`, Frontend access: Internal, Enabled
- Вкладка Host permissions: Select, отметить нужные группы узлов, в переключателе выбрать **Read**, нажать ссылку **Add** под полем групп (в списке должны появиться строки с правом Read), затем нажать кнопку сохранения формы.

Важно: право Deny имеет приоритет над остальными. Если группы выбраны, но не добавлены ссылкой Add, права не сохраняются, и пользователь не увидит ни одного узла.
<img width="1090" height="619" alt="image" src="https://github.com/user-attachments/assets/29668bec-8074-4d62-92ab-c5bec44a99ac" />
<img width="1433" height="349" alt="image" src="https://github.com/user-attachments/assets/0d2bddec-a41c-47cb-a2cc-ca3a57f60f74" />

### 3.3. Пользователь

Users → Users → Create user.

- Username: `api-ro`, Groups: `api-ro-group`
- Password: случайный, не короче 16 символов; для работы через API не используется, хранить в менеджере паролей
- Вкладка Permissions, Role: `api-ro`
<img width="1103" height="791" alt="image" src="https://github.com/user-attachments/assets/9a51b36b-f88d-41c5-a70d-c9ac6c0752c1" />
<img width="949" height="408" alt="image" src="https://github.com/user-attachments/assets/8c4d66bd-3bb4-4ffc-9dc1-14ea3a643320" />

### 3.4. API-токен

Users → API tokens → Create API token (раздел меню Users, а не User settings: последний создаёт токены только для своей учётной записи).

- Name: `api-ro-cli`, User: `api-ro`
- Set expiration date and time: включить и задать срок
- Enabled: включено

Значение токена показывается один раз. Окно нельзя закрывать, пока токен не сохранён на сервере.
<img width="1380" height="675" alt="image" src="https://github.com/user-attachments/assets/bbdb5c93-62e6-4995-b902-fbed74a5d9a6" />

### 3.5. Сохранение токена на сервере

```bash
install -m 600 /dev/null /root/.zbx_ro_token
read -rsp 'Вставьте токен и нажмите Enter: ' T; echo
printf '%s' "$T" > /root/.zbx_ro_token; unset T
ls -l /root/.zbx_ro_token
wc -c /root/.zbx_ro_token
```

Ожидается: права `-rw-------`, владелец root, размер 64 байта.

### 3.6. Проверка

Список узлов (токен передаётся через конвейер и не виден в списке процессов):

```bash
printf 'Authorization: Bearer %s\n' "$(cat /root/.zbx_ro_token)" | \
curl -s -X POST -H "Content-Type: application/json-rpc" -H @- \
  -d '{"jsonrpc":"2.0","method":"host.get","params":{"output":["hostid","host","status"]},"id":1}' \
  http://localhost/api_jsonrpc.php | jq -c '.result[]'
```

Проверка запрета записи (узла с таким идентификатором нет, изменить ничего нельзя):

```bash
printf 'Authorization: Bearer %s\n' "$(cat /root/.zbx_ro_token)" | \
curl -s -X POST -H "Content-Type: application/json-rpc" -H @- \
  -d '{"jsonrpc":"2.0","method":"host.update","params":{"hostid":"99999999","status":0},"id":1}' \
  http://localhost/api_jsonrpc.php | jq .
```

Ожидается ответ `No permissions to call "host.update"`.

## 4. Контур записи (api-rw)

Создаётся по той же схеме, что и контур чтения, со следующими отличиями.

- Роль `api-rw`: User type **Admin**; методы Allow list: `*.get`, `apiinfo.version`, `item.create`, `item.update`, `trigger.create`, `trigger.update`, `configuration.export`. Методов удаления и методов работы с узлами, пользователями и настройками в списке нет намеренно.
- Группа `api-rw-group`: права **Read-write** на группы узлов, где разрешено создавать и менять элементы и триггеры (ссылка Add обязательна, как в п. 3.2).
- Пользователь `api-rw`: роль `api-rw`, группа `api-rw-group`.
- Токен `api-rw-cli`: короткий срок действия (30 дней), сохраняется в `/root/.zbx_rw_token` теми же командами, что в п. 3.5, с заменой имени файла.

Проверка прав записи: запросы `hostgroup.get` и `host.get` с параметром `"editable":true` возвращают только те группы и узлы, на которые есть право Read-write.

## 5. Порядок выполнения записи

1. **Резервная копия.** Перед первой записью выгрузить конфигурацию нужных узлов (в примере узлы с идентификаторами 10686, 10687, 10688):

```bash
install -d -m 700 /root/zbx-backup
printf 'Authorization: Bearer %s\n' "$(cat /root/.zbx_rw_token)" | \
curl -s -X POST -H "Content-Type: application/json-rpc" -H @- \
  -d '{"jsonrpc":"2.0","method":"configuration.export","params":{"options":{"hosts":["10686","10687","10688"]},"format":"json"},"id":1}' \
  http://localhost/api_jsonrpc.php | jq -r '.result // .error' > /root/zbx-backup/hosts_2026-10-29.json
chmod 600 /root/zbx-backup/hosts_2026-10-29.json
```

2. **Чтение текущего состояния** (`item.get`, `trigger.get`) токеном чтения.
3. **Запись** одним вызовом после подтверждения администратора. Для элементов, которые могут вернуть -1, тип данных Numeric (float). Имена элементов и триггеров описательные, Description на русском: короткое пояснение, затем значения, норма, последствия. Элемент создаётся раньше триггера.
4. **Проверка** чтением токеном `api-ro-cli`.
5. **Откат.** Метода удаления в роли записи нет, поэтому лишние объекты удаляются вручную в веб-интерфейсе (Data collection → Hosts → узел → Items или Triggers). Если удалён не тот объект, состояние восстанавливается по резервной копии.

Пример проверочной записи: выключенный элемент типа Zabbix trapper на узле DC.

```bash
printf 'Authorization: Bearer %s\n' "$(cat /root/.zbx_rw_token)" | \
curl -s -X POST -H "Content-Type: application/json-rpc" -H @- \
  -d '{"jsonrpc":"2.0","method":"item.create","params":{"hostid":"10687","name":"Тест записи через API (можно удалить)","key_":"api.test.write","type":2,"value_type":4,"status":1},"id":1}' \
  http://localhost/api_jsonrpc.php | jq -c .
```

Ожидается ответ с полем `itemids`. После проверки элемент удаляется вручную.

## 6. Типичные проблемы

- **`File not found.`** при вызове API: неверный путь. В данной установке API доступен как `/api_jsonrpc.php`, без `/zabbix/`.
- **`host.get` возвращает пустой список:** у группы пользователей не сохранились права на группы узлов (выбран Deny вместо Read или не нажата ссылка Add).
- **`Not authorized` или `Session terminated`:** токен отключён, просрочен или сохранён неверно (проверить размер файла: 64 байта).
- **`No permissions to call "..."`:** метод не входит в список разрешённых методов роли.
- **`No permissions to referred object or it does not exist!`:** нет права записи на группу узла либо объект не существует.
- **Строки вида `^[[200~` в терминале:** артефакт вставки (bracketed paste), на результат не влияет.

## 7. Эксплуатация и рекомендации

- Сроки действия токенов внести в календарь. Токен `api-rw-cli` действует до 2026-11-28. Продление: создать новый токен, заменить файл, удалить старый токен.
- При подозрении на утечку удалить токен: Users → API tokens → отметить токен → Delete; файл на сервере удалить командой `rm`.
- В текущей настройке группы `api-ro-group` и `api-rw-group` имеют права на все группы узлов. Рекомендуется сузить права до групп, где лежат обслуживаемые узлы (например, «Virtual machines» и «Databases»), а Read-write оставить только там, где требуется запись.
- В учётной записи администратора существует бессрочный токен `zabbix` (создан 2026-10-26, не использовался). Рекомендуется решить, нужен ли он, и при отсутствии потребности отключить или удалить.
- Резервные копии из `/root/zbx-backup/` хранить с правами 600 и удалять, когда они перестают быть нужными.
