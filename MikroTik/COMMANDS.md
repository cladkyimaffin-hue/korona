---
schema_version: "1.1"
status: "in_progress"
date_created: 2026-10-24
date_modified: 2026-10-24
maintainer: "cladkyimaffin-hue"
file_type: "commands_reference"
confidence: "Команды перенесены из документов домена без изменения смысла; контекст, ожидаемый вывод и ограничения — в документе-источнике. Покрытие неполное: список источников и то, что не вошло, — в конце файла."
---

# COMMANDS.md — команды MikroTik (RouterOS)

Справочник команд, к которым нужно возвращаться, отдельно от общих описаний.
Команды остаются и в своих документах (там контекст, ожидаемый вывод и
ограничения), здесь — быстрый доступ, сгруппированный по задачам.

## Как пользоваться

Каждый блок начинается со строки-комментария: `[класс] что делает — источник`.

Классы риска:

- **[R]** — только чтение. Безопасно выполнять для диагностики.
- **[W]** — меняет конфигурацию или состояние устройства. Перед выполнением
  проверить текущее состояние (`print`), знать откат.
- **[D]** — разрушающая или необратимая (удаление правил, объектов). Только по
  явному подтверждению администратора (метка `REQUIRES_APPROVAL`, см.
  `AI-INSTRUCTIONS.md`, раздел 3.3).

Правила:

- **Блок с несколькими командами — перечень, а не скрипт.** Выполнять нужные
  строки по одной. Только если в комментарии написано «по порядку», команды
  блока выполняются подряд.
- `<угловые скобки>` — плейсхолдер, подставить своё значение. Конкретные адреса,
  имена интерфейсов и подсети брать из `AI-environment_facts-korona-mikrotik.md`
  или из свежего вывода команд, не из этого файла.
- Секреты (пароли, парольные фразы, приватные ключи) здесь не хранятся.
- Команды выполняются в терминале RouterOS (SSH, Winbox, WebFig) на устройстве,
  указанном в комментарии блока. Если устройство не указано, имеется в виду
  основной маршрутизатор.
- Номера правил в `print` (`#0`, `#10`, …) меняются после добавления и удаления
  правил: номер брать из свежего вывода, не из документов.
- Все исправления из аудита 2026-09-19 на момент документов-источников НЕ
  применялись. Применены ли они сейчас, проверять на устройстве, а не по этому файлу.
- Источник указан как `document_id` из `00_Meta/registry.csv`.

---

## 1. Диагностика: чтение состояния

```routeros
# [R] Базовый набор для диагностики — MikroTik/START-HERE.md
/interface print detail
/ip address print detail
/ip route print detail
/ip firewall filter print detail
/ip firewall nat print detail
/interface wireguard print detail
/log print
```

```routeros
# [R] Policy routing отсутствует? — NETWORK-MIKROTIK-TOPOLOGY-2026-001
# Ожидается: пустой вывод mangle (нет mark-routing); в маршрутах — default и connected
/ip firewall mangle print
/ip route print detail
```

```routeros
# [R] Маршрутизируется ли подсеть — NETWORK-MIKROTIK-VPN-PROFILE-BROKEN-2026-001
# Пустой результат означает, что подсеть нигде не маршрутизируется на устройстве.
# Наличие активных VPN-сессий не доказывает, что VPN работает: смотреть, из какой подсети
# клиент получил адрес и маршрутизируется ли она
/ip route print where dst-address~"<часть_адреса_подсети>"
```

```routeros
# [R] Журнал: нестабильный линк порта — NETWORK-MIKROTIK-TOPOLOGY-2026-001
# Признак flapping: повторяющиеся link down / link up у одного порта с чередованием скорости
# (в источнике 10M и 1G каждые 10–15 секунд). Это физическая проблема (патч-корд, порт,
# устройство на другом конце), командами RouterOS она не устраняется
/log print
```

## 2. Firewall и NAT

RouterOS обрабатывает правила по порядку, первое совпадение побеждает: правило, стоящее после
`accept all`, никогда не сработает. Перед правкой порядка сначала решить, нужен ли `accept all`
вообще, а не просто переставить правила (`NETWORK-MIKROTIK-FIREWALL-NAT-CLEANUP-2026-001`).

```routeros
# [R] Счётчики пакетов и байтов по правилам Filter — NETWORK-MIKROTIK-FIREWALL-NAT-CLEANUP-2026-001
# Не удалять правило только потому, что оно «выглядит мёртвым»: сверять счётчики
/ip firewall filter print stats
```

