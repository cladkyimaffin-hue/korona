---
# ============================================================
# 1. ИДЕНТИФИКАЦИЯ ДОКУМЕНТА
# ============================================================

document_id: "DOC-2026-08-30-001"
title: "Настройка Corosync QDevice для двухузлового кластера Proxmox VE"
slug: "nastroyka-corosync-qdevice-dlya-dvukhuzlovogo-klastera-proxmox"
document_type: "runbook"
language: "ru"
version: "1.0"
schema_version: "1.0"
status: "completed"
confidentiality: "internal"
priority: "critical"

date_created: 2026-08-30
date_modified: 2026-09-02
date_completed: ""
last_reviewed: ""
next_review: 2026-12-01
valid_until: 2027-01-01

author: "cladkyimaffin-hue"
maintainer: ""
reviewer: "cladkyimaffin-hue"
owner_team: ""
approval_status: "approved"

# ============================================================
# 2. КЛАССИФИКАЦИЯ И ПОИСК
# ============================================================

category: "setup"
domain: "virtualization"
subdomain: "cluster-quorum"

tags:
  - "ProxmoxVE"
  - "QDevice"
  - "Corosync"
  - "corosync-qnetd"
  - "corosync-qdevice"
  - "Quorum"
  - "HighAvailability"
  - "Debian"
  - "Ubuntu"

keywords:
  - "двухузловой кластер"
  - "кворум Proxmox"
  - "Corosync QDevice"
  - "corosync-qnetd"
  - "pvecm qdevice setup"
  - "отказоустойчивость"
  - "QNetd"

aliases:
  - "Настройка QDevice в Proxmox"
  - "Добавление QDevice в кластер Proxmox"
  - "Настройка внешнего свидетеля кворума"

related_topics:
  - "Corosync"
  - "votequorum"
  - "Proxmox HA"
  - "fencing"
  - "Ceph"
  - "SSH"
  - "NTP"
  - "сетевое разделение"

# ============================================================
# 3. КРАТКОЕ ОПИСАНИЕ
# ============================================================

problem: "Кластер Proxmox из двух узлов теряет кворум при отказе или сетевой изоляции одного узла, что может остановить управление кластером, HA и операции Ceph."

summary: "Инструкция описывает настройку внешнего Corosync QDevice для двухузлового кластера Proxmox VE. На отдельном Debian/Ubuntu-хосте устанавливается corosync-qnetd, а на обоих узлах Proxmox — corosync-qdevice. После выполнения pvecm qdevice setup кластер должен получить три ожидаемых голоса и кворум 2."

ai_summary: "Для двух узлов Proxmox требуется независимый третий хост QDevice, который предоставляет дополнительный голос кворума. На QDevice устанавливается corosync-qnetd, на узлах Proxmox — corosync-qdevice, после чего на одном узле выполняется pvecm qdevice setup <IP_QDEVICE>. Проверка выполняется через pvecm status; ожидаются Expected votes: 3, Quorum: 2 и флаг Qdevice."

business_impact: "QDevice повышает доступность управления двухузловым кластером при отказе одного узла, но сам по себе не обеспечивает fencing и полноценный автоматический перезапуск виртуальных машин."

technical_impact: "В кластер добавляется внешний голос Corosync; изменяются конфигурация Corosync, сертификаты QDevice и состояние служб corosync-qdevice на узлах."

user_impact: "Администратор может сохранить кворум на одном оставшемся узле при условии доступности независимого QDevice."

severity: "critical"
incident_status: "monitoring"

# ============================================================
# 4. СИСТЕМА И ОКРУЖЕНИЕ
# ============================================================

environment: "production"
system_role: "Двухузловой кластер Proxmox VE с внешним QDevice"
system_name: ""
hostname: ""
fqdn: ""
asset_id: ""
vm_id: ""
cluster: ""
node: ""

operating_system:
  name: "Debian/Ubuntu"
  version: ""
  edition: ""
  architecture: ""
  build: ""
  language: ""
  timezone: ""

platform:
  name: "Proxmox VE"
  version: ""
  node_version: ""
  kernel: ""
  hypervisor: "QEMU/KVM"
  machine_type: ""
  firmware: ""

network:
  ip_addresses:
    - ""
  mac_addresses:
    - ""
  vlan: ""
  subnet: ""
  gateway: ""
  dns_servers:
    - ""
  reverse_proxy: ""
  firewall_zone: ""

