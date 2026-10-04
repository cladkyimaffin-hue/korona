### USER
Изучи скрипт и построчно поясни что делает и что выдает
#!/usr/bin/python3
# Лавриненко. Временный пассивный мониторинг ERP 2026.
import datetime as dt,json,os,pathlib,socket,subprocess,time
ROOT=pathlib.Path('/var/log/lavrinenko-erp-2026')
DEADLINE=dt.datetime.fromisoformat('2026-09-23T00:00:00+03:00').timestamp()
if time.time()>=DEADLINE:
 subprocess.run(['systemctl','disable','--now','lavrinenko-erp-2026.timer'],timeout=10)
 raise SystemExit(0)
ROOT.mkdir(mode=0o700,exist_ok=True)
now=dt.datetime.now(dt.timezone.utc)
p=ROOT/('host-'+now.strftime('%Y%m%d')+'.jsonl')
st=os.statvfs(ROOT)
if st.f_bavail*st.f_frsize<5*1024**3:raise RuntimeError('Less than 5 GiB free')
if p.exists() and p.stat().st_size>256*1024**2:raise RuntimeError('Daily diagnostic size cap reached')
start=time.monotonic()
d={'time':now.isoformat(),'host':socket.gethostname(),'epoch':time.time()}
def cmd(args):
 try:return subprocess.check_output(args,timeout=5,stderr=subprocess.STDOUT,text=True).strip()
 except Exception as e:return {'error':str(e)}
for name in ['diskstats','meminfo','vmstat','stat','loadavg']:
 d[name]=pathlib.Path('/proc/'+name).read_text()
d['pressure']={name:pathlib.Path('/proc/pressure/'+name).read_text() for name in ['cpu','io','memory']}
d['boot_id']=pathlib.Path('/proc/sys/kernel/random/boot_id').read_text().strip()
d['tcp']={name:pathlib.Path('/proc/net/'+name).read_text() for name in ['snmp','netstat']}
d['network']={}
for name in ['nic2','nic4','nic5','bond0']:
 path=pathlib.Path('/sys/class/net')/name/'statistics'
 if path.exists():d['network'][name]={k:int((path/k).read_text()) for k in ['rx_bytes','tx_bytes','rx_dropped','tx_dropped','rx_errors','tx_errors','rx_missed_errors']}
# Small local Ceph counters; cumulative values are interpreted as interval deltas.
osdid='0' if socket.gethostname()=='pve01' else '2'
asok='/var/run/ceph/ceph-osd.'+osdid+'.asok'
if pathlib.Path(asok).exists():
 raw=cmd(['ceph','--admin-daemon',asok,'perf','dump'])
 if isinstance(raw,str):
  try:
   perf=json.loads(raw);d['osd']={group:{k:v for k,v in perf.get(group,{}).items() if any(x in k for x in ['lat','op_w','op_r','queue','commit','kv_flush','kv_sync'])} for group in ['osd','bluestore','bluefs']}
  except Exception as e:d['osd_error']=str(e)
 else:d['osd_error']=raw
# Heavier API snapshots once a minute (timer runs at seconds 00/15/30/45).
if now.second<15:
 for key,args in [('ceph_health',['ceph','status','--format','json']),('ceph_perf',['ceph','osd','perf','--format','json'])]:
  raw=cmd(args)
  try:d[key]=json.loads(raw) if isinstance(raw,str) else raw
  except ValueError:d[key]=raw
 if socket.gethostname()=='pve01':
  raw=cmd(['pvesh','get','/nodes/pve01/qemu/2001/status/current','--output-format','json'])
  try:d['vm2001']=json.loads(raw) if isinstance(raw,str) else raw
  except ValueError:d['vm2001']=raw
 peer='10.10.10.2' if socket.gethostname()=='pve01' else '10.10.10.1'
 d['tcp_connections']=cmd(['ss','-tin','dst',peer])
 if socket.gethostname()=='pve01':
  try:
   with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as sock:
    sock.settimeout(2);sock.connect('/var/run/qemu-server/2001.qmp')
    with sock.makefile('rwb') as stream:
     json.loads(stream.readline())
     for operation in ['qmp_capabilities','query-blockstats']:
      stream.write((json.dumps({'execute':operation})+'\n').encode());stream.flush()
      for _ in range(30):
       reply=json.loads(stream.readline())
       if 'return' in reply or 'error' in reply:break
      if operation=='query-blockstats':d['qmp_blockstats']=reply
  except Exception as e:d['qmp_error']=str(e)
 d['ntp']=cmd(['timedatectl','show','-p','NTPSynchronized','--value'])
