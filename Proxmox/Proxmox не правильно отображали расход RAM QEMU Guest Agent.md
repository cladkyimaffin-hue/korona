---
# ============================================================
# 1. ИДЕНТИФИКАЦИЯ ДОКУМЕНТА
# ============================================================

document_id: "DOC-2026-09-02-001"
title: "Некорректное отображение расхода RAM в Proxmox при использовании QEMU Guest Agent"
slug: "nekorrektnoe-otobrazhenie-rashoda-ram-proxmox-qemu-guest-agent"
document_type: "troubleshooting"
language: "ru"
version: "1.0"
schema_version: "1.0"
status: "completed"
confidentiality: "internal"
priority: "medium"

date_created: 2026-09-02
date_modified: 2026-09-07
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

category: "troubleshooting"
domain: "virtualization"
subdomain: "memory-management"

tags:
  - "Proxmox"
  - "QEMU Guest Agent"
  - "VirtIO"
  - "BalloonService"
  - "Windows Server 2025"
  - "управление памятью"
  - "диагностика"
  - "VM 2002"
  - "AD"

keywords:
  - "Proxmox Memory usage"
  - "QEMU Guest Agent"
  - "VirtIO Balloon Driver"
  - "BalloonService"
  - "Windows Server 2025"
  - "расход RAM"

aliases:
  - "Неправильное отображение расхода RAM в Proxmox"
  - "Proxmox показывает больше 100 процентов памяти"
  - "Корректировка Memory usage через BalloonService"

related_topics:
  - "VirtIO Balloon Driver"
  - "QEMU Guest Agent"
  - "Host memory usage"
  - "Windows Server 2025"
  - "службы Windows"
  - "qm guest cmd"

# ============================================================
# 3. КРАТКОЕ ОПИСАНИЕ
# ============================================================

problem: "Proxmox отображал использование памяти виртуальной машины 2002 выше 100 процентов: 4.36 GiB из 4.00 GiB, несмотря на фактическое использование Windows около 2.43 GiB."

summary: "ВМ 2002 с Windows Server 2025 Datacenter Evaluation использовала около 2.43 GiB RAM из 3.93 GB внутри гостевой ОС, однако Proxmox показывал 4.36 GiB из выделенных 4.00 GiB, или 108.92 процента. QEMU Guest Agent был установлен и отвечал на команды, но показатель Memory usage не изменился. После создания и запуска службы BalloonService с корректным путем к blnsvr.exe Proxmox начал показывать около 2.55 GiB из 4.00 GiB, или 63.70 процента."

ai_summary: "На ВМ 2002 Proxmox некорректно показывал использование памяти выше 100 процентов, хотя Windows фактически использовала около 61.84 процента RAM. QEMU Guest Agent обеспечил связь с гостевой ОС, но для передачи статистики памяти потребовалась служба BalloonService из virtio-win-0.1.302. После запуска BalloonService с путем D:\\Balloon\\2k25\\amd64\\blnsvr.exe показатель Proxmox изменился на 63.70 процента."

business_impact: "Создавалось впечатление переполнения памяти виртуальной машины и возможной нехватки ресурсов, хотя фактической утечки или переполнения RAM внутри Windows не было."

technical_impact: "Некорректно отображался показатель Memory usage в Proxmox для ВМ 2002. Host memory usage оставался выше выделенной памяти из-за потребления процесса QEMU и накладных расходов виртуализации."

user_impact: "Администратор видел значение использования памяти 108.92 процента вместо фактического использования около 61.84 процента внутри Windows."

severity: "medium"
incident_status: "resolved"

# ============================================================
# 4. СИСТЕМА И ОКРУЖЕНИЕ
# ============================================================

environment: "production"
system_role: "Виртуальная машина контроллера домена AD"
system_name: "AD"
hostname: ""
fqdn: ""
asset_id: ""
vm_id: "2002"
cluster: ""
node: "pve01"

operating_system:
  name: "Windows Server"
  version: "2025"
  edition: "Datacenter Evaluation"
  architecture: "x86_64"
  build: "26100"
  language: ""
  timezone: ""

platform:
  name: "Proxmox VE"
  version: "9.2.11"
  node_version: ""
  kernel: ""
  hypervisor: "QEMU/KVM"
  machine_type: "pc-q35-11.0+pve2"
  firmware: "UEFI"

network:
  ip_addresses:
    - ""
  mac_addresses:
    - "BC:24:11:D2:C7:4F"
  vlan: ""
  subnet: ""
  gateway: ""
  dns_servers:
    - ""
  reverse_proxy: ""
  firewall_zone: ""

hardware:
  cpu_model: "x86-64-v2-AES"
  cpu_sockets: "1"
  cpu_cores: "2"
  cpu_threads: ""
  memory_allocated: "4096 MiB"
  memory_type: ""
  storage:
    - type: "Ceph"
      name: "ceph-fast:vm-2002-disk-1"
      size: "100G"
      filesystem: ""
      mount_point: ""

# ============================================================
# 5. КОМПОНЕНТЫ И ВЕРСИИ
# ============================================================

components:
  - name: "QEMU Guest Agent"
    type: "software"
    version: ""
    status_before: "missing"
    status_after: "running"
    configuration: "Служба QEMU-GA установлена из D:\\guest-agent\\qemu-ga-x86_64.msi."

  - name: "VirtIO Balloon Driver"
    type: "driver"
    version: "virtio-win-0.1.302"
    status_before: "installed"
    status_after: "running"
    configuration: "Устройство отображалось как VirtIO Balloon Driver со статусом OK."

  - name: "BalloonService"
    type: "service"
    version: "virtio-win-0.1.302"
    status_before: "missing"
    status_after: "running"
    configuration: "Executable: D:\\Balloon\\2k25\\amd64\\blnsvr.exe; startup type: Automatic."

dependencies:
  - name: "virtio-win ISO"
    version: "0.1.302"
    required: true
    purpose: "Предоставляет QEMU Guest Agent, VirtIO Balloon Driver и blnsvr.exe."

related_files:
  - "Proxmox разобраться в причине заполнения памяти.md"

depends_on:
  - ""

supersedes: ""
superseded_by: ""

# ============================================================
# 6. ВРЕМЕННАЯ ШКАЛА
# ============================================================

timeline:
  detected_at: "2026-09-01"
  reported_at: ""
  investigation_started_at: "2026-09-01"
  mitigation_started_at: ""
  resolved_at: "2026-09-02"
  closed_at: ""

  events:
    - timestamp: "2026-09-01"
      event: "В Proxmox обнаружено отображение Memory usage 4.36 GiB из 4.00 GiB, или 108.92 процента."
      actor: "cladkyimaffin-hue"
      evidence: "Показатель Memory usage в Proxmox для ВМ 2002."

    - timestamp: "2026-09-01"
      event: "В Windows зафиксировано использование 2.43 GB из 3.93 GB, или 61.84 процента."
      actor: "cladkyimaffin-hue"
      evidence: "Вывод PowerShell Get-CimInstance Win32_OperatingSystem."

    - timestamp: "2026-09-01"
      event: "Установлен и запущен QEMU Guest Agent."
      actor: "cladkyimaffin-hue"
      evidence: "Get-Service QEMU-GA показал статус Running."

    - timestamp: "2026-09-01"
      event: "Связь с QEMU Guest Agent подтверждена командой qm guest cmd 2002 get-osinfo."
      actor: "cladkyimaffin-hue"
      evidence: "Команда вернула сведения о Windows Server 2025."

    - timestamp: "2026-09-02"
      event: "Создана и запущена служба BalloonService с корректным путем к blnsvr.exe."
      actor: "cladkyimaffin-hue"
      evidence: "Get-Service -Name BalloonService показал статус Running."

    - timestamp: "2026-09-02"
      event: "Memory usage в Proxmox изменился до 2.55 GiB из 4.00 GiB, или 63.70 процента."
      actor: "cladkyimaffin-hue"
      evidence: "Зафиксированный результат после запуска BalloonService."

last_incident: 2026-09-01
incident_duration: ""
recurrence_count: 0
recurrence_pattern: ""

# ============================================================
# 7. СИМПТОМЫ И ФАКТИЧЕСКИЕ НАБЛЮДЕНИЯ
# ============================================================

symptoms:
  - "Proxmox отображал Memory usage 4.36 GiB из 4.00 GiB."
  - "Процент использования памяти отображался выше 100 процентов."
  - "Windows фактически использовала около 2.43 GB RAM."
  - "QEMU Guest Agent первоначально отсутствовал."
  - "После установки QEMU Guest Agent показатель Memory usage не изменился."
  - "Служба BalloonService отсутствовала."
  - "Служба BalloonService с путем D:\\balloon\\blnsvr.exe не запускалась."

observed_behavior:
  - metric: "Memory usage в Proxmox до исправления"
    value_before: "4.36"
    value_after: "2.55"
    expected_value: ""
    unit: "GiB из 4.00 GiB"
    source: "Proxmox"
    timestamp: ""

  - metric: "Displayed usage до исправления"
    value_before: "108.92"
    value_after: "63.70"
    expected_value: ""
    unit: "процент"
    source: "Proxmox"
    timestamp: ""

  - metric: "Использование RAM внутри Windows"
    value_before: "2.43"
    value_after: ""
    expected_value: ""
    unit: "GB"
    source: "PowerShell"
    timestamp: ""

  - metric: "Usage внутри Windows"
    value_before: "61.84"
    value_after: ""
    expected_value: ""
    unit: "процент"
    source: "PowerShell"
    timestamp: ""

  - metric: "Host memory usage"
    value_before: "4.36"
    value_after: "4.36"
    expected_value: ""
    unit: "GiB"
    source: "Proxmox"
    timestamp: ""

expected_behavior:
  - "Proxmox должен отображать фактическое использование памяти гостевой ОС."
  - "Показатель Memory usage не должен превышать 100 процентов без соответствующего фактического расхода памяти внутри Windows."
  - "Служба BalloonService должна быть запущена при использовании соответствующего VirtIO Balloon Driver."

actual_behavior:
  - "Proxmox отображал Host memory usage вместо корректной статистики использования RAM гостевой ОС."
  - "QEMU Guest Agent работал, но сам по себе не исправил Memory usage."
  - "После запуска BalloonService Proxmox начал отображать значение, близкое к фактическому расходу памяти Windows."

affected_services:
  - name: "Proxmox Memory usage metrics"
    impact: "Показатель использования памяти был некорректным."
    availability: "degraded"

  - name: "QEMU Guest Agent"
    impact: "Изначально отсутствовал; после установки отвечал на команды."
    availability: "available"

  - name: "BalloonService"
    impact: "Изначально отсутствовала; после создания и запуска передала статистику памяти."
    availability: "available"

# ============================================================
# 8. ПРОБЛЕМА, РЕШЕНИЕ И ПРИЧИНА
# ============================================================

problem_statement: |
  На виртуальной машине 2002 с именем AD, работающей в Proxmox VE 9.2.11
  на узле pve01, интерфейс Proxmox отображал Memory usage 4.36 GiB
  из выделенных 4.00 GiB, или 108.92 процента. При этом внутри Windows
  Server 2025 Datacenter Evaluation использовалось около 2.43 GB из 3.93 GB,
  или 61.84 процента. Требовалось определить, является ли превышение
  реальной проблемой памяти и восстановить корректное отображение метрики.

solution: |
  Внутри Windows Server 2025 был установлен QEMU Guest Agent из ISO
  virtio-win-0.1.302, после чего служба QEMU-GA была запущена.
  Работоспособность канала связи подтверждена командами qm guest cmd 2002 ping
  и qm guest cmd 2002 get-osinfo. Поскольку после установки агента значение
  Memory usage не изменилось, была создана служба BalloonService.
  Первоначальный путь D:\balloon\blnsvr.exe оказался неверным. После поиска
  файла служба была пересоздана с путем D:\Balloon\2k25\amd64\blnsvr.exe,
  настроена на автоматический запуск и запущена. После этого Proxmox начал
  отображать 2.55 GiB из 4.00 GiB, или 63.70 процента.

