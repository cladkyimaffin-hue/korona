---
document_id: "PROXMOX-AD-THIRD-DC-PROMOTION-2026-001"
title: "Добавление третьего контроллера домена (WIN-AD, ВМ 2002) в домен krnn.ru — НЕ ЗАВЕРШЕНО"
document_type: "runbook"
status: "in_progress"
priority: "high"
date_created: 2026-09-07
date_modified: 2026-09-07
next_review: 2026-09-14
author: "cladkyimaffin-hue"
category: "05_VirtualMachines"
tags:
  - "ActiveDirectory"
  - "AD-DS"
  - "WindowsServer2022"
  - "WindowsServer2025"
  - "krnn.ru"
  - "ProxmoxVE"
  - "Replication"
  - "DNS"
  - "Troubleshooting"
ai_summary: "Попытка повышения ВМ 2002 (WIN-AD, клон шаблона 2000) до третьего контроллера домена krnn.ru (существующие DC: ANDQ 192.168.200.10, DC 192.168.200.2). Сервер введён в домен, роль AD-Domain-Services установлена. Первый запуск Install-ADDSDomainController был случайно прерван (Ctrl+C/Ctrl+Z во время длительного выполнения) и дал ошибку 8200/Event 2542 «база данных была заменена». После перезагрузки и подтверждения отсутствия артефактов (ntds.dit, DSA Database Epoch) подготовлена чистая повторная попытка — но её результат в этом документе НЕ ПОДТВЕРЖДЁН, задача осталась незавершённой на моменте передачи в новый чат."
dont_repeat:
  - "НИКОГДА не нажимать Ctrl+C/Ctrl+Z во время выполнения Install-ADDSDomainController, даже если окно PowerShell выглядит зависшим — процесс может законно идти 5-15 минут без видимого вывода."
  - "Не повторять Install-ADDSDomainController сразу после прерванной попытки — сначала проверить и удалить артефакты (C:\\Windows\\NTDS\\ntds.dit, параметр реестра DSA Database Epoch в HKLM:\\System\\CurrentControlSet\\Services\\NTDS\\Parameters), иначе повтор гарантированно даст ошибку 8200/Event 2542."
  - "Не использовать 192.168.200.1 как единственный DNS перед повышением до контроллера домена."
  - "Не считать член домена (member server) третьим контроллером до успешного повышения, подтверждённого repadmin и Get-ADDomainController."
  - "Не переносить роли FSMO на новый DC без отдельного согласованного плана — не входит в эту задачу."
related_files:
  - "PROXMOX-WINSRV2022-TEMPLATE-2026-001"
schema_version: "1.0"
---

# ⚠️ Добавление третьего контроллера домена — НЕ ЗАВЕРШЕНО

**Этот документ описывает незаконченную работу.** Финальная команда
повышения подготовлена и должна быть чистой (артефакты предыдущей ошибки
подтверждённо удалены), но её фактическое выполнение и результат в
исходной переписке не зафиксированы — диалог был передан в новый чат
на этом моменте, и продолжение в архиве репозитория пока не найдено.
**Перед использованием этого документа — сначала проверить текущее
состояние `WIN-AD` (`Get-ADDomainController -Filter *`), возможно, с тех
пор задача уже была доведена до конца в другой сессии.**

## Цель
Повысить ВМ 2002 (`WIN-AD`, Windows Server 2022, полный клон шаблона 2000)
до третьего писабельного контроллера домена `krnn.ru` с Global Catalog,
рядом с уже существующими `ANDQ` (192.168.200.10) и `DC` (192.168.200.2,
оба Windows Server 2025).

## Параметры целевой ВМ
| Параметр | Значение |
|---|---|
| VMID / имя в Proxmox | 2002 / `win-ad-ds-01` |
| Узел | pve01 |
| Имя хоста Windows | `WIN-AD` |
| Ресурсы | 2 vCPU, 4096 MiB RAM, диск 100 ГБ |
| IP / маска / шлюз | `192.168.200.225` / `255.255.252.0` (/22) / `192.168.200.1` |
| DNS | `192.168.200.2` (DC), `192.168.200.10` (ANDQ) |

## Шаги, выполненные и подтверждённые
1. `qm clone 2000 2002 --name win-ad-ds-01 --full --storage ceph-fast`, `qm set 2002 --cores 2`, отключены установочные ISO.
2. Сеть настроена, `ping` до обоих существующих DC — 0% потерь, `nslookup krnn.ru` резолвит оба DC.
3. Доступ по FQDN к `\\ANDQ.krnn.ru\C$` и `\\ANDQ.krnn.ru\SYSVOL` под доменным администратором — подтверждён.
4. `Rename-Computer -NewName "WIN-AD" -Restart`, `Add-Computer -DomainName "krnn.ru" ... -Restart` — сервер в домене как member server.
5. `Install-WindowsFeature AD-Domain-Services -IncludeManagementTools` — роль установлена (`Success`).