d['collection_ms']=round((time.monotonic()-start)*1000)
with p.open('a') as f:f.write(json.dumps(d,separators=(',',':'))+'\n')
os.chmod(p,0o600)
(ROOT/'status.json').write_text(json.dumps({'time':now.isoformat(),'state':'collecting','file':str(p),'collection_ms':d['collection_ms']}))

### ASSISTANT
Режим: **Подробный** (анализ кода).

### Шаг 1.0 — Построчный разбор скрипта мониторинга ERP

Ниже представлен подробный разбор скрипта, сгруппированный по логическим блокам для удобства чтения, но с пояснением каждой строки.

#### Блок 1: Инициализация, дедлайн и самоотключение
```python
1: #!/usr/bin/python3
2: # Лавриненко. Временный пассивный мониторинг ERP 2026.
3: import datetime as dt,json,os,pathlib,socket,subprocess,time
4: ROOT=pathlib.Path('/var/log/lavrinenko-erp-2026')
5: DEADLINE=dt.datetime.fromisoformat('2026-09-23T00:00:00+03:00').timestamp()
6: if time.time()>=DEADLINE:
7:  subprocess.run(['systemctl','disable','--now','lavrinenko-erp-2026.timer'],timeout=10)
8:  raise SystemExit(0)
```
**Что делает:**
- Строки 1-3: Shebang, комментарий автора и импорт стандартных библиотек.
- Строка 4: Задает корневую директорию для логов.
- Строка 5: Вычисляет timestamp дедлайна (23 сентября 2026, 00:00 МСК). *Примечание: сегодня 22 сентября, скрипт активен.*
- Строки 6-8: Если текущее время >= дедлайна, скрипт отключает свой же systemd-таймер (`lavrinenko-erp-2026.timer`) и завершается. Это делает мониторинг строго временным.
**Что выдает:** Не выдает данных, только управляет жизненным циклом (отключает таймер).

#### Блок 2: Подготовка директории и защитные ограничения (Failsafes)
```python
9: ROOT.mkdir(mode=0o700,exist_ok=True)
10: now=dt.datetime.now(dt.timezone.utc)
11: p=ROOT/('host-'+now.strftime('%Y%m%d')+'.jsonl')
12: st=os.statvfs(ROOT)
13: if st.f_bavail*st.f_frsize<5*1024**3:raise RuntimeError('Less than 5 GiB free')
14: if p.exists() and p.stat().st_size>256*1024**2:raise RuntimeError('Daily diagnostic size cap reached')
```
**Что делает:**
- Строка 9: Создает директорию логов с правами `700` (только для root).
- Строки 10-11: Формирует имя файла на текущую дату в UTC (например, `host-20260922.jsonl`).
- Строки 12-13: Проверяет свободное место. Если меньше 5 ГиБ, прерывает выполнение с ошибкой (защита от заполнения диска).
- Строка 14: Проверяет размер текущего дневного файла. Если больше 256 МиБ, прерывает выполнение (защита от разрастания одного файла).
**Что выдает:** При срабатывании защит — исключение `RuntimeError` и остановка скрипта.

#### Блок 3: Базовые метрики и хелпер для команд
```python
15: start=time.monotonic()
16: d={'time':now.isoformat(),'host':socket.gethostname(),'epoch':time.time()}
17: def cmd(args):
18:  try:return subprocess.check_output(args,timeout=5,stderr=subprocess.STDOUT,text=True).strip()
19:  except Exception as e:return {'error':str(e)}
```
**Что делает:**
- Строка 15: Засекает время начала сбора (для метрики длительности).
- Строка 16: Инициализирует словарь `d` (основной объект данных) временем, именем хоста и epoch.
- Строки 17-19: Объявляет функцию `cmd` для выполнения shell-команд. Возвращает `stdout` (обрезанный) или словарь с текстом ошибки. Таймаут 5 секунд, `stderr` перенаправляется в `stdout`.
**Что выдает:** Формирует базу словаря `d`.

