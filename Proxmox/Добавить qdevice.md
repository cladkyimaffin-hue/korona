### USER
Proxmox у меня два сервера как настроить qdevice

### ASSISTANT
Скорее всего вы имеете в виду **qdevice** — Quorum Device для кластера Proxmox. Если у вас **2 сервера Proxmox**, без qdevice кластер теряет кворум при отказе одного сервера. qdevice — это третий независимый «свидетель», который даёт дополнительный голос и позволяет одному оставшемуся узлу сохранить кворум.

Важно: **qdevice должен быть на третьем независимом хосте**, не на одном из двух боевых Proxmox-серверов. Иначе он не даёт нормальной отказоустойчивости.

---

## Пример схемы

Допустим:

```text
node1: 192.168.1.10   # первый Proxmox
node2: 192.168.1.11   # второй Proxmox
qdevice: 192.168.1.12 # отдельная машина/VPS/Raspberry Pi/мини-ПК/CT
```

---

# 1. Установите пакеты qdevice на обоих Proxmox-узлах

Выполните на **node1** и **node2**:

```bash
apt update
apt install -y corosync-qdevice
```

---

# 2. Подготовьте отдельный сервер для qdevice

На третьей машине, например на Debian/Ubuntu/Raspberry Pi, выполните:

```bash
apt update
apt install -y corosync-qnetd
systemctl enable --now corosync-qnetd
```

Проверьте, что служба запущена:

```bash
systemctl status corosync-qnetd
```

Желательно проверить, что qnetd слушает порт:

```bash
ss -ltnp | grep 5403
```

По умолчанию используется TCP-порт **5403**.

---

# 3. Разрешите порт 5403, если есть firewall

На машине с qdevice:

Если используется `ufw`:

```bash
ufw allow 5403/tcp
```

Если используется `firewalld`:

```bash
firewall-cmd --permanent --add-port=5403/tcp
firewall-cmd --reload
```

Если используется `iptables`:

```bash
iptables -I INPUT -p tcp --dport 5403 -j ACCEPT
```

Также убедитесь, что оба Proxmox-узла могут подключиться к qdevice по TCP 5403.

---

# 4. Подключите qdevice к кластеру Proxmox

Выполните на **любом одном** узле Proxmox, например на `node1`:

```bash
pvecm qdevice setup 192.168.1.12
```

Замените `192.168.1.12` на адрес вашего qdevice-сервера.

Во время настройки может понадобиться SSH-доступ к qdevice-хосту. Если команда не подключается автоматически, заранее проверьте:

```bash
ssh root@192.168.1.12
```

Если нужно, добавьте SSH-ключ:

```bash
ssh-copy-id root@192.168.1.12
```

---

# 5. Проверка

На узле Proxmox выполните:

```bash
pvecm status
```

Вы должны увидеть примерно:

```text
Quorate: Yes
Expected votes: 3
Total votes: 3
Quorum: 2
```

Также можно проверить:

```bash
corosync-quorumtool -s
systemctl status corosync-qdevice
```

На qdevice-сервере:

```bash
systemctl status corosync-qnetd
corosync-qnetd-tool -s
```

---

# 6. Как это должно работать

Когда оба узла и qdevice онлайн:

```text
node1 + node2 + qdevice = 3 голоса
quorum = 2
```

Если падает один Proxmox-узел, оставшийся узел всё равно получает кворум вместе с qdevice:

```text
node1 + qdevice = 2 голоса
quorum = 2
```

Поэтому кластер остаётся работоспособным.

---

# 7. Если у вас только два сервера

Для полноценной отказоустойчивости нужен **третий независимый qdevice-хост**.

Подойдёт даже очень слабая машина:

- Raspberry Pi;
- мини-ПК;
- дешевый VPS;
- отдельный LXC/VM на другом физическом хосте;
- старый ПК;
- NAS с возможностью запустить Debian/Ubuntu контейнер.

Запускать qdevice на одном из двух ваших Proxmox-серверов — плохая идея. Например, если qdevice работает на `node2`, то при падении `node2` вы теряете и узел, и qdevice, и кворум.

---

# 8. Важные замечания

## Добавляйте qdevice при живом кластере

Желательно, чтобы оба узла Proxmox были онлайн и кластер был в состоянии `Quorate`.

Проверить:

