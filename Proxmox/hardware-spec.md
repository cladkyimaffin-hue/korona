---
# ============================================================
# 1. ИДЕНТИФИКАЦИЯ ДОКУМЕНТА
# ============================================================

document_id: "DOC-2026-08-30-001"
title: "Сводная спецификация аппаратного обеспечения кластера Proxmox VE"
slug: "svodnaya-specifikaciya-apparatnogo-oborudovaniya-klastera-proxmox"
document_type: "reference"
language: "ru"
version: "1.0"
schema_version: "1.0"
status: "in_progress"
confidentiality: "internal"
priority: "info"

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
approval_status: "draft"

# ============================================================
# 2. КЛАССИФИКАЦИЯ И ПОИСК
# ============================================================

category: "documentation"
domain: "virtualization"
subdomain: "hardware-specification"

tags:
  - "Hardware Specifications"
  - "Huawei 2288H V5"
  - "Proxmox VE"
  - "Ceph"
  - "Intel X722"
  - "Intel X710"
  - "10G SFP+"

keywords:
  - "Huawei FusionServer 2288H V5"
  - "аппаратная спецификация"
  - "Ceph OSD"
  - "HBA"
  - "JBOD"
  - "10GBASE-SR"
  - "SFP+"

aliases:
  - "Спецификация железа кластера"
  - "Hardware specification Proxmox"
  - "Комплектация Huawei 2288H V5"

related_topics:
  - "Ceph"
  - "Proxmox VE"
  - "RAID"
  - "HBA/JBOD"
  - "SFP+"
  - "iBMC"
  - "сетевое оборудование"

# ============================================================
# 3. КРАТКОЕ ОПИСАНИЕ
# ============================================================

problem: "Отсутствует централизованная сводная спецификация аппаратного обеспечения кластера для планирования обновлений, закупки комплектующих и диагностики."

summary: "Документ описывает аппаратную платформу кластера Proxmox VE из трёх одинаковых серверов Huawei FusionServer 2288H V5. Зафиксированы сведения о шасси, системных и дисках данных, архитектуре Ceph, сетевых картах Intel X722 и X710, оптических модулях, кабелях и требованиях к коммутаторам. Модель и количество CPU, объём RAM, режим дискового контроллера, наличие NVMe, блоки питания и финальная модель коммутатора требуют уточнения."

ai_summary: "Документ является незавершённой справочной спецификацией трёхузлового кластера Proxmox VE на Huawei FusionServer 2288H V5. Каждый 7 ТБ диск должен использоваться как отдельный Ceph OSD без локального RAID1; для сетевой инфраструктуры используются Intel X722/X710 и 10G SFP+, но часть характеристик оборудования ещё не подтверждена."

business_impact: "Документ используется для планирования закупок, обновлений, совместимости сетевого оборудования и диагностики инфраструктуры."

technical_impact: "Зафиксированы предполагаемая дисковая, сетевая и серверная архитектуры кластера; неподтверждённые аппаратные параметры пока ограничивают полноту спецификации."

user_impact: "Администраторы получают централизованное описание аппаратной конфигурации и список характеристик, которые необходимо уточнить."

severity: "info"
incident_status: "monitoring"

# ============================================================
# 4. СИСТЕМА И ОКРУЖЕНИЕ
# ============================================================

environment: "production"
system_role: "Узлы кластера Proxmox VE"
system_name: "Huawei FusionServer 2288H V5"
hostname: ""
fqdn: ""
asset_id: ""
vm_id: ""
cluster: "Proxmox VE cluster"
node: ""

operating_system:
  name: "Proxmox VE"
  version: ""
  edition: ""
  architecture: ""
  build: ""
  language: ""
  timezone: ""

platform:
  name: "Huawei FusionServer 2288H V5"
  version: ""
  node_version: ""
  kernel: ""
  hypervisor: "Proxmox VE"
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
    - type: "SSD"
      name: "Системный диск"
      size: "480 GB"
      filesystem: ""
      mount_point: ""
    - type: "SSD"
      name: "Системный диск"
      size: "480 GB"
      filesystem: ""
      mount_point: ""
    - type: "HDD"
      name: "Диск данных Ceph OSD"
      size: "7 TB"
      filesystem: ""
      mount_point: ""
    - type: "HDD"
      name: "Диск данных Ceph OSD"
      size: "7 TB"
      filesystem: ""
      mount_point: ""