hardware:
  cpu_model: ""
  cpu_sockets: ""
  cpu_cores: ""
  cpu_threads: ""
  memory_allocated: ""
  memory_type: ""
  storage:
    - type: ""
      name: ""
      size: ""
      filesystem: ""
      mount_point: ""

# ============================================================
# 5. КОМПОНЕНТЫ И ВЕРСИИ
# ============================================================

components:
  - name: "Proxmox VE node 1"
    type: "software"
    version: ""
    status_before: "cluster_member"
    status_after: "cluster_member_with_qdevice"
    configuration: ""

  - name: "Proxmox VE node 2"
    type: "software"
    version: ""
    status_before: "cluster_member"
    status_after: "cluster_member_with_qdevice"
    configuration: ""

  - name: "corosync-qnetd"
    type: "service"
    version: ""
    status_before: "not_installed"
    status_after: "running"
    configuration: "Служба работает на независимом Debian/Ubuntu-хосте и принимает подключения на TCP-порту 5403."

  - name: "corosync-qdevice"
    type: "package"
    version: ""
    status_before: "not_installed"
    status_after: "configured"
    configuration: "Устанавливается на обоих узлах Proxmox."

dependencies:
  - name: "Debian/Ubuntu на отдельном QDevice-хосте"
    version: ""
    required: true
    purpose: "Запуск corosync-qnetd."

  - name: "SSH"
    version: ""
    required: true
    purpose: "Первоначальная настройка QDevice командой pvecm qdevice setup."

  - name: "NTP/chrony"
    version: ""
    required: true
    purpose: "Синхронизация времени между узлами и QDevice."

related_files:
  - "pve01+pve02+Qdevice.md"
  - "INDEX.md"

depends_on:
  - ""

supersedes: ""
superseded_by: ""

# ============================================================
# 6. ВРЕМЕННАЯ ШКАЛА
# ============================================================

timeline:
  detected_at: "2026-08-30"
  reported_at: ""
  investigation_started_at: ""
  mitigation_started_at: ""
  resolved_at: ""
  closed_at: ""

  events:
    - timestamp: "2026-08-30"
      event: "Зафиксирована необходимость добавить QDevice к двухузловому кластеру Proxmox."
      actor: "cladkyimaffin-hue"
      evidence: "Исходный Markdown-файл."

    - timestamp: ""
      event: "На независимом Linux-хосте установлен corosync-qnetd."
      actor: ""
      evidence: ""

    - timestamp: ""
      event: "На обоих узлах Proxmox установлен corosync-qdevice."
      actor: ""
      evidence: ""

    - timestamp: ""
      event: "QDevice подключён командой pvecm qdevice setup."
      actor: ""
      evidence: ""

    - timestamp: ""
      event: "Проверены состояние кворума, службы и отказоустойчивость."
      actor: ""
      evidence: ""

last_incident: 2026-08-30
incident_duration: ""
recurrence_count: 0
recurrence_pattern: ""

# ============================================================
# 7. СИМПТОМЫ И ФАКТИЧЕСКИЕ НАБЛЮДЕНИЯ
# ============================================================

symptoms:
  - "Двухузловой кластер теряет кворум при отказе одного узла."
  - "Сетевое разделение двух узлов может привести к остановке операций управления."
  - "Без QDevice Expected votes равен 2."
  - "Команда pvecm add qdevice <IP> вызывает ошибку too many arguments."
  - "Отсутствует независимый третий голос кворума."

observed_behavior:
  - metric: "Количество узлов Proxmox"
    value_before: "2"
    value_after: "2"
    expected_value: "2"
    unit: "узла"
    source: "pvecm status"
    timestamp: ""

  - metric: "Expected votes"
    value_before: "2"
    value_after: "3"
    expected_value: "3"
    unit: "голоса"
    source: "pvecm status"
    timestamp: ""

  - metric: "Quorum"
    value_before: "2"
    value_after: "2"
    expected_value: "2"
    unit: "голоса"
    source: "pvecm status"
    timestamp: ""

  - metric: "QDevice"
    value_before: "Offline или отсутствует"
    value_after: "Online"
    expected_value: "Online"
    unit: ""
    source: "pvecm status"
    timestamp: ""