```routeros
# [R] Есть ли внешний порт в NAT — NETWORK-MIKROTIK-REMOTE-ACCESS-PROCEDURE-2026-001
# Перед выдачей нового внешнего порта сверяться с фактическим выводом на устройстве,
# а не с реестром портов в документе (он исторический, снимок 2026-09-20)
/ip firewall nat print
/ip firewall nat print where dst-port=<порт>
```

```routeros
# [W] Добавить проброс порта (dstnat) на один сервер — NETWORK-MIKROTIK-REMOTE-ACCESS-PROCEDURE-2026-001
# Предварительно проверить, что внешний порт свободен (блок выше). Без dst-address правило
# самое универсальное и действует для любого адреса роутера; привязка к публичному IP — по
# решению администратора. src-address — внешний адрес источника ПОСЛЕ NAT его провайдера,
# не внутренний; для «любого» источника строку src-address убрать. Паттерн с dst-address
# легаси-подсети (см. раздел 2, очистка) для новых правил без проверки на устройстве не использовать
/ip firewall nat add chain=dstnat action=dst-nat protocol=tcp \
  in-interface=<WAN-интерфейс> \
  src-address=<источник> \
  dst-port=<внешний порт> \
  to-addresses=<внутренний IP сервера> to-ports=<внутренний порт> \
  comment="<Сервис>_<Сервер> from <Источник>"
```

```routeros
# [R] Проверка проброса — NETWORK-MIKROTIK-REMOTE-ACCESS-PROCEDURE-2026-001
/ip firewall nat print detail where comment="<comment>"
/ip firewall connection print where dst-port=<внешний порт>
```

```powershell
# [W] Встречное правило Windows Defender Firewall на целевом сервере (внутри Windows-гостя)
# NETWORK-MIKROTIK-REMOTE-ACCESS-PROCEDURE-2026-001
# Обязательный шаг после создания проброса: с ограничением по RemoteAddress, иначе проброс
# либо не работает, либо открыт всем
New-NetFirewallRule -DisplayName "<Сервис> from <Источник>" -Direction Inbound -LocalPort <внутренний_порт> -Protocol TCP -Action Allow -RemoteAddress <источник>
```

Очистка мёртвых правил (аудит 2026-09-19: 7 правил Filter и 5 правил NAT, привязанные к
несуществующей подсети `192.168.199.0/24`). Все блоки ниже — класс [D]: не выполнять
одной сессией и одной командой на всё сразу; перед каждым блоком смотреть счётчики
(`/ip firewall filter print stats`) и получить подтверждение администратора на каждый блок
отдельно. Адрес легаси-подсети оставлен как есть: он и есть критерий поиска правил.

```routeros
# [D] REQUIRES_APPROVAL — удалить правила Filter без action и с легаси-подсетью, по комментариям
# NETWORK-MIKROTIK-FIREWALL-NAT-CLEANUP-2026-001
# Правила #2, #3, #4 (без action) и #9 (drop для легаси-подсети). Регулярное выражение — в том виде,
# как в источнике, но без комментариев правил #14/#15 (они вынесены в отдельный блок ниже).
# Что именно найдёт find, смотреть заранее: /ip firewall filter print where comment~"<то же выражение>"
/ip firewall filter remove [find comment~"Allow L2TP/IPsec|Allow IPsec ESP|Allow IPsec AH|No internet for VPN clients"]
```

```routeros
# [D] REQUIRES_APPROVAL — удалить правило Filter #5 с легаси-адресом — NETWORK-MIKROTIK-FIREWALL-NAT-CLEANUP-2026-001
/ip firewall filter remove [find dst-address=192.168.199.1]
```

```routeros
# [D] REQUIRES_APPROVAL — удалить 5 мёртвых правил NAT (#3–#7, dst-address легаси-подсети)
# NETWORK-MIKROTIK-FIREWALL-NAT-CLEANUP-2026-001
# Правило NAT #10 (TCP 3432, DISABLED) в это не входит: оно выключено, а не мёртвое.
# Прежде чем удалять или включать его, уточнить у администратора назначение
/ip firewall nat remove [find dst-address=192.168.199.1]
```