#### Блок 4: Сбор метрик ядра (procfs) и сетевых интерфейсов
```python
20: for name in ['diskstats','meminfo','vmstat','stat','loadavg']:
21:  d[name]=pathlib.Path('/proc/'+name).read_text()
22: d['pressure']={name:pathlib.Path('/proc/pressure/'+name).read_text() for name in ['cpu','io','memory']}
23: d['boot_id']=pathlib.Path('/proc/sys/kernel/random/boot_id').read_text().strip()
24: d['tcp']={name:pathlib.Path('/proc/net/'+name).read_text() for name in ['snmp','netstat']}
25: d['network']={}
26: for name in ['nic2','nic4','nic5','bond0']:
27:  path=pathlib.Path('/sys/class/net')/name/'statistics'
28:  if path.exists():d['network'][name]={k:int((path/k).read_text()) for k in ['rx_bytes','tx_bytes','rx_dropped','tx_dropped','rx_errors','tx_errors','rx_missed_errors']}
```
**Что делает:**
- Строки 20-21: Читает сырой текст из `/proc/` для дисков, памяти, виртуальной памяти, статистики и loadavg.
- Строка 22: Читает PSI (Pressure Stall Information) для CPU, IO и памяти.
- Строка 23: Читает уникальный ID текущей загрузки ядра.
- Строка 24: Читает сетевую SNMP и netstat статистику ядра.
- Строки 25-28: Для жестко заданных интерфейсов (`nic2`, `nic4`, `nic5`, `bond0`) читает счетчики из `/sys/class/net/...` и конвертирует их из строк в `int`.
**Что выдает:** Добавляет в `d` сырые текстовые срезы `/proc` и `/sys`, а также словари с целочисленными счетчиками сетевых интерфейсов.

#### Блок 5: Локальные метрики Ceph OSD (через admin socket)
```python
29: # Small local Ceph counters; cumulative values are interpreted as interval deltas.
30: osdid='0' if socket.gethostname()=='pve01' else '2'
31: asok='/var/run/ceph/ceph-osd.'+osdid+'.asok'
32: if pathlib.Path(asok).exists():
33:  raw=cmd(['ceph','--admin-daemon',asok,'perf','dump'])
34:  if isinstance(raw,str):
35:   try:
36:    perf=json.loads(raw);d['osd']={group:{k:v for k,v in perf.get(group,{}).items() if any(x in k for x in ['lat','op_w','op_r','queue','commit','kv_flush','kv_sync'])} for group in ['osd','bluestore','bluefs']}
37:   except Exception as e:d['osd_error']=str(e)
38:  else:d['osd_error']=raw
```
**Что делает:**
- Строка 30: Определяет ID локального OSD в зависимости от хоста (`pve01` -> OSD 0, иначе -> OSD 2).
- Строка 31: Формирует путь к admin-сокету OSD.
- Строки 32-38: Если сокет существует, выполняет `ceph perf dump`. Парсит JSON и фильтрует метрики: оставляет только те, что содержат подстроки `lat`, `op_w`, `op_r`, `queue`, `commit`, `kv_flush`, `kv_sync` для групп `osd`, `bluestore`, `bluefs`. Это снижает объем данных, оставляя только важные счетчики производительности.
**Что выдает:** Словарь `d['osd']` с отфильтрованными метриками Bluestore/Bluefs/OSD или `d['osd_error']`.

#### Блок 6: Тяжелые API-запросы (выполняются раз в минуту)
```python
39: # Heavier API snapshots once a minute (timer runs at seconds 00/15/30/45).
40: if now.second<15:
41:  for key,args in [('ceph_health',['ceph','status','--format','json']),('ceph_perf',['ceph','osd','perf','--format','json'])]:
42:   raw=cmd(args)
43:   try:d[key]=json.loads(raw) if isinstance(raw,str) else raw
44:   except ValueError:d[key]=raw
```
**Что делает:**
- Строки 39-44: Условие `now.second < 15` означает, что этот блок выполняется только в первую 15-секундную четверть минуты (таймер запускает скрипт на 00, 15, 30, 45 секундах, но тяжелые запросы идут только на 00-й секунде). Собирает `ceph status` и `ceph osd perf` в формате JSON.
**Что выдает:** `d['ceph_health']` и `d['ceph_perf']`.