root_cause: |
  QEMU Guest Agent первоначально отсутствовал, а после его установки
  и подтверждения связи не была запущена служба BalloonService,
  необходимая в данной конфигурации для передачи статистики памяти
  через VirtIO Balloon. Поэтому Proxmox отображал потребление процесса
  QEMU на хосте вместе с накладными расходами виртуализации.
  Дополнительной причиной неудачного запуска службы был неправильный
  путь D:\balloon\blnsvr.exe вместо D:\Balloon\2k25\amd64\blnsvr.exe.

contributing_factors:
  - "QEMU Guest Agent не был установлен в первоначальной конфигурации."
  - "Работающий QEMU Guest Agent ошибочно рассматривался как достаточное условие для корректной метрики памяти."
  - "Служба BalloonService отсутствовала."
  - "Использовался путь D:\\balloon\\blnsvr.exe, в котором отсутствовал каталог версии Windows и архитектуры."
  - "Host memory usage интерпретировался как фактическое использование памяти внутри Windows."

trigger:
  type: "configuration_change"
  description: "Диагностика отображения расхода памяти виртуальной машины 2002 в Proxmox."

resolution_confidence: "confirmed"
evidence_level: "verified"

# ============================================================
# 9. ДИАГНОСТИКА
# ============================================================

diagnostic_method: |
  Сравнивались показатели памяти в Proxmox и внутри Windows.
  Дополнительно проверялись конфигурация ВМ, наличие и состояние QEMU Guest Agent,
  наличие VirtIO Balloon Driver, доступность канала qm guest cmd и расположение
  исполняемого файла blnsvr.exe на подключенном ISO virtio-win.

diagnostic_steps:
  - step: 1
    action: "Проверить службу QEMU Guest Agent внутри Windows."
    command: "Get-Service -Name QEMU-GA"
    expected_result: "Служба найдена и имеет статус Running."
    actual_result: "Первоначально служба не найдена."
    conclusion: "QEMU Guest Agent отсутствовал."
    status: "completed"
    evidence: "Get-Service сообщил NoServiceFoundForGivenName."

  - step: 2
    action: "Проверить VirtIO Balloon Driver."
    command: "Get-PnpDevice | Where-Object {$_.Class -eq \"System\" -or $_.FriendlyName -like \"*Balloon*\"} | Format-Table Status, Class, FriendlyName, DeviceID"
    expected_result: "VirtIO Balloon Driver присутствует со статусом OK."
    actual_result: "VirtIO Balloon Driver присутствовал со статусом OK."
    conclusion: "Драйвер установлен и работает."
    status: "completed"
    evidence: "Вывод Get-PnpDevice."

  - step: 3
    action: "Измерить фактическое использование памяти внутри Windows."
    command: "Get-CimInstance Win32_OperatingSystem | Select-Object TotalVisibleMemorySize, FreePhysicalMemory | ForEach-Object { [PSCustomObject]@{ 'Total RAM (GB)' = [math]::Round($_.TotalVisibleMemorySize / 1MB, 2); 'Free RAM (GB)' = [math]::Round($_.FreePhysicalMemory / 1MB, 2); 'Used RAM (GB)' = [math]::Round( ($_.TotalVisibleMemorySize - $_.FreePhysicalMemory) / 1MB, 2 ); 'Usage %' = [math]::Round( ($_.TotalVisibleMemorySize - $_.FreePhysicalMemory) / $_.TotalVisibleMemorySize * 100, 2 ) } } | Format-Table"
    expected_result: "Получить фактический расход RAM гостевой ОС."
    actual_result: "Total RAM: 3.93 GB; Used RAM: 2.43 GB; Usage: 61.84%."
    conclusion: "Реального использования 108.92% внутри Windows не обнаружено."
    status: "completed"
    evidence: "Вывод PowerShell."

  - step: 4
    action: "Проверить конфигурацию ВМ на узле Proxmox."
    command: "qm config 2002"
    expected_result: "Проверить memory, agent, machine и подключенный virtio-win ISO."
    actual_result: "agent: 1; memory: 4096; machine: pc-q35-11.0+pve2; ide0: local:iso/virtio-win.iso."
    conclusion: "QEMU Guest Agent включен в конфигурации, но его служба отсутствовала внутри гостя."
    status: "completed"
    evidence: "Вывод qm config 2002."

  - step: 5
    action: "Определить букву диска с virtio-win ISO."
    command: "Get-WmiObject Win32_CDROMDrive | Select-Object Drive, VolumeName"
    expected_result: "Определить букву диска с томом virtio-win."
    actual_result: "D: virtio-win-0.1.302."
    conclusion: "ISO доступен на диске D:."
    status: "completed"
    evidence: "Вывод Get-WmiObject Win32_CDROMDrive."

  - step: 6
    action: "Установить QEMU Guest Agent."
    command: "Start-Process msiexec.exe -ArgumentList '/i D:\\guest-agent\\qemu-ga-x86_64.msi /qn /norestart' -Wait"
    expected_result: "Служба QEMU-GA установлена."
    actual_result: "Get-Service QEMU-GA показал статус Running."
    conclusion: "QEMU Guest Agent установлен и запущен."
    status: "completed"
    evidence: "Вывод Get-Service QEMU-GA."

  - step: 7
    action: "Проверить канал связи с QEMU Guest Agent."
    command: "qm guest cmd 2002 get-osinfo"
    expected_result: "Получить сведения об операционной системе в JSON."
    actual_result: "Получен JSON с данными Windows Server 2025."
    conclusion: "Канал связи между Proxmox и агентом работает."
    status: "completed"
    evidence: "Вывод qm guest cmd 2002 get-osinfo."

  - step: 8
    action: "Проверить наличие службы BalloonService."
    command: "Get-Service -Name \"*balloon*\""
    expected_result: "Служба BalloonService найдена и запущена."
    actual_result: "Служба не найдена."
    conclusion: "BalloonService отсутствовала."
    status: "completed"
    evidence: "Пустой вывод Get-Service."

  - step: 9
    action: "Проверить запуск службы с первоначальным путем."
    command: "Start-Process sc.exe -ArgumentList \"create BalloonService binPath= `\"D:\\balloon\\blnsvr.exe`\" start= auto\" -Wait"
    expected_result: "Служба запускается."
    actual_result: "Служба создана, но Start-Service завершился ошибкой."
    conclusion: "Путь к исполняемому файлу неверен или файл отсутствует."
    status: "failed"
    evidence: "Ошибка Start-Service и статус Stopped."

  - step: 10
    action: "Найти точное расположение blnsvr.exe."
    command: "Get-ChildItem -Path D:\\ -Recurse -Filter 'blnsvr.exe' -ErrorAction SilentlyContinue | Select-Object FullName"
    expected_result: "Получить полный путь к исполняемому файлу для Windows Server 2025 amd64."
    actual_result: "Найден файл D:\\Balloon\\2k25\\amd64\\blnsvr.exe."
    conclusion: "Использован корректный путь для Windows Server 2025 x64."
    status: "completed"
    evidence: "Вывод Get-ChildItem."

  - step: 11
    action: "Пересоздать и запустить BalloonService."
    command: "sc.exe delete BalloonService; sc.exe create BalloonService binPath= \"D:\\Balloon\\2k25\\amd64\\blnsvr.exe\" start= auto; Start-Service -Name BalloonService"
    expected_result: "Служба создана и запущена."
    actual_result: "Get-Service показал Running."
    conclusion: "BalloonService работает."
    status: "completed"
    evidence: "Вывод Get-Service -Name BalloonService."

checks_performed:
  - "Проверена конфигурация ВМ командой qm config 2002."
  - "Проверено наличие и состояние службы QEMU-GA."
  - "Проверен VirtIO Balloon Driver в диспетчере устройств."
  - "Сравнены показатели памяти внутри Windows и в Proxmox."
  - "Проверена связь через qm guest cmd 2002 ping."
  - "Проверена связь через qm guest cmd 2002 get-osinfo."
  - "Проверено наличие BalloonService."
  - "Проверено расположение blnsvr.exe на virtio-win ISO."
  - "Проверено состояние BalloonService после запуска."

logs_examined:
  - path: ""
    source: ""
    time_range: ""
    relevant_entries: ""

metrics_examined:
  - name: "Memory usage"
    source: "Proxmox"
    unit: "GiB и процент"
    collection_method: "Интерфейс Proxmox"
    result: "Изменилось с 4.36 GiB и 108.92% до 2.55 GiB и 63.70%."

  - name: "Использование памяти внутри Windows"
    source: "PowerShell Win32_OperatingSystem"
    unit: "GB и процент"
    collection_method: "Get-CimInstance"
    result: "2.43 GB и 61.84%."

# ============================================================
# 10. ГИПОТЕЗЫ
# ============================================================

hypotheses:
  - id: "H1"
    description: "В Windows отсутствует QEMU Guest Agent."
    status: "confirmed"
    verification_method: "Get-Service -Name QEMU-GA."
    evidence_for:
      - "Служба первоначально не была найдена."
    evidence_against: []
    conclusion: "Гипотеза подтверждена как один из факторов, но не объясняет сохранение некорректной метрики после установки агента."

  - id: "H2"
    description: "VirtIO Balloon Driver отсутствует или не работает."
    status: "rejected"
    verification_method: "Проверка Get-PnpDevice."
    evidence_for: []
    evidence_against:
      - "VirtIO Balloon Driver присутствовал со статусом OK."
    conclusion: "Гипотеза отвергнута."

  - id: "H3"
    description: "В Windows действительно используется более 100 процентов выделенной памяти."
    status: "rejected"
    verification_method: "Сравнение с показателями Win32_OperatingSystem."
    evidence_for: []
    evidence_against:
      - "Windows использовала 2.43 GB из 3.93 GB, или 61.84 процента."
    conclusion: "Реального переполнения памяти Windows не подтверждено."

  - id: "H4"
    description: "Proxmox отображает Host memory usage с накладными расходами процесса QEMU."
    status: "confirmed"
    verification_method: "Сравнение показателей Proxmox и Windows до запуска BalloonService."
    evidence_for:
      - "Proxmox показывал 4.36 GiB при выделенных 4.00 GiB."
      - "Windows показывала использование 2.43 GB."
    evidence_against: []
    conclusion: "Гипотеза подтверждена."

  - id: "H5"
    description: "BalloonService отсутствует, поэтому статистика памяти не передаётся корректно."
    status: "confirmed"
    verification_method: "Проверка службы, создание службы и сравнение показателя после запуска."
    evidence_for:
      - "Служба BalloonService первоначально отсутствовала."
      - "После запуска показатель изменился до 2.55 GiB и 63.70 процента."
    evidence_against: []
    conclusion: "Гипотеза подтверждена."

  - id: "H6"
    description: "Служба BalloonService не запускается из-за неверного пути к blnsvr.exe."
    status: "confirmed"
    verification_method: "Поиск blnsvr.exe на диске D: и пересоздание службы."
    evidence_for:
      - "Путь D:\\balloon\\blnsvr.exe не позволил запустить службу."
      - "Корректный файл найден по пути D:\\Balloon\\2k25\\amd64\\blnsvr.exe."
    evidence_against: []
    conclusion: "Гипотеза подтверждена."

# ============================================================
# 11. ПРОВЕРЕННЫЕ И ОТВЕРГНУТЫЕ РЕШЕНИЯ
# ============================================================

tested_solutions:
  - action: "Установить QEMU Guest Agent из D:\\guest-agent\\qemu-ga-x86_64.msi."
    result: "Служба QEMU-GA установлена и запущена; qm guest cmd 2002 get-osinfo вернул данные."
    status: "partially_successful"
    reason: "Установлена связь с гостевой ОС, но показатель Memory usage не исправился."

  - action: "Проверить VirtIO Balloon Driver."
    result: "Драйвер найден со статусом OK."
    status: "neutral"
    reason: "Проверка подтвердила наличие драйвера, но не устранила проблему."

  - action: "Создать BalloonService с путем D:\\balloon\\blnsvr.exe."
    result: "Служба создалась, но не запустилась."
    status: "failed"
    reason: "Исполняемый файл находится во вложенной папке версии Windows и архитектуры."

  - action: "Найти blnsvr.exe рекурсивным поиском на диске D:."
    result: "Найден путь D:\\Balloon\\2k25\\amd64\\blnsvr.exe."
    status: "successful"
    reason: "Получен корректный путь для Windows Server 2025 x64."

  - action: "Пересоздать BalloonService с путем D:\\Balloon\\2k25\\amd64\\blnsvr.exe."
    result: "Служба запущена; Memory usage в Proxmox изменился до 63.70 процента."
    status: "successful"
    reason: "Корректный executable path позволил службе передавать статистику памяти."