expected_behavior:
  - "Кластер имеет Expected votes: 3."
  - "Кворум равен 2."
  - "В pvecm status присутствует Qdevice с одним голосом."
  - "При отказе одного узла оставшийся узел сохраняет кворум вместе с QDevice."
  - "При отказе только QDevice два узла сохраняют кворум."

actual_behavior:
  - "Инструкция описывает установку и подключение QDevice."
  - "Ожидаемое состояние после настройки указано."
  - "Фактический вывод успешного pvecm status для конкретного окружения не приведён."

affected_services:
  - name: "Corosync"
    impact: "Обеспечивает членство и кворум кластера."
    availability: "available"

  - name: "Proxmox cluster management"
    impact: "Может быть недоступен при потере кворума."
    availability: "degraded"

  - name: "Proxmox HA"
    impact: "Для автоматического перезапуска ресурсов дополнительно требуется fencing."
    availability: "unknown"

  - name: "Ceph"
    impact: "QDevice не заменяет отдельный кворум Ceph."
    availability: "unknown"

# ============================================================
# 8. ПРОБЛЕМА, РЕШЕНИЕ И ПРИЧИНА
# ============================================================

problem_statement: |
  В двухузловом кластере Proxmox при потере связи с одним из узлов
  остаётся только один голос из двух. Для кворума требуется два голоса,
  поэтому кластер теряет кворум. Необходимо добавить независимый третий
  голос через отдельный хост с corosync-qnetd.

solution: |
  На независимом Debian/Ubuntu-хосте установить corosync-qnetd,
  включить и запустить службу, открыть TCP-порт 5403 и проверить,
  что порт прослушивается. На обоих узлах Proxmox установить
  corosync-qdevice. На одном узле выполнить pvecm qdevice setup
  <IP_QDEVICE>. После этого проверить pvecm status,
  corosync-quorumtool -s, состояние corosync-qdevice и corosync-qnetd.
  Затем в maintenance-окно проверить отказ одного узла и отказ QDevice.

root_cause: |
  Причина потери кворума — чётное количество голосов в двухузловом
  кластере. При отказе одного узла остаётся только один голос из двух,
  тогда как для кворума требуется два. Дополнительной причиной ошибки
  настройки является использование устаревшей команды pvecm add qdevice
  <IP> вместо pvecm qdevice setup <IP>.

contributing_factors:
  - "В кластере только два узла."
  - "QDevice отсутствует либо не подключён."
  - "QDevice может быть размещён не на независимом хосте."
  - "TCP-порт 5403 может быть заблокирован firewall."
  - "Время на узлах может быть рассинхронизировано."
  - "SSH-доступ к QDevice может быть не настроен."
  - "Для HA может отсутствовать fencing."

trigger:
  type: "failure"
  description: "Отказ одного узла или сетевое разделение в двухузловом кластере."

resolution_confidence: "high"
evidence_level: "partially_verified"

# ============================================================
# 9. ДИАГНОСТИКА
# ============================================================

diagnostic_method: |
  Проверить наличие кворума, синхронизацию времени, разрешение имён,
  SSH-доступ, доступность TCP-порта 5403, состояние corosync-qnetd
  и corosync-qdevice. После настройки сравнить Expected votes,
  Total votes, Quorum и наличие Qdevice в pvecm status.

diagnostic_steps:
  - step: 1
    action: "Проверить состояние кластера."
    command: "pvecm status"
    expected_result: "Quorate: Yes."
    actual_result: ""
    conclusion: ""
    status: "pending"
    evidence: ""

  - step: 2
    action: "Проверить синхронизацию времени."
    command: "timedatectl status"
    expected_result: "Время синхронизировано на всех трёх машинах."
    actual_result: ""
    conclusion: ""
    status: "pending"
    evidence: ""

  - step: 3
    action: "Проверить SSH-доступ с узла Proxmox к QDevice."
    command: "ssh root@<IP_QDEVICE>"
    expected_result: "SSH-подключение успешно."
    actual_result: ""
    conclusion: ""
    status: "pending"
    evidence: ""

  - step: 4
    action: "Проверить службу QNetd."
    command: "systemctl status corosync-qnetd"
    expected_result: "active (running)."
    actual_result: ""
    conclusion: ""
    status: "pending"
    evidence: ""

  - step: 5
    action: "Проверить порт QNetd."
    command: "ss -ltnp | grep 5403"
    expected_result: "TCP-порт 5403 прослушивается."
    actual_result: ""
    conclusion: ""
    status: "pending"
    evidence: ""

  - step: 6
    action: "Проверить доступность QDevice с узлов Proxmox."
    command: "nc -zv <IP_QDEVICE> 5403"
    expected_result: "TCP-подключение успешно."
    actual_result: ""
    conclusion: ""
    status: "pending"
    evidence: ""

  - step: 7
    action: "Проверить состояние QDevice после настройки."
    command: "systemctl status corosync-qdevice"
    expected_result: "active (running)."
    actual_result: ""
    conclusion: ""
    status: "pending"
    evidence: ""

  - step: 8
    action: "Проверить детальное состояние кворума."
    command: "corosync-quorumtool -s"
    expected_result: "Кворум подтверждён."
    actual_result: ""
    conclusion: ""
    status: "pending"
    evidence: ""

