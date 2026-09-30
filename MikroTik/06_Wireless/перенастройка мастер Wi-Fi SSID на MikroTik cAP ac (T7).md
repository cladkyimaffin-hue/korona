---
document_id: MIKROTIK-WIFI-SSID-2026-001
title: перенастройка мастер Wi-Fi SSID на MikroTik cAP ac (T7)
document_type: troubleshooting
status: completed
priority: medium
date_created: 2026-09-28
date_modified: '2026-09-30'
next_review: 2026-12-01
author: cladkyimaffin-hue
category: 06_Wireless
tags:
- RouterOS
- MikroTik
- Interfaces
- Bridge
- Wi-Fi
- Troubleshooting
- Configuration
ai_summary: 'Перенос SSID Korona.ru на мастер-интерфейсы MikroTik cAP ac (RouterOS
  7.23.2, пакет wifi-qcom-ac). Явное задание channel.band ломает инициализацию радио
  на этой модели. После сброса к заводским настройкам 2026-09-30 точка настроена
  повторно: профили sec-korona и conf-korona применены к wifi-2 и wifi-5 (переименованы
  из wifi1 и wifi2), на обоих интерфейсах явно задан datapath.bridge=bridge1, клиент
  подключился на 2.4 ГГц. Флаг R в выводе print нестабилен: по наблюдению администратора
  он появляется в момент подключения клиента; выводом команд не подтверждено.'
dont_repeat:
- Не задавать явно параметр channel.band (например, 2ghz-n, 5ghz-ac, 2ghz-only) на
  устройствах с пакетом wifi-qcom-ac в RouterOS 7 — гарантированно ломает инициализацию
  радио (потеря флага R, синтаксические ошибки, 0 bps трафика).
- Не создавать/не оставлять виртуальные интерфейсы wifi-*-<ssid> для дублирования
  SSID — используйте мастер-интерфейсы напрямую, дубли только мешают диагностике.
- После сброса к заводским настройкам радиоинтерфейсы называются wifi1 (2.4 ГГц) и
  wifi2 (5 ГГц); обращение по именам wifi-2 и wifi-5 даёт no such item до переименования.
related_files: []
schema_version: '1.0'
---

# перенастройка мастер Wi-Fi SSID на MikroTik cAP ac (T7)

## Цель и исходные условия
Обеспечить параллельную работу Wi-Fi 2.4 ГГц и 5 ГГц под единым SSID `Korona.ru` на мастер-интерфейсах (для поддержки старых 802.11g-клиентов и новых), удалив старые виртуальные интерфейсы `wifi-*-korona`.

Устройство: MikroTik cAP ac (RBcAPGi-5acD2nD, псевдоним **T7**), RouterOS 7.23.2, пакет `wifi-qcom-ac`. Исходно: мастера `wifi-2`/`wifi-5` отключены (флаг `X`) в `bridge1`, виртуальные `wifi-*-korona` неактивны (флаг `I`), в профиле `conf-korona` отсутствовал параметр `country`.

## Сущности и окружение
| Объект | Роль | Значения | Прим. |
| --- | --- | --- | --- |
| T7 | Точка доступа | MikroTik cAP ac (RBcAPGi-5acD2nD), ROS 7.23.2, `wifi-qcom-ac` | — |
| wifi-2 | Мастер-интерфейс 2.4 ГГц | MAC D0:EA:11:0D:42:D9, default-name `wifi1` | не держит флаг R |
| wifi-5 | Мастер-интерфейс 5 ГГц | MAC D0:EA:11:0D:42:DA, default-name `wifi2` | работает штатно |
| conf-korona | Профиль Wi-Fi | SSID `Korona.ru`, security `sec-korona`, `country=Russia` | country добавлен в ходе работы |
| bridge1 | Мост | объединяет Wi-Fi интерфейсы | очищен от ghost-портов |
| wifi-2-korona, wifi-5-korona | Виртуальные интерфейсы | удалены как дублирующие | — |

## Отвергнутые гипотезы
- **`channel.band=2ghz-only`** решит совместимость со старыми клиентами. Опровергнуто: `syntax error (line 1 column 41)` в ROS 7.23.2 [подтверждено выводом].
- **Аппаратное ограничение** на параллельную работу двух диапазонов. Опровергнуто: cAP ac имеет два независимых радиочипа и сертифицирован для одновременной работы [опровергнуто спецификацией].
- **Зависшая запись порта в мосту** решается `remove`+`add`. Опровергнуто: после пересоздания порт `wifi-2` снова получает статус `INACTIVE` [подтверждено выводом].

## Диагностика и хронология действий
1. Профиль `conf-korona` не имел `country` → `/interface wifi configuration set conf-korona country=Russia` — успешно.
2. `/interface wifi set wifi-2/wifi-5 configuration=conf-korona` → `wifi-5` получил флаг `R`, `wifi-2` — нет, порт в `bridge1` остался `INACTIVE`.
3. Попытка `channel.band=2ghz-only`/`2ghz-only-n` → `syntax error`.
4. `channel.frequency=2412-2472` для `wifi-2` → применилось, `monitor` показывает `state: running`, но флага `R` всё ещё нет, порт `INACTIVE`.
5. `bridge port remove`+`add` для `wifi-2` → порт пересоздан с новым индексом, статус не изменился.
6. Удалены виртуальные `wifi-2-korona`/`wifi-5-korona` и их ghost-записи (`*9`, `*A`) в `bridge1`.
7. Явное `channel.band=2ghz-n` и `=5ghz-ac` на обоих интерфейсах → **оба** потеряли флаг `R`, трафик упал до 0 bps — драйвер `wifi-qcom-ac` критически реагирует на этот параметр.
8. Откат `channel.band=""` на обоих интерфейсах выполнен, но подтверждение результата от пользователя не получено (ответ «там нет клиентов» без вывода команд) [предложено, выполнение не подтверждено].

