---
document_id: "PROXMOX-CEPH-NIC0-DIRECT-LINK-2026-001"
title: "Миграция Ceph на прямой оптический канал nic0 и восстановление после сбоя"
document_type: "troubleshooting"
status: "in_progress"
priority: "high"
date_created: 2026-09-30
date_modified: 2026-09-30
next_review: 2026-10-30
author: "cladkyimaffin-hue"
category: "04_Storage_Ceph"
tags: [ProxmoxVE, Ceph, Networking, nic0, MTU, 10GbE, OSD, Configuration, Corosync, pve01, pve02, Troubleshooting]
ai_summary: "Успешная миграция кластерного трафика Ceph на прямой оптический канал 10GbE (nic0). Инцидент с падением OSD (start-limit-hit) был вызван некорректными жесткими привязками IP в /etc/ceph/ceph.conf, которые переопределяли настройки монитора. Проблема решена очисткой локального конфига и явным указанием корректных подсетей."
dont_repeat:
  - "Не комментировать параметры network в /etc/ceph/ceph.conf без их замены на корректные значения подсетей, иначе OSD будут использовать fallback на public interface или падать."
related_files:
  - "NETWORK-BOND0-CEPH-ACTIVEBACKUP-2026-001"
  - "PROXMOX-CEPH-OSD-POOLS-DEPLOYMENT-2026-001"
  - "PROXMOX-CEPH-BOND0-LATENCY-INVESTIGATION-2026-001"
schema_version: "1.0"
---

# Миграция Ceph на прямой оптический канал nic0 и восстановление после сбоя

## 1. Контекст и цель
- **Окружение:** Proxmox VE 9.2.11 (Debian 13), узлы `pve01`, `pve02`, кластер Ceph (4 OSD, 65 PG).
- **Цель:** перевести кластерный трафик Ceph (`cluster_network`) с резервного канала `bond0` (nic4/nic5, `10.10.10.0/24`) на прямой оптический канал `nic0` (`10.10.11.0/24`, point-to-point между узлами, без коммутатора).
- **Требование:** Jumbo Frames (MTU 9000).
- Метки достоверности в тексте: VERIFIED — подтверждено выводом команд; INFERRED — вывод, напрямую не подтверждён; UNKNOWN — данных нет.

## 2. Хронология (30.09.2026)
1. **Подготовка.** В `/etc/network/interfaces` обоих узлов добавлен `iface nic0 inet static` (`pve01` — `10.10.11.1/24`, `pve02` — `10.10.11.2/24`), выполнен `ifup nic0`. Вначале `nic0` был в состоянии `NO-CARRIER`; после подключения оптики `Link detected: yes` на обоих узлах, `ping` между адресами проходит. MTU интерфейса — 1500.
2. **Настройка Ceph.** До изменения в мониторе стояло `cluster_network = 10.10.10.0/24,10.10.11.0/24`. Выполнено `ceph config set mon cluster_network 10.10.11.0/24`. Кластер оставался `HEALTH_OK`.
3. **Проверка Jumbo Frames.** `ip link set nic0 mtu 9000` на обоих узлах, затем `ping -M do -s 8972 -c 3 10.10.11.2` — без потерь, около 0,07–0,08 мс (VERIFIED).
4. **Отключение резервного канала.** Кабель `bond0` извлечён. Corosync остался стабилен: кольцо `ring0` идёт через `vmbr0` (`192.168.202.0/22`).
5. **Инцидент.** `HEALTH_WARN` → `HEALTH_ERR`, все PG в `peering`. По `ss -tulnp` OSD продолжали слушать старые адреса `10.10.10.x`. Оркестратор недоступен (`ceph orch` → `No orchestrator configured`), перезапуск OSD выполняется через systemd. OSD на `pve01` перешли в `failed` со статусом `start-limit-hit`.
6. **Диагностика `/etc/ceph/ceph.conf`** (одинаково на обоих узлах): в `[global]` — `cluster_network = 10.10.10.1/24` и `public_network = 192.168.202.121/22` (адрес узла с маской вместо подсети); в секциях `[mon.pve01]` и `[mon.pve02]` — по одной строке `public_addr` (`192.168.202.121` и `192.168.202.179`). Локальный файл имеет приоритет над `ceph config` монитора при старте демонов OSD.
7. **Первая попытка исправления.** Строки `cluster_network`, `public_network` и `public_addr` закомментированы. Результат: OSD не смогли определить сети автоматически; на `pve01` они привязались только к public-адресу (`192.168.202.121`), инцидент продолжился (вторая причина сбоя).
8. **Исправление.** В `[global]` явно заданы `cluster_network = 10.10.11.0/24` и `public_network = 192.168.200.0/22` на обоих узлах; `public_addr` в секциях `[mon.*]` оставлены закомментированными. Выполнены `systemctl reset-failed ceph-osd@N` и `systemctl restart ceph-osd.target`.
9. **Результат.** `HEALTH_OK`, 4 OSD `up/in`, 65 PG `active+clean`; OSD слушают адреса `10.10.11.x` (`ss -tlnp | grep ceph-osd`) (VERIFIED).

