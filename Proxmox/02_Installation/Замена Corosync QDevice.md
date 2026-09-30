---
document_id: "PROXMOX-QDEVICE-REPLACEMENT-2026-001"
title: "Замена Corosync QDevice в кластере krnn (192.168.202.251 → 192.168.200.84)"
document_type: "runbook"
status: "completed"
priority: "high"
date_created: 2026-09-30
date_modified: 2026-09-30
next_review: 2026-12-01
author: "cladkyimaffin-hue"
category: "02_Installation"
tags: [ProxmoxVE, Cluster, QDevice, Corosync, Quorum, corosync-qnetd, corosync-qdevice, Debian13, SSH, Hostname, krnn, pve01, pve02]
ai_summary: "Процедура замены внешнего Corosync QDevice кластера krnn: удалён прежний хост 192.168.202.251, подготовлен новый (Debian 13, 192.168.200.84, hostname qdevice.krnn.ru, пакет corosync-qnetd), подключение выполнено командой pvecm qdevice setup 192.168.200.84 с pve01. Итог: Expected votes 3, Quorate, State Connected. Типовые сбои: root SSH по ключу (ошибка формата authorized_keys) и запись в /etc/hosts через sudo с перенаправлением."
dont_repeat:
  - "Не использовать sudo echo ... >> /etc/hosts: перенаправление выполняется от обычного пользователя. Использовать echo ... | sudo tee -a /etc/hosts."
  - "При копировании публичного ключа в authorized_keys сохранять пробелы между типом ключа, телом и комментарием: ключ вида ssh-rsaAAAA... сервер отвергает."
  - "Команды pvecm qdevice status не существует; состояние смотреть через pvecm status и corosync-qdevice-tool -s."
related_files:
  - "PROXMOX-CLUSTER-QDEVICE-SETUP-2026-001"
  - "ARCHIVE-QDEVICE-DRAFT-2026-001"
schema_version: "1.0"
---

# Замена Corosync QDevice в кластере krnn (192.168.202.251 → 192.168.200.84)

## Цель
Заменить внешний арбитр кворума (Corosync QDevice) кластера `krnn` на новый хост без остановки ВМ. Выполнено 30.09.2026; прежний хост `192.168.202.251` выведен из эксплуатации.

## Предварительные условия
- [x] Кластер `krnn` в кворуме (`Quorate: Yes`), оба узла доступны; до замены `Expected votes: 3`, QNetd host `192.168.202.251:5403`, `State: Connected`.
- [x] Новый хост: Debian 13, IP `192.168.200.84` (сеть управления `192.168.200.0/22`), доступен с `pve01` и `pve02` (порт `5403/tcp`).
- [x] На новом хосте есть обычный пользователь с `sudo`.
- [x] На прежнем QDevice не было данных, требующих переноса (по словам администратора, сервер пустой).

## Шаги
Все команды кластера выполняются на `pve01` под `root`.

1. **Диагностика.** `pvecm status` — `Flags: Quorate Qdevice`. Состояние демона: `corosync-qdevice-tool -s`.
2. **Удаление прежнего QDevice:** `pvecm qdevice remove` (Config Version 3 → 4). После удаления `Expected votes: 2`, `Total votes: 2`: кворум держится только на двух узлах, поэтому потеря любого узла в этом окне остановит кластер. В выводе ещё некоторое время присутствует `Qdevice (votes 0)`.
3. **Подготовка нового хоста:** `apt update && apt install -y corosync-qnetd`; проверка `systemctl status corosync-qnetd` — `active (running)`.
4. **Имя хоста:** `sudo hostnamectl set-hostname qdevice.krnn.ru`; запись в hosts: `echo "192.168.200.84 qdevice.krnn.ru qdevice" | sudo tee -a /etc/hosts`; проверка `hostname -f`.
5. **Доступ root по SSH с ключом.** Для `pvecm qdevice setup` требуется вход `root` с `pve01` на новый хост без пароля (в Debian 13 вход root по паролю отключён, `PermitRootLogin prohibit-password`). Открытый ключ `pve01` (`/root/.ssh/id_rsa.pub`) добавить в `/root/.ssh/authorized_keys` на новом хосте (права: каталог `700`, файл `600`). Проверка с `pve01`: `ssh -o StrictHostKeyChecking=accept-new root@192.168.200.84 "hostname -f"` — должно вернуть `qdevice.krnn.ru` без запроса пароля.
6. **Подключение нового QDevice:** `pvecm qdevice setup 192.168.200.84` (Config Version 4 → 5).
7. **Вывод прежнего хоста:** сервер `192.168.202.251` выключен.

## Проверка результата
- [x] `pvecm status` → `Expected votes: 3`, `Total votes: 3`, `Quorate: Yes`, `Flags: Quorate Qdevice`, у `Qdevice` флаги `A,V,NMW`.
- [x] `corosync-qdevice-tool -s` → `QNetd host: 192.168.200.84:5403`, `State: Connected`.

## Факты и статус
- **VERIFIED (выводы команд):** хронология Config Version 3 → 4 → 5; окно с двумя голосами — от `pvecm qdevice remove` (19:55 MSK) до завершения `setup` (проверено в 20:38 MSK); новый QDevice `Connected`.
- **VERIFIED:** первая попытка входа по ключу не сработала из-за отсутствия пробела между `ssh-rsa` и телом ключа в `authorized_keys`; после исправления вход без пароля заработал.
- **UNKNOWN:** обновлены ли DNS-запись `qdevice.krnn.ru` (A/PTR) в домене и учётные данные инвентаризации — не проверялось. `pvecm qdevice setup` работает по IP, на кворум это не влияет.
- **INFERRED (рекомендация ассистента, не проверялась):** имя хоста лучше задать до `pvecm qdevice setup`, так как сертификаты привязываются к имени.

## ⛔ Don't repeat
- `sudo echo ... >> /etc/hosts` не работает: перенаправление выполняется от обычного пользователя — использовать `| sudo tee -a`.
- Ключ в `authorized_keys` копировать целой строкой вместе с пробелами (`ssh-rsa`, тело ключа, комментарий).
- Команды `pvecm qdevice status` нет; `pvecm add qdevice <IP>` в PVE 9.2 не использовать (см. `PROXMOX-CLUSTER-QDEVICE-SETUP-2026-001`).
- Не выполнять замену, когда один из узлов кластера недоступен: в окне между `remove` и `setup` кворум держится на двух голосах.

## Связанные документы
- `PROXMOX-CLUSTER-QDEVICE-SETUP-2026-001` — создание кластера и исходная установка QDevice (адрес `192.168.202.251` в нём относится к первоначальной установке).
- `ARCHIVE-QDEVICE-DRAFT-2026-001` — архивный черновик.