# ============================================================
# 5. КОМПОНЕНТЫ И ВЕРСИИ
# ============================================================

components:
  - name: "Huawei FusionServer 2288H V5"
    type: "server"
    version: ""
    status_before: ""
    status_after: "documented"
    configuration: "Три одинаковых сервера, форм-фактор 2U, восемь SFF-отсеков."

  - name: "Intel X722"
    type: "network_adapter"
    version: ""
    status_before: ""
    status_after: "documented"
    configuration: "2 порта 10GbE SFP+ и 2 порта 1GbE RJ45."

  - name: "Intel X710"
    type: "network_adapter"
    version: ""
    status_before: ""
    status_after: "documented"
    configuration: "2 порта 10GbE SFP+ в PCIe SLOT 3."

  - name: "Ceph OSD"
    type: "storage"
    version: ""
    status_before: ""
    status_after: "planned"
    configuration: "Каждый 7 ТБ диск используется как отдельный OSD."

dependencies:
  - name: "10G SFP+ коммутаторы"
    version: ""
    required: true
    purpose: "Подключение 10GbE-портов серверов."

  - name: "Intel 10GBASE-SR трансиверы"
    version: ""
    required: true
    purpose: "Работа оптических 10GbE-соединений."

related_files:
  - "INDEX.md"
  - "Полная комплектация сервера, идентификация сетевых карт, расположение портов и рекомендации по установке Proxmox без оптики.md"

depends_on:
  - ""

supersedes: ""
superseded_by: ""

# ============================================================
# 6. ВРЕМЕННАЯ ШКАЛА
# ============================================================

timeline:
  detected_at: 2026-08-30
  reported_at: ""
  investigation_started_at: ""
  mitigation_started_at: ""
  resolved_at: ""
  closed_at: ""

  events:
    - timestamp: 2026-08-30
      event: "Создана сводная спецификация аппаратного обеспечения кластера."
      actor: "cladkyimaffin-hue"
      evidence: "Исходный Markdown-файл."

    - timestamp: 2026-09-02
      event: "Документ обновлён."
      actor: "cladkyimaffin-hue"
      evidence: "Поле date_modified в исходном Markdown-файле."

last_incident: 2026-08-30
incident_duration: ""
recurrence_count: 0
recurrence_pattern: ""

# ============================================================
# 7. СИМПТОМЫ И ФАКТИЧЕСКИЕ НАБЛЮДЕНИЯ
# ============================================================

symptoms:
  - "Отсутствует единая полная спецификация аппаратного обеспечения."
  - "Некоторые ключевые параметры оборудования не подтверждены."
  - "Финальная модель коммутатора не зафиксирована."
  - "Наличие NVMe под Ceph WAL/DB не подтверждено."

observed_behavior:
  - metric: "Количество узлов"
    value_before: ""
    value_after: "3"
    expected_value: "3"
    unit: "сервера"
    source: "Исходный Markdown-файл"
    timestamp: ""

  - metric: "Системные диски на сервер"
    value_before: ""
    value_after: "2 x 480 GB"
    expected_value: "2 x 480 GB"
    unit: ""
    source: "Исходный Markdown-файл"
    timestamp: ""

  - metric: "Диски данных на сервер"
    value_before: ""
    value_after: "2 x 7 TB"
    expected_value: "2 x 7 TB"
    unit: ""
    source: "Исходный Markdown-файл"
    timestamp: ""

  - metric: "Диски данных в кластере"
    value_before: ""
    value_after: "6 x 7 TB"
    expected_value: "6 x 7 TB"
    unit: ""
    source: "Исходный Markdown-файл"
    timestamp: ""

  - metric: "Порты 10GbE на сервер"
    value_before: ""
    value_after: "4"
    expected_value: "4"
    unit: "порта"
    source: "Исходный Markdown-файл"
    timestamp: ""