## ⚠️ Известная проблема: прерванная установка → ошибка 8200 / Event 2542

**Что произошло:** во время выполнения `Install-ADDSDomainController`
(процесс закономерно «завис» на 5-15 минут без вывода) администратор
случайно нажал `Ctrl+C`/`Ctrl+Z`, вызвав запрос подтверждения отмены, и
ответил `Y` — установка прервалась.

**Симптом:** `Get-Service NTDS` → «Не удается найти службу» (роль не
активирована, хотя пакет установлен).

**При повторном запуске без очистки** — ошибка:
```
Install-ADDSDomainController : Сбой операции...
EVENTLOG (Error): NTDS Database / Архивация данных : 2542
Сервер службы каталогов обнаружил, что база данных была заменена.
```
Код **8200**. Причина — рассинхронизация параметра `DSA Database Epoch`
в реестре с состоянием файла базы `ntds.dit` от прерванной попытки.

**Диагностика и очистка (выполнено и подтверждено):**
```powershell
Test-Path C:\Windows\NTDS\ntds.dit                                                          # → False
Get-ChildItem C:\Windows\NTDS -Force -ErrorAction SilentlyContinue                            # → пусто
Get-ItemProperty 'HKLM:\System\CurrentControlSet\Services\NTDS\Parameters' `
  -Name 'DSA Database Epoch' -ErrorAction SilentlyContinue                                    # → пусто
```
Артефактов не найдено уже при первой проверке; дополнительно выполнена
`Restart-Computer -Force` для полного сброса блокировок/кэша, после чего
обе проверки повторены и подтверждены пустыми.

Также проверено: объект `WIN-AD` в контейнере `CN=Domain Controllers` в
AD отсутствует — конфликтующих остатков нет.

## 🚀 Единственный оставшийся и НЕ выполненный шаг

```powershell
Install-ADDSDomainController `
  -DomainName "krnn.ru" `
  -Credential (Get-Credential) `
  -SiteName "Default-First-Site-Name" `
  -InstallDns:$true `
  -NoGlobalCatalog:$false `
  -ReplicationSourceDC "ANDQ.krnn.ru" `
  -DatabasePath "C:\Windows\NTDS" `
  -LogPath "C:\Windows\NTDS" `
  -SysvolPath "C:\Windows\SYSVOL" `
  -SafeModeAdministratorPassword (Read-Host -AsSecureString "Введите пароль DSRM") `
  -Confirm:$false
```
⚠️ Не прерывать выполнение ни при каких признаках «зависания».

## Проверка результата (после выполнения — не выполнено на момент этого документа)
- [ ] `Get-ADDomainController -Filter *` — `WIN-AD` присутствует в списке.
- [ ] `Get-ADDomainController -Identity WIN-AD` — `IsGlobalCatalog: True`, `IsReadOnly: False`.
- [ ] `net share` на `WIN-AD` — присутствуют `SYSVOL` и `NETLOGON`.
- [ ] `repadmin /replsummary` — без ошибок.
- [ ] `repadmin /showrepl` — подтверждена входящая репликация.
- [ ] `nslookup -type=SRV _ldap._tcp.dc._msdcs.krnn.ru` — новый DC присутствует в SRV-записях.
- [ ] FSMO-роли остались на прежних владельцах (`netdom query fsmo`) — перенос не планировался в рамках этой задачи.

## ⛔ Don't repeat
См. `dont_repeat` во фронтматтере — главное: никогда не прерывать
`Install-ADDSDomainController` вручную, и не повторять её без
предварительной проверки артефактов после любого прерывания.

## Открытые вопросы (не решены на момент документа)
- Выполнена ли финальная команда повышения, и был ли результат успешным?
- Каковы результаты `repadmin /replsummary`/`dcdiag /v` на всех трёх DC после повышения (если оно состоялось)?
- Как называется AD Site новой ВМ?

## Связанные документы
- «Шаблон Windows Server 2022» — исходный шаблон (ID 2000), из которого клонирована ВМ 2002

---
*Примечание при миграции (2026-09-11): статус `in_progress` сохранён
осознанно и не заменён на `completed` — исходный файл заканчивается на
подготовленной, но не подтверждённо выполненной финальной команде, с
явной передачей контекста в новый чат. Огромный (266-строчный)
фронтматтер сжат до ядра `SCHEMA.md` v1.0, содержательные поля
(reasoning, ошибка 8200, дезинфекция артефактов, финальный протокол)
перенесены в тело. Если с момента создания исходного файла задача была
доведена до конца в другой, ещё не найденной в архиве сессии — этот
документ обновить по факту находки, не оставлять помеченным как
незавершённый навсегда.*
