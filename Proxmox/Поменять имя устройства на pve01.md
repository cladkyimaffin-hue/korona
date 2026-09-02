---
# === БАЗОВАЯ ИНФОРМАЦИЯ ===
date_created: 2026-08-30
date_modified: 2026-09-02
author: cladkyimaffin-hue
status: "completed"
# === КОНТЕКСТ СИСТЕМЫ ===
target_system: "Proxmox VE Node (Debian Linux)"
environment: "production"
# === БЫСТРАЯ КЛАССИФИКАЦИЯ ===
category: "setup"
severity: "high"
problem: "Необходимость корректного изменения hostname узла Proxmox после установки без нарушения работы кластера и SSL-сертификатов."
solution: "Использование утилиты `pvenode` для смены имени, обновление `/etc/hosts` и `/etc/hostname` с последующей перезагрузкой."
root_cause: "Прямое редактирование только файлов конфигурации без использования инструментов Proxmox приводит к рассинхронизации и ошибкам SSL."
# === AI-СПЕЦИФИЧНЫЕ ПОЛЯ ===
ai_summary: "Инструкция по безопасному переименованию узла Proxmox VE. Описывает использование `pvenode set`, правку системных файлов и перегенерацию сертификатов."
key_takeaways:
  - "Имя узла должно быть FQDN (например, pve01.krnn.ru)."
  - "После смены имени требуется перезагрузка узла для применения изменений во всех службах."
dont_repeat:
  - "Не предлагать изменение hostname только через `/etc/hostname` или `hostnamectl` без использования `pvenode set` и обновления `/etc/hosts`."
  - "Не выполнять переименование узла, если он уже является частью активного кластера (требуется выход из кластера)."
assumptions:
  - "Узел еще не добавлен в кластер, или кластер временно остановлен для обслуживания."
# === АРТЕФАКТЫ ===
commands: |
  # Смена имени узла
  pvenode set pve01.krnn.ru
  # Обновление /etc/hosts (пример)
  # 192.168.202.121 pve01.krnn.ru pve01
  # Перезагрузка
  reboot
config_snippets:
  etc_hosts_example: |
    127.0.0.1 localhost.localdomain localhost
    192.168.202.121 pve01.krnn.ru pve01
urls: []
# === СВЯЗИ ===
related_files:
  - "INDEX.md"
  - "Скрипт pstInstal после установки Proxmox.md"
depends_on: []
superseded_by: ""
tags:
  - "ProxmoxVE"
  - "Configuration"
  - "Hostname"
# === ВРЕМЕННОЙ КОНТЕКСТ ===
last_incident: 2026-08-30
next_review: 2026-12-01
valid_until: 2027-01-01
# === ОТВЕТСТВЕННОСТЬ ===
reviewer: "cladkyimaffin-hue"
approval_status: "approved"
---
### USER
Поменять имя устройства на pve01

### ASSISTANT
Имя ноды в Proxmox — это системный hostname, поэтому править нужно `/etc/hosts` + `/etc/hostname`, а после переименования — перенести каталог конфигураций VM. Порядок действий (если нода **не в кластере** — проверьте `pvecm status`):

**1. Поправьте `/etc/hosts`** (как раз окно на вашем скриншоте). Замените строку с IP ноды — сначала FQDN, затем короткое имя:

```
127.0.0.1 localhost.localdomain localhost
192.168.202.121 pve01.01.krnn.ru pve01
```

(если ваш домен `krnn.ru`, а не `01.krnn.ru` — пишите `pve01.krnn.ru pve01`). Главное: имя ноды **не** должно указывать на 127.0.0.1. Нажмите Save.

**2. Поменяйте `/etc/hostname`** (Node → Shell или по SSH):

```bash
echo "pve01" > /etc/hostname
```

**3. Перезагрузите ноду:**

```bash
reboot
```

**4. После перезагрузки** зайдите в веб‑интерфейс по тому же IP. Нода будет называться `pve01`, но список VM будет пуст — конфигурации лежат в каталоге со старым именем. Перенесите их:

```bash
ls /etc/pve/nodes/
# если каталог pve01 ещё не создан:
mv /etc/pve/nodes/pve /etc/pve/nodes/pve01

# если pve01 уже создан (пустой) — слейте содержимое:
cp -a /etc/pve/nodes/pve/. /etc/pve/nodes/pve01/
rm -rf /etc/pve/nodes/pve
```

Затем перезапустите службы (или просто ещё раз `reboot`):

```bash
systemctl restart pvedaemon pveproxy pvestatd pvescheduler
```

**5.** Готово — VM, LXC и снапшоты появятся на ноде `pve01`.

Замечания:
- Делайте в maintenance‑окно: перезагрузка остановит работающие VM.
- Самоподписанный сертификат останется со старым именем — не критично; при желании перегенерируйте в Node → Certificates.
- Если нода **в кластере** (даже в single‑node), процедура другая: придётся ещё править имя в `corosync.conf` при остановленном кластере. В этом случае лучше свериться с wiki‑страницей «Renaming a Node».

### USER
Составь полную инструкцию правельных ответов

### ASSISTANT