```bash
pvecm status
```

Должно быть:

```text
Quorate: Yes
```

Если кластер уже без кворума, сначала восстановите второй узел или аккуратно используйте временный аварийный режим:

```bash
pvecm expected 1
```

Это только временная операция, не для постоянной работы.

---

## Если вы используете Ceph

Qdevice помогает для кворума кластера Proxmox/HA, но **не решает проблему кворума Ceph**.

Для Ceph обычно нужно минимум три monitor-узла или третий внешний monitor.

---

# 9. Если вы имели в виду не qdevice, а QEMU Guest Agent

Иногда под похожим словом имеют в виду **qemu-guest-agent**.

Он ставится **внутри виртуальной машины**, а не на хосте Proxmox.

Для Linux VM:

```bash
apt update
apt install -y qemu-guest-agent
systemctl enable --now qemu-guest-agent
```

Затем в Proxmox:

1. Выключите VM.
2. Откройте VM → Options.
3. Включите **QEMU Guest Agent**.
4. Запустите VM.

Для Windows VM нужно установить драйверы VirtIO и `qemu-guest-agent` из образа `virtio-win`.

---

## Коротко

Для двух Proxmox-серверов:

```bash
# На обоих Proxmox
apt update
apt install -y corosync-qdevice

# На третьем сервере
apt update
apt install -y corosync-qnetd
systemctl enable --now corosync-qnetd

# На одном Proxmox
pvecm qdevice setup <IP_QDEVICE>

# Проверка
pvecm status
```

Если скажете, есть ли у вас уже кластер, версии Proxmox и адреса серверов, я могу дать точную пошаговую команду именно под вашу сеть.

### USER
Если я установил Proxmox на двух серверах и на простом пк, простой пк я хочу использовать как qdrivec 

### ASSISTANT
Отличный план. Использование отдельного ПК в качестве **qdevice** (вы, скорее всего, имели в виду именно его, а не «qdrivec») — это единственно правильный способ сделать двухузовой кластер Proxmox отказоустойчивым.

Ниже приведена пошаговая инструкция. Предполагаем, что на «простом ПК» вы установили чистый Debian/Ubuntu (или уже имеете какую-то Linux-систему). **Не устанавливайте на этот ПК сам Proxmox VE**, если он нужен только как qdevice — достаточно минимального Linux.

### 1. Подготовка простого ПК (QDevice Host)

На этом ПК должен быть установлен только `corosync-qnetd`. Никаких VM, Ceph или тяжелых сервисов здесь быть не должно.

```bash
# Обновите систему
apt update && apt upgrade -y

# Установите пакет qnetd
apt install -y corosync-qnetd

# Включите и запустите службу
systemctl enable --now corosync-qnetd

# Проверьте, что порт 5403 слушается
ss -ltnp | grep 5403
```

> ⚠️ **Важно:** Убедитесь, что на этом ПК **нет firewall**, блокирующего TCP-порт **5403**. Если есть `ufw`, `firewalld` или `iptables`, добавьте правило на разрешение входящих соединений по этому порту. Также убедитесь, что оба сервера Proxmox могут пинговать этот ПК и подключаться к нему по SSH (для первоначальной настройки).

---

### 2. Подготовка обоих серверов Proxmox

Выполните на **обоих** узлах кластера:

```bash
apt update
apt install -y corosync-qdevice
```

> 💡 Пакет `corosync-qdevice` — это клиентская часть, которая общается с `corosync-qnetd` на вашем простом ПК. Он должен быть установлен на всех узлах кластера.

---

### 3. Подключение QDevice к кластеру

Выполните эту команду **только на одном** из серверов Proxmox (например, на node1):

```bash
pvecm qdevice setup <IP_ПРОСТОГО_ПК>
```

Пример:
```bash
pvecm qdevice setup 192.168.1.50
```

Скрипт автоматически:
- Подключится к простому ПК по SSH;
- Скопирует необходимые сертификаты;
- Настроит `corosync-qdevice` на обоих узлах кластера;
- Запустит службу `corosync-qdevice`.

Если скрипт запросит подтверждение SSH-ключа или пароль root — введите их. Рекомендуется заранее настроить беспарольный SSH-доступ (`ssh-copy-id root@<IP_ПК>`), чтобы избежать проблем.

---

### 4. Проверка работоспособности

