---
document_id: "PROXMOX-WINSRV2022-TEMPLATE-2026-001"
title: "Создание шаблона Windows Server 2022 (VirtIO, UEFI+TPM, Sysprep) — итоговый ID 2000"
document_type: "setup"
status: "completed"
priority: "high"
date_created: 2026-09-05
date_modified: 2026-09-05
next_review: 2026-12-01
author: "cladkyimaffin-hue"
category: "05_VirtualMachines"
tags:
  - "ProxmoxVE"
  - "WindowsServer2022"
  - "Template"
  - "VirtIO"
  - "QEMUGuestAgent"
  - "Sysprep"
  - "UEFI"
  - "TPM"
ai_summary: "Создание мастер-шаблона Windows Server 2022 в Proxmox VE: q35+OVMF(UEFI)+TPM2.0, VirtIO SCSI/Network, QEMU Guest Agent, включение RDP, корректный запуск Sysprep (Generalize + Shutdown, полный путь к sysprep.exe), конвертация в шаблон. Итоговый готовый шаблон — VMID 2000 (win2022-template), диск 100 ГБ на ceph-fast, RAM 4096 MiB, CPU 4 ядра. Промежуточная ошибка: первый клон (VMID 2000, до финального) был создан как linked clone от исходного шаблона (VMID 100) и блокировал его удаление — пересоздан как full clone."
dont_repeat:
  - "Не запускать `sysprep` как команду PowerShell — это исполняемый файл, вызывать по полному пути: & 'C:\\Windows\\System32\\Sysprep\\sysprep.exe'."
  - "В окне Sysprep обязательно ставить галочку «Подготовка к использованию» (Generalize) — без неё SID не обобщается, клоны будут конфликтовать в AD."
  - "В окне Sysprep выбирать «Завершение работы», не «Перезагрузка» — перезагрузка запустит OOBE и испортит шаблон."
  - "Не удалять исходный шаблон сразу после клонирования — сначала проверить `qm config <id> | grep -E \"(template|clone)\"`; если клон связанный (linked), сначала пересоздать как full clone (`--full 1`), потом удалять исходник."
  - "Не использовать IDE/SATA для системного диска Windows — только VirtIO SCSI с ISO virtio-win, подключённым уже на этапе установки."
  - "Не путать `qm` (KVM/QEMU ВМ) и `pct` (LXC-контейнеры) по одному только ID — путь конфигурации (`qemu-server/` vs `lxc/`) однозначно показывает тип объекта."
related_files:
  - "PROXMOX-VM-CLONE-2001-2026-001"
  - "PROXMOX-LXC-DEBIAN12-TEMPLATE-2026-001"
schema_version: "1.0"
---

# Создание шаблона Windows Server 2022

## Что настраивается и зачем
Мастер-шаблон Windows Server 2022 с преднастроенными VirtIO-драйверами,
QEMU Guest Agent, UEFI+TPM — чтобы дальше клонировать без повторной
установки ОС и драйверов под каждую роль (AD, терминальный сервер, 1С).

## Предварительные условия
- [ ] ISO Windows Server 2022 и `virtio-win.iso` загружены в хранилище Proxmox.
- [ ] ВМ будет на Ceph RBD (`ceph-fast`) — для live migration и HA.

## Шаги

**1. Создать базовую ВМ (обязательные параметры):**
```bash
qm create 100 --name "ws2022-template" --memory 4096 --cores 4 --cpu host \
  --machine q35 --bios ovmf --ostype win11 \
  --scsihw virtio-scsi-single \
  --scsi0 ceph-fast:100,iothread=1,discard=on,ssd=1 \
  --ide2 local:iso/windows-server-2022.iso,media=cdrom \
  --ide3 local:iso/virtio-win.iso,media=cdrom \
  --net0 virtio,bridge=vmbr0 \
  --boot order=ide2 \
  --tpmstate0 ceph-fast:version=v2.0
```
Обязательно именно так: `machine=q35` (не `i440fx`), `bios=ovmf` (UEFI),
`scsihw=virtio-scsi-single` (не IDE/SATA), сеть — `virtio` (не E1000/Realtek).
Виртуальный TPM обязателен для Windows Server 2022 — без него установка не пройдёт.

**2. Установить Windows**, на этапе выбора диска подключить драйвер VirtIO SCSI
с примонтированного `virtio-win.iso` (иначе установщик не увидит диск).

**3. После установки — драйверы и Guest Agent:**
Установить остальные VirtIO-драйверы (сеть, balloon, qxldod) из того же ISO,
затем:
```bash
qm set 100 --agent enabled=1,fstrim_cloned_disks=1
```
Внутри гостя убедиться, что служба `QEMU Guest Agent` запущена.

