---
document_id: "PROXMOX-VM-MEMORY-BALLOON-2026-001"
title: "Некорректное отображение расхода RAM в Proxmox при использовании QEMU Guest Agent"
document_type: "troubleshooting"
status: "completed"
priority: "medium"
date_created: 2026-09-02
date_modified: 2026-09-07
next_review: 2026-12-01
author: "cladkyimaffin-hue"
category: "06_Troubleshooting"
tags:
  - "ProxmoxVE"
  - "QEMUGuestAgent"
  - "VirtIO"
  - "BalloonService"
  - "WindowsServer2025"
  - "Diagnostics"
ai_summary: "На VM 2002 (Windows Server 2025, узел pve01) Proxmox показывал Memory usage 108.92% (4.36 из 4.00 GiB), хотя внутри Windows реально использовалось 61.84%. Причина: QEMU Guest Agent был установлен, но не запущена служба BalloonService (VirtIO Balloon), передающая реальную статистику памяти — без неё Proxmox показывает потребление процесса QEMU на хосте, а не память гостя. После запуска BalloonService с верным путём D:\\Balloon\\2k25\\amd64\\blnsvr.exe показатель исправился до 63.70%."
dont_repeat:
  - "Не считать Host memory usage в Proxmox фактическим использованием памяти внутри Windows — это разные метрики."
  - "Не считать, что установленный и отвечающий QEMU Guest Agent сам по себе достаточен для корректной метрики памяти — нужна ещё и служба BalloonService."
  - "Не создавать BalloonService с обобщённым путём вроде D:\\balloon\\blnsvr.exe — путь версиозависим (например, D:\\Balloon\\2k25\\amd64\\ для Windows Server 2025 x64), сначала найти файл через Get-ChildItem."
  - "Не использовать команду `qm guest info` на версиях Proxmox, где она отсутствует (использовать `qm guest cmd ... get-osinfo`)."
related_files:
  - "TBD: Клонирование шаблона ВМ 2001 (win-1c-app-01).md — тот же тип конфигурации Windows Server, ещё не мигрирован"
schema_version: "1.0"
---

# Некорректное отображение расхода RAM в Proxmox при использовании QEMU Guest Agent

## 1. Симптомы
- На VM 2002 (имя `AD`, Windows Server 2025 Datacenter Evaluation, узел `pve01`) Proxmox показывал **Memory usage: 4.36 GiB из 4.00 GiB — 108.92%** (больше 100%).
- Внутри самой Windows фактически использовалось **2.43 GB из 3.93 GB — 61.84%**.
- QEMU Guest Agent изначально отсутствовал; после установки и подтверждения работы (`qm guest cmd 2002 ping`/`get-osinfo`) показатель Memory usage **не изменился**.
- Служба `BalloonService` отсутствовала; первая попытка создать её с путём `D:\balloon\blnsvr.exe` завершилась ошибкой запуска.

## 2. Отвергнутые гипотезы

| Гипотеза | Статус | Комментарий |
|---|---|---|
| Отсутствие QEMU Guest Agent — единственная причина | ❌ Отклонена | После установки и подтверждённой связи агента показатель не изменился |
| Реальная утечка памяти в Windows | ❌ Отклонена | Внутренние метрики Windows (`Get-CimInstance Win32_OperatingSystem`) показали нормальные 61.84% |
| **Отсутствующая/неверно настроенная служба BalloonService** | ✅ Подтверждена | См. диагностику |

## 3. Диагностика