rejected_solutions:
  - action: "Считать Host memory usage фактическим использованием RAM внутри Windows."
    reason_rejected: "Показатель включает потребление процесса QEMU и накладные расходы виртуализации."
    risk: "Можно ошибочно диагностировать утечку памяти или нехватку RAM."

  - action: "Считать установку QEMU Guest Agent достаточной для корректной метрики памяти."
    reason_rejected: "После установки и запуска агента показатель Memory usage не изменился."
    risk: "Можно остановить диагностику до проверки BalloonService."

  - action: "Создать BalloonService с путем D:\\balloon\\blnsvr.exe."
    reason_rejected: "По указанному пути файл отсутствует."
    risk: "Служба будет создана, но не запустится."

  - action: "Создать BalloonService с путем для другой версии Windows или архитектуры."
    reason_rejected: "В ISO присутствуют отдельные каталоги для версий Windows и архитектур."
    risk: "Служба может не запуститься или работать некорректно."

  - action: "Использовать qm guest info 2002."
    reason_rejected: "В установленной версии Proxmox команда отсутствует."
    risk: "Диагностика завершится ошибкой unknown command."

dont_repeat:
  - "Не считать Host memory usage в Proxmox фактическим использованием памяти внутри Windows."
  - "Не считать отсутствие QEMU-GA единственной причиной после проверки, что QEMU Guest Agent установлен, запущен и отвечает на qm guest cmd."
  - "Не создавать BalloonService с путем D:\\balloon\\blnsvr.exe."
  - "Не создавать BalloonService с путем от другой версии Windows или другой архитектуры."
  - "Не диагностировать утечку памяти без сравнения показателей Windows и Proxmox."
  - "Не использовать команду qm guest info 2002 в версии Proxmox, где она отсутствует."

# ============================================================
# 12. КОМАНДЫ И КОНФИГУРАЦИЯ
# ============================================================

commands: |
  # На узле Proxmox
  qm config 2002
  qm guest cmd 2002 ping
  qm guest cmd 2002 get-osinfo

  # В Windows
  Get-Service -Name QEMU-GA
  Get-PnpDevice | Where-Object {$_.Class -eq "System" -or $_.FriendlyName -like "*Balloon*"} | Format-Table Status, Class, FriendlyName, DeviceID
  Get-WmiObject Win32_CDROMDrive | Select-Object Drive, VolumeName
  Get-Service -Name "*balloon*"
  Get-ChildItem -Path D:\ -Recurse -Filter 'blnsvr.exe' -ErrorAction SilentlyContinue | Select-Object FullName
  sc.exe delete BalloonService
  sc.exe create BalloonService binPath= "D:\Balloon\2k25\amd64\blnsvr.exe" start= auto
  Start-Service -Name BalloonService
  Get-Service -Name BalloonService

  # Установка QEMU Guest Agent
  Start-Process msiexec.exe -ArgumentList '/i D:\guest-agent\qemu-ga-x86_64.msi /qn /norestart' -Wait

commands_by_system:
  proxmox: |
    qm config 2002
    qm guest cmd 2002 ping
    qm guest cmd 2002 get-osinfo

  windows_powershell: |
    Get-Service -Name QEMU-GA
    Get-PnpDevice | Where-Object {$_.Class -eq "System" -or $_.FriendlyName -like "*Balloon*"} | Format-Table Status, Class, FriendlyName, DeviceID
    Get-WmiObject Win32_CDROMDrive | Select-Object Drive, VolumeName
    Get-Service -Name "*balloon*"
    Get-ChildItem -Path D:\ -Recurse -Filter 'blnsvr.exe' -ErrorAction SilentlyContinue | Select-Object FullName
    Start-Process msiexec.exe -ArgumentList '/i D:\guest-agent\qemu-ga-x86_64.msi /qn /norestart' -Wait
    sc.exe delete BalloonService
    sc.exe create BalloonService binPath= "D:\Balloon\2k25\amd64\blnsvr.exe" start= auto
    Start-Service -Name BalloonService
    Get-Service -Name BalloonService

  linux_shell: |
    -

command_safety:
  requires_administrator: true
  requires_reboot: false
  causes_downtime: false
  modifies_data: false
  modifies_configuration: true
  reversible: true

config_snippets:
  main_configuration: |
    agent: 1
    memory: 4096
    machine: pc-q35-11.0+pve2
    name: AD
    ostype: win11
    numa: 0
    ide0: local:iso/virtio-win.iso,media=cdrom
    scsi0: ceph-fast:vm-2002-disk-1,iothread=1,size=100G,ssd=1

  service_configuration: |
    Service name: BalloonService
    Executable: 'D:\Balloon\2k25\amd64\blnsvr.exe'
    Startup type: Automatic
    Final status: Running

  before_change: |
    QEMU-GA: отсутствует
    BalloonService: отсутствует
    Proxmox Memory usage: 4.36 GiB of 4.00 GiB
    Displayed usage: 108.92%

  after_change: |
    QEMU-GA: Running
    BalloonService: Running
    Proxmox Memory usage: 2.55 GiB of 4.00 GiB
    Displayed usage: 63.70%

configuration_changes:
  - parameter: "QEMU Guest Agent"
    old_value: "Отсутствует"
    new_value: "Установлен и запущен"
    reason: "Обеспечить канал связи между Proxmox и гостевой ОС."
    reversible: true

  - parameter: "BalloonService"
    old_value: "Отсутствует"
    new_value: "Automatic; D:\\Balloon\\2k25\\amd64\\blnsvr.exe"
    reason: "Передавать статистику использования памяти через VirtIO Balloon."
    reversible: true

# ============================================================
# 13. ИЗМЕНЕНИЯ И ОТКАТ
# ============================================================

changes_applied:
  - change: "Установлен QEMU Guest Agent."
    operator: "cladkyimaffin-hue"
    timestamp: ""
    target: "ВМ 2002, Windows Server 2025"
    backup_created: false
    change_reference: ""

  - change: "Создана служба BalloonService с корректным путем к blnsvr.exe."
    operator: "cladkyimaffin-hue"
    timestamp: ""
    target: "ВМ 2002, Windows Server 2025"
    backup_created: false
    change_reference: ""

  - change: "Служба BalloonService настроена на автоматический запуск и запущена."
    operator: "cladkyimaffin-hue"
    timestamp: ""
    target: "ВМ 2002, Windows Server 2025"
    backup_created: false
    change_reference: ""

rollback_available: true
rollback_plan: |
  В PowerShell от имени администратора удалить службу BalloonService.
  При необходимости удалить QEMU Guest Agent штатным способом Windows.
  Перед откатом проверить, что удаление служб не требуется для других
  диагностических или эксплуатационных задач.

rollback_commands: |
  sc.exe delete BalloonService

rollback_conditions:
  - "BalloonService не запускается после проверки корректного пути и архитектуры."
  - "После изменения появляются ошибки службы или ухудшается работа ВМ."
  - "Требуется удалить компонент, установленный только для диагностики."

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
  - "Служба QEMU-GA имеет статус Running."
  - "Команда qm guest cmd 2002 get-osinfo возвращает данные."
  - "Служба BalloonService имеет статус Running."
  - "BalloonService использует путь D:\\Balloon\\2k25\\amd64\\blnsvr.exe."
  - "Proxmox отображает Memory usage около фактического использования Windows."
  - "Показатель Memory usage не отображает ошибочное значение выше 100 процентов."

validation_steps:
  - step: 1
    action: "Проверить службу QEMU Guest Agent."
    expected_result: "Running"
    actual_result: "Running"
    status: "completed"

  - step: 2
    action: "Проверить канал связи с QEMU Guest Agent."
    expected_result: "Команда возвращает сведения о гостевой ОС."
    actual_result: "Возвращён JSON Windows Server 2025."
    status: "completed"

  - step: 3
    action: "Проверить службу BalloonService."
    expected_result: "Running"
    actual_result: "Running"
    status: "completed"

  - step: 4
    action: "Проверить Memory usage в Proxmox."
    expected_result: "Значение близко к фактическому использованию Windows."
    actual_result: "2.55 GiB из 4.00 GiB, или 63.70 процента."
    status: "completed"

before_after_comparison:
  - metric: "Proxmox Memory usage"
    before: "4.36 GiB из 4.00 GiB"
    after: "2.55 GiB из 4.00 GiB"
    expected: "Корректное значение использования памяти гостевой ОС"
    improvement: "Показатель приведён к значению, близкому к фактическому."
    source: "Proxmox"

  - metric: "Displayed usage"
    before: "108.92%"
    after: "63.70%"
    expected: "Значение без ошибочного превышения 100%"
    improvement: "Устранено некорректное отображение выше 100%."
    source: "Proxmox"

  - metric: "QEMU Guest Agent"
    before: "Отсутствует"
    after: "Running"
    expected: "Running"
    improvement: "Установлен и запущен."
    source: "Get-Service QEMU-GA"

  - metric: "BalloonService"
    before: "Отсутствует или Stopped"
    after: "Running"
    expected: "Running"
    improvement: "Служба создана, настроена и запущена."
    source: "Get-Service -Name BalloonService"

post_change_observation_period: ""
post_change_status: "stable"
regression_risk: "medium"
known_side_effects:
  - "Host memory usage может оставаться выше выделенной памяти из-за накладных расходов процесса QEMU."
  - "Показатель Host memory usage не следует использовать как замену Memory usage гостевой ОС."

# ============================================================
# 15. БЕЗОПАСНОСТЬ И РИСКИ
# ============================================================

security_impact: "none"
security_considerations:
  - "Команды создания и удаления службы требуют прав администратора."
  - "Перед удалением службы следует проверить, что она не используется другими задачами."
  - "Не следует использовать исполняемый файл BalloonService от другой версии Windows или архитектуры."

data_loss_risk: "low"
downtime_required: false
estimated_downtime: ""
requires_maintenance_window: false

dangerous_operations:
  - "Не удалять QEMU Guest Agent или BalloonService без проверки их роли."
  - "Не использовать sc.exe delete для службы без подтверждения имени службы."
  - "Не создавать службу с неподтвержденным путем к исполняемому файлу."

secrets_present: false
secret_locations:
  - ""

# ============================================================
# 16. ДОКАЗАТЕЛЬСТВА И ИСТОЧНИКИ
# ============================================================

evidence:
  - type: "metric"
    description: "До исправления Proxmox показывал 4.36 GiB из 4.00 GiB и 108.92%."
    location: ""
    collected_at: ""
    collected_by: "cladkyimaffin-hue"
    integrity_check: ""

  - type: "command_output"
    description: "PowerShell показал 3.93 GB общей RAM, 2.43 GB использованной RAM и 61.84% использования."
    location: ""
    collected_at: ""
    collected_by: "cladkyimaffin-hue"
    integrity_check: ""

  - type: "command_output"
    description: "qm config 2002 показал agent: 1 и memory: 4096."
    location: ""
    collected_at: ""
    collected_by: "cladkyimaffin-hue"
    integrity_check: ""

  - type: "command_output"
    description: "qm guest cmd 2002 get-osinfo вернул сведения о Windows Server 2025."
    location: ""
    collected_at: ""
    collected_by: "cladkyimaffin-hue"
    integrity_check: ""

  - type: "command_output"
    description: "После запуска BalloonService Get-Service показал статус Running."
    location: ""
    collected_at: ""
    collected_by: "cladkyimaffin-hue"
    integrity_check: ""

  - type: "metric"
    description: "После запуска BalloonService Proxmox показывал 2.55 GiB из 4.00 GiB и 63.70%."
    location: ""
    collected_at: ""
    collected_by: "cladkyimaffin-hue"
    integrity_check: ""

