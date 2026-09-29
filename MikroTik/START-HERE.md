---
title: MikroTik Domain Entry Point
author: Korona
version: 1.0
tags:
  - mikrotik
  - routeros
  - documentation
  - ai
---

# START-HERE.md

## Назначение

Этот файл является основной точкой входа для ИИ и администратора при работе с доменом `MikroTik`.

Если новый чат начинается без предварительного контекста, ИИ обязан сначала ознакомиться с материалами, указанными в этом документе, и только после этого отвечать на вопросы пользователя.

---

# Порядок инициализации

## Шаг 1. Изучить структуру домена

Открыть и прочитать:

- `AI-README.md`
- `00_Meta/INDEX.md`
- либо `00_Meta/registry.csv`

Цель:

- понять структуру домена;
- определить доступные категории документов;
- найти расположение нужной информации.

---

## Шаг 2. Изучить факты среды

Открыть:

- `AI-environment_facts-korona-mikrotik.md`

Цель:

- определить используемые площадки;
- определить устройства;
- определить соглашения по именованию;
- определить особенности инфраструктуры.

---

## Шаг 3. Найти профильный раздел

В зависимости от вопроса использовать следующие разделы.

### Интерфейсы

Путь:

```text
01_Interfaces/
```

Использовать для:

- bridge;
- vlan;
- bonding;
- ether-порты;
- интерфейсные настройки.

### Firewall и NAT

Путь:

```text
02_Firewall_NAT/
```

Использовать для:

- firewall filter;
- firewall raw;
- firewall mangle;
- NAT;
- port forwarding.

### VPN

Путь:

```text
03_VPN/
```

Использовать для:

- WireGuard;
- IPsec;
- L2TP;
- SSTP;
- OpenVPN;
- site-to-site туннелей.

### Routing

Путь:

```text
04_Routing/
```

Использовать для:

- статических маршрутов;
- policy routing;
- BGP;
- OSPF;
- VRF.

### Troubleshooting

Путь:

```text
05_Troubleshooting/
```

Использовать для:

- диагностики;
- типовых ошибок;
- сценариев восстановления.

### Wireless

Путь:

```text
06_Wireless/
```

Использовать для:

- CAPsMAN;
- Wi-Fi;
- радиомостов;
- беспроводных клиентов.

---

# Алгоритм поиска ответа

Для любого вопроса:

1. Определить объект.
2. Определить раздел.
3. Найти документ через INDEX или registry.
4. Проверить YAML-метаданные.
5. Проверить Quick Answers.
6. Проверить связанные документы.
7. Дать ответ с указанием источника.

---

# Если информации недостаточно

Запросить:

```text
Имя устройства:
IP адрес:
Подсеть:
VPN:
Интерфейс:
VLAN:
Ошибка:
Ожидаемый результат:
```

---

# Безопасные команды для диагностики

```bash
/interface print detail

/ip address print detail

/ip route print detail

/ip firewall filter print detail

/ip firewall nat print detail

/interface wireguard print detail

/log print
```

Изменяющие конфигурацию команды не выполнять без явного запроса пользователя.

---

# Обязательные ссылки

Основные файлы домена:

```text
MikroTik/AI-README.md
MikroTik/AI-environment_facts-korona-mikrotik.md
MikroTik/00_Meta/INDEX.md
MikroTik/00_Meta/registry.csv
```

Если вопрос не удаётся сопоставить с документом, необходимо сначала проверить INDEX/registry и только потом делать выводы.
