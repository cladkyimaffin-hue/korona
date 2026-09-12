---
document_id: "LINUX-SSH-DEBIAN-ACCESS-2026-001"
title: "Чек-лист диагностики: доступ по SSH к Debian (неверный адрес, PermitRootLogin, статический IP)"
document_type: "troubleshooting"
status: "completed"
priority: "high"
date_created: 2026-08-30
date_modified: 2026-09-02
next_review: 2026-12-01
author: "cladkyimaffin-hue"
category: "06_Troubleshooting"
tags:
  - "Troubleshooting"
  - "SSH"
  - "Debian"
  - "Security"
ai_summary: "Три независимые типовые проблемы при первичной настройке SSH-доступа к Debian: (1) использование broadcast-адреса (.255) вместо реального IP хоста, (2) отказ входа под root из-за PermitRootLogin prohibit-password/without-password, (3) перевод интерфейса с DHCP на статический IP через /etc/network/interfaces или nmtui."
dont_repeat:
  - "Не предлагать полное отключение PasswordAuthentication до успешной проверки входа по SSH-ключам."
  - "Не предлагать смену порта SSH по умолчанию без обновления правил брандмауэра."
  - "Не путать адрес хоста (inet) с broadcast-адресом (brd) при копировании IP из вывода `ip -br addr` — `.255` при /24 это не хост."
related_files: []
schema_version: "1.0"
---

# Чек-лист диагностики: доступ по SSH к Debian

## Назначение
Общий (не привязанный к конкретному узлу) справочник по трём типовым
проблемам при первичном подключении к свежеустановленному Debian по SSH.
IP-адреса в примерах — иллюстративные (`192.168.203.x`), не относятся к
реальной инфраструктуре кластера.

## Проблема 1: «Cannot assign requested address» — использован broadcast-адрес

**Симптом:** клиент не может даже начать подключение к введённому адресу.

**Причина:** адрес `X.X.X.255` при маске `/24` — это broadcast-адрес сети,
не адрес хоста. Частая ошибка — скопировать не то поле из вывода Debian:
```
inet 192.168.203.10/24 brd 192.168.203.255 scope global ens33
       ^^^^^^^^^^^^^^      ^^^^^^^^^^^^^^
       адрес хоста         broadcast (не подключаться сюда)
```

**Решение:**
```bash
hostname -I
# или
ip -br addr
```
Использовать значение после `inet` (например, `192.168.203.10`), не `brd`.

**Если всё равно не подключается:**
- проверить, что клиент в той же подсети (`ipconfig` на Windows);
- проверить, что `sshd` слушает порт 22: `sudo systemctl status ssh`, `ss -tln | grep :22`;
- проверить фаервол: `sudo ufw status` / `sudo iptables -L -n`;
- если Debian — ВМ в VirtualBox/VMware: сетевой адаптер должен быть в режиме Bridge/Host-only (при NAT нужен проброс порта 22).

## Проблема 2: «Access denied» при входе под root

**Причина:** стандартное поведение Debian — в `/etc/ssh/sshd_config` по
умолчанию `PermitRootLogin prohibit-password` (в старых версиях —
`without-password`, то же самое): root пускает только по ключу, пароль для
root по SSH отключён.

**Вариант 1 — разрешить вход по паролю (проще, годится для лаборатории):**
```bash
sudo passwd root                    # если у root ещё нет пароля
sudo nano /etc/ssh/sshd_config
# PermitRootLogin yes
# PasswordAuthentication yes
sudo systemctl restart ssh
```
Проверить применение: `sudo sshd -T | grep -i permitroot` → должно
показать `permitrootlogin yes`. Если по-прежнему `prohibit-password` —
в конфиге есть дублирующая строка выше по файлу (первая имеет приоритет).

**Вариант 2 — оставить только вход по ключу (правильнее для продакшена):**
```bash
sudo mkdir -p /root/.ssh && sudo chmod 700 /root/.ssh
echo "ssh-rsa AAAA...ваш_публичный_ключ..." | sudo tee /root/.ssh/authorized_keys
sudo chmod 600 /root/.ssh/authorized_keys
```
Права обязательны именно такие: `700` на `~/.ssh`, `600` на `authorized_keys`.

**Более правильный вариант в любом случае:** заходить под обычным
пользователем, повышать права через `su -`/`sudo`, root по SSH не пускать
вообще.

**Если не помогло:** посмотреть `ssh -v root@<host>` со стороны клиента и
`sudo journalctl -u ssh -n 20` на сервере — там видна точная причина отказа.

## Проблема 3: перевод сети с DHCP на статический IP

**Определить текущие параметры перед изменением:**
```bash
ip -br addr          # текущий IP и имя интерфейса
ip route              # default via ... — это шлюз
```

**Вариант А — классический `/etc/network/interfaces`:**
```bash
sudo nano /etc/network/interfaces
```
Заменить:
```
allow-hotplug eno1
iface eno1 inet dhcp
```
на:
```
auto eno1
iface eno1 inet static
    address 192.168.203.20/24
    gateway 192.168.203.1
    dns-nameservers 192.168.203.1 8.8.8.8
```
Применить: `sudo systemctl restart networking` (или `ifdown eno1 && ifup eno1`).

**Вариант Б — NetworkManager (`nmtui`):**
1. Edit a connection → выбрать соединение.
2. IPv4 CONFIGURATION: `Automatic` → `Manual`.
3. Addresses → Add → адрес/24, Gateway, DNS.
4. `sudo nmcli con up <имя_соединения>`.

⚠️ Текущая SSH-сессия при применении отвалится — переподключаться уже на
новый адрес.

**Важно при выборе адреса:**
- брать адрес **вне диапазона DHCP** роутера, иначе возможен конфликт с другим устройством;
- не использовать `.0` (адрес сети) и `.255` (broadcast);
- если после смены пропал DNS (пакет `resolvconf` установлен не всегда), прописать вручную в `/etc/resolv.conf`.

**Проверка:**
```bash
ip -br addr
ping -c 3 <gateway>
ping -c 3 ya.ru        # работает ли DNS
```

## ⛔ Don't repeat
- Не путать `inet` и `brd` в выводе `ip addr` — реальный адрес хоста, а не broadcast.
- Не отключать `PasswordAuthentication` до подтверждённого входа по ключу.
- Не менять порт SSH без синхронной правки фаервола.

## Связанные документы
Не найдено пересечений с уже мигрированными документами — этот чек-лист
общий, не привязан к конкретному узлу кластера (IP из примеров не
пересекаются с реальной сетью `192.168.202.0/22`).

---
*Примечание при миграции (2026-09-11): исходный файл содержал три отдельные
проблемы одной сессии диагностики Debian — оставлены вместе одним
документом (единая тема «первичный SSH-доступ к Debian»), а не разбиты на
три файла, в отличие от `bond0.md`, где темы были значительно крупнее и
менее связаны друг с другом. Убрана диалоговая рамка USER/ASSISTANT,
содержание не изменено.*