expected_behavior:
  - "Все аппаратные характеристики серверов подтверждены и документированы."
  - "Каждый 7 ТБ диск используется как отдельный Ceph OSD."
  - "Коммутаторы совместимы с Intel 10GBASE-SR без vendor-lock."
  - "Системные диски используются под зеркало ОС Proxmox."

actual_behavior:
  - "Часть характеристик обозначена как требующая уточнения."
  - "Архитектура Ceph с отдельными OSD для дисков данных описана."
  - "Требования к коммутаторам описаны, но модель не выбрана."
  - "Наличие NVMe WAL/DB не подтверждено."

affected_services:
  - name: "Proxmox VE"
    impact: "Аппаратная платформа документирована частично."
    availability: "available"

  - name: "Ceph"
    impact: "Описана предполагаемая схема OSD; режим контроллера и NVMe требуют проверки."
    availability: "unknown"

  - name: "Сетевая инфраструктура 10GbE"
    impact: "Порты и трансиверы описаны, совместимость финального коммутатора не подтверждена."
    availability: "unknown"

# ============================================================
# 8. ПРОБЛЕМА, РЕШЕНИЕ И ПРИЧИНА
# ============================================================

problem_statement: |
  Для кластера Proxmox VE из трёх серверов Huawei FusionServer 2288H V5
  отсутствовала централизованная сводка аппаратных характеристик.
  Требовалось собрать сведения о серверной платформе, дисковой подсистеме,
  Ceph OSD, сетевых адаптерах, оптических модулях, кабелях и требованиях
  к коммутаторам.

solution: |
  Создан справочный документ с описанием трёх серверов Huawei FusionServer
  2288H V5, системных SSD 2 x 480 GB, дисков данных 2 x 7 TB на сервер,
  архитектуры Ceph с отдельным OSD для каждого 7 ТБ диска, сетевых карт
  Intel X722 и X710, трансиверов Intel FTLX8571D3BCVIT1, кабелей CABEUS
  OM3 LC-LC и минимальных требований к 10G SFP+ коммутаторам.
  Неподтверждённые характеристики вынесены в чек-лист.

root_cause: |
  Неприменимо: документ является проактивной документацией,
  а не записью об инциденте.

contributing_factors:
  - "Не зафиксированы точные модели и количество CPU."
  - "Не зафиксированы объём и тип RAM."
  - "Не подтверждён режим работы дискового контроллера."
  - "Не подтверждено наличие NVMe под Ceph WAL/DB."
  - "Не выбрана финальная модель коммутатора."

trigger:
  type: "unknown"
  description: "Потребность централизовать сведения об аппаратной конфигурации кластера."

resolution_confidence: "medium"
evidence_level: "partially_verified"

# ============================================================
# 9. ДИАГНОСТИКА
# ============================================================

diagnostic_method: |
  Для проверки аппаратной конфигурации предлагается использовать сведения
  из операционной системы, инвентаризацию PCI-устройств и отдельную проверку
  дисков, контроллера, NVMe и сетевых портов. Исходный файл содержит команды
  lshw -short и lspci | grep -i eth, но результаты их выполнения не приведены.

diagnostic_steps:
  - step: 1
    action: "Проверить краткую аппаратную конфигурацию сервера."
    command: "lshw -short"
    expected_result: "Вывод списка основных аппаратных компонентов."
    actual_result: ""
    conclusion: ""
    status: "pending"
    evidence: ""

  - step: 2
    action: "Проверить сетевые PCI-устройства."
    command: "lspci | grep -i eth"
    expected_result: "Обнаружены сетевые адаптеры Intel X722 и Intel X710."
    actual_result: ""
    conclusion: ""
    status: "pending"
    evidence: ""

  - step: 3
    action: "Уточнить модель и количество CPU."
    command: ""
    expected_result: "Точная модель и количество процессоров."
    actual_result: ""
    conclusion: ""
    status: "pending"
    evidence: ""

  - step: 4
    action: "Уточнить объём и тип оперативной памяти."
    command: ""
    expected_result: "Подтверждённый объём и тип RAM."
    actual_result: ""
    conclusion: ""
    status: "pending"
    evidence: ""

  - step: 5
    action: "Проверить наличие NVMe-дисков под Ceph WAL/DB."
    command: ""
    expected_result: "Подтверждено наличие или отсутствие NVMe."
    actual_result: ""
    conclusion: ""
    status: "pending"
    evidence: ""

  - step: 6
    action: "Подтвердить режим работы дискового контроллера."
    command: ""
    expected_result: "Подтверждён режим IT/JBOD или иная конфигурация."
    actual_result: ""
    conclusion: ""
    status: "pending"
    evidence: ""