**4. Включить RDP** (известная проблема: по умолчанию выключен):
```powershell
Set-ItemProperty -Path 'HKLM:\System\CurrentControlSet\Control\Terminal Server' -Name "fDenyTSConnections" -Value 0
Enable-NetFirewallRule -DisplayGroup "Remote Desktop"
```
Диагностика, если не помогло: `ipconfig` (реальный IP или APIPA
169.254.x.x — DHCP не сработал), `Get-NetFirewallRule -DisplayGroup
"Remote Desktop"`.

## Sysprep — обязателен перед шаблонированием, две частые ошибки

**Запуск (не PowerShell-командлет, а исполняемый файл):**
```powershell
& 'C:\Windows\System32\Sysprep\sysprep.exe'
```

**Правильные настройки в открывшемся окне System Preparation Tool:**

| Параметр | Значение | Почему |
|---|---|---|
| Действие по очистке системы | Переход в OOBE | Штатно |
| **Подготовка к использованию (Generalize)** | **☑ обязательно включить** | Без неё SID не обобщается — клоны конфликтуют в домене |
| **Параметры завершения работы** | **Завершение работы** (не «Перезагрузка») | Перезагрузка запускает OOBE и портит шаблон |

## Конвертация в шаблон и клонирование — известная проблема linked clone

```bash
qm stop 100
qm template 100
qm clone 100 <новый_id> --name "<имя>" --full 1
```
⚠️ **`--full 1` обязателен.** Без него Proxmox создаёт **linked clone**
(связанный клон) — он зависит от диска исходного шаблона, и исходный
шаблон **нельзя будет удалить**:
```
base volume 'ceph-fast:base-100-disk-1' is still in use by linked cloned
```
**Если это уже произошло** (как в этой сессии — первая попытка клона 2000
оказалась связанной):
```bash
qm destroy 2000 --destroy-unreferenced-disks --purge   # удалить связанный клон
qm clone 100 2000 --name win2022-template --full 1      # пересоздать как full clone
qm shutdown 2000
qm template 2000
qm destroy 100 --destroy-unreferenced-disks --purge     # теперь исходник можно удалить
```
Проверка типа клона перед удалением исходника:
```bash
qm config <id> | grep -E "(template|clone)"
```
`template: 1` в выводе — это шаблон, не обычная ВМ (шаблоны нельзя
запускать, только клонировать — разные иконки в GUI это и означают,
это нормальное поведение, не ошибка).

## Проверка результата — итоговое состояние шаблона (VMID 2000, `win2022-template`)
- [x] CPU: 4 ядра, тип Default (x86-64-v2-AES: aes/md-clear/pdpe1gb/spec-ctrl/ssbd).
- [x] RAM: 4096 MiB, ballooning включен, KSM разрешён.
- [x] Диск: VirtIO SCSI single, `ceph-fast`, raw, discard=on, ssd=1, **100 ГБ** (уточнено по документу клонирования; при клонировании под конкретную роль размер увеличивается отдельно командой `qm resize`, см. «Клонирование шаблона ВМ 2001»).
- [x] Сеть: VirtIO, `vmbr0`.
- [x] UEFI (OVMF) + TPM 2.0, QEMU Guest Agent включен, RDP включен, драйверы VirtIO установлены.
- [x] Sysprep выполнен с Generalize, машина выключена — готова к клонированию без конфликта SID.
- [x] Исходный промежуточный шаблон (VMID 100) удалён после перехода на full-clone-шаблон 2000.

## ⛔ Don't repeat
См. `dont_repeat` во фронтматтере — шесть пунктов, все подтверждены реальными ошибками в этой сессии, не гипотетические.

## Побочная находка (не по теме этого документа)
В этой же сессии была предпринята попытка переименовать объект с ID 1000
(`qm set 1000 --name ...`) — команда упала с «Configuration file... does
not exist», так как объект **1000 — это LXC-контейнер** (`debian12-pattern`
из `PROXMOX-LXC-DEBIAN12-TEMPLATE-2026-001`), а не KVM-ВМ; управляется
через `pct set 1000 --name ...`, а не `qm set`. Результат самой команды
`pct set` в этой сессии не был подтверждён (диалог перешёл в новый чат) —
не считать переименование выполненным без отдельного подтверждения.

## Связанные документы
- «Клонирование шаблона ВМ 2001 (win-1c-app-01)» — клонирование из этого шаблона под конкретную роль (1С)
- «Создание шаблона Debian 12 LXC и клонирование» — контекст по объекту ID 1000

---
*Примечание при миграции (2026-09-11): убрана рамка USER/ASSISTANT и
пошаговая нумерация чата, содержание объединено в единый setup-документ
с готовым итоговым состоянием. Ничего не изменено по сути — включая обе
реальные ошибки (linked clone, sysprep.exe) и их фактические решения.*