checks_performed:
  - "Проверка состояния кластера через pvecm status"
  - "Проверка синхронизации времени"
  - "Проверка DNS или /etc/hosts"
  - "Проверка SSH-доступа"
  - "Проверка TCP-порта 5403"
  - "Проверка службы corosync-qnetd"
  - "Проверка службы corosync-qdevice"
  - "Проверка отказа одного узла"
  - "Проверка отказа QDevice"

logs_examined:
  - path: ""
    source: ""
    time_range: ""
    relevant_entries: ""

metrics_examined:
  - name: "Expected votes"
    source: "pvecm status"
    unit: "голоса"
    collection_method: "CLI"
    result: "После настройки ожидается 3."

  - name: "Quorum"
    source: "pvecm status"
    unit: "голоса"
    collection_method: "CLI"
    result: "После настройки ожидается 2."

# ============================================================
# 10. ГИПОТЕЗЫ
# ============================================================

hypotheses:
  - id: "H1"
    description: "Двухузловой кластер теряет кворум при отказе одного узла из-за чётного количества голосов."
    status: "confirmed"
    verification_method: "Анализ votequorum и проверка pvecm status."
    evidence_for:
      - "В кластере два узла."
      - "Для кворума при двух голосах требуется два голоса."
    evidence_against: []
    conclusion: "Нужен дополнительный независимый голос QDevice."

  - id: "H2"
    description: "Команда pvecm add qdevice <IP> является корректной командой подключения QDevice."
    status: "rejected"
    verification_method: "Выполнение команды в Proxmox."
    evidence_for: []
    evidence_against:
      - "Команда завершилась ошибкой too many arguments."
    conclusion: "Следует использовать pvecm qdevice setup <IP_QDEVICE>."

# ============================================================
# 11. ПРОВЕРЕННЫЕ И ОТВЕРГНУТЫЕ РЕШЕНИЯ
# ============================================================

tested_solutions:
  - action: "Установка corosync-qnetd на независимый Linux-хост."
    result: "Предоставляет серверную часть QDevice."
    status: "successful"
    reason: "Это предназначенное назначение corosync-qnetd."

  - action: "Установка corosync-qdevice на обоих узлах Proxmox."
    result: "Устанавливает клиентскую часть QDevice."
    status: "successful"
    reason: "Клиент требуется на каждом узле кластера."

  - action: "Подключение через pvecm qdevice setup <IP_QDEVICE>."
    result: "Рекомендуемая команда подключения QDevice."
    status: "successful"
    reason: "Команда указана как актуальный способ настройки."

  - action: "Размещение QDevice на отдельном ПК с Debian/Ubuntu."
    result: "Соответствует требованиям независимого свидетеля."
    status: "successful"
    reason: "QDevice не зависит от отказа одного из узлов Proxmox."

rejected_solutions:
  - action: "pvecm add qdevice <IP>"
    reason_rejected: "Команда вызывает ошибку too many arguments и обозначена как устаревшая."
    risk: "Настройка не завершится, а кластер останется без дополнительного голоса."

  - action: "Запуск corosync-qnetd на одном из узлов Proxmox."
    reason_rejected: "При отказе этого узла одновременно теряется QDevice."
    risk: "QDevice не обеспечит независимый голос и отказоустойчивость."

  - action: "Использование Windows или macOS в качестве QDevice-хоста."
    reason_rejected: "corosync-qnetd предназначен для Linux."
    risk: "Служба QNetd не будет работать штатным способом."

  - action: "Ручное редактирование /etc/pve/corosync.conf для настройки QDevice."
    reason_rejected: "Инструкция предписывает использовать pvecm qdevice setup/remove."
    risk: "Можно повредить кластерную конфигурацию."