checks_performed:
  - "Зафиксирована модель серверной платформы."
  - "Зафиксировано количество узлов."
  - "Зафиксирована конфигурация системных и дисков данных."
  - "Описана схема использования дисков в Ceph."
  - "Описаны сетевые адаптеры и оптические компоненты."
  - "Сформирован список характеристик, требующих уточнения."

logs_examined:
  - path: ""
    source: ""
    time_range: ""
    relevant_entries: ""

metrics_examined:
  - name: ""
    source: ""
    unit: ""
    collection_method: ""
    result: ""

# ============================================================
# 10. ГИПОТЕЗЫ
# ============================================================

hypotheses:
  - id: "H1"
    description: "Для дисков данных используется режим HBA/JBOD без аппаратного RAID."
    status: "proposed"
    verification_method: "Проверить конфигурацию дискового контроллера."
    evidence_for:
      - "В документе указано, что для Ceph критичен режим JBOD/IT."
    evidence_against: []
    conclusion: "Требует подтверждения."

  - id: "H2"
    description: "На каждой ноде отсутствуют NVMe-диски под Ceph WAL/DB."
    status: "inconclusive"
    verification_method: "Проверить наличие NVMe-дисков на каждой ноде."
    evidence_for: []
    evidence_against: []
    conclusion: "В исходном файле наличие NVMe обозначено как требующее уточнения."

# ============================================================
# 11. ПРОВЕРЕННЫЕ И ОТВЕРГНУТЫЕ РЕШЕНИЯ
# ============================================================

tested_solutions:
  - action: "Использовать каждый 7 ТБ диск как отдельный Ceph OSD."
    result: "Решение указано как архитектура Ceph."
    status: "successful"
    reason: "Позволяет не терять 50% ёмкости на локальном зеркале и не создавать двойную репликацию."

  - action: "Использовать локальное зеркало RAID1/mdadm/ZFS mirror для дисков данных."
    result: "Решение отклонено."
    status: "failed"
    reason: "Приводит к потере 50% ёмкости и двойной репликации."

rejected_solutions:
  - action: "Создать локальное зеркало RAID1/mdadm/ZFS mirror из двух дисков по 7 ТБ."
    reason_rejected: "В исходном документе указано, что локальное зеркало из дисков данных не делается."
    risk: "Потеря 50% ёмкости и двойная репликация поверх Ceph."

dont_repeat:
  - "Не объединять два 7 ТБ диска каждого сервера в локальное RAID1, mdadm или ZFS mirror перед использованием в Ceph."
  - "Не предполагать наличие аппаратного RAID-контроллера для дисков данных без проверки режима HBA/JBOD."
  - "Не считать наличие NVMe под Ceph WAL/DB подтверждённым без проверки на каждой ноде."
  - "Не выбирать коммутатор без проверки совместимости с трансиверами Intel 10GBASE-SR."

# ============================================================
# 12. КОМАНДЫ И КОНФИГУРАЦИЯ
# ============================================================

commands: |
  lshw -short
  lspci | grep -i eth

commands_by_system:
  proxmox: |
    lshw -short
    lspci | grep -i eth

  windows_powershell: |

  linux_shell: |
    lshw -short
    lspci | grep -i eth

command_safety:
  requires_administrator: false
  requires_reboot: false
  causes_downtime: false
  modifies_data: false
  modifies_configuration: false
  reversible: true