```routeros
# [D] REQUIRES_APPROVAL — вариант А для правил Filter #14 и #15: удалить (printer MU) — NETWORK-MIKROTIK-FIREWALL-NAT-CLEANUP-2026-001
# Правила #14 и #15 стоят после permissive accept-all #10 и никогда не срабатывают.
# Вариант А (удалить) и вариант Б (блок ниже, переместить) взаимоисключающи: в источниках
# предложены оба (блок очистки и пункт 5 плана устранения). Выбор — решение администратора;
# выполнять только один из двух
/ip firewall filter remove [find comment~"printer MU|pinter MU zapret"]
```

```routeros
# [W] Вариант Б для правил Filter #14 и #15: переместить перед accept-all #10
# NETWORK-MIKROTIK-FIREWALL-NAT-CLEANUP-2026-001, MikroTik-CRITICAL-SECURITY-PLAN-2026-001
# Номер 10 — из аудита 2026-09-19, взять из свежего print. Простая перестановка не убирает
# пермиссивность самого accept-all #10: сначала решить, нужен ли он вообще
/ip firewall filter move [find comment~"printer MU|pinter MU zapret"] place-before=10
```

## 3. VPN: профиль PPP для L2TP/IPsec и SSTP

В аудите 2026-09-19 все 18 PPP-пользователей работали на `profile=default`, а `vpn_profile`
ссылался на нерабочую подсеть и содержал `dns-server=255.255.255.255` (широковещательный адрес
не может быть DNS-сервером). Порядок важен: **сначала** исправить сам профиль, **потом**
переводить на него пользователей.

```routeros
# [R] PPP-профили, пользователи и пул — NETWORK-MIKROTIK-VPN-PROFILE-BROKEN-2026-001
# Команды print в источнике не приведены дословно; ниже стандартные просмотры по тем объектам,
# о которых идёт речь (профили, учётные записи, пул) — убедиться перед правкой, какой профиль у кого
/ppp profile print
/ppp secret print
/ip pool print
```

```routeros
# [W] Шаг 1 — исправить профиль vpn_profile — NETWORK-MIKROTIK-VPN-PROFILE-BROKEN-2026-001
# local-address и dns-server — из реально маршрутизируемой подсети (в источнике — адрес шлюза основной LAN).
# Как вариант вместо внутреннего DNS — публичный DNS, если клиентам не нужен внутренний домен
/ppp profile set vpn_profile local-address=<адрес_шлюза_LAN> dns-server=<адрес_DNS>
```

```routeros
# [W] Шаг 2 — перевести пользователей на исправленный профиль (только после шага 1)
# NETWORK-MIKROTIK-VPN-PROFILE-BROKEN-2026-001
# Первая команда затрагивает всех PPP-пользователей разом (18 в аудите). В источнике рекомендовано
# сначала применить к 1–2 тестовым учётным записям, подтвердить рабочий доступ и только потом
# переводить остальных; вторая строка — вариант для тестовой записи (в источнике дословно не приведён)
/ppp secret set [find] profile=vpn_profile
/ppp secret set [find name=<пользователь>] profile=vpn_profile
```

```text
# [R] Проверка результата на стороне клиента — NETWORK-MIKROTIK-VPN-PROFILE-BROKEN-2026-001
# Критерии: новое подключение получает адрес из маршрутизируемой подсети (не из легаси-пула);
# клиент резолвит внутренние DNS-имена (nslookup <имя_внутреннего_хоста> или аналог);
# клиент имеет доступ к внутренним ресурсам (ping, RDP по назначению)
```

## 4. Укрепление управления и защиты (план, не применён)

Источник — `MikroTik-CRITICAL-SECURITY-PLAN-2026-001` (статус `in_progress`: план подготовлен по
итогам аудита, на устройстве ничего не применено). Порядок внедрения из источника: один логический
шаг за раз, с подтверждением перед следующим, начиная с критических; не выполнять несколько
пунктов одной командой или сессией. Пункты плана про неисправный VPN-профиль и мёртвые правила —
в разделах 3 и 2; пункт про link flapping — физическая замена патч-корда, команд нет.

```routeros
# [W] Ограничить источники для служб управления — MikroTik-CRITICAL-SECURITY-PLAN-2026-001
# ВЫСОКИЙ РИСК потери доступа: неверный список немедленно закрывает вход самому администратору.
# Сначала выяснить, с каких адресов администратор реально подключается. Список источников — из
# AI-environment_facts-korona-mikrotik.md: внутренние LAN и доверенный внешний адрес
/ip service set ssh allowed-addresses=<LAN1>,<LAN2>,<доверенный_внешний_IP>/32
/ip service set www allowed-addresses=<LAN1>,<LAN2>
/ip service set winbox allowed-addresses=<LAN1>,<LAN2>,<доверенный_внешний_IP>/32
```