На любом узле Proxmox выполните:

```bash
pvecm status
```

Ожидаемый вывод:
```text
Quorate:          Yes
Expected votes:   3
Total votes:      3
Quorum:           2
Nodes:            2
QDevice:          Online
```

Дополнительные проверки:
```bash
# Статус quorum
corosync-quorumtool -s

# Статус службы qdevice на узле
systemctl status corosync-qdevice
```

На простом ПК проверьте:
```bash
systemctl status corosync-qnetd
corosync-qnetd-tool -s
```

---

### 5. Тестирование отказоустойчивости

Чтобы убедиться, что всё работает корректно:

1. Выключите один из серверов Proxmox (или отключите его сетевой интерфейс).
2. На оставшемся сервере выполните `pvecm status`.
3. Вы должны увидеть `Quorate: Yes`, несмотря на то, что один узел недоступен.
4. VM/CT должны продолжать работать, и HA-ресурсы должны мигрировать (если настроен HA + fencing).

> ⚠️ **Для полноценного HA также необходим fencing-механизм** (IPMI/iLO, PDU, watchdog). Без него при потере связи кластер может не перезапустить ресурсы на выжившем узле, даже если кворум сохранён благодаря qdevice.

---

### Чего НЕЛЬЗЯ делать

| Ошибка | Почему это плохо |
| :--- | :--- |
| Запускать qnetd на одном из узлов Proxmox | При падении этого узла теряется и qdevice → кворум потерян |
| Использовать Windows/macOS как qdevice | `corosync-qnetd` работает только на Linux |
| Игнорировать синхронизацию времени | Расхождение часов > нескольких секунд ломает corosync |
| Ставить qnetd за NAT без проброса порта 5403 | Узлы не смогут подключиться |

---

### Если что-то пошло не так

- **Ошибка SSH при `pvecm qdevice setup`**: проверьте `ssh root@<IP_ПК>` вручную, убедитесь, что root-вход разрешён в `/etc/ssh/sshd_config` (`PermitRootLogin yes`), перезапустите sshd.
- **QDevice показывает `Offline`**: проверьте firewall на простом ПК, доступность порта 5403, статус службы `corosync-qnetd`.
- **Нужно перенастроить qdevice на другой хост**: сначала удалите старый, затем добавьте новый:
  ```bash
  pvecm qdevice remove
  pvecm qdevice setup <НОВЫЙ_IP>
  ```

Если напишете IP-адреса всех трёх машин и версию Proxmox (`pveversion -v`), смогу дать более точные команды под вашу конфигурацию.

### USER
Напиши подробную пошаговую инструкцию 

### ASSISTANT
Ниже представлена максимально подробная, пошаговая инструкция по настройке **QDevice** для двухузового кластера Proxmox VE с использованием отдельного ПК в качестве свидетеля (quorum device).

> ⚠️ **Предупреждение:** Перед выполнением любых действий сделайте резервные копии конфигурации кластера и важных данных. Ошибки при работе с кворумом могут привести к остановке VM/CT.

---

## 📋 Исходные данные (пример)

| Роль | Имя хоста | IP-адрес | ОС |
| :--- | :--- | :--- | :--- |
| Node 1 | pve-node1 | 192.168.1.10 | Proxmox VE 8.x / 9.x |
| Node 2 | pve-node2 | 192.168.1.11 | Proxmox VE 8.x / 9.x |
| QDevice | qdevice-pc | 192.168.1.50 | Debian 12 / Ubuntu 22.04+ |

Замените адреса на свои реальные значения во всех командах ниже.

---

## Шаг 0. Предварительные требования

Убедитесь, что выполнены следующие условия:

1.  **Кластер уже создан** и оба узла Proxmox находятся в состоянии `Quorate`.
    ```bash
    # На любом узле Proxmox
    pvecm status
    # Должно быть: Quorate: Yes, Nodes: 2
    ```
2.  **Время синхронизировано** на всех трёх машинах (NTP/chrony). Расхождение более нескольких секунд ломает corosync.
    ```bash
    timedatectl status
    ```
3.  **DNS или /etc/hosts**: все три машины должны резолвить имена друг друга. Проще всего прописать в `/etc/hosts` на каждой машине:
    ```text
    192.168.1.10  pve-node1
    192.168.1.11  pve-node2
    192.168.1.50  qdevice-pc
    ```