## Корневая причина / известная проблема
`channel.band`, заданный вручную, критически ломает инициализацию радио на пакете `wifi-qcom-ac` — это системная особенность драйвера на данной модели, а не ошибка конфигурации. Отдельно и независимо от этого: `wifi-2` демонстрирует рассинхронизацию состояния — `monitor` сообщает `state: running` и активный канал, но интерфейс не получает флаг `R`, и мост считает порт `INACTIVE`, даже без `channel.band`. Причина этой второй проблемы не установлена [противоречие, подтверждено выводом].

## Решение (сессия 28–29.09; частично применено, не подтверждено до конца)
```routeros
# 1. Страна в профиле (обязательно для ROS 7 wifi)
/interface wifi configuration set conf-korona country=Russia

# 2. Профиль на мастер-интерфейсы
/interface wifi set wifi-2 configuration=conf-korona
/interface wifi set wifi-5 configuration=conf-korona

# 3. Частотный диапазон для 2.4 ГГц (обходной путь вместо channel.band)
/interface wifi set wifi-2 channel.frequency=2412-2472

# 4. Очистка моста
/interface bridge port remove [find where interface="*9"]
/interface bridge port remove [find where interface="*A"]
/interface bridge port remove [find interface=wifi-2-korona bridge=bridge1]
/interface bridge port remove [find interface=wifi-5-korona bridge=bridge1]
/interface wifi remove wifi-2-korona
/interface wifi remove wifi-5-korona

# 5. КРИТИЧЕСКИЙ ОТКАТ — вернуть управление стандартом драйверу
/interface wifi set wifi-2 channel.band=""
/interface wifi set wifi-5 channel.band=""
```
Откат к исходным (нерабочим) конфигурациям, если потребуется:
```routeros
/interface wifi set wifi-2 configuration=cfg_2
/interface wifi set wifi-5 configuration=cfg_5
```

## Повторная настройка после сброса к заводским настройкам (2026-09-30)
Точка T7 сброшена к заводским настройкам (RouterOS 7.23.2, `RBcAPGi-5acD2nD`, `wifi-qcom-ac`); SSID `Korona.ru` настроен заново.
1. Подключение по MAC (Winbox), проверка `/system resource print`.
2. Созданы профиль безопасности `sec-korona` (`authentication-types=wpa2-psk`) и профиль `conf-korona` (SSID `Korona.ru`, `country=Russia`, режим `ap`). Парольная фраза в репозитории не хранится.
3. После сброса интерфейсы называются `wifi1` (2.4 ГГц) и `wifi2` (5 ГГц); администратор переименовал их в `wifi-2` и `wifi-5` (до переименования обращение по этим именам давало `no such item`).
4. `conf-korona` применён к `wifi-2` и `wifi-5`: у интерфейсов флаги `M` и `B`, флага `R` нет, `monitor` показывает работу радио, порты в `bridge1` — `I` (INACTIVE).
5. `disable` / `enable` обоих интерфейсов результата не дали (как и в сессии 28–29.09).
6. Мост задан явно на самих интерфейсах: `/interface wifi set wifi-2 datapath.bridge=bridge1` и `/interface wifi set wifi-5 datapath.bridge=bridge1`. `channel.band` не задавался.
7. Результат: клиент подключился к `Korona.ru` на 2.4 ГГц (подтверждено администратором).

Статус фактов:
- **Подтверждено администратором:** подключение клиента на 2.4 ГГц после шага 6.
- **Предположение администратора, выводом команд не проверено:** флаг `R` выставляется только в момент подключения клиента (радио переключается между каналами).
- **Не проверено в сессии 30.09:** подключение клиента на 5 ГГц; состояние портов в `bridge1` после шага 6. В сессии 28–29.09 `wifi-5` работал штатно.

## Проверка результата
- [ ] `/interface wifi print detail where name="wifi-2" or name="wifi-5"` → у обоих должен быть флаг `R` (например `MBR`/`RSMB`).
- [ ] `/interface wifi monitor wifi-2/wifi-5 once` → `status: running` у обоих.
- [ ] `/interface bridge port print where interface~"wifi"` → ни один порт не `I`/`X`.
- [ ] Подключить тестового клиента к SSID `Korona.ru`: `registered-peers` должен смениться с 0 на 1, счётчики трафика растут.

## Риски
При сбросе `channel.frequency=""` радио само выберет канал при следующей перезагрузке/переконфигурации — возможно кратковременное переподключение клиентов, если они уже есть. Отсутствие трафика (0 bps) само по себе не показатель проблемы, если флаг `R` присутствует; а вот отсутствие `R` означает, что клиенты точку не увидят или не подключатся.

## Открытые вопросы
- Подтвердить выводом команд: `/interface wifi registration-table print` при подключённом клиенте и флаги `R` у `wifi-2` / `wifi-5` в этот момент.
- Проверить подключение клиента на 5 ГГц и состояние портов `wifi-2` / `wifi-5` в `bridge1` после `datapath.bridge=bridge1`.
- Причина отсутствия флага `R` в простое не установлена (есть только предположение администратора).
- Если проблема вернётся: `/log print`, как крайний вариант — `/system reboot`.
## ⛔ Don't repeat
- Не задавать явно `channel.band` на `wifi-qcom-ac` в RouterOS 7.
- Не создавать/не оставлять виртуальные интерфейсы `wifi-*-<ssid>` для дублирования SSID.
- После сброса к заводским настройкам интерфейсы называются `wifi1` / `wifi2`; `wifi-2` и `wifi-5` — только после переименования.

## Связанные документы
—