```routeros
# [W] Запретить mac-server на всех интерфейсах — MikroTik-CRITICAL-SECURITY-PLAN-2026-001
# После none управление по MAC (в том числе вход Winbox по MAC) недоступно: если оно нужно на LAN,
# вместо none указать список доверенных интерфейсов
/tool mac-server set allowed-interface-list=none
```

```routeros
# [W] Отключить открытый DNS-резолвер и NTP-сервер — MikroTik-CRITICAL-SECURITY-PLAN-2026-001
# Риск ниже, чем «открыто в интернет»: WAN уже частично прикрыт правилами drop по входящему интерфейсу.
# Не выполнять, если клиенты LAN используют роутер как DNS или NTP: проверить, кто их использует
/ip dns set allow-remote-requests=no
/system ntp server set enabled=no
```

```routeros
# [W] Добавить drop для invalid в цепочку input — MikroTik-CRITICAL-SECURITY-PLAN-2026-001
# Номер 8 — из аудита 2026-09-19 (правило established,related): взять из свежего print
/ip firewall filter add chain=input action=drop connection-state=invalid place-before=8
```

```routeros
# [W] Усилить SSTP — MikroTik-CRITICAL-SECURITY-PLAN-2026-001
# В аудите: pfs=no, tls-version=any. Точный синтаксис значения tls-version сверить с версией
# RouterOS перед выполнением (в источнике это отдельно оговорено). Перезапуск SSTP-сервера
# может разорвать текущие VPN-сессии
/interface sstp-server server set pfs=yes tls-version=only-1.2;only-1.3
```

## 5. Wi-Fi на точках доступа cAP ac (RouterOS 7, пакет wifi-qcom-ac)

Все блоки раздела выполняются **на точке доступа**, а не на основном маршрутизаторе.
На точках cAP ac пакет `wifi-qcom-ac` означает стек `/interface wifi`: команды
`/interface wireless` и `/caps-man` на нём дают `bad command name`.

Ограничения из источников:

- **Не задавать явно `channel.band`** (`2ghz-n`, `5ghz-ac`, `2ghz-only` и т. п.) на устройствах
  с `wifi-qcom-ac`: `2ghz-only` даёт `syntax error`, а `2ghz-n` и `5ghz-ac` на обоих
  интерфейсах привели к потере флага `R` и трафику 0 bps (`MIKROTIK-WIFI-SSID-2026-001`).
  `channel.frequency=2412-2472` тоже пробовали: применилось, но флаг `R` не появился.
- Команды `add` неидемпотентны: повторный запуск создаёт дубликаты профилей, интерфейсов и
  портов моста. Перед созданием проверить, что объектов с такими именами нет.
- После сброса к заводским настройкам радиоинтерфейсы называются `wifi1` (2,4 ГГц) и `wifi2`
  (5 ГГц). Имена `wifi-2` и `wifi-5` появляются только после переименования администратором
  (команда переименования в источнике не приведена); до него обращение по ним даёт `no such item`.
- Дополнительный SSID (раздел 5.2) в источнике делали виртуальными интерфейсами на мастерах.
  Для основного SSID, дублированного виртуальными интерфейсами, подход признан лишним: использовать
  мастер-интерфейсы напрямую (раздел 5.3). Расхождение подходов в источниках не разрешено.

### 5.1 Диагностика

```routeros
# [R] Модель, версия RouterOS, Wi-Fi-стек и привязка к мосту — MIKROTIK-WIFI-SSID-RSK-2026-001
# Ожидается на cAP ac: пакет wifi-qcom-ac. Флаг I у порта в bridge означает inactive;
# его причина в источнике отдельно не проверялась
/system resource print
/system package print where name~"wifi|wireless"
/interface wifi print
/interface bridge port print where interface~"wifi"
```

### 5.2 Дополнительный SSID виртуальными интерфейсами