config_snippets:
  main_configuration: |
    Серверная платформа: Huawei FusionServer 2288H V5
    Узлов в кластере: 3
    Системные диски: 2 x 480 GB SSD
    Диски данных: 2 x 7 TB на сервер
    Ceph: каждый 7 TB диск является отдельным OSD

  service_configuration: |
    Proxmox VE и Ceph

  before_change: |
    Не указано.

  after_change: |
    Создана сводная аппаратная спецификация с перечнем подтверждённых
    и требующих уточнения характеристик.

configuration_changes:
  - parameter: "Документирование аппаратной конфигурации"
    old_value: ""
    new_value: "Создана сводная спецификация"
    reason: "Централизация сведений о кластере"
    reversible: true

# ============================================================
# 13. ИЗМЕНЕНИЯ И ОТКАТ
# ============================================================

changes_applied:
  - change: "Создан и обновлён Markdown-документ с аппаратной спецификацией."
    operator: "cladkyimaffin-hue"
    timestamp: ""
    target: "Документация кластера Proxmox VE"
    backup_created: false
    change_reference: ""

rollback_available: true
rollback_plan: |
  При необходимости удалить или заменить документ в репозитории.
  Операции с аппаратной конфигурацией серверов исходным документом
  не описаны.

rollback_commands: |

rollback_conditions:
  - "Документ содержит устаревшие или подтверждённо ошибочные сведения."
  - "Изменена аппаратная конфигурация серверов или сетевая топология."

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
  - "В документе указана модель серверной платформы и количество узлов."
  - "Описаны системные и диски данных."
  - "Зафиксирована схема Ceph OSD."
  - "Описаны сетевые карты, трансиверы и кабели."
  - "Сформирован список характеристик, требующих уточнения."

validation_steps:
  - step: 1
    action: "Сверить фактическую модель и количество CPU."
    expected_result: "Данные подтверждены."
    actual_result: ""
    status: "pending"

  - step: 2
    action: "Сверить фактический объём и тип RAM."
    expected_result: "Данные подтверждены."
    actual_result: ""
    status: "pending"

  - step: 3
    action: "Проверить дисковый контроллер и режим HBA/JBOD."
    expected_result: "Режим подтверждён."
    actual_result: ""
    status: "pending"

  - step: 4
    action: "Проверить наличие NVMe под Ceph WAL/DB."
    expected_result: "Наличие или отсутствие подтверждено."
    actual_result: ""
    status: "pending"

  - step: 5
    action: "Зафиксировать финальную модель коммутатора."
    expected_result: "Модель коммутатора указана."
    actual_result: ""
    status: "pending"

before_after_comparison:
  - metric: "Полнота аппаратной спецификации"
    before: "Отсутствует централизованный документ"
    after: "Создана частично заполненная спецификация"
    expected: "Полностью подтверждённая спецификация"
    improvement: "Сформирована единая структура данных и чек-лист"
    source: "Исходный Markdown-файл"

post_change_observation_period: ""
post_change_status: "monitoring"

regression_risk: "medium"
known_side_effects:
  - "Неподтверждённые параметры могут привести к ошибкам при закупке или планировании совместимости."

# ============================================================
# 15. БЕЗОПАСНОСТЬ И РИСКИ
# ============================================================

security_impact: "none"
security_considerations:
  - "Проверять доступ к внутренней аппаратной документации."
  - "Не публиковать сведения об инфраструктуре без разрешения."

data_loss_risk: "low"
downtime_required: false
estimated_downtime: ""
requires_maintenance_window: false

dangerous_operations:
  - "Не менять схему дисков Ceph без проверки резервирования и состояния кластера."
  - "Не переводить дисковый контроллер в другой режим без резервной копии и плана восстановления."

secrets_present: false
secret_locations: []

# ============================================================
# 16. ДОКАЗАТЕЛЬСТВА И ИСТОЧНИКИ
# ============================================================