source_urls:
  - "https://github.com/cladkyimaffin-hue/korona/blob/903a086a1bc40a67415e8b0e02ac1d65fff970de/Proxmox/Proxmox%20%D0%BD%D0%B5%20%D0%BF%D1%80%D0%B0%D0%B2%D0%B8%D0%BB%D1%8C%D0%BD%D0%BE%20%D0%BE%D1%82%D0%BE%D0%B1%D1%80%D0%B0%D0%B6%D0%B0%D0%BB%D0%B8%20%D1%80%D0%B0%D1%81%D1%85%D0%BE%D0%B4%20RAM%20QEMU%20Guest%20Agent.md"

urls:
  - "https://github.com/cladkyimaffin-hue/korona/blob/659b8918e91e830a7d0154dd1ed21c6cf192f676/Proxmox/Proxmox%20%D0%BD%D0%B5%20%D0%BF%D1%80%D0%B0%D0%B2%D0%B8%D0%BB%D1%8C%D0%BD%D0%BE%20%D0%BE%D1%82%D0%BE%D0%B1%D1%80%D0%B0%D0%B6%D0%B0%D0%BB%D0%B8%20%D1%80%D0%B0%D1%81%D1%85%D0%BE%D0%B4%20RAM%20QEMU%20Guest%20Agent.md"
  - "https://github.com/cladkyimaffin-hue/korona/tree/5a00f31944967a795e4953e9f6c8bcad57701627/Proxmox"

references:
  - title: "Предыдущая версия документа о некорректном отображении расхода RAM"
    url: "https://github.com/cladkyimaffin-hue/korona/blob/659b8918e91e830a7d0154dd1ed21c6cf192f676/Proxmox/Proxmox%20%D0%BD%D0%B5%20%D0%BF%D1%80%D0%B0%D0%B2%D0%B8%D0%BB%D1%8C%D0%BD%D0%BE%20%D0%BE%D1%82%D0%BE%D0%B1%D1%80%D0%B0%D0%B6%D0%B0%D0%BB%D0%B8%20%D1%80%D0%B0%D1%81%D1%85%D0%BE%D0%B4%20RAM%20QEMU%20Guest%20Agent.md"
    type: "internal_note"
    accessed_at: "2026-09-07"
    relevance: "Связанная версия документа с теми же результатами диагностики."

github:
  repository: "cladkyimaffin-hue/korona"
  file_path: "Proxmox/Proxmox не правильно отображали расход RAM QEMU Guest Agent.md"
  branch: "903a086a1bc40a67415e8b0e02ac1d65fff970de"
  commit: "903a086a1bc40a67415e8b0e02ac1d65fff970de"
  issue: ""
  pull_request: ""
  related_commits:
    - "659b8918e91e830a7d0154dd1ed21c6cf192f676"

# ============================================================
# 17. ИНСТРУКЦИИ ДЛЯ ИИ
# ============================================================

ai_instructions:
  primary_goal: "Диагностировать некорректное отображение расхода памяти ВМ Windows в Proxmox и проверить работу QEMU Guest Agent, VirtIO Balloon Driver и BalloonService."

  use_this_document_for:
    - "Диагностика отображения Memory usage выше 100 процентов в Proxmox."
    - "Проверка связи с QEMU Guest Agent."
    - "Проверка состояния VirtIO Balloon Driver."
    - "Настройка BalloonService для Windows Server 2025."
    - "Сравнение показателей памяти внутри Windows и в Proxmox."

  do_not_use_this_document_for:
    - "Автоматическое утверждение, что Host memory usage равен реальному использованию RAM гостевой ОС."
    - "Установку службы с путем от другой версии Windows или архитектуры."
    - "Диагностику других версий Windows без проверки расположения blnsvr.exe."
    - "Использование команды qm guest info в версии Proxmox, где она отсутствует."
    - "Диагностику реальной утечки памяти без измерения внутри гостевой ОС."

  required_context:
    - "Версия Proxmox VE."
    - "VMID и имя виртуальной машины."
    - "Версия и редакция Windows."
    - "Выделенный объем памяти ВМ."
    - "Версия virtio-win."
    - "Наличие и буква диска с virtio-win ISO."
    - "Точный путь к blnsvr.exe."

  ask_before_recommending:
    - "Удаление службы QEMU-GA."
    - "Удаление службы BalloonService."
    - "Изменение конфигурации ВМ."
    - "Перезагрузка или остановка production-ВМ."
    - "Использование пути к исполняемому файлу, который не проверен командой поиска."

  response_requirements:
    - "Сначала сравнить показатели памяти внутри Windows и в Proxmox."
    - "Отделить Memory usage от Host memory usage."
    - "Проверить QEMU Guest Agent и связь через доступную команду qm guest cmd."
    - "Проверить VirtIO Balloon Driver."
    - "Проверить наличие и состояние BalloonService."
    - "Проверить путь и архитектуру blnsvr.exe."
    - "Проверить показатель Memory usage после изменения."
    - "Не повторять действия из dont_repeat."

  confidence_limitations:
    - "Результат подтверждён для ВМ 2002 с Windows Server 2025 Datacenter Evaluation x86_64."
    - "Результат подтверждён для Proxmox VE 9.2.11 и virtio-win-0.1.302."
    - "Результат для ВМ 2001 в рамках этого файла не подтверждён."
    - "Показатель Host memory usage после исправления остаётся выше выделенной памяти."

key_takeaways:
  - "Работающий QEMU Guest Agent подтверждает связь с гостевой ОС, но сама по себе не гарантирует корректный Memory usage."
  - "В данной конфигурации для передачи статистики памяти требуется запущенная служба BalloonService."
  - "Для Windows Server 2025 x64 использован путь D:\\Balloon\\2k25\\amd64\\blnsvr.exe."
  - "Показатель изменился с 4.36 GiB и 108.92% до 2.55 GiB и 63.70% после запуска BalloonService."
  - "Host memory usage может оставаться выше выделенной памяти из-за накладных расходов процесса QEMU."
  - "Результаты внутри Windows нужно сравнивать с Memory usage, а не автоматически с Host memory usage."

assumptions:
  - "ВМ 2002 использует Windows Server 2025 Datacenter Evaluation x86_64."
  - "ВМ 2002 имеет VMID 2002 и выделенные 4096 MiB RAM."
  - "VirtIO ISO virtio-win-0.1.302 подключен к гостевой ОС как диск D:."
  - "Для Windows Server 2025 используется файл D:\\Balloon\\2k25\\amd64\\blnsvr.exe."
  - "Показатель 63.70% из 4.00 GiB зафиксирован после запуска BalloonService."
  - "Результат для ВМ 2001 не подтвержден в рамках данного файла."

open_questions:
  - "Какой точный пакет или версия QEMU Guest Agent была установлена?"
  - "Какой точный статус Memory usage сохраняется после перезагрузки ВМ?"
  - "Какой результат настройки BalloonService получен на ВМ 2001?"
  - "Требуется ли оставить VirtIO ISO подключенным после установки компонентов?"

# ============================================================
# 18. КАЧЕСТВО ДАННЫХ
# ============================================================

data_quality:
  completeness: "partial"
  accuracy: "verified"
  freshness: "current"
  reproducibility: "partially_reproducible"
  source_quality: "primary"

missing_data:
  - "Точные время и часовой пояс событий не указаны."
  - "Не указана точная версия Proxmox VE в metadata исходного файла, кроме значения 9.2.11."
  - "Не указана точная версия QEMU Guest Agent."
  - "Не указаны IP-адрес, FQDN и сетевые параметры ВМ 2002."
  - "Не приведён полный вывод команды qm guest cmd 2002 ping."
  - "Не указан результат после перезагрузки ВМ."
  - "Не указан результат аналогичных изменений для ВМ 2001."
  - "Не указано, был ли создан backup перед изменением служб."

uncertainties:
  - "В исходном документе не указано, является ли BalloonService официальным компонентом virtio-win или способом ручного запуска blnsvr.exe."
  - "Не указан точный механизм, которым Proxmox получает показатель Memory usage после запуска BalloonService."
  - "Не указано, сохраняется ли корректный показатель после отключения virtio-win ISO."
  - "Не указано, требуется ли перезагрузка Windows после установки или изменения служб."

needs_follow_up: true
follow_up_tasks:
  - task: "Проверить состояние QEMU-GA и BalloonService после перезагрузки ВМ 2002"
    owner: ""
    due_date: ""
    status: "pending"

  - task: "Проверить, сохраняется ли показатель Memory usage около 63.70% после отключения virtio-win ISO"
    owner: ""
    due_date: ""
    status: "pending"

  - task: "Отдельно проверить ВМ 2001 и не переносить на неё результат без подтверждения"
    owner: ""
    due_date: ""
    status: "pending"

# ============================================================
# 19. АУДИТ ДОКУМЕНТА
# ============================================================

audit:
  created_by: "cladkyimaffin-hue"
  created_at: "2026-09-02"
  last_modified_by: "cladkyimaffin-hue"
  last_modified_at: "2026-09-07"
  reviewed_by: "cladkyimaffin-hue"
  reviewed_at: ""
  review_result: "approved"

change_history:
  - version: "1.0"
    date: "2026-09-07"
    author: "cladkyimaffin-hue"
    changes:
      - "Зафиксирована диагностика некорректного отображения RAM для ВМ 2002."
      - "Добавлены результаты установки QEMU Guest Agent."
      - "Добавлены результаты создания и запуска BalloonService."
      - "Зафиксирован корректный путь D:\\Balloon\\2k25\\amd64\\blnsvr.exe."
      - "Зафиксировано изменение Memory usage до 63.70%."

# ============================================================
# 20. ФИНАЛЬНЫЕ ПОЛЯ
# ============================================================

review_notes: |
  Результат подтверждён для ВМ 2002 с Windows Server 2025 Datacenter Evaluation,
  Proxmox VE 9.2.11 и virtio-win-0.1.302. При повторении процедуры необходимо
  сначала проверить версию Windows, архитектуру и фактическое расположение
  blnsvr.exe. Host memory usage следует отделять от Memory usage гостевой ОС.

notes: |
  ВМ 2001 упоминается в ходе диагностики, однако результат настройки для неё
  в исходном файле не подтверждён. В исходном материале также указано,
  что на ВМ 2001 был отмонтирован VirtIO ISO, но это не является результатом
  исправления для ВМ 2002.
---


### USER
https://github.com/cladkyimaffin-hue/korona/tree/5a00f31944967a795e4953e9f6c8bcad57701627/Proxmox
разобраться в причине заполнения памяти

### ASSISTANT
Понял задачу. Вижу две виртуальные машины в Proxmox с переполнением памяти:
- **VM 2001 (win-1c)**: 100.44% (160.70 GiB из 160.00 GiB)
- **VM 2002 (AD)**: 108.92% (4.36 GiB из 4.00 GiB)

**Шаг 1 — Анализ репозитория GitHub**

Предлагаю начать с изучения содержимого репозитория, который вы указали. Мне нужно понять:
- Какую конфигурацию Proxmox вы используете
- Есть ли там скрипты мониторинга или управления памятью
- Какие настройки виртуальных машин заданы

Разрешите мне изучить структуру и содержимое репозитория по ссылке: https://github.com/cladkyimaffin-hue/korona/tree/5a00f31944967a795e4953e9f6c8bcad57701627/Proxmox

**Вопрос:** 
1. Это ваша конфигурация Proxmox?
2. Когда началась проблема с памятью?
3. Guest Agent не запущен на обеих ВМ (вижу в интерфейсе) — это намеренно?

Жду вашего подтверждения для перехода к следующему шагу.

### USER
1- да
2 - незнаю
3 - надо проверить
разрешаю изучить структуру и содержимое репозитория по ссылке:

### ASSISTANT
**Шаг 1 — Изучение структуры и содержимого репозитория Proxmox**

**Действие:** 
Я запрашиваю содержимое указанной вами директории репозитория, чтобы проанализировать конфигурационные файлы, скрипты или документацию, связанные с настройкой виртуальных машин (особенно VM 2001 и VM 2002) и управлением памятью.


**Шаг 1 — Проверка состояния службы QEMU Guest Agent внутри гостевой ОС**

Для точного отображения использования памяти в интерфейсе Proxmox и корректной работы механизма динамического управления памятью (VirtIO Balloon), внутри гостевой ОС (Windows) должна быть установлена и запущена служба QEMU Guest Agent. 