```python
45:  if socket.gethostname()=='pve01':
46:   raw=cmd(['pvesh','get','/nodes/pve01/qemu/2001/status/current','--output-format','json'])
47:   try:d['vm2001']=json.loads(raw) if isinstance(raw,str) else raw
48:   except ValueError:d['vm2001']=raw
```
**Что делает:**
- Строки 45-48: Только для `pve01`. Запрашивает через Proxmox API (`pvesh`) текущий статус VM с ID 2001.
**Что выдает:** `d['vm2001']` с JSON-статусом виртуальной машины.

```python
49:  peer='10.10.10.2' if socket.gethostname()=='pve01' else '10.10.10.1'
50:  d['tcp_connections']=cmd(['ss','-tin','dst',peer])
```
**Что делает:**
- Строки 49-50: Определяет IP соседнего узла (pve01 смотрит на .2, другой узел на .1). Выполняет `ss -tin dst <peer>` для сбора детальной информации об установленных TCP-соединениях (включая метрики TCP stack, т.к. есть флаг `-i`).
**Что выдает:** `d['tcp_connections']` (текстовый вывод `ss`).

```python
51:  if socket.gethostname()=='pve01':
52:   try:
53:    with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as sock:
54:     sock.settimeout(2);sock.connect('/var/run/qemu-server/2001.qmp')
55:     with sock.makefile('rwb') as stream:
56:      json.loads(stream.readline())
57:      for operation in ['qmp_capabilities','query-blockstats']:
58:       stream.write((json.dumps({'execute':operation})+'\n').encode());stream.flush()
59:       for _ in range(30):
60:        reply=json.loads(stream.readline())
61:        if 'return' in reply or 'error' in reply:break
62:       if operation=='query-blockstats':d['qmp_blockstats']=reply
63:   except Exception as e:d['qmp_error']=str(e)
```
**Что делает:**
- Строки 51-63: Только для `pve01`. Подключается к QMP (QEMU Monitor Protocol) сокету VM 2001.
- Инициализирует capabilities (обязательный шаг QMP).
- Отправляет команду `query-blockstats` для получения статистики блочных устройств (дисков) виртуальной машины. Читает ответ построчно, ожидая `return` или `error`.
**Что выдает:** `d['qmp_blockstats']` с детальной статистикой дисков VM 2001 или `d['qmp_error']`.

```python
64:  d['ntp']=cmd(['timedatectl','show','-p','NTPSynchronized','--value'])
```
**Что делает:**
- Строка 64: Проверяет, синхронизировано ли время через NTP.
**Что выдает:** `d['ntp']` (строка `yes` или `no`).

#### Блок 7: Финализация, запись и статус
```python
65: d['collection_ms']=round((time.monotonic()-start)*1000)
66: with p.open('a') as f:f.write(json.dumps(d,separators=(',',':'))+'\n')
67: os.chmod(p,0o600)
68: (ROOT/'status.json').write_text(json.dumps({'time':now.isoformat(),'state':'collecting','file':str(p),'collection_ms':d['collection_ms']}))
```
**Что делает:**
- Строка 65: Вычисляет время сбора в миллисекундах.
- Строка 66: Открывает файл на дозапись (`a`) и пишет словарь `d` в виде компактной JSON-строки (без пробелов) с переносом строки (формат JSONL).
- Строка 67: Устанавливает права `600` на файл (чтение/запись только для root).
- Строка 68: Перезаписывает файл `status.json`, указывая время, состояние, имя текущего файла и время сбора.
**Что выдает:** Файл `host-YYYYMMDD.jsonl` (пополняется новой строкой) и обновленный `status.json`.

---

### Сверка с environment_facts
- **Хосты и роли:** Скрипт жестко завязан на `pve01` (OSD 0, VM 2001, peer .2) и второй узел кластера (OSD 2, peer .1). Это полностью соответствует инфраструктуре `korona/Proxmox` (кластер pve01/pve02).
- **Сеть:** Используются IP `10.10.10.1` и `10.10.10.2`. Это внутренние IP-адреса узлов кластера (вероятно, сеть для Ceph/корзины, судя по контексту мониторинга TCP между ними).
- **VM 2001:** Мониторится конкретная виртуальная машина (вероятно, сама ERP-система или её критичный компонент, раз мониторинг называется "ERP 2026").
- **Дедлайн:** 23 сентября 2026. Сегодня 22 сентября. Скрипт запущен для сбора данных в течение ~24 часов перед неким событием (обновление, миграция, отладка).