4.  **SSH-доступ**: с node1 можно подключиться по SSH к qdevice-pc как root.
    ```bash
    # С node1
    ssh root@192.168.1.50
    ```
    Если не работает — настройте SSH-ключи или разрешите root-вход на qdevice-pc:
    ```bash
    # На qdevice-pc: /etc/ssh/sshd_config
    PermitRootLogin yes
    systemctl restart sshd
    ```
5.  **На простом ПК НЕ установлен Proxmox VE**. Только минимальный Linux.

---

## Шаг 1. Настройка простого ПК (QNetd Server)

Выполняйте все команды **на qdevice-pc (192.168.1.50)**.

### 1.1 Установка пакета

```bash
apt update && apt upgrade -y
apt install -y corosync-qnetd
```

### 1.2 Запуск и автозапуск службы

```bash
systemctl enable --now corosync-qnetd
```

### 1.3 Проверка работоспособности

```bash
systemctl status corosync-qnetd
```

Должно быть `active (running)`.

Проверьте, что порт открыт:
```bash
ss -ltnp | grep 5403
```

Ожидаемый вывод:
```text
LISTEN 0 5 *:5403 *:* users:(("corosync-qnetd",pid=...,fd=...))
```

### 1.4 Настройка Firewall (если есть)

Если на qdevice-pc включён фаервол, откройте TCP-порт 5403:

**UFW:**
```bash
ufw allow 5403/tcp
ufw reload
```

**Firewalld:**
```bash
firewall-cmd --permanent --add-port=5403/tcp
firewall-cmd --reload
```

**iptables:**
```bash
iptables -I INPUT -p tcp --dport 5403 -j ACCEPT
# Сохраните правила вашей утилитой (iptables-save / netfilter-persistent)
```

> 💡 Если firewall отключён полностью — этот подшаг можно пропустить, но убедитесь, что порт действительно доступен с обоих узлов Proxmox:
> ```bash
> # С node1 и node2
> nc -zv 192.168.1.50 5403
> ```

---

## Шаг 2. Подготовка узлов Proxmox

Выполните **на обоих узлах** (node1 и node2):

```bash
apt update
apt install -y corosync-qdevice
```

Проверьте, что пакет установился:
```bash
dpkg -l | grep corosync-qdevice
```

> ⚠️ Не запускайте и не настраивайте службу `corosync-qdevice` вручную! Это сделает команда `pvecm qdevice setup` автоматически.

---

## Шаг 3. Подключение QDevice к кластеру

Выполните **только на одном узле** (например, на node1):

```bash
pvecm qdevice setup 192.168.1.50
```

### Что произойдёт автоматически:

1.  Скрипт подключится к `192.168.1.50` по SSH.
2.  Скопирует сертификаты CA и клиентские сертификаты.
3.  Создаст конфигурацию qdevice в `/etc/pve/corosync.conf`.
4.  Распространит конфиг на все узлы через pmxcfs.
5.  Запустит и включит службу `corosync-qdevice` на обоих узлах.

### Возможные вопросы скрипта:

| Вопрос | Ответ |
| :--- | :--- |
| `Are you sure you want to continue?` | `y` |
| SSH host key fingerprint | Проверьте и подтвердите |
| Password for root@qdevice-pc | Введите пароль root (если нет ключей) |

Если команда завершилась без ошибок — переходите к проверке.

---

## Шаг 4. Проверка работоспособности

### 4.1 Статус кластера

На любом узле Proxmox:
```bash
pvecm status
```

**Ожидаемый результат:**
```text
Cluster information
~~~~~~~~~~~~~~~~~~~
Name:             mycluster
Config Version:   X
Transport:        knet
Secure auth:      on

Quorum information
~~~~~~~~~~~~~~~~~~
Date:             ...
Quorum provider:  corosync_votequorum
Nodes:            2
Node ID:          0x00000001
Ring ID:          1.xxx
Quorate:          Yes

Votequorum information
~~~~~~~~~~~~~~~~~~~~~~
Expected votes:   3
Highest expected: 3
Total votes:      3
Quorum:           2
Flags:            Quorate Qdevice

Membership information
~~~~~~~~~~~~~~~~~~~~~~
    Nodeid      Votes Name
         1          1 192.168.1.10 (local)
         2          1 192.168.1.11
         0          1 Qdevice
```