evidence:
  - type: "documentation"
    description: "Сводная аппаратная спецификация Huawei FusionServer 2288H V5."
    location: "Proxmox/hardware-spec.md"
    collected_at: "2026-08-30"
    collected_by: "cladkyimaffin-hue"
    integrity_check: "Commit d819bdd630d0e5cd59c7755de1f433ca5624d278"

  - type: "documentation"
    description: "Чек-лист характеристик, требующих уточнения."
    location: "Proxmox/hardware-spec.md"
    collected_at: "2026-09-02"
    collected_by: "cladkyimaffin-hue"
    integrity_check: "Commit d819bdd630d0e5cd59c7755de1f433ca5624d278"

source_urls:
  - "https://github.com/cladkyimaffin-hue/korona/blob/d819bdd630d0e5cd59c7755de1f433ca5624d278/Proxmox/hardware-spec.md"

urls:
  - "https://github.com/cladkyimaffin-hue/korona/blob/d819bdd630d0e5cd59c7755de1f433ca5624d278/Proxmox/hardware-spec.md"

references:
  - title: "hardware-spec.md"
    url: "https://github.com/cladkyimaffin-hue/korona/blob/d819bdd630d0e5cd59c7755de1f433ca5624d278/Proxmox/hardware-spec.md"
    type: "internal_note"
    accessed_at: "2026-09-07"
    relevance: "Основной источник аппаратной спецификации."

github:
  repository: "cladkyimaffin-hue/korona"
  file_path: "Proxmox/hardware-spec.md"
  branch: ""
  commit: "d819bdd630d0e5cd59c7755de1f433ca5624d278"
  issue: ""
  pull_request: ""
  related_commits:
    - ""

# ============================================================
# 17. ИНСТРУКЦИИ ДЛЯ ИИ
# ============================================================

ai_instructions:
  primary_goal: "Использовать документ как справочную основу для анализа аппаратной конфигурации, планирования закупок и проверки совместимости компонентов кластера."

  use_this_document_for:
    - "Проверка заявленной аппаратной конфигурации серверов."
    - "Планирование дисковой архитектуры Ceph."
    - "Проверка сетевых портов, трансиверов и требований к коммутаторам."
    - "Подготовка списка недостающих характеристик."

  do_not_use_this_document_for:
    - "Подтверждение точной модели CPU без дополнительной проверки."
    - "Подтверждение объёма и типа RAM без инвентаризации."
    - "Предположение о наличии NVMe под Ceph WAL/DB."
    - "Выбор коммутатора без проверки совместимости."

  required_context:
    - "Точная модель и количество CPU."
    - "Объём и тип RAM."
    - "Модель и режим работы дискового контроллера."
    - "Наличие NVMe-дисков."
    - "Финальная модель коммутатора."
    - "Фактическая конфигурация каждой из трёх нод."

  ask_before_recommending:
    - "Изменение режима дискового контроллера."
    - "Создание или удаление Ceph OSD."
    - "Изменение сетевой схемы 10GbE."
    - "Закупка трансиверов, DAC-кабелей или коммутаторов."
    - "Изменение дисковой архитектуры кластера."

  response_requirements:
    - "Отделять подтверждённые сведения от пунктов, требующих уточнения."
    - "Не считать примерные значения фактическими характеристиками."
    - "Учитывать, что каждый 7 ТБ диск предназначен для отдельного Ceph OSD."
    - "Предупреждать о риске потери ёмкости при создании локального зеркала."
    - "Проверять совместимость Intel 10GBASE-SR с выбранным коммутатором."
    - "Не повторять действия из dont_repeat."

  confidence_limitations:
    - "Спецификация является неполной и содержит поля, отмеченные как требующие уточнения."
    - "Результаты команд инвентаризации в исходном файле не приведены."
    - "Фактическая совместимость коммутаторов не подтверждена."