### Как проверить результат
1. **Факт работы:** `cat /var/log/lavrinenko-erp-2026/status.json` (должен обновляться каждые 15 секунд).
2. **Собранные данные:** `tail -n 1 /var/log/lavrinenko-erp-2026/host-20260922.jsonl | jq .` (покажет последний срез).
3. **Работа таймера:** `systemctl status lavrinenko-erp-2026.timer`.

### Риск
- **Риск исчерпания диска:** Автор предусмотрел жесткие лимиты (5 ГиБ свободно, 256 МиБ на файл). Риск минимален.
- **Риск нагрузки:** Тяжелые запросы (`ceph status`, `pvesh`, `ss`, QMP) выполняются только раз в минуту (`now.second < 15`). Базовые метрики из `/proc` и `/sys` читаются каждые 15 секунд, но они крайне дешевые. Риск нагрузки на прод минимален.
- **Риск самоотключения:** Если часы на сервере сбиты и `time.time()` покажет время >= дедлайна, скрипт немедленно отключит таймер.

### Идемпотентность
Чтение. Скрипт идемпотентен. Повторный запуск просто добавит новую строку в JSONL.

### Откат
Не требуется (только чтение). Если нужно остановить: `systemctl disable --now lavrinenko-erp-2026.timer`.

### Протокол
- Проанализирован скрипт `lavrinenko-erp-2026`.
- Подтверждено, что это пассивный сборщик метрик (JSONL) с жесткими лимитами и дедлайном 23.09.2026.
- Среда: Proxmox (pve01/pve02), Ceph, VM 2001.

### Вопросы
1. Нужно ли парсить этот JSONL в какой-либо график/дашборд, или анализ будет производиться вручную через `jq` / Python-скрипты?
2. VM 2001 — это сама ERP, или это инфраструктурная ВМ (например, БД)? От этого может зависеть интерпретация `qmp_blockstats`.

### USER
Как парсить этот JSONL ? куда загрузить чтобы просмотреть в гравике и тексте?

### ASSISTANT
Режим: **Подробный**.

### Шаг 1.0 — Определение цели и выбор инструмента

Прежде чем предлагать конкретный инструмент, нужно зафиксировать **цель анализа**, потому что от неё зависит выбор стека. Скрипт временный (дедлайн 23.09.2026, ~сутки работы), данные — до 256 МиБ JSONL, ~5760 записей в сутки. Это небольшой объем, и тяжелые решения (Elasticsearch, Grafana+Loki, InfluxDB) здесь избыточны.

**Возможные сценарии:**

| Сценарий | Рекомендуемый инструмент | Плюсы | Минусы |
|---|---|---|---|
| **А. Быстрый осмотр "что там внутри" прямо на сервере** | `jq` + `less` | Ничего ставить не надо, есть на любом Linux | Нет графиков |
| **Б. Интерактивный табличный просмотр в терминале** | `visidata` (`vd`) | Открывает JSONL как таблицу, есть фильтры, гистограммы | Нужно установить (`pip install visidata` или `apt`) |
| **В. Разовый анализ с графиками после сбора** | Python + `pandas` + `plotly` (Jupyter) | Полный контроль, любые графики, можно сохранить HTML-отчет | Нужен Python на рабочей машине |
| **Г. SQL-анализ JSONL без загрузки в БД** | `DuckDB` | Запрос `SELECT * FROM read_json_auto(...)` прямо по файлу, очень быстро | Нужно установить DuckDB |
| **Д. Живой дашборд во время сбора** | `Grafana` + `Loki` / `Promtail` | Красиво, в реальном времени | Тяжеловесно для суточного мониторинга |

### Сверка с environment_facts
- Файл лежит на `pve01` и `pve02` в `/var/log/lavrinenko-erp-2026/host-YYYYMMDD.jsonl`.
- Доступ по SSH есть (ты работаешь с этими хостами).
- Структура JSONL вложенная: есть плоские поля (`time`, `host`, `epoch`, `collection_ms`, `ntp`, `boot_id`), есть сырые тексты (`meminfo`, `diskstats` — их парсить отдельно), есть вложенные словари (`pressure`, `network`, `osd`, `tcp`, `vm2001`, `qmp_blockstats`).