Если эта служба не работает или драйвер Balloon отсутствует, Proxmox не получает актуальные данные от гостевой системы и часто показывает некорректные значения (например, 100% или более 100%), даже если реальная нагрузка ниже.

**Действие:**
Пожалуйста, подключитесь к виртуальной машине **2001 (win-1c)** (через RDP или консоль Proxmox) и выполните следующую команду в PowerShell от имени администратора:

```powershell
Get-Service QEMU-GA
```

**Протокол (обновлённый):**
- **Задача:** Разобраться в причине заполнения памяти на ВМ 2001 (160 ГБ, 100.44%) и ВМ 2002 (4 ГБ, 108.92%).
- **Рабочая гипотеза:** Некорректное отображение или утечка памяти из-за отсутствия/остановки службы QEMU Guest Agent или драйвера VirtIO Balloon в гостевой ОС.
- **Текущий этап:** Шаг 1. Проверка статуса службы QEMU Guest Agent на ВМ 2001.

**Вопрос:**
1. Выполните указанную команду и пришлите её вывод (статус службы). Если служба отсутствует, остановлена или выдает ошибку, это станет первым ключевым фактом для анализа.

Жду вывода команды или вашего подтверждения («ок», «готово») для перехода к следующему шагу.

### USER
Get-Service : Не удается найти службу с именем службы "QEMU-GA".
строка:1 знак:1
+ Get-Service QEMU-GA
+ ~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : ObjectNotFound: (QEMU-GA:String) [Get-Service], ServiceCommandException
    + FullyQualifiedErrorId : NoServiceFoundForGivenName,Microsoft.PowerShell.Commands.GetServiceCommand

PS C:\WINDOWS\system32>


### ASSISTANT
**Шаг 2 — Проверка наличия драйвера VirtIO Balloon в диспетчере устройств**

Служба QEMU Guest Agent не найдена. Это критично — без неё Proxmox не получает корректные данные об использовании памяти из гостевой ОС, что объясняет отображение 100.44% (фактическое значение может быть ниже).

Для работы механизма управления памятью в Windows должны быть:
1. Драйвер VirtIO Balloon (отображается в диспетчере устройств)
2. Служба QEMU Guest Agent (которой сейчас нет)

**Действие:**
Пожалуйста, выполните в PowerShell команду для проверки наличия драйвера Balloon:

```powershell
Get-PnpDevice | Where-Object {$_.Class -eq "System" -or $_.FriendlyName -like "*Balloon*"} | Format-Table Status, Class, FriendlyName, DeviceID
```

**Протокол (обновлённый):**
- **Задача:** Разобраться в причине заполнения памяти на ВМ 2001 (160 ГБ, 100.44%) и ВМ 2002 (4 ГБ, 108.92%).
- **Рабочая гипотеза:** Некорректное отображение памяти из-за отсутствия QEMU Guest Agent и/или драйвера VirtIO Balloon.
- **Текущий этап:** Шаг 2. Проверка наличия драйвера VirtIO Balloon в системе.
- **Зафиксировано:** Служба QEMU-GA отсутствует на ВМ 2001.

**Вопрос:**
1. Выполните команду и пришлите вывод. Если драйвер не найден или имеет статус "Error"/"Disabled", это потребует установки драйверов с ISO virtio-win.

Жду вывода команды.

### USER
Get-PnpDevice | Where-Object {$_.Class -eq "System" -or $_.FriendlyName -like "*Balloon*"} | Format-Table Status, Class, FriendlyName, DeviceID

Status Class  FriendlyName                                            DeviceID
------ -----  ------------                                            --------
OK     System Мост PCI–PCI                                            PCI\VEN_1B36&DEV_000C&SUBSYS_00001B36&REV_00\3...
OK     System Мост PCI–PCI                                            PCI\VEN_1B36&DEV_000C&SUBSYS_00001B36&REV_00\3...
OK     System Мост PCI–PCI                                            PCI\VEN_1B36&DEV_000C&SUBSYS_00001B36&REV_00\3...
OK     System Мост PCI–PCI                                            PCI\VEN_1B36&DEV_000C&SUBSYS_00001B36&REV_00\3...
OK     System Расширенная шина ввода-вывода                           ACPI\PNP0A06\CPU_HOTPLUG_RESOURCES
OK     System CMOS системы и часы реального времени                   ACPI\PNP0B00\4&22F5829E&0
OK     System Диспетчер томов                                         ROOT\VOLMGR\0000
OK     System Базовый видеодрайвер (Майкрософт)                       ROOT\BASICDISPLAY\0000
OK     System Системная плата                                         ACPI\PNP0C01\2&DABA3FF&0
OK     System UMBus перечислитель                                     UMB\UMB\1&841921D&0&TERMINPUT_BUS
OK     System Контроллер High Definition Audio (Microsoft)            PCI\VEN_8086&DEV_293E&SUBSYS_11001AF4&REV_03\3...
OK     System Перечислитель композитной шины                          ROOT\COMPOSITEBUS\0000
OK     System Перечислитель виртуальных дисков (Майкрософт)           ROOT\VDRVROOT\0000
OK     System Расширенная шина ввода-вывода                           ACPI\PNP0A06\GPE0_RESOURCES
OK     System Расширенная шина ввода-вывода                           ACPI\PNP0A06\PCI_HOTPLUG_RESOURCES
OK     System Устройство контейнера процессора ACPI                   ACPI\ACPI0010\2&DABA3FF&0
OK     System VirtIO Serial Driver                                    PCI\VEN_1AF4&DEV_1003&SUBSYS_00031AF4&REV_00\5...
OK     System UMBus перечислитель корневой шины                       ROOT\UMBUS\0000
OK     System Расширенная шина ввода-вывода                           ACPI\PNP0A06\SMI_RESOURCES
OK     System PCI Express Root Complex                                ACPI\PNP0A08\0
OK     System Microsoft ACPI-совместимая система                      ACPI_HAL\PNP0C08\0
OK     System Базовый драйвер отрисовки (Майкрософт)                  ROOT\BASICRENDER\0000
OK     System Мост PCI–PCI                                            PCI\VEN_1B36&DEV_0001&SUBSYS_00000000&REV_00\4...
OK     System Фиксированная функциональная кнопка ACPI                ACPI\FIXEDBUTTON\2&DABA3FF&0
OK     System Контроллер CPU–IO                                       PCI\VEN_8086&DEV_29C0&SUBSYS_11001AF4&REV_00\3...
OK     System Контроллер шины SM                                      PCI\VEN_8086&DEV_2930&SUBSYS_11001AF4&REV_02\3...
OK     System Мост PCI–PCI                                            PCI\VEN_1B36&DEV_0001&SUBSYS_00000000&REV_00\4...
OK     System Мост PCI–PCI                                            PCI\VEN_1B36&DEV_0001&SUBSYS_00000000&REV_00\4...
OK     System Перечислитель виртуальных сетевых адаптеров NDIS        ROOT\NDISVIRTUALBUS\0000
OK     System Счетчик создания Microsoft Hyper-V                      ACPI\QEMUVGID\2&DABA3FF&0
OK     System Контроллер LPC                                          PCI\VEN_8086&DEV_2918&SUBSYS_11001AF4&REV_02\3...
OK     System Драйвер Microsoft System Management BIOS                ROOT\MSSMBIOS\0000
OK     System Мост PCI–PCI                                            PCI\VEN_1B36&DEV_0001&SUBSYS_00000000&REV_00\4...
OK     System VirtIO Balloon Driver                                   PCI\VEN_1AF4&DEV_1002&SUBSYS_00051AF4&REV_00\5...
OK     System Перечислитель программных устройств Plug and Play       ROOT\SYSTEM\0000
OK     System Шина перенаправителя устройств удаленных рабочих столов ROOT\RDPBUS\0000
OK     System Мост PCI–PCI                                            PCI\VEN_8086&DEV_244E&SUBSYS_00000000&REV_92\3...


### ASSISTANT
**Шаг 3 — Проверка реального использования памяти внутри гостевой ОС**

Драйвер **VirtIO Balloon Driver** установлен и работает (статус OK). Это хорошо. Однако служба **QEMU Guest Agent** отсутствует, и это ключевая проблема.

**Что это значит:**
Когда QEMU Guest Agent не работает, Proxmox не может получить данные об использовании памяти изнутри Windows. Поэтому в интерфейсе Proxmox отображается **"Host memory usage"** (сколько памяти выделено ВМ на уровне гипервизора), а не реальное использование памяти внутри гостевой ОС. Значение 100.44% (160.70 GiB из 160.00 GiB) показывает, что ВМ выделено 160 ГБ на уровне хоста, но это не означает, что Windows реально использует всю эту память.

**Действие:**
Чтобы понять, есть ли реальная проблема с памятью или это только неправильное отображение в Proxmox, нужно проверить фактическое использование памяти внутри Windows.

Выполните в PowerShell команду:

```powershell
Get-CimInstance Win32_OperatingSystem | Select-Object TotalVisibleMemorySize, FreePhysicalMemory | ForEach-Object { [PSCustomObject]@{ 'Total RAM (GB)' = [math]::Round($_.TotalVisibleMemorySize/1MB, 2); 'Free RAM (GB)' = [math]::Round($_.FreePhysicalMemory/1MB, 2); 'Used RAM (GB)' = [math]::Round(($_.TotalVisibleMemorySize - $_.FreePhysicalMemory)/1MB, 2); 'Usage %' = [math]::Round(($_.TotalVisibleMemorySize - $_.FreePhysicalMemory)/$_.TotalVisibleMemorySize*100, 2) } } | Format-Table
```

**Протокол (обновлённый):**
- **Задача:** Разобраться в причине заполнения памяти на ВМ 2001 (160 ГБ, 100.44%) и ВМ 2002 (4 ГБ, 108.92%).
- **Рабочая гипотеза:** Proxmox показывает "Host memory usage" вместо реального использования памяти внутри гостя из-за отсутствия QEMU Guest Agent.
- **Текущий этап:** Шаг 3. Проверка реального использования памяти внутри Windows на ВМ 2001.
- **Зафиксировано:** Драйвер VirtIO Balloon установлен и работает (OK). Служба QEMU Guest Agent отсутствует.

**Вопрос:**
1. Выполните команду и пришлите вывод. Это покажет, сколько памяти реально использует Windows, и мы сможем определить, есть ли реальная утечка или проблема только в отображении Proxmox.

Жду вывода команды.

### USER
Total RAM (GB) Free RAM (GB) Used RAM (GB) Usage %
-------------- ------------- ------------- -------
          3,93           1,5          2,44   61,91


### ASSISTANT
**Шаг 4 — Проверка ограничений памяти в загрузчике Windows**

Мы обнаружили критическое расхождение:
- **Proxmox** выделил виртуальной машине **160 ГБ** оперативной памяти (и хост фактически использует 160.70 GiB, что и показывает 100.44%).
- **Windows** внутри этой же машины видит и использует только **~4 ГБ** (3.93 ГБ).

Из-за этого дисбаланса драйвер VirtIO Balloon не может корректно синхронизировать состояние, а Proxmox отображает 100%+ заполнение, так как хост-система держит выделенные 160 ГБ в памяти процесса QEMU, хотя гость их не использует.

Чтобы понять, почему Windows игнорирует выделенные 160 ГБ и видит только 4 ГБ, необходимо проверить настройки загрузчика Windows. Часто при клонировании шаблонов или миграции там может быть жестко прописан лимит памяти.

**Действие:**
Пожалуйста, выполните в PowerShell (от имени администратора) следующую команду:

```powershell
bcdedit /enum
```

**Протокол (обновлённый):**
- **Задача:** Разобраться в причине отображения 100.44% памяти в Proxmox для ВМ 2001.
- **Ключевое наблюдение:** Proxmox выделил 160 ГБ, но гостевая ОС Windows видит только ~4 ГБ. Хост-машина фактически потребляет 160 ГБ под процесс ВМ.
- **Текущий этап:** Шаг 4. Проверка конфигурации загрузчика Windows на наличие искусственных ограничений памяти (`maxmem`).

**Вопрос:**
1. Выполните команду `bcdedit /enum` и пришлите её полный вывод. Нас особенно интересуют параметры `memory` или `maxmem` в секции загрузчика Windows Boot Loader.