Ключевые показатели:
- ✅ `Expected votes: 3`
- ✅ `Quorum: 2`
- ✅ `Flags: Quorate Qdevice`
- ✅ В таблице участников есть строка `Qdevice` с 1 голосом

### 4.2 Детальная проверка quorum

```bash
corosync-quorumtool -s
```

### 4.3 Статус службы qdevice на узлах

На **обоих** узлах Proxmox:
```bash
systemctl status corosync-qdevice
```

Должно быть `active (running)`.

### 4.4 Статус QNetd на простом ПК

На qdevice-pc:
```bash
corosync-qnetd-tool -s
```

Должен показать подключённые узлы кластера.

---

## Шаг 5. Тестирование отказоустойчивости

> ⚠️ Выполняйте только в maintenance-окно или на тестовом кластере!

### Тест 1: Отказ одного узла Proxmox

1.  Корректно выключите node2:
    ```bash
    # На node2
    shutdown -h now
    ```
2.  На node1 проверьте:
    ```bash
    pvecm status
    ```
    Должно быть: `Quorate: Yes`, `Total votes: 2`, `Quorum: 2`.
3.  Убедитесь, что VM/CT продолжают работать и управление через GUI доступно.
4.  Включите node2 обратно и дождитесь восстановления кластера.

### Тест 2: Отказ QDevice

1.  Выключите qdevice-pc.
2.  На любом узле Proxmox:
    ```bash
    pvecm status
    ```
    Кластер должен остаться `Quorate: Yes` (два живых узла = 2 голоса, quorum = 2).
3.  Включите qdevice-pc обратно.

### Тест 3: Одновременный отказ узла + QDevice (НЕБЕЗОПАСНО)

Если упадут одновременно node2 и qdevice-pc, оставшийся node1 будет иметь только 1 голос из требуемых 2 → **кворум потерян**. Это ожидаемое поведение и именно поэтому qdevice должен быть независимым.

---

## Шаг 6. Настройка HA (опционально, но рекомендуется)

QDevice даёт кворум, но для автоматического перезапуска VM на выжившем узле нужен **fencing**. Без fencing HA-менеджер не может быть уверен, что упавший узел действительно мёртв, и не запустит ресурсы на другом узле (риск split-brain).

Минимальные варианты fencing для двух узлов:
- IPMI/iLO/DRAC (рекомендуется);
- Управляемая PDU;
- SBD + shared storage (для Ceph/RBD);
- Watchdog-based self-fencing (`ha-manager` + watchdog).

Настройка fencing выходит за рамки данной инструкции, но без неё qdevice сохраняет только доступность управления кластером, а не автоматическую миграцию VM.

---

## 🔧 Устранение неполадок

| Проблема | Диагностика | Решение |
| :--- | :--- | :--- |
| `pvecm qdevice setup` зависает или ошибка SSH | `ssh -v root@<IP_QDEVICE>` | Проверьте SSH-ключи, `PermitRootLogin`, firewall на порту 22 |
| QDevice показывает `Offline` в `pvecm status` | `systemctl status corosync-qdevice`; `journalctl -u corosync-qdevice` | Проверьте доступность порта 5403, статус `corosync-qnetd` на ПК |
| `corosync-qnetd-tool -s` пустой | `ss -ltnp \| grep 5403` | Перезапустите `corosync-qnetd`, проверьте firewall |
| Кластер не становится Quorate после добавления | `corosync-quorumtool -s` | Убедитесь, что `Expected votes = 3`, время синхронизировано |
| Нужно заменить qdevice на другой хост | — | `pvecm qdevice remove`, затем `pvecm qdevice setup <NEW_IP>` |
| Ошибка сертификатов | Журналы corosync-qdevice | Удалите qdevice (`pvecm qdevice remove`) и настройте заново |

---

## ❌ Чего категорически нельзя делать

1.  **Не запускайте `corosync-qnetd` на node1 или node2** — это уничтожает смысл qdevice.
2.  **Не редактируйте `/etc/pve/corosync.conf` вручную** для настройки qdevice — используйте только `pvecm qdevice setup/remove`.
3.  **Не игнорируйте NTP** — рассинхронизация времени > 2–3 секунд вызывает отказы corosync.
4.  **Не используйте Windows/macOS** в качестве qdevice-host — `corosync-qnetd` существует только для Linux.
5.  **Не размещайте qdevice на том же физическом хосте**, что и один из узлов Proxmox (даже в VM/LXC на этом же железе).