key_takeaways:
  - "Кластер состоит из трёх одинаковых Huawei FusionServer 2288H V5."
  - "На каждом сервере два SSD по 480 GB предназначены для зеркала ОС Proxmox."
  - "Каждый 7 ТБ диск должен использоваться как отдельный Ceph OSD без локального зеркала."
  - "Бортовая Intel X722 предоставляет два 10G SFP+ и два 1G RJ45 порта."
  - "Дополнительная Intel X710 в PCIe SLOT 3 предоставляет два 10G SFP+ порта."
  - "Для коммутаторов требуется минимум четыре 10G SFP+ порта, рекомендуется восемь."
  - "Модель CPU, RAM, контроллера, NVMe, PSU и коммутатора необходимо уточнить."

assumptions:
  - "Серверы имеют выделенный порт iBMC для удалённого управления."
  - "NVMe-диски под Ceph WAL/DB могут отсутствовать, но это требует проверки."
  - "Три сервера имеют одинаковую аппаратную конфигурацию."
  - "Системные SSD используются под зеркало ОС Proxmox."

open_questions:
  - "Каковы точная модель и количество CPU?"
  - "Каковы объём и тип оперативной памяти?"
  - "Какова модель дискового контроллера?"
  - "Работает ли контроллер в режиме HBA/JBOD или IT?"
  - "Есть ли NVMe-диски под Ceph WAL/DB?"
  - "Каковы количество и мощность блоков питания?"
  - "Какова финальная модель закупленного коммутатора?"
  - "Каково назначение двух портов Intel X710?"

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
  - "Точная модель и количество CPU."
  - "Объём и тип RAM."
  - "Модель дискового контроллера."
  - "Режим работы дискового контроллера."
  - "Наличие и модель NVMe-дисков."
  - "Количество и мощность PSU."
  - "Финальная модель коммутатора."
  - "Назначение портов Intel X710."
  - "Результаты команд lshw -short и lspci | grep -i eth."

uncertainties:
  - "Фактическая конфигурация серверов не подтверждена результатами инвентаризации."
  - "Не подтверждено наличие NVMe под Ceph WAL/DB."
  - "Не подтверждён режим HBA/JBOD или IT."
  - "Не подтверждена совместимость выбранного коммутатора с Intel 10GBASE-SR."

needs_follow_up: true
follow_up_tasks:
  - task: "Уточнить модель и количество CPU."
    owner: ""
    due_date: ""
    status: "pending"

  - task: "Уточнить объём и тип RAM."
    owner: ""
    due_date: ""
    status: "pending"

  - task: "Проверить наличие NVMe под Ceph WAL/DB."
    owner: ""
    due_date: ""
    status: "pending"

  - task: "Подтвердить режим работы дискового контроллера."
    owner: ""
    due_date: ""
    status: "pending"

  - task: "Зафиксировать финальную модель коммутатора."
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
  review_result: "pending"

change_history:
  - version: "1.0"
    date: "2026-08-30"
    author: "cladkyimaffin-hue"
    changes:
      - "Создана сводная спецификация аппаратного обеспечения."

  - version: "1.0"
    date: "2026-09-02"
    author: "cladkyimaffin-hue"
    changes:
      - "Документ обновлён."

# ============================================================
# 20. ФИНАЛЬНЫЕ ПОЛЯ
# ============================================================

review_notes: |
  Документ является незавершённой спецификацией.
  Перед использованием для закупок, планирования Ceph или проверки
  совместимости необходимо заполнить характеристики CPU, RAM,
  дискового контроллера, NVMe, PSU и коммутатора.

notes: |
  Исходный документ не содержит результатов выполнения команд
  инвентаризации и не подтверждает фактическую конфигурацию всех
  аппаратных компонентов.
---


# 🖥️ Спецификация аппаратного обеспечения (Hardware Specification)

Этот документ содержит сводную информацию о железе кластера Proxmox VE.

## 1. Серверная платформа
- **Модель:** Huawei FusionServer 2288H V5
- **Артикул:** H22H-05-S8AFF / 02311XBK
- **Форм-фактор:** 2U, Rackmount
- **Количество узлов:** 3 одинаковых сервера
- **Шасси:** 8 × 2.5" отсеков под диски (SFF)
- **Процессор (CPU):** `[УТОЧНИТЬ: Модель и количество CPU, например: 2× Intel Xeon Silver 4210]`
- **Оперативная память (RAM):** `[УТОЧНИТЬ: Общий объём и тип, например: 128 ГБ DDR4 ECC]`
- **Контроллер дисков:** `[УТОЧНИТЬ: Модель RAID-контроллера или режим HBA/JBOD. Для Ceph критичен режим JBOD/IT]`
- **Блоки питания (PSU):** `[УТОЧНИТЬ: Количество и мощность, например: 2× 800W с резервированием]`