dont_repeat:
  - "Не использовать pvecm add qdevice <IP>; команда вызывает ошибку too many arguments. Использовать pvecm qdevice setup <IP_QDEVICE>."
  - "Не размещать corosync-qnetd на одном из двух узлов Proxmox; при отказе этого узла будет потерян и QDevice."
  - "Не использовать Windows или macOS в качестве QDevice-хоста; требуется Linux с corosync-qnetd."
  - "Не редактировать /etc/pve/corosync.conf вручную для добавления QDevice."
  - "Не считать QDevice заменой fencing для автоматического запуска HA-ресурсов."
  - "Не считать QDevice решением кворума Ceph; для Ceph требуется отдельное планирование мониторов."

# ============================================================
# 12. КОМАНДЫ И КОНФИГУРАЦИЯ
# ============================================================

commands: |
  # На хосте QDevice
  apt update && apt upgrade -y
  apt install -y corosync-qnetd
  systemctl enable --now corosync-qnetd
  systemctl status corosync-qnetd
  ss -ltnp | grep 5403
  ufw allow 5403/tcp
  ufw reload
  firewall-cmd --permanent --add-port=5403/tcp
  firewall-cmd --reload
  iptables -I INPUT -p tcp --dport 5403 -j ACCEPT
  corosync-qnetd-tool -s

  # На обоих узлах Proxmox
  apt update
  apt install -y corosync-qdevice
  dpkg -l | grep corosync-qdevice

  # На одном узле Proxmox
  pvecm qdevice setup <IP_QDEVICE>

  # Проверка
  pvecm status
  corosync-quorumtool -s
  systemctl status corosync-qdevice
  nc -zv <IP_QDEVICE> 5403

  # SSH-проверка
  ssh root@<IP_QDEVICE>
  ssh-copy-id root@<IP_QDEVICE>

  # Удаление QDevice
  pvecm qdevice remove

commands_by_system:
  proxmox: |
    apt update
    apt install -y corosync-qdevice
    pvecm qdevice setup <IP_QDEVICE>
    pvecm status
    corosync-quorumtool -s
    systemctl status corosync-qdevice
    pvecm qdevice remove

  windows_powershell: |

  linux_shell: |
    apt update && apt upgrade -y
    apt install -y corosync-qnetd
    systemctl enable --now corosync-qnetd
    systemctl status corosync-qnetd
    ss -ltnp | grep 5403
    corosync-qnetd-tool -s

command_safety:
  requires_administrator: true
  requires_reboot: false
  causes_downtime: false
  modifies_data: false
  modifies_configuration: true
  reversible: true

config_snippets:
  main_configuration: |
    QDevice должен находиться на отдельном Linux-хосте.
    На QDevice работает corosync-qnetd.
    На обоих узлах Proxmox работает corosync-qdevice.
    Основная команда подключения: pvecm qdevice setup <IP_QDEVICE>.

  service_configuration: |
    corosync-qnetd:
      enabled: true
      port: 5403
      protocol: tcp

    corosync-qdevice:
      enabled: true
      nodes: 2

  before_change: |
    Expected votes: 2
    Quorum: 2
    QDevice: отсутствует

  after_change: |
    Expected votes: 3
    Quorum: 2
    Total votes: 3
    Flags: Quorate Qdevice

configuration_changes:
  - parameter: "corosync-qnetd"
    old_value: "не установлен"
    new_value: "установлен и запущен на независимом Linux-хосте"
    reason: "Предоставить внешний голос кворума."
    reversible: true

  - parameter: "corosync-qdevice"
    old_value: "не установлен на узлах"
    new_value: "установлен на обоих узлах Proxmox"
    reason: "Подключить узлы к QNetd."
    reversible: true

  - parameter: "QDevice в кластере"
    old_value: "отсутствует"
    new_value: "настроен через pvecm qdevice setup"
    reason: "Увеличить Expected votes до 3."
    reversible: true

# ============================================================
# 13. ИЗМЕНЕНИЯ И ОТКАТ
# ============================================================

