---
date_created: 2026-08-30
target_system: "Proxmox VE Node (Standalone or Cluster)"
author: cladkyimaffin-hue
purpose: "Безопасное переименование ноды Proxmox с переносом конфигураций виртуальных машин"
status: "completed"
related_files: []
tags:
  - ProxmoxVE
  - Administration
  - Hostname
  - Troubleshooting
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