```routeros
# [W] Добавить дополнительный SSID на оба диапазона — MIKROTIK-WIFI-SSID-RSK-2026-001
# По порядку. Перед выполнением проверить, что объектов с такими именами ещё нет (блок 5.1).
# Подставить реальную парольную фразу: значение «****» из источника — плейсхолдер, а не пароль.
# Мост — тот же, что у основных Wi-Fi-интерфейсов (в источнике bridge1)
/interface wifi security add name=sec-<метка> authentication-types=wpa2-psk,wpa3-psk passphrase="<парольная_фраза>"
/interface wifi configuration add name=conf-<метка> ssid=<SSID> security=sec-<метка>
/interface wifi add name=wifi-2-<метка> master-interface=<мастер_2ГГц> configuration=conf-<метка> disabled=no
/interface wifi add name=wifi-5-<метка> master-interface=<мастер_5ГГц> configuration=conf-<метка> disabled=no
/interface bridge port add bridge=<мост> interface=wifi-2-<метка>
/interface bridge port add bridge=<мост> interface=wifi-5-<метка>
```

```routeros
# [R] Проверка дополнительного SSID — MIKROTIK-WIFI-SSID-RSK-2026-001
# В источнике у виртуального интерфейса 5 ГГц был флаг B без R, и позднее RUNNING не подтверждён:
# успешное подключение клиента не доказывает, что работают оба диапазона. Пустой вывод leases
# на точке доступа сам по себе неисправность не доказывает (DHCP-сервер мог быть на другом устройстве)
/interface wifi print where name~"<метка>"
/interface bridge port print where interface~"<метка>"
/log print where topics~"wifi" limit=50
/ip dhcp-server lease print where active=yes
```

```routeros
# [W] Сменить парольную фразу SSID — MIKROTIK-WIFI-SSID-RSK-2026-001
# В источнике после замены пароля с символом # на пароль без него всё заработало. Объяснение
# «# в терминале воспринят как комментарий» не подтверждено ни логами, ни проверкой сохранённого
# значения: причину сбоя не считать доказанной
/interface wifi security set sec-<метка> passphrase="<парольная_фраза>"
```

### 5.3 Основной SSID на мастер-интерфейсах (после сброса точки)

```routeros
# [W] Применить профиль к мастер-интерфейсам и задать мост — MIKROTIK-WIFI-SSID-2026-001
# По порядку, на точке после сброса (профили sec-<метка> и conf-<метка> созданы, парольная фраза
# в репозитории не хранится). Страна в профиле обязательна для wifi в ROS 7 (в источнике — Russia).
# channel.band не задавать. Результат в источнике: клиент подключился на 2,4 ГГц;
# на 5 ГГц и состояние портов в мосту после этих команд не проверялись
/interface wifi configuration set conf-<метка> country=<страна>
/interface wifi set <мастер_2ГГц> configuration=conf-<метка>
/interface wifi set <мастер_5ГГц> configuration=conf-<метка>
/interface wifi set <мастер_2ГГц> datapath.bridge=<мост>
/interface wifi set <мастер_5ГГц> datapath.bridge=<мост>
```

```routeros
# [R] Проверка работы точки — MIKROTIK-WIFI-SSID-2026-001
# Ожидается: у обоих мастеров флаг R, status: running, порты в мосту не I/X, при подключённом клиенте
# registered-peers меняется с 0 на 1 и растут счётчики. Флаг R в простое нестабилен: по наблюдению
# администратора он появляется в момент подключения клиента (выводом не подтверждено).
# Без R клиенты точку могут не увидеть; 0 bps без клиентов при наличии R проблемой не считается
/interface wifi print detail where name="<мастер_2ГГц>" or name="<мастер_5ГГц>"
/interface wifi monitor <мастер_2ГГц> once
/interface wifi monitor <мастер_5ГГц> once
/interface bridge port print where interface~"wifi"
/interface wifi registration-table print
/log print
```

```routeros
# [W] Вернуть управление диапазоном драйверу после ошибочного channel.band — MIKROTIK-WIFI-SSID-2026-001
# Результат отката в источнике не подтверждён выводом команд
/interface wifi set <мастер_2ГГц> channel.band=""
/interface wifi set <мастер_5ГГц> channel.band=""
```

```routeros
# [D] REQUIRES_APPROVAL — удалить дублирующие виртуальные интерфейсы и «призрачные» порты в мосту
# MIKROTIK-WIFI-SSID-2026-001
# Призрачный порт — запись в мосту для уже несуществующего интерфейса (в источнике идентификаторы
# вида *9, *A): идентификатор брать из свежего /interface bridge port print.
# Пересоздание порта (remove + add) статус INACTIVE не исправило
/interface bridge port remove [find where interface="<идентификатор_призрака>"]
/interface bridge port remove [find interface=<виртуальный_интерфейс> bridge=<мост>]
/interface wifi remove <виртуальный_интерфейс>
```

