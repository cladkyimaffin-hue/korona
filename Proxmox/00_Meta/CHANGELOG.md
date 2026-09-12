---
schema_version: "1.0"
status: "active"
maintainer: "cladkyimaffin-hue"
---

# 📜 CHANGELOG.md — журнал изменений конвейера и служебных файлов

Формат записи: `ГГГГ-ММ-ДД | тип | что сделано | кем/чем`.
Типы: `bootstrap`, `schema-change`, `tag-add`, `migrate`, `new-doc`, `conflict-resolved`.

Этот файл — не место для истории содержимого документов (для этого есть
`date_modified` в самих документах и `superseded_by` при архивации). Здесь —
только события уровня самого конвейера и служебных файлов.

---

- 2026-09-11 | bootstrap | Создан каркас `00_Meta/` (`SCHEMA.md` v1.0, `TAGS.md`, `registry.csv` с заголовками, `CONFLICTS.md`, `TEMPLATES/`), папки категорий `01_Hardware`...`99_Archive`, `00_Inbox/`. Основание: анализ существующего архива из 28 файлов выявил дубли `document_id` (4 файла с одним ID), 19 файлов без `document_id`, 3 несовместимых схемы фронтматтера, разнобой написания тегов | Claude (по запросу cladkyimaffin-hue)
- 2026-09-11 | schema-change | В `AI-INSTRUCTIONS.md` добавлен раздел 8а «Протокол конвейера» (7 шагов обработки документов) и запись в раздел 9 (внутренний журнал файла) | Claude (по запросу cladkyimaffin-hue)
- 2026-09-11 | schema-change | В `AI-README.md` раздел 3 «Структура репозитория» заменён с построчного перечня файлов (устаревал при каждом переносе; содержал битую ссылку на несуществующий файл и оборванный текст) на таблицу из 10 категорийных папок; точный список документов вынесен в `00_Meta/registry.csv` / `INDEX.md` | Claude (по запросу cladkyimaffin-hue)
- 2026-09-11 | migrate | Перенесён «Поменять имя устройства на pve01.md» → `02_Installation/Смена hostname узла Proxmox VE.md`, ID `PROXMOX-NODE-RENAME-2026-001`. Обнаружено: исходный файл — сырая переписка `### USER/### ASSISTANT`, обрывавшаяся на невыполненном запросе; в новую версию перенесён только фактически данный ответ, обрыв зафиксирован как примечание, не восстановлен. Обнаружена и учтена нерешённая ссылка на немигрированный документ (скрипт pstInstal) — оставлена как TBD | Claude (по запросу cladkyimaffin-hue)
- 2026-09-11 | migrate | Перенесён «Полная комплектация сервера, идентификация сетевых карт...md» → `01_Hardware/Комплектация и маппинг портов Huawei 2288H V5.md`, ID `HARDWARE-HUAWEI-2288H-PORTMAP-2026-001`. Убрана нумерация реплик «Полный чат», содержание не изменено. Найдена связь с ещё не мигрированным `hardware-spec.md`: этот документ уже содержит CPU/RAM, отмеченные там как неподтверждённые — не конфликт, а материал для заполнения при будущей миграции hardware-spec.md | Claude (по запросу cladkyimaffin-hue)
- 2026-09-11 | migrate | Перенесён «web меню.md» → `03_Network/Справочник меню Datacenter Proxmox VE.md`, ID `PROXMOX-WEBGUI-DATACENTER-2026-001`. Плейсхолдеры узлов pve1/pve2 заменены на подтверждённые pve01/pve02 | Claude (по запросу cladkyimaffin-hue)
- 2026-09-11 | conflict-resolved | Разрешён конфликт «bond0: план LACP vs факт active-backup» — см. CONFLICTS.md, архив решённых. Администратор подтвердил: active-backup — источник истины | cladkyimaffin-hue (подтверждено), зафиксировано Claude
- 2026-09-11 | migrate | «Настройка сети bond0.md» разделён на 2 документа: `06_Troubleshooting/Диагностика SFP-модулей Intel X710.md` (ID NETWORK-SFP-OPTICAL-MISMATCH-2026-001) и `03_Network/Настройка bond0 active-backup для сети Ceph.md` (ID NETWORK-BOND0-CEPH-ACTIVEBACKUP-2026-001). Причина разделения: исходный файл смешивал диагностику физической проблемы (SFP-модули) и итоговую сетевую конфигурацию (bond0) — по смыслу это два разных документа | Claude (по запросу cladkyimaffin-hue)
- 2026-09-11 | migrate | Пачка 2 (SSH и диагностика) завершена, 3 документа перенесены в `06_Troubleshooting`: (1) «Проблемы с доступом по SSH на Debian.md» → `Диагностика SSH-доступа к Debian.md`, ID `LINUX-SSH-DEBIAN-ACCESS-2026-001`; (2) «Зависание ssh...pam_systemd.so.md» → `Задержка SSH в LXC pam_systemd.md`, ID сохранён `LINUX-SSH-PAM-SYSTEMD-ZABBIX-2026-001` (уже был качественным и уникальным); (3) «Proxmox не правильно отображали расход RAM...md» → `Некорректный расход RAM QEMU Guest Agent.md`, ID заменён с неинформативного `DOC-2026-09-02-001` на `PROXMOX-VM-MEMORY-BALLOON-2026-001`. Во всех трёх — сжатие объёмного фронтматтера (до 266 строк) в ядро SCHEMA.md v1.0, содержание перенесено в тело по шаблону troubleshooting без изменений по сути | Claude (по запросу cladkyimaffin-hue)