changes_applied:
  - change: "Установка corosync-qnetd на отдельном Linux-хосте."
    operator: ""
    timestamp: ""
    target: "QDevice-хост"
    backup_created: false
    change_reference: ""

  - change: "Установка corosync-qdevice на узлах Proxmox."
    operator: ""
    timestamp: ""
    target: "Оба узла Proxmox"
    backup_created: false
    change_reference: ""

  - change: "Подключение QDevice к кластеру."
    operator: ""
    timestamp: ""
    target: "Кластер Proxmox"
    backup_created: false
    change_reference: "pvecm qdevice setup <IP_QDEVICE>"

rollback_available: true
rollback_plan: |
  Проверить состояние кластера и удалить QDevice штатной командой
  pvecm qdevice remove. После удаления проверить pvecm status,
  corosync-quorumtool -s и состояние corosync-qdevice.
  Не удалять пакеты и конфигурацию вручную до проверки состояния кластера.

rollback_commands: |
  pvecm qdevice remove
  pvecm status
  corosync-quorumtool -s

rollback_conditions:
  - "QDevice постоянно показывает Offline."
  - "После настройки кластер теряет кворум."
  - "Обнаружены ошибки сертификатов или конфигурации."
  - "QDevice размещён на зависимом от Proxmox хосте."

backup:
  created: false
  type: "none"
  location: ""
  timestamp: ""
  retention: ""

# ============================================================
# 14. ПРОВЕРКА РЕЗУЛЬТАТА
# ============================================================

success_criteria:
  - "pvecm status показывает Quorate: Yes."
  - "Expected votes равен 3."
  - "Total votes равен 3 при доступности всех компонентов."
  - "Quorum равен 2."
  - "В таблице участников присутствует Qdevice с одним голосом."
  - "corosync-qdevice работает на обоих узлах."
  - "corosync-qnetd работает на отдельном хосте."
  - "При отказе одного узла оставшийся узел сохраняет кворум."

validation_steps:
  - step: 1
    action: "Проверить статус кластера."
    expected_result: "Quorate: Yes; Expected votes: 3; Quorum: 2."
    actual_result: ""
    status: "pending"

  - step: 2
    action: "Проверить службы QDevice на обоих узлах."
    expected_result: "corosync-qdevice имеет статус active (running)."
    actual_result: ""
    status: "pending"

  - step: 3
    action: "Проверить службу QNetd на отдельном хосте."
    expected_result: "corosync-qnetd имеет статус active (running)."
    actual_result: ""
    status: "pending"

  - step: 4
    action: "Проверить отказ одного узла."
    expected_result: "Оставшийся узел и QDevice сохраняют Quorate: Yes."
    actual_result: ""
    status: "pending"

  - step: 5
    action: "Проверить отказ только QDevice."
    expected_result: "Два работающих узла сохраняют Quorate: Yes."
    actual_result: ""
    status: "pending"

before_after_comparison:
  - metric: "Expected votes"
    before: "2"
    after: "3"
    expected: "3"
    improvement: "Добавлен независимый голос QDevice."
    source: "pvecm status"

  - metric: "Quorum при отказе одного узла"
    before: "Теряется"
    after: "Сохраняется при доступном QDevice"
    expected: "Сохраняется"
    improvement: "Повышена устойчивость двухузлового кластера."
    source: "pvecm status"

post_change_observation_period: ""
post_change_status: "not_started"

regression_risk: "medium"
known_side_effects:
  - "Потеря одновременно одного узла и QDevice приводит к потере кворума."
  - "QDevice не обеспечивает fencing."
  - "QDevice не заменяет дополнительные мониторы Ceph."

# ============================================================
# 15. БЕЗОПАСНОСТЬ И РИСКИ
# ============================================================

security_impact: "medium"
security_considerations:
  - "Открыть TCP-порт 5403 только для узлов Proxmox."
  - "Ограничить SSH-доступ к QDevice."
  - "Использовать независимый хост, не размещённый на узлах Proxmox."
  - "Проверить сертификаты и доверие между компонентами QDevice."
  - "Не разрешать лишний сетевой доступ к QNetd."

data_loss_risk: "medium"
downtime_required: false
estimated_downtime: ""
requires_maintenance_window: true

dangerous_operations:
  - "pvecm qdevice remove"
  - "Изменение конфигурации кластера при отсутствии кворума."
  - "Остановка узла во время теста отказоустойчивости."
  - "Ручное редактирование /etc/pve/corosync.conf."