## 2. Дисковая подсистема (Storage)
- **Системные диски:** 2 × 480 ГБ SSD (используются под зеркало для ОС Proxmox).
- **Диски данных:** 2 × 7 ТБ на каждый сервер (итого 6 × 7 ТБ на кластер).
  - **Архитектура Ceph:** Каждый 7 ТБ диск создаётся как **отдельный OSD**. 
  - ⚠️ **Важно:** Локальное зеркало (RAID1/mdadm/ZFS mirror) из этих дисков **не делается**, чтобы избежать потери 50% ёмкости и двойной репликации.
- **NVMe под Ceph WAL/DB:** `[УТОЧНИТЬ: Наличие и модель NVMe-диска на каждой ноде для метаданных Ceph. Критично для производительности при использовании HDD]`

## 3. Сетевая инфраструктура (Networking)
Каждый сервер имеет **6 физических портов**, разделённых на две группы:

### Бортовая карта (LOM) — Intel X722
| Имя в ОС | Тип порта | Скорость | Разъём | Назначение |
|----------|-----------|----------|--------|------------|
| LOM1 | 10GbE SFP+ | 10 Гбит/с | SFP+ | Ceph Cluster / VM Traffic |
| LOM2 | 10GbE SFP+ | 10 Гбит/с | SFP+ | Ceph Cluster / VM Traffic |
| LOM3 | 1GbE | 1 Гбит/с | RJ45 | Management / Proxmox Web UI |
| LOM4 | 1GbE | 1 Гбит/с | RJ45 | Резерв / iBMC (если не выделен) |

### Дополнительная карта (PCIe SLOT 3) — Intel X710
| Имя в ОС | Тип порта | Скорость | Разъём | Назначение |
|----------|-----------|----------|--------|------------|
| SLOT3 Порт 1 | 10GbE SFP+ | 10 Гбит/с | SFP+ | `[УТОЧНИТЬ назначение]` |
| SLOT3 Порт 2 | 10GbE SFP+ | 10 Гбит/с | SFP+ | `[УТОЧНИТЬ назначение]` |

### Оптика и кабели
- **Трансиверы (SFP+):** Intel `FTLX8571D3BCVIT1` (Finisar FTLX8571D3BCV с Intel-кодировкой).
- **Стандарт:** 10GBASE-SR, dual-rate 1G/10G, 850 нм.
- **Кабели:** Патч-корды CABEUS OM3 LC-LC duplex, 3 м, 50/125 мкм, LSZH (или пассивные DAC-кабели для коротких дистанций).

## 4. Коммутаторы (Switches)
- **Требуемая конфигурация:** Минимум 4 × 10G SFP+ порта на коммутатор (с запасом рекомендуется 8 портов).
- **Финальная модель:** `[УТОЧНИТЬ: Например, MikroTik CRS309-1G-8S+IN или TP-Link TL-SX3008F]`
- **Статус совместимости:** Выбранный коммутатор должен корректно работать с модулями Intel 10GBASE-SR без vendor-lock.

## 5. Управление (Management)
- **Порт iBMC:** Выделенный порт RJ45 `Mgmt` на задней панели для удалённого управления сервером (аналог IPMI/iLO).

---

## 📝 Чек-лист для заполнения (To-Do)
- [ ] Уточнить модель и количество CPU.
- [ ] Уточнить объём и тип оперативной памяти.
- [ ] Проверить наличие NVMe-дисков под Ceph WAL/DB.
- [ ] Подтвердить режим работы дискового контроллера (IT/JBOD).
- [ ] Зафиксировать финальную модель закупленного коммутатора.
