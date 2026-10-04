### USER
изучи https://github.com/cladkyimaffin-hue/korona/tree/b6ade19c354ad1fb78b202bfc114d1ca01895019/Proxmox
Найди где мы говорили про зависание ssh при входе на pve01

### ASSISTANT
Я нашел обсуждение этой проблемы в нашей истории переписки. 

Мы говорили об этом **4 сентября 2026 года**:
- В **19:30:34** вы написали: *"после ввода пароля долго не выдает строку состояния"*
- В **19:43:40** вы уточнили: *"Нет - зависает"*

Это классический симптом зависания SSH-сессии именно **после успешной аутентификации**, но до появления командной строки (prompt).

### Что указано в вашем репозитории
В указанной вами директории `Proxmox` репозитория есть файл [`Проблемы с доступом по SSH на Debian.md`](https://github.com/cladkyimaffin-hue/korona/blob/b6ade19c354ad1fb78b202bfc114d1ca01895019/Proxmox/%D0%9F%D1%80%D0%BE%D0%B1%D0%BB%D0%B5%D0%BC%D1%8B%20%D1%81%20%D0%B4%D0%BE%D1%81%D1%82%D1%83%D0%BF%D0%BE%D0%BC%20%D0%BF%D0%BE%20SSH%20%D0%BD%D0%B0%20Debian.md). В нем задокументирован чек-лист диагностики SSH (проверка `sshd_config`, прав на ключи, статуса службы), но конкретное слово "зависание" там напрямую не фигурирует.

### Наиболее вероятные причины зависания после ввода пароля на pve01
Обычно такая задержка (зависание) возникает из-за таймаутов сетевых запросов, которые SSH-демон пытается выполнить перед выдачей оболочки. Два главных виновника:

1. **Обратное разрешение DNS (`UseDNS`)**  
   Сервер пытается сделать обратный DNS-запрос (reverse lookup) вашего IP-адреса. Если DNS-сервер недоступен или не отвечает, SSH ждет таймаута (обычно 10–30 секунд).
2. **Аутентификация GSSAPI/Kerberos (`GSSAPIAuthentication`)**  
   Сервер пытается использовать Kerberos для аутентификации. Если контроллер домена недоступен или не настроен, происходит задержка до отмены запроса.

### Как это исправить на `pve01`
Подключитесь к консоли Proxmox (через веб-интерфейс, если SSH зависает) и проверьте/измените следующие параметры в файле `/etc/ssh/sshd_config`:

```bash
# Отключаем обратный DNS-lookup
UseDNS no

# Отключаем GSSAPI аутентификацию (если не используется активно в домене)
GSSAPIAuthentication no
```

После внесения изменений перезапустите службу SSH:
```bash
systemctl restart sshd
```

Если вы хотите, я могу проверить текущее содержимое `sshd_config` на `pve01` или помочь добавить эти параметры через скрипт.

### USER

-bash: UseDNS: command not found
нади полные каманды

### ASSISTANT
Ошибка возникла потому, что `UseDNS` — это не команда для терминала, а параметр, который нужно записать внутрь конфигурационного файла `/etc/ssh/sshd_config`.

Чтобы не открывать текстовые редакторы вручную, вы можете просто **скопировать и выполнить по очереди** следующие команды в консоли (лучше всего делать это через веб-консоль Proxmox: выберите ноду `pve01` → вкладка **Console**, чтобы не зависеть от зависающего SSH).

### Полные команды для исправления (копируйте по одной строке):

```bash
# 1. Создаем резервную копию текущего конфигурационного файла
sudo cp /etc/ssh/sshd_config /etc/ssh/sshd_config.bak

# 2. Удаляем старые строки с UseDNS и GSSAPIAuthentication (если они там есть, чтобы не было дублей)
sudo sed -i '/^#*UseDNS/d' /etc/ssh/sshd_config
sudo sed -i '/^#*GSSAPIAuthentication/d' /etc/ssh/sshd_config

# 3. Добавляем правильные настройки в конец файла
echo "UseDNS no" | sudo tee -a /etc/ssh/sshd_config
echo "GSSAPIAuthentication no" | sudo tee -a /etc/ssh/sshd_config

# 4. Проверяем синтаксис файла на ошибки (должно вывести пустую строку, если всё ОК)
sudo sshd -t

# 5. Перезапускаем службу SSH для применения настроек
sudo systemctl restart sshd
```

### Как проверить, что помогло:
Попробуйте подключиться по SSH к `pve01` с вашего рабочего компьютера. Вход должен происходить мгновенно после ввода пароля или использования ключа, без задержек и зависаний.

*Если команда `sudo sshd -t` выдаст ошибку, не перезапускайте службу, а напишите мне текст ошибки, и мы её исправим.*

### USER
перезагрузил продолжает зависать

### ASSISTANT
Если перезагрузка не помогла, значит проблема не в самом SSH-демонe, а в том, что система пытается сделать **сразу после успешной аутентификации**, но **до появления командной строки**. 

В Proxmox это чаще всего вызвано одной из трех причин:
1. Скрипт приветствия (MOTD) пытается проверить статус кластера (`pvecm status`) или Ceph, и зависает из-за таймаута (например, если второй узел кластера недоступен).
2. Система не может разрешить собственное имя хоста (`pve01`) через `/etc/hosts`.
3. Что-то в файлах инициализации оболочки (`/root/.bashrc`, `/etc/profile`) обращается к недоступному сетевому ресурсу.

Давайте локализуем проблему. Выполняйте эти шаги (лучше всего через **веб-консоль Proxmox (NoVNC)**, чтобы не зависеть от зависающего SSH).

---

### Шаг 1. Проверка без загрузки оболочки (самый важный тест)
С вашего рабочего компьютера выполните команду, которая **не** загружает профиль и не показывает приветствие:
```bash
ssh root@<IP-адрес-pve01> 'echo "ТЕСТ ПРОШЕЛ"'
```
*(Замените `<IP-адрес-pve01>` на реальный IP)*

- **Если ответ пришел мгновенно** ("ТЕСТ ПРОШЕЛ"): Проблема 100% в скриптах приветствия (MOTD) или `.bashrc`. Переходите к Шагу 3.
- **Если команда тоже зависла**: Проблема глубже (сеть, PAM, resolv). Переходите к Шагу 2.

---

### Шаг 2. Включаем подробный режим (чтобы увидеть, где именно затык)
С вашего рабочего компьютера подключитесь с флагом `-v` (verbose):
```bash
ssh -v root@<IP-адрес-pve01>
```
Посмотрите на последние 5–10 строк перед тем, как вывод остановится. 
*(Часто там видно что-то вроде `Entering interactive session`, после чего идет тишина, или запрос к `pvecm`, или `reverse mapping checking`).* 
**Скопируйте сюда эти последние строки**, это даст точный ответ.

---

### Шаг 3. Исправление самых частых причин в Proxmox

#### А. Проверка `/etc/hosts` (Критично для Proxmox)
Proxmox должен мгновенно разрешать свое имя. Выполните в консоли:
```bash
cat /etc/hosts
```
Убедитесь, что там есть строка, связывающая IP ноды и её имя. Она должна выглядеть примерно так (замените `192.168.12.154` на реальный IP вашей ноды):
```text
127.0.0.1 localhost.localdomain localhost
192.168.12.154 pve01.local pve01
# Следующая строка желательна для IPv6
::1     ip6-localhost ip6-loopback
```
Если строки с `pve01` нет или там указан неверный IP, исправьте это:
```bash
nano /etc/hosts
```
*(Вставьте правильную строку, сохраните через `Ctrl+O`, `Enter`, выход `Ctrl+X`)*.

#### Б. Временное отключение приветствия Proxmox (MOTD)
Если зависание вызывает проверка статуса кластера при входе, отключите генерацию MOTD:
```bash
# Делаем скрипты приветствия невыполняемыми
chmod -x /etc/update-motd.d/*
```
После этого попробуйте войти по SSH снова. Если вход стал мгновенным — мы нашли виновника.

#### В. Проверка логов аутентификации
Если ничего не помогло, посмотрите, что пишет система в момент вашего подключения (в веб-консоли):
```bash
tail -f /var/log/auth.log
```
Попробуйте подключиться по SSH с другого терминала и смотрите, какие ошибки или задержки появляются в этом логе в реальном времени.

---

**Что делать дальше:**
Напишите мне:
1. Прошел ли тест из **Шага 1** мгновенно или завис?
2. На какой строке останавливается вывод из **Шага 2** (`ssh -v`)?
3. Что показывает `cat /etc/hosts`?

Это позволит нам точно устранить причину, а не гадать.

### USER

127.0.0.1       localhost
::1             localhost ip6-localhost ip6-loopback
ff02::1         ip6-allnodes
ff02::2         ip6-allrouters
# --- BEGIN PVE ---
192.168.200.230 passwd.01.krnn.ru passwd
# --- END PVE ---
root@passwd:~#
rs\User>ssh -v root@192.168.200.230 'echo "ТЕСТ ПРОШЕЛ"'
OpenSSH_for_Windows_8.1p1, LibreSSL 3.0.2
debug1: Connecting to 192.168.200.230 [192.168.200.230] port 22.
debug1: Connection established.
debug1: identity file C:\\Users\\User/.ssh/id_rsa type -1
debug1: identity file C:\\Users\\User/.ssh/id_rsa-cert type -1
debug1: identity file C:\\Users\\User/.ssh/id_dsa type -1
debug1: identity file C:\\Users\\User/.ssh/id_dsa-cert type -1
debug1: identity file C:\\Users\\User/.ssh/id_ecdsa type -1
debug1: identity file C:\\Users\\User/.ssh/id_ecdsa-cert type -1
debug1: identity file C:\\Users\\User/.ssh/id_ed25519 type -1
debug1: identity file C:\\Users\\User/.ssh/id_ed25519-cert type -1
debug1: identity file C:\\Users\\User/.ssh/id_xmss type -1
debug1: identity file C:\\Users\\User/.ssh/id_xmss-cert type -1
debug1: Local version string SSH-2.0-OpenSSH_for_Windows_8.1
debug1: Remote protocol version 2.0, remote software version OpenSSH_9.2p1 Debian-2+deb12u7
debug1: match: OpenSSH_9.2p1 Debian-2+deb12u7 pat OpenSSH* compat 0x04000000
debug1: Authenticating to 192.168.200.230:22 as 'root'
debug1: SSH2_MSG_KEXINIT sent
debug1: SSH2_MSG_KEXINIT received
debug1: kex: algorithm: curve25519-sha256
debug1: kex: host key algorithm: ecdsa-sha2-nistp256
debug1: kex: server->client cipher: chacha20-poly1305@openssh.com MAC: <implicit> compression: none
debug1: kex: client->server cipher: chacha20-poly1305@openssh.com MAC: <implicit> compression: none
debug1: expecting SSH2_MSG_KEX_ECDH_REPLY
debug1: Server host key: ecdsa-sha2-nistp256 SHA256:iMoPwcP3mYPT3wknGzpGJmai2mWoiI+gZtNUEZO/xj0
debug1: Host '192.168.200.230' is known and matches the ECDSA host key.
debug1: Found key in C:\\Users\\User/.ssh/known_hosts:1
debug1: rekey out after 134217728 blocks
debug1: SSH2_MSG_NEWKEYS sent
debug1: expecting SSH2_MSG_NEWKEYS
debug1: SSH2_MSG_NEWKEYS received
debug1: rekey in after 134217728 blocks
debug1: pubkey_prepare: ssh_get_authentication_socket: No such file or directory
debug1: Will attempt key: C:\\Users\\User/.ssh/id_rsa
debug1: Will attempt key: C:\\Users\\User/.ssh/id_dsa
debug1: Will attempt key: C:\\Users\\User/.ssh/id_ecdsa
debug1: Will attempt key: C:\\Users\\User/.ssh/id_ed25519
debug1: Will attempt key: C:\\Users\\User/.ssh/id_xmss
debug1: SSH2_MSG_EXT_INFO received
debug1: kex_input_ext_info: server-sig-algs=<ssh-ed25519,sk-ssh-ed25519@openssh.com,ecdsa-sha2-nistp256,ecdsa-sha2-nistp384,ecdsa-sha2-nistp521,sk-ecdsa-sha2-nistp256@openssh.com,webauthn-sk-ecdsa-sha2-nistp256@openssh.com,ssh-dss,ssh-rsa,rsa-sha2-256,rsa-sha2-512>
debug1: kex_input_ext_info: publickey-hostbound@openssh.com (unrecognised)
debug1: SSH2_MSG_SERVICE_ACCEPT received
debug1: Authentications that can continue: publickey,password
debug1: Next authentication method: publickey
debug1: Trying private key: C:\\Users\\User/.ssh/id_rsa
debug1: Trying private key: C:\\Users\\User/.ssh/id_dsa
debug1: Trying private key: C:\\Users\\User/.ssh/id_ecdsa
debug1: Trying private key: C:\\Users\\User/.ssh/id_ed25519
debug1: Trying private key: C:\\Users\\User/.ssh/id_xmss
debug1: Next authentication method: password
debug1: read_passphrase: can't open /dev/tty: No such file or directory
root@192.168.200.230's password:

C:\Users\User>ssh -v root@192.168.200.230 'echo "ТЕСТ ПРОШЕЛ"'
OpenSSH_for_Windows_8.1p1, LibreSSL 3.0.2
debug1: Connecting to 192.168.200.230 [192.168.200.230] port 22.
debug1: Connection established.
debug1: identity file C:\\Users\\User/.ssh/id_rsa type -1
debug1: identity file C:\\Users\\User/.ssh/id_rsa-cert type -1
debug1: identity file C:\\Users\\User/.ssh/id_dsa type -1
debug1: identity file C:\\Users\\User/.ssh/id_dsa-cert type -1
debug1: identity file C:\\Users\\User/.ssh/id_ecdsa type -1
debug1: identity file C:\\Users\\User/.ssh/id_ecdsa-cert type -1
debug1: identity file C:\\Users\\User/.ssh/id_ed25519 type -1
debug1: identity file C:\\Users\\User/.ssh/id_ed25519-cert type -1
debug1: identity file C:\\Users\\User/.ssh/id_xmss type -1
debug1: identity file C:\\Users\\User/.ssh/id_xmss-cert type -1
debug1: Local version string SSH-2.0-OpenSSH_for_Windows_8.1
debug1: Remote protocol version 2.0, remote software version OpenSSH_9.2p1 Debian-2+deb12u7
debug1: match: OpenSSH_9.2p1 Debian-2+deb12u7 pat OpenSSH* compat 0x04000000
debug1: Authenticating to 192.168.200.230:22 as 'root'
debug1: SSH2_MSG_KEXINIT sent
debug1: SSH2_MSG_KEXINIT received
debug1: kex: algorithm: curve25519-sha256
debug1: kex: host key algorithm: ecdsa-sha2-nistp256
debug1: kex: server->client cipher: chacha20-poly1305@openssh.com MAC: <implicit> compression: none
debug1: kex: client->server cipher: chacha20-poly1305@openssh.com MAC: <implicit> compression: none
debug1: expecting SSH2_MSG_KEX_ECDH_REPLY
debug1: Server host key: ecdsa-sha2-nistp256 SHA256:iMoPwcP3mYPT3wknGzpGJmai2mWoiI+gZtNUEZO/xj0
debug1: Host '192.168.200.230' is known and matches the ECDSA host key.
debug1: Found key in C:\\Users\\User/.ssh/known_hosts:1
debug1: rekey out after 134217728 blocks
debug1: SSH2_MSG_NEWKEYS sent
debug1: expecting SSH2_MSG_NEWKEYS
debug1: SSH2_MSG_NEWKEYS received
debug1: rekey in after 134217728 blocks
debug1: pubkey_prepare: ssh_get_authentication_socket: No such file or directory
debug1: Will attempt key: C:\\Users\\User/.ssh/id_rsa
debug1: Will attempt key: C:\\Users\\User/.ssh/id_dsa
debug1: Will attempt key: C:\\Users\\User/.ssh/id_ecdsa
debug1: Will attempt key: C:\\Users\\User/.ssh/id_ed25519
debug1: Will attempt key: C:\\Users\\User/.ssh/id_xmss
debug1: SSH2_MSG_EXT_INFO received
debug1: kex_input_ext_info: server-sig-algs=<ssh-ed25519,sk-ssh-ed25519@openssh.com,ecdsa-sha2-nistp256,ecdsa-sha2-nistp384,ecdsa-sha2-nistp521,sk-ecdsa-sha2-nistp256@openssh.com,webauthn-sk-ecdsa-sha2-nistp256@openssh.com,ssh-dss,ssh-rsa,rsa-sha2-256,rsa-sha2-512>
debug1: kex_input_ext_info: publickey-hostbound@openssh.com (unrecognised)
debug1: SSH2_MSG_SERVICE_ACCEPT received
debug1: Authentications that can continue: publickey,password
debug1: Next authentication method: publickey
debug1: Trying private key: C:\\Users\\User/.ssh/id_rsa
debug1: Trying private key: C:\\Users\\User/.ssh/id_dsa
debug1: Trying private key: C:\\Users\\User/.ssh/id_ecdsa
debug1: Trying private key: C:\\Users\\User/.ssh/id_ed25519
debug1: Trying private key: C:\\Users\\User/.ssh/id_xmss
debug1: Next authentication method: password
debug1: read_passphrase: can't open /dev/tty: No such file or directory
root@192.168.200.230's password:



### ASSISTANT
Судя по логам, проблема локализована с высокой точностью: 
1. Соединение устанавливается успешно.
2. Аутентификация по паролю проходит.
3. **Зависание происходит ровно после ввода пароля**, до выполнения команды `echo "ТЕСТ ПРОШЕЛ"`.

Это классический признак того, что сервер (Proxmox/Debian 12) "затыкается" на этапе **инициализации сессии PAM** или **генерации приветствия (MOTD)**. Чаще всего в Proxmox это происходит, когда скрипт приветствия пытается проверить статус кластера (`pvecm status`) или Ceph, а второй узел недоступен или сеть настроена некорректно, из-за чего возникает таймаут (30–60 секунд).

Также видно, что имя хоста у вас сейчас `passwd` (судя по строке `root@passwd:~#` и записи в `/etc/hosts`), а не `pve01`. Это нормально, главное, что `/etc/hosts` соответствует текущему имени.

Давайте применим точечные исправления. Выполняйте эти команды в **веб-консоли Proxmox** (чтобы не зависеть от SSH).

---

### Шаг 1. Отключаем генерацию приветствия (MOTD)
Это причина №1 зависаний после ввода пароля в Proxmox. Мы делаем скрипты приветствия невыполняемыми.

```bash
# Делаем все скрипты motd невыполняемыми
chmod -x /etc/update-motd.d/*

# Удаляем кэш динамического motd, если он есть
rm -f /var/run/motd.dynamic
```
*После этого сразу попробуйте подключиться по SSH. Если зашло мгновенно — проблема решена.*

---

### Шаг 2. Проверка через SSH без выделения терминала (TTY)
Если Шаг 1 не помог, попробуем подключиться с флагом `-T`. Этот флаг запрещает SSH запрашивать выделение псевдотерминала, что часто позволяет обойти зависания, связанные с `pam_systemd` или `pam_motd`.

С вашего компьютера (Windows) выполните:
```cmd
ssh -T root@192.168.200.230 "echo УСПЕХ_БЕЗ_TTY"
```
*Если эта команда отработала мгновенно и вывела "УСПЕХ_БЕЗ_TTY", значит, проблема 100% в PAM-модулях сессии (например, `pam_systemd.so` или `pam_env.so`).*

---

### Шаг 3. Диагностика через логи в реальном времени
Чтобы точно увидеть, на каком модуле происходит затык, нам нужно посмотреть логи сервера в момент подключения.

1. Откройте **веб-консоль Proxmox** (ноду `passwd`).
2. Введите команду для отслеживания логов SSH в реальном времени:
   ```bash
   journalctl -u sshd -f
   ```
3. Не закрывая веб-консоль, откройте командную строку Windows и попробуйте подключиться:
   ```cmd
   ssh root@192.168.200.230
   ```
4. Введите пароль и дождитесь зависания.
5. Посмотрите в веб-консоль: какая **последняя строка** появилась в логе перед тем, как всё замерло? (Скопируйте её сюда).

---

### Шаг 4. Проверка, применились ли прошлые настройки
На всякий случай убедимся, что файлы конфигурации действительно изменились после наших прошлых правок. Выполните в веб-консоли:

```bash
grep -E "UseDNS|GSSAPIAuthentication" /etc/ssh/sshd_config
```
*Ожидаемый вывод:*
```text
UseDNS no
GSSAPIAuthentication no
```
*(Если вывод пустой или там стоит `yes`, напишите мне, мы перезапишем файл принудительно).*

---

**Что делать дальше:**
Попробуйте **Шаг 1** и **Шаг 2**. Если зависание сохранится, выполните **Шаг 3** и пришлите мне последнюю строку из `journalctl`, на которой обрывается лог. Это даст нам точное имя модуля, который вызывает задержку.

### USER
root@passwd:~# grep -E "UseDNS|GSSAPIAuthentication" /etc/ssh/sshd_config
UseDNS no
root@passwd:~#



### ASSISTANT
Отлично, мы нашли одну из причин: в конфигурации есть `UseDNS no`, но **отсутствует** `GSSAPIAuthentication no`. 

Из-за этого сервер при каждом входе всё ещё пытается использовать Kerberos-аутентификацию (GSSAPI), не находит её и ждет таймаута, что вызывает зависание сразу после ввода пароля.

Выполните эти **3 команды** в веб-консоли Proxmox (одну за другой):

```bash
# 1. Добавляем отсутствующую настройку в конец файла
echo "GSSAPIAuthentication no" >> /etc/ssh/sshd_config

# 2. Отключаем скрипты приветствия Proxmox (они часто зависают, проверяя статус кластера pvecm)
chmod -x /etc/update-motd.d/*

# 3. Перезапускаем службу SSH для применения изменений
systemctl restart sshd
```

После этого **сразу же проверьте вход по SSH** с вашего компьютера:
```cmd
ssh root@192.168.200.230
```

Вход должен произойти мгновенно. Если вдруг всё равно будет зависать, напишите, и мы посмотрим логи PAM (это будет означать, что затык происходит на уровне системных модулей авторизации, а не SSH).

### USER

root@passwd:~# grep -E "UseDNS|GSSAPIAuthentication" /etc/ssh/sshd_config
UseDNS no
GSSAPIAuthentication no
root@passwd:~#

висит и жду строки состояния очень долго

### ASSISTANT
Понимаю, это раздражает, но мы уже отсекли самые частые причины (DNS и GSSAPI). Раз зависание сохраняется, проблема находится либо в **скриптах запуска оболочки** (`.bashrc`), либо в **модулях PAM** (система авторизации), которые пытаются что-то сделать перед выдачей приглашения.

Давайте разделим задачу пополам, чтобы точно найти виновника. Выполните эти шаги по порядку.

---

### Шаг 1. Тест в обход оболочки (Ключевой тест)
С вашего компьютера (Windows) выполните команду, которая **не запускает** `.bashrc`, `.profile` и не создает полноценный интерактивный терминал:

```cmd
ssh root@192.168.200.230 /bin/sh -c "echo УСПЕХ"
```

- **Если ответ "УСПЕХ" пришел МГНОВЕННО**: Проблема на 100% внутри файлов `/root/.bashrc` или `/root/.profile` (например, там есть команда `pvecm status`, которая ждет таймаута, или какая-то сетевая проверка). Переходите к Шагу 3.
- **Если команда тоже ЗАВИСАЕТ**: Проблема на уровне системной авторизации (PAM) или сети. Переходите к Шагу 2.

---

### Шаг 2. Ловим момент зависания в логах
Нам нужно увидеть, на какой именно строчке система "замирает".

1. Откройте **веб-консоль Proxmox** (нода `passwd`).
2. Введите команду для просмотра логов SSH в реальном времени:
   ```bash
   journalctl -u sshd -f
   ```
3. Не закрывая веб-консоль, откройте Windows и попробуйте подключиться как обычно:
   ```cmd
   ssh root@192.168.200.230
   ```
4. Введите пароль и дождитесь зависания (секунд 10-15).
5. Посмотрите в веб-консоль: какие **последние 3-5 строк** появились в логе в момент зависания? 
   *(Скопируйте их и пришлите мне. Там будет видно, например, `pam_systemd(sshd:session): ...` или `Accepted password`, после которого тишина).*

---

### Шаг 3. Проверка файлов запуска (если Шаг 1 прошел мгновенно)
Если тест из Шага 1 сработал быстро, посмотрим, что мешает обычному входу. Выполните в веб-консоли:

```bash
cat /root/.bashrc
```
Пришлите мне вывод этой команды. Мы ищем там любые команды, которые могут обращаться к сети, кластеру (`pvecm`, `ceph`) или другим серверам.

---

### Шаг 4. Временное отключение PAM-сессий (если Шаг 2 показал зависание на PAM)
Если в логах видно, что зависание происходит на этапе `pam_systemd` или `session opened`, это известная проблема Debian/Proxmox, когда `systemd-logind` не отвечает вовремя. 

Для проверки выполните в веб-консоли:
```bash
# Временно комментируем создание сессии systemd для SSH
sed -i 's/^session\s\+optional\s\+pam_systemd.so/#session optional pam_systemd.so/' /etc/pam.d/sshd
systemctl restart sshd
```
После этого попробуйте подключиться по SSH. Если стало быстро — мы нашли причину (можно будет решить её корректным обновлением или настройкой systemd, а не костылем).

---

**Жду от вас:**
1. Результат теста из **Шага 1** (мгновенно или висит).
2. Если висит — последние строки из **Шага 2**.
3. Если мгновенно — вывод **Шага 3** (`cat /root/.bashrc`). 

Это точно приведет нас к решению.

### USER
root@passwd:~# journalctl -u sshd -f
^C
root@passwd:~# cat /root/.bashrc
# ~/.bashrc: executed by bash(1) for non-login shells.

# Note: PS1 and umask are already set in /etc/profile. You should not
# need this unless you want different defaults for root.
# PS1='${debian_chroot:+($debian_chroot)}\h:\w\$ '
# umask 022

# You may uncomment the following lines if you want `ls' to be colorized:
# export LS_OPTIONS='--color=auto'
# eval "$(dircolors)"
# alias ls='ls $LS_OPTIONS'
# alias ll='ls $LS_OPTIONS -l'
# alias l='ls $LS_OPTIONS -lA'
#
# Some more alias to avoid making mistakes:
# alias rm='rm -i'
# alias cp='cp -i'
# alias mv='mv -i'
root@passwd:~#


### ASSISTANT
Хорошая новость: `.bashrc` абсолютно чистый, стандартный Debian. Проблема **не в нём**.

Но вы не выполнили самый важный тест — команду, которая полностью обходит все скрипты входа. Без неё мы вслепую. Давайте сделаем это сейчас.

---

### Выполните по порядку:

**1. Ключевой тест (с вашего компьютера Windows):**
```cmd
ssh root@192.168.200.230 /bin/sh -c "echo УСПЕХ"
```
*Введите пароль. Ответ пришёл мгновенно или зависло?*

---

**2. Проверка профиля входа (в веб-консоли Proxmox):**
```bash
cat /root/.profile
```

---

**3. Проверка системных скриптов входа (в веб-консоли Proxmox):**
```bash
ls -la /etc/profile.d/
```

---

**4. Проверка PAM-конфига SSH (в веб-консоли Proxmox):**
```bash
cat /etc/pam.d/sshd
```

---

Пришлите результат теста из пункта 1 (мгновенно/зависло) и вывод команд из пунктов 2–4. Это позволит точно определить, где происходит задержка: в скриптах `/etc/profile.d/`, в `/root/.profile` или в PAM-модулях (например, `pam_systemd`).