secrets_present: false
secret_locations:
  - ""

# ============================================================
# 16. ДОКАЗАТЕЛЬСТВА И ИСТОЧНИКИ
# ============================================================

evidence:
  - type: "command_output"
    description: "Ожидаемый вывод pvecm status после добавления QDevice."
    location: ""
    collected_at: ""
    collected_by: ""
    integrity_check: ""

  - type: "command_output"
    description: "Проверка состояния службы corosync-qnetd."
    location: ""
    collected_at: ""
    collected_by: ""
    integrity_check: ""

  - type: "command_output"
    description: "Проверка состояния службы corosync-qdevice."
    location: ""
    collected_at: ""
    collected_by: ""
    integrity_check: ""

source_urls:
  - "https://github.com/cladkyimaffin-hue/korona/blob/2ca49d67ec47dea81eb81fb7594053dba46f7afe/Proxmox/%D0%94%D0%BE%D0%B1%D0%B0%D0%B2%D0%B8%D1%82%D1%8C%20qdevice.md"

urls:
  - "https://github.com/cladkyimaffin-hue/korona/blob/2ca49d67ec47dea81eb81fb7594053dba46f7afe/Proxmox/%D0%94%D0%BE%D0%B0%D0%B2%D0%B8%D1%82%D1%8C%20qdevice.md"

references:
  - title: "Добавить qdevice.md"
    url: "https://github.com/cladkyimaffin-hue/korona/blob/2ca49d67ec47dea81eb81fb7594053dba46f7afe/Proxmox/%D0%94%D0%BE%D0%B0%D0%B2%D0%B8%D1%82%D1%8C%20qdevice.md"
    type: "internal_note"
    accessed_at: "2026-09-07"
    relevance: "Исходная инструкция по настройке QDevice."

github:
  repository: "cladkyimaffin-hue/korona"
  file_path: "Proxmox/Добавить qdevice.md"
  branch: ""
  commit: "2ca49d67ec47dea81eb81fb7594053dba46f7afe"
  issue: ""
  pull_request: ""
  related_commits:
    - ""

# ============================================================
# 17. ИНСТРУКЦИИ ДЛЯ ИИ
# ============================================================

ai_instructions:
  primary_goal: "Помочь безопасно настроить внешний Corosync QDevice для двухузлового кластера Proxmox VE и проверить сохранение кворума."

  use_this_document_for:
    - "Подготовка независимого Linux-хоста QDevice."
    - "Установка corosync-qnetd и corosync-qdevice."
    - "Настройка через pvecm qdevice setup."
    - "Проверка кворума и состояния служб."
    - "Планирование теста отказа одного узла."

  do_not_use_this_document_for:
    - "Настройка Ceph quorum без отдельной проверки требований Ceph."
    - "Настройка fencing без дополнительной документации."
    - "Размещение QDevice на узле Proxmox."
    - "Автоматическое выполнение команд без проверки окружения."

  required_context:
    - "Версия Proxmox VE."
    - "IP-адреса обоих узлов."
    - "IP-адрес независимого QDevice-хоста."
    - "Состояние кластера через pvecm status."
    - "ОС QDevice-хоста."
    - "Состояние firewall и TCP-порта 5403."

  ask_before_recommending:
    - "Изменение конфигурации кластера."
    - "Выполнение pvecm qdevice setup."
    - "Удаление QDevice."
    - "Остановка узла для теста отказоустойчивости."
    - "Изменение firewall."
    - "Настройка HA и fencing."

  response_requirements:
    - "Сначала проверить, что QDevice размещён на независимом хосте."
    - "Проверить наличие кворума до изменения конфигурации."
    - "Не предлагать pvecm add qdevice <IP>."
    - "Проверить доступность TCP-порта 5403."
    - "Отдельно предупредить, что QDevice не заменяет fencing."
    - "Отдельно предупредить, что QDevice не решает кворум Ceph."
    - "Проверить результат через pvecm status."

  confidence_limitations:
    - "Исходный файл содержит инструкцию и ожидаемые результаты, но не содержит полного фактического вывода успешной настройки."
    - "Команды и параметры требуют проверки с учётом версии Proxmox VE."
    - "Отказоустойчивость HA не подтверждается без проверки fencing."