## 3. Отвергнутые гипотезы
- Достаточно `ceph config set mon cluster_network ...` без правки локального файла — отвергнуто: `ceph.conf` переопределил значение монитора.
- Достаточно закомментировать сетевые параметры в `ceph.conf` — отвергнуто: OSD не определяют сети автоматически и привязываются к public-адресу.
- Причина только в MTU — отвергнуто: MTU 1500 на `nic0` был дополнительным фактором, но после его исправления OSD продолжали слушать `10.10.10.x`.

## 4. Корневая причина
Локальный `/etc/ceph/ceph.conf` содержал устаревшие и некорректно записанные значения (`cluster_network = 10.10.10.1/24`, `public_network = 192.168.202.121/22`). Они имели приоритет над настройками монитора и привязывали OSD к отключённому `bond0`. Первая попытка исправления (закомментировать параметры) создала вторую проблему: без явных значений OSD не привязывались к `nic0`.
Происхождение этих значений в `ceph.conf` — UNKNOWN.

## 5. Факты окружения (на 2026-09-30)
- **VERIFIED:** `nic0` на обоих узлах, `pve01` = `10.10.11.1/24`, `pve02` = `10.10.11.2/24`; `cluster_network = 10.10.11.0/24`, `public_network = 192.168.200.0/22` (в `[global]` `ceph.conf` и в мониторе); `bond0` (nic4/nic5) физически отключён и Ceph не используется.
- **VERIFIED:** MTU 9000 выставлен на работающем интерфейсе `nic0` (команда `ip link set`), Jumbo-пинг проходит.
- **VERIFIED (вывод `grep -A4 "iface nic0" /etc/network/interfaces`, оба узла):** строки `mtu 9000` в файле нет; для `nic0` присутствуют два определения — прежнее `iface nic0 inet manual` и добавленное `iface nic0 inet static` с адресом.
- **INFERRED:** после перезагрузки узла `nic0` вернётся к MTU 1500, и сценарий инцидента (несовпадение MTU на кластерной сети Ceph) может повториться. Перезагрузкой не проверялось.

## 6. Открытые вопросы
1. **Сохранение MTU.** Добавить `mtu 9000` в блок `iface nic0 inet static` на обоих узлах; решить судьбу дублирующего `iface nic0 inet manual`. Изменение не выполнено.
2. **Очистка старых записей в `monmap`** — задача поставлена администратором, не выполнена.
3. **`osd_crush_chooseleaf_type` для кластера из двух узлов** — задача поставлена администратором, не выполнена.
4. **`public_addr` в `[mon.pve01]` и `[mon.pve02]`** оставлены закомментированными (автоопределение); решение о возврате не принималось.
5. **Связанное расследование** `PROXMOX-CEPH-BOND0-LATENCY-INVESTIGATION-2026-001` остаётся `in_progress`: задержки записи после перехода на `nic0` не измерялись. Решение по записи — за администратором.

## 7. ⛔ Don't repeat
- Не комментировать `cluster_network` / `public_network` в `/etc/ceph/ceph.conf` без замены корректными значениями подсетей: OSD теряют привязку к нужной сети.
- Значения `cluster_network` и `public_network` указывать подсетью (`10.10.11.0/24`, `192.168.200.0/22`), а не адресом узла с маской.
- Перед отключением резервного канала проверять `ss -tulnp | grep ceph-osd`: OSD должны слушать адреса нового интерфейса.
- Менять MTU на обоих концах point-to-point канала до перезапуска сервисов Ceph и сохранять значение в `/etc/network/interfaces`.
- Для перезапуска OSD использовать `systemctl` (`ceph orch` в этом кластере не настроен); после `start-limit-hit` сначала `systemctl reset-failed ceph-osd@N`.

## 8. Проверка результата
- [x] `ceph -s` → `HEALTH_OK`, 4 OSD `up/in`, 65 PG `active+clean`.
- [x] `ss -tlnp | grep ceph-osd` → адреса `10.10.11.x`.
- [x] `ping -M do -s 8972 -c 3 10.10.11.2` → без потерь.
- [ ] `grep -A4 "iface nic0" /etc/network/interfaces` → есть `mtu 9000` (на 2026-09-30 отсутствует).

## 9. Связанные документы
- `NETWORK-BOND0-CEPH-ACTIVEBACKUP-2026-001` — прежняя кластерная сеть Ceph (`bond0`).
- `PROXMOX-CEPH-OSD-POOLS-DEPLOYMENT-2026-001` — развёртывание OSD и пулов.
- `PROXMOX-CEPH-BOND0-LATENCY-INVESTIGATION-2026-001` — расследование задержек записи.