```powershell
# Проверить QEMU Guest Agent внутри Windows
Get-Service -Name QEMU-GA
# → изначально: NoServiceFoundForGivenName

# Проверить VirtIO Balloon Driver
Get-PnpDevice | Where-Object {$_.Class -eq "System" -or $_.FriendlyName -like "*Balloon*"} | Format-Table Status, Class, FriendlyName, DeviceID
# → драйвер присутствовал, статус OK (то есть проблема не в драйвере)

# Реальное использование RAM внутри гостя
Get-CimInstance Win32_OperatingSystem | Select-Object TotalVisibleMemorySize, FreePhysicalMemory | ForEach-Object {
  [PSCustomObject]@{
    'Total RAM (GB)' = [math]::Round($_.TotalVisibleMemorySize / 1MB, 2)
    'Used RAM (GB)'  = [math]::Round(($_.TotalVisibleMemorySize - $_.FreePhysicalMemory) / 1MB, 2)
    'Usage %'        = [math]::Round(($_.TotalVisibleMemorySize - $_.FreePhysicalMemory) / $_.TotalVisibleMemorySize * 100, 2)
  }
}
# → Total 3.93 GB, Used 2.43 GB, 61.84%
```
```bash
# На узле Proxmox — конфигурация ВМ
qm config 2002
# → agent: 1; memory: 4096; ide0: local:iso/virtio-win.iso (agent включён в конфиге, но служба внутри гостя отсутствовала)
```
```powershell
# Найти диск с ISO virtio-win и установить агента
Get-WmiObject Win32_CDROMDrive | Select-Object Drive, VolumeName
# → D: virtio-win-0.1.302
Start-Process msiexec.exe -ArgumentList '/i D:\guest-agent\qemu-ga-x86_64.msi /qn /norestart' -Wait
```
```bash
# Подтвердить канал связи агента
qm guest cmd 2002 get-osinfo
# → JSON с данными Windows Server 2025 — канал работает
```
```powershell
# Проверить BalloonService — отсутствует
Get-Service -Name "*balloon*"
# → пусто

# Первая попытка — неверный путь
sc.exe create BalloonService binPath= "D:\balloon\blnsvr.exe" start= auto
Start-Service -Name BalloonService
# → служба создана, но запуск завершился ошибкой (файл по этому пути отсутствует)

# Найти реальный путь для этой версии/архитектуры Windows
Get-ChildItem -Path D:\ -Recurse -Filter 'blnsvr.exe' -ErrorAction SilentlyContinue | Select-Object FullName
# → D:\Balloon\2k25\amd64\blnsvr.exe

# Пересоздать службу с верным путём
sc.exe delete BalloonService
sc.exe create BalloonService binPath= "D:\Balloon\2k25\amd64\blnsvr.exe" start= auto
Start-Service -Name BalloonService
# → Running
```

## 4. Корневая причина
QEMU Guest Agent был установлен и подтверждённо работал (канал связи через
`qm guest cmd` активен), но без запущенной службы **BalloonService**
(реализация VirtIO Balloon Driver в пространстве пользователя) реальная
статистика памяти гостя в Proxmox не передаётся — интерфейс вместо этого
показывает потребление процесса QEMU на хосте вместе с накладными
расходами виртуализации, что и даёт значение выше 100%. Дополнительная
причина неудачного первого запуска — путь к `blnsvr.exe` версиозависим
(разный для разных версий/архитектур Windows), а использованный путь
`D:\balloon\blnsvr.exe` не существовал на этом ISO.

## 5. Решение
1. Установить и подтвердить работу QEMU Guest Agent (`qm guest cmd <vmid> get-osinfo` возвращает данные).
2. Найти точный путь `blnsvr.exe` для конкретной версии/архитектуры Windows на смонтированном ISO virtio-win — не полагаться на путь из документации для другой версии.
3. Создать службу `BalloonService` с найденным путём, `start= auto`, запустить.
4. Убедиться, что Proxmox начал отображать значение, близкое к фактическому использованию внутри гостя.

**Результат:** Memory usage в Proxmox изменился с `4.36 GiB / 108.92%` на `2.55 GiB / 63.70%` — близко к фактическим `61.84%` внутри Windows.

## 6. ⛔ Don't repeat
- Не путать Host memory usage (метрика процесса QEMU на хосте) с реальным использованием памяти внутри гостя.
- Работающий QEMU Guest Agent не гарантирует корректность метрики памяти — отдельно нужен BalloonService.
- Не использовать обобщённый путь к `blnsvr.exe` — версиозависим, сначала искать `Get-ChildItem -Recurse`.
- Не использовать `qm guest info` на версиях Proxmox, где команда отсутствует — использовать `qm guest cmd <vmid> get-osinfo`.

## 7. Проверка результата
- [x] `Get-Service -Name QEMU-GA` → `Running`
- [x] `qm guest cmd 2002 get-osinfo` возвращает данные
- [x] `Get-Service -Name BalloonService` → `Running`, путь `D:\Balloon\2k25\amd64\blnsvr.exe`
- [x] Memory usage в Proxmox близок к фактическому использованию внутри Windows, не превышает 100%

## Открытые вопросы (перенесены из исходника, не решены)
- Сохраняется ли корректный показатель после перезагрузки ВМ?
- Какой результат аналогичной настройки на VM 2001?
- Нужно ли оставлять ISO virtio-win подключённым после установки компонентов?

## Связанные документы
- «Клонирование шаблона ВМ 2001 (win-1c-app-01).md» — та же категория конфигурации Windows Server на этой инфраструктуре (ещё не мигрирован)

---
*Примечание при миграции (2026-09-11): исходный `document_id` (`DOC-2026-09-02-001`,
не описательный и не по формату `SCHEMA.md`) заменён на
`PROXMOX-VM-MEMORY-BALLOON-2026-001`; конфликта с другими ID не было —
исходный был уникален. 266-строчный фронтматтер сжат до ядра `SCHEMA.md`
v1.0, содержательные поля (симптомы, гипотезы, диагностика, причина,
решение, don't repeat, открытые вопросы) перенесены в тело по шаблону
`troubleshooting`. Содержание не изменено и не дополнено.*