### Вопросы перед следующим шагом
1. **Где ты хочешь смотреть графики?** На самом сервере (консоль/браузер) или скачать файл и анализировать локально (Windows/Linux/Mac)?
2. **Какие метрики в приоритете?** Например:
   - Загрузка CPU/RAM (`meminfo`, `pressure`, `loadavg`)
   - Дисковая подсистема Ceph (`osd.lat`, `osd.op_r`, `osd.commit`)
   - Сеть (`network.*_bytes`, `tcp_connections`)
   - Виртуалка 2001 (`vm2001`, `qmp_blockstats`)
3. **Нужен ли живой просмотр** (пока скрипт еще пишет) или **ретроспективный** (после 23.09)?

### Предлагаемый первый шаг (универсальный, read-only, без установки)

Независисимо от выбора инструмента, первый шаг всегда один — **проверить структуру и выгрузить файл на рабочую машину**:

**На сервере (pve01 или pve02):**
```bash
# 1. Посмотреть последнюю запись в читаемом виде
tail -n 1 /var/log/lavrinenko-erp-2026/host-20260922.jsonl | jq .

# 2. Посмотреть только ключи верхнего уровня (какие секции вообще есть)
tail -n 1 /var/log/lavrinenko-erp-2026/host-20260922.jsonl | jq 'keys'

# 3. Оценить размер файла и количество записей
ls -lh /var/log/lavrinenko-erp-2026/host-20260922.jsonl
wc -l /var/log/lavrinenko-erp-2026/host-20260922.jsonl
```

**Скопировать файл на локальную машину** (с твоего рабочего ПК):
```bash
scp root@pve01:/var/log/lavrinenko-erp-2026/host-20260922.jsonl ./
```

После этого можно переходить к конкретному инструменту из таблицы выше.

### Риск
Нет, все команды read-only.

### Идемпотентность
Применимо только для `scp` — идемпотентно (перезапишет локальный файл).

### Откат
Не требуется.

### Протокол
- Проанализирован скрипт `lavrinenko-erp-2026` (пассивный сборщик JSONL, дедлайн 23.09.2026).
- Запрошены цели анализа для выбора инструмента парсинга.
- Предложен универсальный первый шаг: `jq` для осмотра + `scp` для выгрузки.

### Вопросы
1. Какой сценарий из таблицы (А–Д) ближе к твоей задаче?
2. Какие метрики в приоритете для графиков?
3. Где будешь смотреть — на сервере или локально?

### USER
tail -n 1 /var/log/lavrinenko-erp-2026/host-20260922.jsonl | jq .

### ASSISTANT


### USER
jq команда не найдена

### ASSISTANT
### Шаг 2.0 — Установка `jq` для парсинга JSONL

На сервере отсутствует пакет `jq`. Поскольку это Proxmox VE (Debian-based), установка стандартная через `apt`.

**Команда для выполнения на сервере (pve01 или pve02):**
```bash
apt update && apt install -y jq
```

**Что делает:**
- `apt update` — обновляет список пакетов (не обязательно, если недавно обновлялся, но гарантирует актуальность).
- `apt install -y jq` — устанавливает `jq` без запроса подтверждения.

**Сверка с environment_facts:**
- Proxmox VE основан на Debian, `jq` доступен в стандартных репозиториях.
- Требуются права root (или `sudo`).

**Как проверить результат:**
```bash
jq --version
```
Должно вывести что-то вроде `jq-1.6` (или новее).

После установки можно вернуться к командам из предыдущего шага:
```bash
tail -n 1 /var/log/lavrinenko-erp-2026/host-20260922.jsonl | jq .
```

**Риск:**
Минимальный. Устанавливается стандартный пакет из официального репозитория Debian. Не затрагивает работающие сервисы.

**Идемпотентность:**
Идемпотентно. Повторный запуск `apt install -y jq` просто сообщит, что пакет уже установлен.

**Откат:**
```bash
apt remove -y jq
```

**Ожидаемое время:**
~10–30 секунд (зависит от скорости репозитория).

---

**Альтернатива без установки** (если не хочешь ставить `jq`):
Можно использовать встроенный Python3 (он точно есть, т.к. скрипт мониторинга на нём работает):
```bash
tail -n 1 /var/log/lavrinenko-erp-2026/host-20260922.jsonl | python3 -m json.tool
```
Это отформатирует JSON, но не даст возможностей фильтрации как у `jq`.

---

**Вопрос:**
Устанавливаем `jq` через `apt`, или используем `python3 -m json.tool` для быстрого просмотра?