Жду вывода команды.

### USER
Расматриваем эту машину

### ASSISTANT
**Шаг 1 — Проверка службы QEMU Guest Agent на ВМ 2002 (AD)**

На скриншоте вижу проблему: **Memory usage 108.88% (4.36 GiB of 4.00 GiB)**. Это аналогичная ситуация с первой ВМ — хост потребляет больше памяти, чем выделено конфигурацией.

Для диагностики подключитесь к ВМ **2002 (AD)** (через RDP или консоль) и выполните команду в PowerShell:

```powershell
Get-Service QEMU-GA
```

**Протокол (обновлённый):**
- **Задача:** Разобраться в причине заполнения памяти на ВМ 2002 (AD).
- **Наблюдение:** Proxmox показывает 108.88% (4.36 GiB из 4.00 GiB). Host memory usage = 4.36 GiB.
- **Текущий этап:** Шаг 1. Проверка наличия службы QEMU Guest Agent на ВМ 2002.

**Вопрос:**
1. Выполните команду и пришлите вывод (или напишите «ок», если служба не найдена, как и на первой ВМ).

Жду вашего подтверждения.

### USER
PS C:\WINDOWS\system32> Get-Service QEMU-GA
Get-Service : Не удается найти службу с именем службы "QEMU-GA".
строка:1 знак:1
+ Get-Service QEMU-GA
+ ~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : ObjectNotFound: (QEMU-GA:String) [Get-Service], ServiceCommandException
    + FullyQualifiedErrorId : NoServiceFoundForGivenName,Microsoft.PowerShell.Commands.GetServiceCommand


### ASSISTANT
**Шаг 2 — Проверка реального использования памяти внутри ВМ 2002 (AD)**

Служба QEMU Guest Agent не найдена на ВМ 2002 (AD), как и на ВМ 2001. Это подтверждает причину некорректного отображения: Proxmox показывает фактическое потребление памяти процессом QEMU на хосте, а не реальное использование внутри Windows.

Чтобы понять, есть ли реальная проблема с памятью или только отображение, нужно проверить фактическое использование памяти внутри гостевой ОС.

**Действие:**
Выполните в PowerShell (на ВМ 2002) команду:

```powershell
Get-CimInstance Win32_OperatingSystem | Select-Object TotalVisibleMemorySize, FreePhysicalMemory | ForEach-Object { [PSCustomObject]@{ 'Total RAM (GB)' = [math]::Round($_.TotalVisibleMemorySize/1MB, 2); 'Free RAM (GB)' = [math]::Round($_.FreePhysicalMemory/1MB, 2); 'Used RAM (GB)' = [math]::Round(($_.TotalVisibleMemorySize - $_.FreePhysicalMemory)/1MB, 2); 'Usage %' = [math]::Round(($_.TotalVisibleMemorySize - $_.FreePhysicalMemory)/$_.TotalVisibleMemorySize*100, 2) } } | Format-Table
```

**Протокол (обновлённый):**
- **Задача:** Разобраться в причине заполнения памяти на ВМ 2002 (AD).
- **Наблюдение:** Proxmox показывает 108.88% (4.36 GiB из 4.00 GiB). Host memory usage = 4.36 GiB.
- **Зафиксировано:** Служба QEMU Guest Agent отсутствует на ВМ 2002 (как и на ВМ 2001).
- **Текущий этап:** Шаг 2. Проверка реального использования памяти внутри Windows на ВМ 2002.

**Вопрос:**
1. Выполните команду и пришлите вывод. Это покажет, сколько памяти реально использует Windows, и мы сможем определить, есть ли реальная утечка или проблема только в отображении Proxmox.

Жду вывода команды.

### USER
Total RAM (GB) Free RAM (GB) Used RAM (GB) Usage %
-------------- ------------- ------------- -------
          3,93           1,5          2,43   61,84



### ASSISTANT
**Шаг 3 — Проверка конфигурации памяти ВМ 2002 на уровне гипервизора**

**Объяснение:**
Внутри Windows всё в порядке: используется 2.43 ГБ из 3.93 ГБ (61.84%), что является абсолютно нормальным показателем для контроллера домена. 

Значение 108.88% (4.36 GiB) в интерфейсе Proxmox означает, что процесс QEMU на хост-сервере фактически потребляет 4.36 ГБ оперативной памяти. Поскольку QEMU Guest Agent не установлен, Proxmox не может получить точные данные изнутри гостевой ОС и вместо этого показывает потребление памяти хост-процессом. Это значение включает в себя не только память, выделенную гостю, но и накладные расходы гипервизора: видеопамять (VRAM), эмуляцию устройств (ACPI, PCI), буферы и сам процесс QEMU. 

Чтобы точно определить, почему потребление хоста превышает базовый лимит в 4 ГБ, необходимо проверить параметры `memory` и `balloon` в конфигурации этой виртуальной машины.

**Действие:**
Пожалуйста, выполните в консоли узла Proxmox (хоста, не внутри виртуальной машины) следующую команду:

```bash
qm config 2002
```

**Протокол (обновлённый):**
- **Задача:** Разобраться в причине отображения 108.88% памяти в Proxmox для ВМ 2002 (AD).
- **Зафиксировано:** 
  1. Служба QEMU Guest Agent отсутствует.
  2. Реальное использование памяти внутри Windows: 2.43 ГБ из 3.93 ГБ (61.84%). Утечки памяти внутри гостевой ОС нет.
  3. Proxmox показывает потребление хост-процессом (4.36 GiB), что включает накладные расходы гипервизора.
- **Текущий этап:** Шаг 3. Анализ конфигурации ВМ 2002 на уровне гипервизора для выявления параметров выделения памяти и ballooning.

**Вопрос:**
1. Выполните команду `qm config 2002` на хосте Proxmox и пришлите её полный вывод. 

Жду вывода команды.

### USER
permitted by applicable law.
root@pve01:~# qm config 2002
agent: 1
bios: ovmf
boot: order=scsi0;ide2;ide0;net0
cores: 2
cpu: x86-64-v2-AES,flags=-nested-virt;+aes;-amd-ssbd;-hv-evmcs;-ibpb;+md-clear;+pdpe1gb;+spec-ctrl;+ssbd;-amd-no-ssb;-virt-ssbd
efidisk0: ceph-fast:vm-2002-disk-0,efitype=4m,ms-cert=2023k,pre-enrolled-keys=1,size=1M
ide0: local:iso/virtio-win.iso,media=cdrom,size=856810K
ide2: local:iso/ru_windows_server_2025_datecenetr_26100_x64_dvd.iso,media=cdrom,size=7920130K
machine: pc-q35-11.0+pve2
memory: 4096
meta: creation-qemu=11.0.3,ctime=1788696623
name: AD
net0: virtio=BC:24:11:D2:C7:4F,bridge=vmbr0,firewall=1
numa: 0
ostype: win11
scsi0: ceph-fast:vm-2002-disk-1,iothread=1,size=100G,ssd=1
scsihw: virtio-scsi-single
smbios1: uuid=a2620c32-386c-4a89-8207-8d05dc2823dc
sockets: 1
tpmstate0: ceph-fast:vm-2002-disk-2,size=4M,version=v2.0
vmgenid: fd9cb479-b8fc-4b90-a2d7-682e3919ea85
root@pve01:~# 

### ASSISTANT
**Шаг 4 — Анализ конфигурации ВМ 2002 на уровне гипервизора**

Конфигурация получена. Ключевые параметры:

- `memory: 4096` — выделено 4 ГБ RAM ✓
- `agent: 1` — QEMU Guest Agent **включен в конфигурации на уровне гипервизора** ✓
- `numa: 0` — NUMA отключен (нормально для 4 ГБ)
- `scsi0: ...size=100G,ssd=1` — диск 100 ГБ ✓

**Критическое наблюдение:**

В конфигурации ВМ параметр `agent: 1` присутствует, что означает: гипервизор ожидает, что внутри гостевой ОС будет работать служба QEMU Guest Agent. Однако мы уже проверили (Шаг 1) — служба **отсутствует** внутри Windows.

Это и есть **корневая причина** проблемы с отображением памяти:

1. Гипервизор включил механизм ожидания данных от агента.
2. Агент внутри гостя не отвечает (служба не установлена).
3. Proxmox не может получить точные данные об использовании памяти из Windows.
4. Вместо этого Proxmox показывает **фактическое потребление памяти процессом QEMU на хосте**, которое всегда превышает выделенный лимит из-за накладных расходов:
   - Видеопамять (VRAM) для виртуального дисплея
   - Эмуляция устройств (ACPI, PCI, TPM)
   - Буферы и структуры данных самого процесса QEMU
   - Драйвер VirtIO Balloon (резервирует память для динамического управления)

**Реального переполнения памяти нет.** Внутри Windows используется ~2.43 ГБ из 3.93 ГБ (61.84%) — это нормальный показатель.

**Протокол (обновлённый):**
- **Задача:** Разобраться в причине отображения 100%+ памяти в Proxmox для ВМ 2001 и 2002.
- **Найдена причина:** 
  1. Служба QEMU Guest Agent отсутствует внутри обеих ВМ (2001 и 2002).
  2. Параметр `agent: 1` включен в конфигурации на уровне гипервизора.
  3. Proxmox показывает потребление хост-процессом QEMU (с накладными расходами), а не реальное использование внутри гостя.
  4. Реального переполнения нет — внутри Windows используется ~62% RAM.
- **Текущий этап:** Шаг 4. Причина установлена. Требуется решение.

**Вопрос:**
1. Подтверждаете ли вы, что причина найдена (отсутствие QEMU Guest Agent внутри гостя)?
2. Готовы ли перейти к следующему шагу — установке QEMU Guest Agent внутри обеих ВМ для корректного отображения памяти в Proxmox?

Жду вашего подтверждения.

### USER
1 - да
2 - готов

### ASSISTANT
**Шаг 5 — Определение буквы диска с ISO-образом virtio-win на ВМ 2002 (AD)**

Для установки QEMU Guest Agent через консоль (PowerShell) нам необходимо точно знать букву диска, под которой внутри Windows смонтирован образ `virtio-win.iso`.

**Действие:**
Выполните в PowerShell (от имени администратора) на ВМ 2002 следующую команду:

```powershell
Get-WmiObject Win32_CDROMDrive | Select-Object Drive, VolumeName
```

* * *

**Протокол (обновлённый):**
- **Задача:** Установить QEMU Guest Agent внутри гостевых ОС (ВМ 2001 и 2002) для корректного отображения памяти в Proxmox.
- **Причина проблемы:** Отсутствие службы QEMU-GA внутри Windows заставляет Proxmox показывать потребление памяти хост-процессом QEMU (с накладными расходами гипервизора), а не реальное использование гостем.
- **Текущий этап:** Шаг 5. Определение буквы CD/DVD-привода с драйверами на ВМ 2002.
- **Зафиксировано:** Образ `virtio-win.iso` подключен к ВМ на уровне гипервизора (параметр `ide0`).

**Вопрос:**
1. Выполните команду и пришлите вывод (букву диска и название тома), чтобы мы могли сформировать точную команду установки.

Жду вашего подтверждения.

### USER

Drive VolumeName
----- ----------
E:    SSS_X64FREE_RU-RU_DV9
D:    virtio-win-0.1.302


### ASSISTANT
**Шаг 6 — Установка QEMU Guest Agent на ВМ 2002 (AD)**

Образ с драйверами VirtIO смонтирован на диске **D:**. Теперь установим службу QEMU Guest Agent.

**Действие:**
Выполните в PowerShell (от имени администратора) на ВМ 2002 следующую команду:

```powershell
Start-Process msiexec.exe -ArgumentList "/i D:\guest-agent\qemu-ga-x86_64.msi /qn /norestart" -Wait
```

**Пояснение:**
- `/i` — установка MSI-пакета
- `D:\guest-agent\qemu-ga-x86_64.msi` — путь к установщику QEMU Guest Agent для 64-битной Windows
- `/qn` — тихая установка без интерфейса
- `/norestart` — запрет автоматической перезагрузки

* * *