---

## 📝 Шпаргалка команд

```bash
# Добавить qdevice
pvecm qdevice setup <IP>

# Удалить qdevice
pvecm qdevice remove

# Статус кластера
pvecm status

# Детальный quorum
corosync-quorumtool -s

# Статус qdevice на узле
systemctl status corosync-qdevice

# Статус qnetd на ПК
systemctl status corosync-qnetd
corosync-qnetd-tool -s
```

Если у вас возникнут ошибки на каком-либо шаге — пришлите вывод команды и версию Proxmox (`pveversion -v`), помогу разобраться.

### USER
Сохрани эту инструкцию в текстовый файл для обсидиан

### ASSISTANT
Вот готовый текст в формате Markdown, оптимизированный для Obsidian. Вы можете скопировать его и сохранить как файл с расширением `.md` (например, `Proxmox_QDevice_Setup.md`).

```markdown
# Proxmox: Настройка QDevice для двухузового кластера

> [!info] Описание
> Пошаговая инструкция по настройке **QDevice** (Quorum Device) для кластера Proxmox VE из двух узлов с использованием отдельного ПК в качестве независимого свидетеля. Это необходимо для сохранения кворума при отказе одного из узлов.

> [!warning] Предупреждение
> Перед выполнением сделайте резервные копии конфигурации и данных. Ошибки при работе с кворумом могут привести к остановке VM/CT.

## 📋 Исходные данные (пример)

| Роль | Имя хоста | IP-адрес | ОС |
| :--- | :--- | :--- | :--- |
| Node 1 | pve-node1 | 192.168.1.10 | Proxmox VE 8.x / 9.x |
| Node 2 | pve-node2 | 192.168.1.11 | Proxmox VE 8.x / 9.x |
| QDevice | qdevice-pc | 192.168.1.50 | Debian 12 / Ubuntu 22.04+ |

> [!tip] Важно
> Замените адреса на свои реальные значения во всех командах ниже.

---

## Шаг 0. Предварительные требования

- [ ] Кластер уже создан и оба узла в состоянии `Quorate` (`pvecm status`)
- [ ] Время синхронизировано на всех трёх машинах (NTP/chrony)
- [ ] DNS или `/etc/hosts`: все машины резолвят имена друг друга
- [ ] SSH-доступ: с node1 можно подключиться к qdevice-pc как root
- [ ] На простом ПК **НЕ** установлен Proxmox VE (только минимальный Linux)

### Проверка SSH-доступа
```bash
# С node1
ssh root@192.168.1.50
```

Если не работает, на qdevice-pc разрешите root-вход:
```bash
# /etc/ssh/sshd_config → PermitRootLogin yes
systemctl restart sshd
```

---

## Шаг 1. Настройка простого ПК (QNetd Server)

> [!note] Выполнять на qdevice-pc (192.168.1.50)

### 1.1 Установка пакета
```bash
apt update && apt upgrade -y
apt install -y corosync-qnetd
```

### 1.2 Запуск службы
```bash
systemctl enable --now corosync-qnetd
```

### 1.3 Проверка
```bash
systemctl status corosync-qnetd
ss -ltnp | grep 5403
```

Ожидаемый вывод: `LISTEN ... *:5403 ...`

### 1.4 Firewall (если включён)

**UFW:**
```bash
ufw allow 5403/tcp && ufw reload
```

**Firewalld:**
```bash
firewall-cmd --permanent --add-port=5403/tcp && firewall-cmd --reload
```

**iptables:**
```bash
iptables -I INPUT -p tcp --dport 5403 -j ACCEPT
```

Проверка доступности с узлов Proxmox:
```bash
nc -zv 192.168.1.50 5403
```

---

## Шаг 2. Подготовка узлов Proxmox

> [!note] Выполнить на ОБА узлах (node1 и node2)

```bash
apt update
apt install -y corosync-qdevice
```

> [!warning] Не запускайте службу вручную!
> Службу `corosync-qdevice` запустит и настроит команда `pvecm qdevice setup` автоматически.

---

## Шаг 3. Подключение QDevice к кластеру

> [!note] Выполнить ТОЛЬКО на одном узле (например, node1)

```bash
pvecm qdevice setup 192.168.1.50
```

Скрипт автоматически:
1. Подключится к qdevice-pc по SSH
2. Скопирует сертификаты
3. Создаст конфиг в `/etc/pve/corosync.conf`
4. Распространит конфиг на все узлы
5. Запустит `corosync-qdevice` на обоих узлах

---

## Шаг 4. Проверка работоспособности

### Статус кластера
```bash
pvecm status
```

**Ожидаемый результат:**
- `Expected votes: 3`
- `Quorum: 2`
- `Flags: Quorate Qdevice`
- В таблице участников есть строка `Qdevice` с 1 голосом

### Дополнительные проверки
```bash
# Детальный quorum
corosync-quorumtool -s

