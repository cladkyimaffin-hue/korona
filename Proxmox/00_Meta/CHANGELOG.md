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