**Протокол (обновлённый):**
- **Задача:** Установить QEMU Guest Agent внутри ВМ 2002 для корректного отображения памяти в Proxmox.
- **Текущий этап:** Шаг 6. Выполнение установки службы QEMU Guest Agent на ВМ 2002 (AD).
- **Зафиксировано:** Диск с драйверами VirtIO: D: (virtio-win-0.1.302).

**Вопрос:**
1. Выполните команду и дождитесь её завершения (команда выполнится и вернёт управление в консоль).
2. Напишите «ок» или пришлите вывод, чтобы подтвердить установку.

Жду вашего подтверждения.

### USER
ок

### ASSISTANT
**Шаг 7 — Проверка статуса службы QEMU Guest Agent на ВМ 2002 (AD)**

После выполнения команды установки необходимо убедиться, что служба QEMU Guest Agent успешно зарегистрирована в системе и запущена.

**Действие:**
Выполните в PowerShell (от имени администратора) на ВМ 2002 следующую команду:

```powershell
Get-Service QEMU-GA
```

* * *

**Протокол (обновлённый):**
- **Задача:** Установить QEMU Guest Agent внутри гостевых ОС (ВМ 2001 и 2002) для корректного отображения памяти в Proxmox.
- **Текущий этап:** Шаг 7. Проверка статуса службы QEMU Guest Agent на ВМ 2002 после установки.
- **Зафиксировано:** Команда установки MSI-пакета выполнена без ошибок.

**Вопрос:**
1. Выполните команду и пришлите её вывод (нас интересует статус `Status` — он должен быть `Running`).

Жду вашего подтверждения.

### USER
ait
PS C:\WINDOWS\system32> Get-Service QEMU-GA

Status   Name               DisplayName
------   ----               -----------
Running  QEMU-GA            QEMU Guest Agent


### ASSISTANT
**Шаг 8 — Проверка отображения памяти в интерфейсе Proxmox для ВМ 2002 (AD)**

Служба QEMU Guest Agent успешно запущена. Теперь гипервизор должен получать корректные данные об использовании памяти напрямую из гостевой ОС Windows, а не измерять потребление процесса QEMU на хосте.

**Действие:**
Откройте веб-интерфейс Proxmox, перейдите на виртуальную машину **2002 (AD)** на вкладку **Summary** и посмотрите на значение **Memory usage**.

* * *

**Протокол (обновлённый):**
- **Задача:** Разобраться в причине заполнения памяти и устранить её.
- **Текущий этап:** Шаг 8. Валидация исправления на ВМ 2002 (AD). Служба QEMU-GA установлена и работает (Status: Running).
- **Зафиксировано:** Ожидается, что интерфейс Proxmox обновит метрику Memory usage и покажет реальное значение (~2.43 GiB из 4.00 GiB, вместо 108.88%).

**Вопрос:**
1. Какое значение Memory usage теперь отображается в интерфейсе Proxmox для ВМ 2002 (AD)?

Жду вашего ответа.

### USER
ничего не изменилось

### ASSISTANT
**Шаг 9 — Проверка связи между Proxmox и QEMU Guest Agent через CLI**

Служба внутри Windows запущена, но интерфейс Proxmox не обновил метрики. Это означает, что гипервизор либо ещё не получил данные от агента, либо канал связи между хостом и гостем не работает корректно.

Необходимо проверить, видит ли Proxmox работающий агент на уровне гипервизора.

**Действие:**
Выполните в консоли узла **pve01** (на хосте Proxmox, не внутри ВМ) следующую команду:

```bash
qm guest cmd 2002 ping
```

**Пояснение:**
Эта команда отправляет тестовый сигнал (ping) через канал virtio-serial напрямую к агенту внутри гостевой ОС. Если агент работает и канал связи активен, команда вернёт ответ. Если агент недоступен — будет ошибка.

* * *

**Протокол (обновлённый):**
- **Задача:** Разобраться в причине отображения 108.92% памяти в Proxmox для ВМ 2002 (AD) после установки QEMU Guest Agent.
- **Наблюдение:** Служба QEMU-GA внутри Windows запущена (Status: Running), но интерфейс Proxmox не обновил метрику Memory usage (по-прежнему 4.36 GiB).
- **Текущий этап:** Шаг 9. Проверка канала связи между хостом Proxmox и гостевым агентом через CLI.

**Вопрос:**
1. Выполните команду `qm guest cmd 2002 ping` на хосте pve01 и пришлите её вывод.

Жду вашего подтверждения.

### USER
пустой вывод

### ASSISTANT
**Шаг 10 — Проверка статуса QEMU Guest Agent через команду info**

Пустой вывод команды `ping` может означать, что агент работает, но канал связи ещё не полностью инициализирован. Проверим статус агента другой командой.

**Действие:**
Выполните в консоли узла **pve01** следующую команду:

```bash
qm guest info 2002
```

**Пояснение:**
Эта команда запрашивает полную информацию от гостевого агента: версию, статус, информацию о файловой системе и сетевых интерфейсах. Если агент работает корректно, мы получим JSON с данными.

* * *

**Протокол (обновлённый):**
- **Задача:** Разобраться в причине отображения 108.92% памяти в Proxmox для ВМ 2002 (AD).
- **Наблюдение:** Служба QEMU-GA внутри Windows запущена, но команда `qm guest cmd 2002 ping` вернула пустой вывод.
- **Текущий этап:** Шаг 10. Проверка полной информации от гостевого агента.

**Вопрос:**
1. Выполните команду `qm guest info 2002` и пришлите вывод (или напишите "пустой вывод", если снова ничего не вернётся).

Жду вашего подтверждения.

### USER
qm guest info 2002
ERROR: unknown command 'qm guest info'
USAGE: qm <COMMAND> [ARGS] [OPTIONS]

       qm cloudinit dump <vmid> <type>
       qm cloudinit pending <vmid>
       qm cloudinit update <vmid>

       qm disk move <vmid> <disk> [<storage>] [OPTIONS]
       qm disk resize <vmid> <disk> <size> [OPTIONS]
       qm disk unlink <vmid> --idlist <string> [OPTIONS]
       qm disk import <vmid> <source> <storage> [OPTIONS]
       qm disk rescan  [OPTIONS]

       qm guest cmd <vmid> <command>
       qm guest exec-status <vmid> <pid>
       qm guest passwd <vmid> <username> [OPTIONS]
       qm guest exec <vmid> [<extra-args>] [OPTIONS]

       qm clone <vmid> <newid> [OPTIONS]
       qm config <vmid> [OPTIONS]
       qm create <vmid> [OPTIONS]
       qm delsnapshot <vmid> <snapname> [OPTIONS]
       qm destroy <vmid> [OPTIONS]
       qm list  [OPTIONS]
       qm listsnapshot <vmid>
       qm migrate <vmid> <target> [OPTIONS]
       qm pending <vmid>
       qm reboot <vmid> [OPTIONS]
       qm reset <vmid> [OPTIONS]
       qm resume <vmid> [OPTIONS]
       qm rollback <vmid> <snapname> [OPTIONS]
       qm sendkey <vmid> <key> [OPTIONS]
       qm set <vmid> [OPTIONS]
       qm shutdown <vmid> [OPTIONS]
       qm snapshot <vmid> <snapname> [OPTIONS]
       qm start <vmid> [OPTIONS]
       qm stop <vmid> [OPTIONS]
       qm suspend <vmid> [OPTIONS]
       qm template <vmid> [OPTIONS]

       qm cleanup <vmid> <clean-shutdown> <guest-requested>
       qm enroll-efi-keys <vmid>
       qm import <vmid> <source> --storage <string> [OPTIONS]
       qm importovf <vmid> <manifest> <storage> [OPTIONS]
       qm monitor <vmid>
       qm mtunnel 
       qm nbdstop <vmid>
       qm remote-migrate <vmid> [<target-vmid>] <target-endpoint> --target-bridge <string> --target-storage <string> [OPTIONS]
       qm showcmd <vmid> [OPTIONS]
       qm status <vmid> [OPTIONS]
       qm terminal <vmid> [OPTIONS]
       qm unlock <vmid>
       qm vncproxy <vmid>
       qm wait <vmid> [OPTIONS]

       qm help [<extra-args>] [OPTIONS]
root@pve01:~# 

### ASSISTANT
**Шаг 11 — Проверка связи с агентом через команду get-osinfo**

Команда `qm guest info` отсутствует в этой версии Proxmox. Используем доступную команду `qm guest cmd` с запросом информации об ОС — она должна вернуть данные, если агент работает.

**Действие:**
Выполните в консоли узла **pve01**:

```bash
qm guest cmd 2002 get-osinfo
```

**Пояснение:**
Эта команда запрашивает у гостевого агента информацию об операционной системе (версия, архитектура, имя хоста). Если агент работает и канал связи активен, вы получите JSON с данными. Если агент недоступен — будет ошибка или пустой вывод.

* * *

**Протокол (обновлённый):**
- **Задача:** Разобраться в причине отображения 108.92% памяти в Proxmox для ВМ 2002 (AD).
- **Наблюдение:** Служба QEMU-GA внутри Windows запущена, но интерфейс Proxmox не обновил метрику Memory usage.
- **Текущий этап:** Шаг 11. Проверка связи с агентом через команду `get-osinfo`.
- **Зафиксировано:** Команда `qm guest info` отсутствует в Proxmox 9.2.11. Доступные команды: `qm guest cmd`, `qm guest exec`.

**Вопрос:**
1. Выполните команду `qm guest cmd 2002 get-osinfo` и пришлите вывод.

Жду вашего подтверждения.

### USER
       qm help [<extra-args>] [OPTIONS]
root@pve01:~# qm guest cmd 2002 get-osinfo
{
   "id" : "mswindows",
   "kernel-release" : "26100",
   "kernel-version" : "10.0",
   "machine" : "x86_64",
   "name" : "Microsoft Windows",
   "pretty-name" : "Windows Server 2025 Datacenter Evaluation",
   "variant" : "server",
   "variant-id" : "server",
   "version" : "Microsoft Windows Server 2025",
   "version-id" : "2025"
}
root@pve01:~# 

### ASSISTANT
**Шаг 12 — Проверка службы BalloonService внутри ВМ 2002**

Команда `get-osinfo` вернула корректный JSON. Это подтверждает, что канал связи между гипервизором и QEMU Guest Agent работает отлично.

**Почему память всё ещё показывает 108%:**
Метрика "Memory usage" в Proxmox для гостевых ОС опирается не на сам Guest Agent, а на статистику драйвера **VirtIO Balloon**. Чтобы этот драйвер передавал данные об использовании памяти гипервизору, внутри Windows должна работать специальная служба `BalloonService` (поставляется вместе с драйверами virtio-win). 

Если эта служба не запущена, Proxmox не получает данные изнутри гостя и в качестве "Memory usage" показывает фактический объем оперативной памяти, который потребляет процесс QEMU на хост-сервере. Этот объем всегда немного превышает выделенный лимит (в вашем случае 4.36 GiB вместо 4.00 GiB) из-за накладных расходов гипервизора (видеопамять, эмуляция устройств, буферы). Это не утечка, а особенность отображения.

**Действие:**
Чтобы Proxmox начал показывать реальное использование памяти (~2.43 GiB), нужно убедиться, что служба балуна запущена. Выполните в PowerShell (от имени администратора) внутри ВМ 2002 следующую команду:

```powershell
Get-Service -Name "*balloon*"
```

* * *

**Протокол (обновлённый):**
- **Задача:** Разобраться в причине отображения 108.92% памяти в Proxmox для ВМ 2002 (AD).
- **Зафиксировано:** 
  1. QEMU Guest Agent установлен, запущен и успешно отвечает на команды хоста (`get-osinfo` вернул данные).
  2. Реальное потребление памяти внутри Windows: ~2.43 GiB.
  3. Значение 108% в Proxmox — это потребление процесса QEMU на хосте (4.36 GiB), так как гостевая статистика не поступает.
- **Текущий этап:** Шаг 12. Проверка статуса службы `BalloonService` внутри гостевой ОС, которая отвечает за передачу метрик памяти.

**Вопрос:**
1. Выполните команду и пришлите её вывод (нас интересует статус `Status` — он должен быть `Running`).

Жду вашего подтверждения.

### USER
пустой вывод