# Служба на узлах Proxmox (на обоих!)
systemctl status corosync-qdevice

# Статус на qdevice-pc
corosync-qnetd-tool -s
```

---

## Шаг 5. Тестирование отказоустойчивости

> [!danger] Только в maintenance-окно или на тестовом кластере!

### Тест 1: Отказ одного узла
1. Выключите node2: `shutdown -h now`
2. На node1: `pvecm status` → должно быть `Quorate: Yes`
3. Включите node2 обратно

### Тест 2: Отказ QDevice
1. Выключите qdevice-pc
2. Кластер должен остаться `Quorate: Yes` (2 узла = 2 голоса)
3. Включите qdevice-pc обратно

> [!important] Одновременный отказ узла + QDevice
> Если упадут одновременно node2 и qdevice-pc → кворум потерян. Это ожидаемое поведение. Именно поэтому qdevice должен быть **независимым**.

---

## 🔧 Устранение неполадок

| Проблема | Диагностика | Решение |
| :--- | :--- | :--- |
| `pvecm qdevice setup` зависает | `ssh -v root@<IP>` | Проверьте SSH-ключи, `PermitRootLogin`, порт 22 |
| QDevice `Offline` | `journalctl -u corosync-qdevice` | Порт 5403, статус `corosync-qnetd` |
| `corosync-qnetd-tool -s` пустой | `ss -ltnp \| grep 5403` | Перезапуск службы, firewall |
| Не Quorate после добавления | `corosync-quorumtool -s` | `Expected votes = 3`, NTP |
| Замена qdevice | — | `pvecm qdevice remove` → `setup <NEW_IP>` |
| Ошибка сертификатов | Журналы | Удалить и настроить заново |

---

## ❌ Чего нельзя делать

- [ ] Запускать `corosync-qnetd` на node1/node2
- [ ] Редактировать `/etc/pve/corosync.conf` вручную для qdevice
- [ ] Игнорировать NTP (рассинхронизация > 2–3 сек ломает corosync)
- [ ] Использовать Windows/macOS как qdevice-host
- [ ] Размещать qdevice на том же физическом хосте, что и узел Proxmox

---

## 📝 Шпаргалка команд

```bash
# Добавить qdevice
pvecm qdevice setup <IP>

# Удалить qdevice
pvecm qdevice remove

# Статус кластера
pvecm status

# Детальный quorum
corosync-quorumtool -s

# Служба qdevice на узле
systemctl status corosync-qdevice

# Статус qnetd на ПК
systemctl status corosync-qnetd
corosync-qnetd-tool -s
```

---

## Связанные заметки

- [[Proxmox Cluster Setup]]
- [[Proxmox HA Fencing]]
- [[Corosync Troubleshooting]]
- [[NTP Sync Linux]]

#proxmox #cluster #qdevice #quorum #ha #linux #sysadmin
```

### Как использовать в Obsidian

1. Создайте новую заметку в вашем хранилище
2. Вставьте содержимое выше
3. Сохраните как `Proxmox_QDevice_Setup.md`
4. Теги внизу позволят найти заметку через поиск
5. Ссылки `[[...]]` в разделе «Связанные заметки» создадут связи с другими вашими заметками (создайте их при необходимости)

Формат использует callout-блоки Obsidian (`> [!info]`, `> [!warning]`, `> [!tip]`, `> [!danger]`, `> [!note]`), которые визуально выделяются в режиме чтения и делают инструкцию удобной для быстрого сканирования.
