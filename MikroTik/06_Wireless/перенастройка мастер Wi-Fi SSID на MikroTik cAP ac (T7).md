---
document_id: MIKROTIK-WIFI-SSID-2026-001
title: перенастройка мастер Wi-Fi SSID на MikroTik cAP ac (T7)
document_type: troubleshooting
status: in_progress
priority: medium
date_created: 2026-09-28
date_modified: '2026-09-29'
next_review: 2026-10-05
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
  на этой модели. wifi-5 (5 ГГц) работает стабильно. wifi-2 (2.4 ГГц) остаётся рассинхронизирован:
  monitor показывает state: running, но флаг R отсутствует, порт в bridge1 — INACTIVE.
  Конфигурация очищена от дублирующих виртуальных интерфейсов и ghost-записей моста.
  Финальное подтверждение восстановления флага R после отката channel.band="" не получено.'
dont_repeat:
- Не задавать явно параметр channel.band (например, 2ghz-n, 5ghz-ac, 2ghz-only) на
  устройствах с пакетом wifi-qcom-ac в RouterOS 7 — гарантированно ломает инициализацию
  радио (потеря флага R, синтаксические ошибки, 0 bps трафика).
- Не создавать/не оставлять виртуальные интерфейсы wifi-*-<ssid> для дублирования
  SSID — используйте мастер-интерфейсы напрямую, дубли только мешают диагностике.
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

## Решение (частично применено, не подтверждено до конца)
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

## Проверка результата
- [ ] `/interface wifi print detail where name="wifi-2" or name="wifi-5"` → у обоих должен быть флаг `R` (например `MBR`/`RSMB`).
- [ ] `/interface wifi monitor wifi-2/wifi-5 once` → `status: running` у обоих.
- [ ] `/interface bridge port print where interface~"wifi"` → ни один порт не `I`/`X`.
- [ ] Подключить тестового клиента к SSID `Korona.ru`: `registered-peers` должен смениться с 0 на 1, счётчики трафика растут.

## Риски
При сбросе `channel.frequency=""` радио само выберет канал при следующей перезагрузке/переконфигурации — возможно кратковременное переподключение клиентов, если они уже есть. Отсутствие трафика (0 bps) само по себе не показатель проблемы, если флаг `R` присутствует; а вот отсутствие `R` означает, что клиенты точку не увидят или не подключатся.

## Открытые вопросы
- Восстановился ли флаг `R` у `wifi-2` и `wifi-5` после отката `channel.band=""` — не подтверждено выводом команд.
- Способен ли `wifi-2` устойчиво держать `R` и `bridge1: active` при автоопределении параметров (без ручного `channel.band`) — требует проверки.
- Если проблема сохранится: смотреть `/log print`, как крайний вариант — `/system reboot`.

## ⛔ Don't repeat
- Не задавать явно `channel.band` на `wifi-qcom-ac` в RouterOS 7.
- Не создавать/не оставлять виртуальные интерфейсы `wifi-*-<ssid>` для дублирования SSID.

## Связанные документы
—