### ASSISTANT
**Шаг 13 — Установка службы BalloonService на ВМ 2002 (AD)**

Служба BalloonService не найдена. Это объясняет, почему Proxmox не получает данные об использовании памяти из гостевой ОС, несмотря на работающий QEMU Guest Agent.

Служба BalloonService должна быть установлена отдельно — она входит в комплект драйверов virtio-win и отвечает за передачу метрик памяти гипервизору.

**Действие:**
Выполните в PowerShell (от имени администратора) внутри ВМ 2002 следующую команду для установки службы Balloon:

```powershell
Start-Process sc.exe -ArgumentList "create BalloonService binPath= `"D:\balloon\blnsvr.exe`" start= auto" -Wait
```

**Пояснение:**
- `sc.exe create` — создание службы Windows
- `BalloonService` — имя службы
- `binPath= "D:\balloon\blnsvr.exe"` — путь к исполняемому файлу службы (драйверы virtio-win содержат утилиту blnsvr.exe в папке balloon)
- `start= auto` — автоматический запуск службы при загрузке

* * *

**Протокол (обновлённый):**
- **Задача:** Разобраться в причине отображения 108.92% памяти в Proxmox для ВМ 2002 (AD).
- **Зафиксировано:** 
  1. QEMU Guest Agent работает ✓
  2. Драйвер VirtIO Balloon установлен ✓
  3. Служба BalloonService **отсутствует** (пустой вывод команды Get-Service)
- **Текущий этап:** Шаг 13. Установка службы BalloonService для передачи метрик памяти гипервизору.

**Вопрос:**
1. Выполните команду и напишите «ок» (или пришлите вывод, если появится ошибка).

Жду вашего подтверждения.

### USER
ок

### ASSISTANT
**Шаг 14 — Запуск службы BalloonService и проверка её статуса**

В предыдущем шаге мы создали службу `BalloonService`. Теперь её необходимо запустить, чтобы драйвер VirtIO Balloon начал передавать метрики использования памяти гипервизору Proxmox.

**Действие:**
Выполните в PowerShell (от имени администратора) внутри ВМ 2002 следующие две команды:

```powershell
Start-Service -Name BalloonService
Get-Service -Name BalloonService
```

**Пояснение:**
1. `Start-Service` — запускает только что созданную службу.
2. `Get-Service` — проверяет её текущий статус. Мы ожидаем увидеть статус `Running`.

* * *

**Протокол (обновлённый):**
- **Задача:** Разобраться в причине отображения 108.92% памяти в Proxmox для ВМ 2002 (AD).
- **Зафиксировано:** 
  1. QEMU Guest Agent работает и отвечает на запросы хоста.
  2. Служба `BalloonService` успешно создана через `sc.exe` с путем к `D:\balloon\blnsvr.exe`.
- **Текущий этап:** Шаг 14. Запуск службы `BalloonService` внутри гостевой ОС.

**Вопрос:**
1. Выполните обе команды и пришлите вывод команды `Get-Service` (нас интересует статус `Status`).

Жду вашего подтверждения.

### USER

PS C:\WINDOWS\system32> Get-Service -Name "*balloon*"
PS C:\WINDOWS\system32> Start-Process sc.exe -ArgumentList "create BalloonService binPath= `"D:\balloon\blnsvr.exe`" start= auto" -Wait
PS C:\WINDOWS\system32> Start-Service -Name BalloonService
Start-Service : Не удается запустить службу "BalloonService (BalloonService)" из-за следующей ошибки: Не удалось запуст
ить службу BalloonService на компьютере '.'.
строка:1 знак:1
+ Start-Service -Name BalloonService
+ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : OpenError: (System.ServiceProcess.ServiceController:ServiceController) [Start-Service],
   ServiceCommandException
    + FullyQualifiedErrorId : CouldNotStartService,Microsoft.PowerShell.Commands.StartServiceCommand

PS C:\WINDOWS\system32> Get-Service -Name BalloonService

Status   Name               DisplayName
------   ----               -----------
Stopped  BalloonService     BalloonService


PS C:\WINDOWS\system32>

### ASSISTANT
**Шаг 15 — Проверка существования файла blnsvr.exe и корректности пути**

Служба создана, но не запускается. Это типичная ситуация — путь к исполняемому файлу может быть неверным, либо файл требует дополнительных параметров. В ISO virtio-win исполняемый файл `blnsvr.exe` находится не в корне папки `balloon`, а во вложенной папке с версией Windows.

**Действие:**
Выполните в PowerShell (от имени администратора) следующую команду для поиска точного расположения `blnsvr.exe`:

```powershell
Get-ChildItem -Path D:\ -Recurse -Filter "blnsvr.exe" -ErrorAction SilentlyContinue | Select-Object FullName
```

**Пояснение:**
Эта команда рекурсивно ищет файл `blnsvr.exe` на диске D: (где смонтирован ISO virtio-win) и выводит его полный путь. Это позволит нам точно указать правильный путь при пересоздании службы.

* * *

**Протокол (обновлённый):**
- **Задача:** Разобраться в причине отображения 108.92% памяти в Proxmox для ВМ 2002 (AD).
- **Зафиксировано:** 
  1. QEMU Guest Agent работает и отвечает на запросы хоста.
  2. Служба `BalloonService` создана, но не запускается (Status: Stopped).
  3. Вероятная причина: неверный путь к `blnsvr.exe` в аргументах службы.
- **Текущий этап:** Шаг 15. Поиск точного расположения файла `blnsvr.exe` на ISO virtio-win.

**Вопрос:**
1. Выполните команду и пришлите полный путь к найденному файлу `blnsvr.exe`.

Жду вашего подтверждения.

### USER

FullName
--------
D:\Balloon\2k12\amd64\blnsvr.exe
D:\Balloon\2k12R2\amd64\blnsvr.exe
D:\Balloon\2k16\amd64\blnsvr.exe
D:\Balloon\2k19\amd64\blnsvr.exe
D:\Balloon\2k22\amd64\blnsvr.exe
D:\Balloon\2k25\ARM64\blnsvr.exe
D:\Balloon\2k25\amd64\blnsvr.exe
D:\Balloon\2k3\amd64\blnsvr.exe
D:\Balloon\2k3\x86\blnsvr.exe
D:\Balloon\2k8\amd64\blnsvr.exe
D:\Balloon\2k8\x86\blnsvr.exe
D:\Balloon\2k8R2\amd64\blnsvr.exe
D:\Balloon\w10\ARM64\blnsvr.exe
D:\Balloon\w10\amd64\blnsvr.exe
D:\Balloon\w10\x86\blnsvr.exe
D:\Balloon\w11\ARM64\blnsvr.exe
D:\Balloon\w11\amd64\blnsvr.exe
D:\Balloon\w7\amd64\blnsvr.exe
D:\Balloon\w7\x86\blnsvr.exe
D:\Balloon\w8\amd64\blnsvr.exe
D:\Balloon\w8\x86\blnsvr.exe
D:\Balloon\w8.1\amd64\blnsvr.exe
D:\Balloon\w8.1\x86\blnsvr.exe
D:\Balloon\xp\amd64\blnsvr.exe
D:\Balloon\xp\x86\blnsvr.exe


PS C:\WINDOWS\system32>


### ASSISTANT
**Шаг 16 — Удаление неправильно созданной службы BalloonService**

Теперь мы знаем точную причину, почему служба не запускалась: мы указали путь `D:\balloon\blnsvr.exe`, но на самом деле файл находится в подпапке `D:\Balloon\2k25\amd64\blnsvr.exe` (так как на ВМ установлена Windows Server 2025).

Сначала нужно удалить старую службу с неверным путём, а затем создать новую с правильным.

**Действие:**
Выполните в PowerShell (от имени администратора) внутри ВМ 2002 следующую команду для удаления старой службы:

```powershell
sc.exe delete BalloonService
```

* * *

**Протокол (обновлённый):**
- **Задача:** Разобраться в причине отображения 108.92% памяти в Proxmox для ВМ 2002 (AD).
- **Зафиксировано:** 
  1. QEMU Guest Agent работает и отвечает на запросы хоста.
  2. Служба `BalloonService` создана, но не запускается из-за неверного пути к `blnsvr.exe`.
  3. Найден правильный путь: `D:\Balloon\2k25\amd64\blnsvr.exe` (для Windows Server 2025 x86_64).
- **Текущий этап:** Шаг 16. Удаление старой службы с неверным путём.

**Вопрос:**
1. Выполните команду и напишите «ок» (или пришлите вывод, если появится ошибка).

Жду вашего подтверждения.

### USER
ок

### ASSISTANT
**Шаг 17 — Создание службы BalloonService с правильным путём**

Теперь создадим службу заново, указав корректный путь к исполняемому файлу для Windows Server 2025 (2k25) на архитектуре amd64.

**Действие:**
Выполните в PowerShell (от имени администратора) внутри ВМ 2002 следующую команду:

```powershell
sc.exe create BalloonService binPath= "D:\Balloon\2k25\amd64\blnsvr.exe" start= auto
```

**Пояснение:**
- `sc.exe create` — создание службы Windows
- `BalloonService` — имя службы
- `binPath= "D:\Balloon\2k25\amd64\blnsvr.exe"` — точный путь к исполняемому файлу для Windows Server 2025 x64
- `start= auto` — автоматический запуск при загрузке системы

* * *

**Протокол (обновлённый):**
- **Задача:** Разобраться в причине отображения 108.92% памяти в Proxmox для ВМ 2002 (AD).
- **Зафиксировано:** 
  1. QEMU Guest Agent работает и отвечает на запросы хоста.
  2. Старая служба `BalloonService` с неверным путём удалена.
  3. Найден правильный путь: `D:\Balloon\2k25\amd64\blnsvr.exe`.
- **Текущий этап:** Шаг 17. Создание службы `BalloonService` с корректным путём.

**Вопрос:**
1. Выполните команду и напишите «ок» (или пришлите вывод, если появится ошибка).

Жду вашего подтверждения.

### USER
32> sc.exe delete BalloonService
[SC] DeleteService: успех
PS C:\WINDOWS\system32> sc.exe create BalloonService binPath= "D:\Balloon\2k25\amd64\blnsvr.exe" start= auto
[SC] CreateService: успех
PS C:\WINDOWS\system32> Start-Service -Name BalloonService
PS C:\WINDOWS\system32> Get-Service -Name BalloonService
На 2001 (win-1c) я отмонтировал VirtIO
Status   Name               DisplayName
------   ----               -----------
Running  BalloonService     BalloonService


PS C:\WINDOWS\system32>

### ASSISTANT
**Шаг 18 — Подтверждение успеха на ВМ 2002 (AD)**

Отлично! Служба **BalloonService** успешно создана и запущена. 

Смотрю на скриншот — **Memory usage** теперь показывает **63.70% (2.55 GiB of 4.00 GiB)** вместо 108.92%! Это корректное значение реального использования памяти внутри Windows.

**Host memory usage** (4.36 GiB) остался прежним — это нормально, так как показывает фактическое потребление процесса QEMU на хосте с учётом накладных расходов гипервизора.

**Проблема с ВМ 2002 (AD) решена!**

* * *

**Протокол (обновлённый):**
- **Задача:** Разобраться в причине отображения 100%+ памяти в Proxmox для ВМ 2001 и 2002.
- **Результат на ВМ 2002 (AD):**
  1. Установлен QEMU Guest Agent ✓
  2. Служба BalloonService создана и запущена ✓
  3. Memory usage теперь показывает корректное значение: 63.70% (2.55 GiB из 4.00 GiB) ✓
- **Текущий этап:** Переход к ВМ 2001 (win-1c).

**Вопрос:**
1. Вы упомянули, что на ВМ 2001 (win-1c) отмонтировали VirtIO ISO. Подтвердите: на ВМ 2001 сейчас нужно также установить QEMU Guest Agent и BalloonService? Если да, начнём с проверки статуса службы QEMU-GA на этой ВМ.

Жду вашего подтверждения.


Метаданные отражают фактический результат диагностики: проблема была не в утечке памяти Windows, а в том, что Proxmox не получал статистику гостевой памяти через BalloonService. Установка QEMU Guest Agent обеспечила связь с гостем, а запуск BalloonService исправил отображение показателя Memory usage.