```routeros
# [W] Откат мастеров к исходным конфигурациям — MIKROTIK-WIFI-SSID-2026-001
# В источнике это были исходные (нерабочие) конфигурации cfg_2 и cfg_5: откат на крайний случай
/interface wifi set <мастер_2ГГц> configuration=<исходная_конфигурация_2ГГц>
/interface wifi set <мастер_5ГГц> configuration=<исходная_конфигурация_5ГГц>
```

```routeros
# [W] Перезагрузка точки — MIKROTIK-WIFI-SSID-2026-001
# Крайний вариант, если проблема вернулась после просмотра /log print. Клиенты на точке
# будут отключены
/system reboot
```

## 6. WireGuard: сервер на основном маршрутизаторе

Параметры (интерфейс сервера, порт, подсеть туннеля, публичный адрес, DNS для клиентов) и список
пиров — в `VPN-MIKROTIK-WIREGUARD-SERVER-2026-001`. Публичные ключи пиров здесь не повторяются.
Приватный ключ клиента остаётся на устройстве клиента: не вставлять его в чат и в репозиторий.

### 6.1 Правила Firewall и NAT

```routeros
# [W] Правила Firewall и NAT для WireGuard-сервера — VPN-MIKROTIK-WIREGUARD-SERVER-2026-001
# Порядок решает: правило Allow WireGuard в input должно стоять ДО правил drop по in-interface WAN,
# иначе handshake не проходит (rx=0, TS-MIKROTIK-WIREGUARD-ACCESS-2026-001). Номер правила
# <номер_первого_drop_правила> брать из свежего /ip firewall filter print.
# port=<порт> в источнике — так работало; port в RouterOS совпадает и по порту источника, и по
# порту назначения, вариант с dst-port в документах не проверялся.
# Для forward в интернет place-before=0 ставит правило первым в цепочке
/ip firewall filter add chain=input action=accept protocol=udp in-interface=<WAN-интерфейс> port=<порт_WG> place-before=<номер_первого_drop_правила> comment="Allow WireGuard"
/ip firewall filter add chain=input action=accept in-interface=<wg-интерфейс> comment="Allow WireGuard to Router"
/ip firewall filter add chain=forward action=accept in-interface=<wg-интерфейс> out-interface=<LAN-мост> comment="Allow WireGuard to LAN"
/ip firewall filter add chain=forward action=accept in-interface=<wg-интерфейс> out-interface=<WAN-интерфейс> place-before=0 comment="Allow WireGuard to Internet"
/ip firewall nat add chain=srcnat action=masquerade src-address=<подсеть_WG> out-interface=<WAN-интерфейс> comment="WireGuard NAT"
```

### 6.2 Добавление пользователя

```text
# [W] Шаг 1 — ключи на клиенте — VPN-MIKROTIK-WIREGUARD-ADD-USER-2026-001
# В приложении WireGuard: Add empty tunnel, скопировать PublicKey. Приватный ключ остаётся у клиента
```

```routeros
# [R] Занятые адреса пиров перед выбором адреса клиента
# Стандартный просмотр; в источнике дословно не приведён (там список пиров дан таблицей в документе сервера)
/interface wireguard peers print
```

```routeros
# [W] Шаг 2 — добавить пир на роутере — VPN-MIKROTIK-WIREGUARD-ADD-USER-2026-001
# allowed-address — свободный адрес /32 из подсети туннеля
/interface wireguard peers add \
  interface=<wg-интерфейс> \
  public-key=<PUBLIC_KEY_клиента> \
  allowed-address=<IP_клиента>/32 \
  comment=<Имя_пользователя>
```

```ini
# [W] Шаг 3 — конфигурация на клиенте (на устройстве клиента, не на роутере)
# VPN-MIKROTIK-WIREGUARD-ADD-USER-2026-001
# AllowedIPs = 0.0.0.0/0 пускает весь трафик клиента через туннель: поэтому нужны правило forward
# в интернет и DNS из внутренней сети (раздел 6.3)
[Interface]
PrivateKey = <PRIVATE_KEY_клиента>
Address = <IP_клиента>/32
DNS = <внутренний_DNS>

[Peer]
PublicKey = <публичный_ключ_сервера>
AllowedIPs = 0.0.0.0/0
Endpoint = <публичный_IP>:<порт_WG>
PersistentKeepalive = 25
```