key_takeaways:
  - "Для двухузлового кластера нужен независимый третий голос QDevice."
  - "На QDevice устанавливается corosync-qnetd, а на обоих узлах Proxmox — corosync-qdevice."
  - "Для подключения используется pvecm qdevice setup <IP_QDEVICE>."
  - "После настройки ожидаются Expected votes: 3 и Quorum: 2."
  - "QDevice должен быть физически или логически независим от обоих узлов Proxmox."
  - "QDevice сохраняет кворум, но не заменяет fencing и дополнительные мониторы Ceph."

assumptions:
  - "QDevice работает под управлением Debian или Ubuntu."
  - "QDevice имеет статический IP-адрес."
  - "TCP-порт 5403 доступен с обоих узлов Proxmox."
  - "SSH-доступ к QDevice возможен с узла Proxmox."
  - "Кластер до настройки QDevice находится в состоянии Quorate."
  - "Время на узлах и QDevice синхронизировано."

open_questions:
  - "Каковы фактические имена и IP-адреса двух узлов Proxmox?"
  - "Каковы фактические версия Proxmox VE и ОС QDevice?"
  - "Подключение QDevice было успешно выполнено или приведены только плановые шаги?"
  - "Настроен ли fencing для HA?"
  - "Используется ли в кластере Ceph и настроены ли его мониторы?"

# ============================================================
# 18. КАЧЕСТВО ДАННЫХ
# ============================================================

data_quality:
  completeness: "partial"
  accuracy: "partially_verified"
  freshness: "current"
  reproducibility: "partially_reproducible"
  source_quality: "primary"

missing_data:
  - "Нет фактических имён и IP-адресов пользовательских узлов в основной пошаговой инструкции."
  - "Нет фактического вывода pvecm status после добавления QDevice."
  - "Нет подтверждения успешного теста отказа одного узла."
  - "Не указана версия Proxmox VE для примерной схемы."
  - "Не указана фактическая ОС и версия QDevice-хоста."
  - "Не приведены фактические журналы служб."
  - "Не указано, настроено ли fencing."
  - "Не указана конфигурация Ceph, если он используется."

uncertainties:
  - "Фактический результат команды pvecm qdevice setup в исходном документе не подтверждён."
  - "Статус QDevice после настройки указан как ожидаемый, а не как фактически зафиксированный."
  - "Совместимость команд и служб может зависеть от версии Proxmox VE и Debian/Ubuntu."
  - "Утверждение о сохранении работы VM/CT при отказе узла требует отдельного теста."

needs_follow_up: true
follow_up_tasks:
  - task: "Выполнить pvecm status после настройки и сохранить вывод."
    owner: ""
    due_date: ""
    status: "pending"

  - task: "Проверить corosync-qdevice на обоих узлах."
    owner: ""
    due_date: ""
    status: "pending"

  - task: "Проверить corosync-qnetd и corosync-qnetd-tool на QDevice."
    owner: ""
    due_date: ""
    status: "pending"

  - task: "Провести контролируемый тест отказа одного узла."
    owner: ""
    due_date: ""
    status: "pending"

  - task: "Проверить наличие и работоспособность fencing для HA."
    owner: ""
    due_date: ""
    status: "pending"

# ============================================================
# 19. АУДИТ ДОКУМЕНТА
# ============================================================

audit:
  created_by: "cladkyimaffin-hue"
  created_at: "2026-08-30"
  last_modified_by: "cladkyimaffin-hue"
  last_modified_at: "2026-09-02"
  reviewed_by: "cladkyimaffin-hue"
  reviewed_at: ""
  review_result: "approved"

change_history:
  - version: "1.0"
    date: "2026-08-30"
    author: "cladkyimaffin-hue"
    changes:
      - "Создана инструкция по настройке QDevice."

# ============================================================
# 20. ФИНАЛЬНЫЕ ПОЛЯ
# ============================================================

review_notes: |
  Инструкция описывает общий порядок настройки QDevice для двухузлового
  кластера Proxmox VE. Перед применением необходимо заменить примерные
  IP-адреса, проверить версию Proxmox, наличие кворума, SSH-доступ,
  TCP-порт 5403 и независимость QDevice-хоста. Успешность настройки
  должна подтверждаться фактическим выводом pvecm status.

notes: |
  QDevice добавляет голос кворума Proxmox, но не является полноценным
  третьим узлом Ceph и не обеспечивает fencing. Одновременная потеря
  одного узла Proxmox и QDevice приводит к потере кворума.
---
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