### 6.3 Диагностика

```routeros
# [W] Handshake есть, интернета нет — TS-MIKROTIK-WIREGUARD-ACCESS-2026-001
# Причина в источнике: неверный DNS на клиенте (нужен внутренний DNS, см. шаг 3 выше) и нет правила
# forward в WAN. Это то же правило, что в разделе 6.1: добавлять, только если его там нет
/ip firewall filter add chain=forward action=accept in-interface=<wg-интерфейс> out-interface=<WAN-интерфейс> place-before=0 comment="Allow WireGuard to Internet"
```

```routeros
# [W] Локальные сервисы не пингуются — TS-MIKROTIK-WIREGUARD-ACCESS-2026-001
# Причина в источнике: firewall блокирует input из WireGuard-интерфейса.
# То же правило, что в разделе 6.1: добавлять, только если его там нет
/ip firewall filter add chain=input action=accept in-interface=<wg-интерфейс> comment="Allow WireGuard to Router"
```

```text
# [R] Handshake не проходит (rx=0) — причина А — TS-MIKROTIK-WIREGUARD-ACCESS-2026-001
# Конфликт с Clash (FlClashX) на клиенте. Решение: закрыть Clash. Причина Б (порядок правил
# firewall на роутере) — блок ниже
```

```routeros
# [D] REQUIRES_APPROVAL — пересоздать Allow WireGuard перед правилами drop (причина Б)
# TS-MIKROTIK-WIREGUARD-ACCESS-2026-001
# Правило Allow WireGuard стояло ПОСЛЕ drop in-interface=<WAN-интерфейс>. Решение: удалить и добавить
# перед первым drop. Пока правило удалено, WireGuard с WAN не принимается: выполнять обе строки подряд
/ip firewall filter remove [find comment="Allow WireGuard"]
/ip firewall filter add chain=input action=accept protocol=udp in-interface=<WAN-интерфейс> port=<порт_WG> place-before=<номер_первого_drop_правила> comment="Allow WireGuard"
```

---

## Покрытие

Команды перенесены из документов:

- `NETWORK-MIKROTIK-TOPOLOGY-2026-001`
- `NETWORK-MIKROTIK-FIREWALL-NAT-CLEANUP-2026-001`
- `NETWORK-MIKROTIK-REMOTE-ACCESS-PROCEDURE-2026-001`
- `NETWORK-MIKROTIK-VPN-PROFILE-BROKEN-2026-001`
- `MikroTik-CRITICAL-SECURITY-PLAN-2026-001`
- `MIKROTIK-WIFI-SSID-RSK-2026-001`
- `MIKROTIK-WIFI-SSID-2026-001`
- `VPN-MIKROTIK-WIREGUARD-SERVER-2026-001`
- `VPN-MIKROTIK-WIREGUARD-ADD-USER-2026-001`
- `TS-MIKROTIK-WIREGUARD-ACCESS-2026-001`
- `MikroTik/START-HERE.md` (базовый набор диагностики)

**Не вошло из разобранных документов:** блок для SSID Korona.ru на точке Т2 (в источнике предложен,
выполнение не подтверждено; при необходимости собирается по шаблону раздела 5.2), команда
переименования `wifi1`/`wifi2` (в источнике не приведена), `channel.frequency=2412-2472`
(применилось, но флаг `R` не появился), список пиров и публичные ключи WireGuard (остаются в
документе сервера).

**Не разбирались:** `INBOX-MIKROTIK-WIREGUARD-RAW-2026-001` (сырой материал, источник для
`VPN-MIKROTIK-WIREGUARD-*`; команды брать из обработанных документов), каталог `99_Archive/`,
файлы вне реестра (`MikroTik.md`, `environment_facts-CRS112-8P-4S№1№2.md`).

## Как дополнять

1. Команду, к которой стоит возвращаться, добавляют в документ-источник и здесь.
2. Формат блока: первая строка-комментарий `[класс] что делает — document_id`.
3. Класс выбирать по самому опасному шагу блока. Сомневаетесь между [W] и [D] — ставьте [D].
4. Секретов нет: пароли, парольные фразы и ключи заменять плейсхолдерами.
5. После правки обновить `date_modified` и список покрытия.
