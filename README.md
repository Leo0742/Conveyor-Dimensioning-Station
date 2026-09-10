# Conveyor Dimensioning Station

Инженерный прототип 3D-измерения габаритов товара на конвейере.

Проект для тестового задания Ozon Tech × Университет Иннополис, трек
«Компьютерное зрение», вариант 1. Требуется оценивать minimum-volume OBB
(minimal-approx) товара 10×10×10…400×300×300 мм на ленте 600 мм при
1 м/с и передавать L/W/H в WMS с допуском `±max(5 %, 5 мм)`.

**Выбранная архитектура:** один двухкамерный лазерный профилометр LMI Gocator
2880, аппаратный encoder trigger, датчик присутствия SICK, промышленный x86 edge
PC и локальный геометрический контур. 2880 выбран вместо одного/двух 2490 прежде
всего из-за двух встречных камер в одном калиброванном корпусе; официальный LMI
материал также показывает 2880 в задаче измерения заполнения коробок.

[Полный инженерный отчёт (PDF)](docs/report.pdf)

> Важно: это программная проверка на упрощённых синтетических данных. Она не
> доказывает физическую погрешность станции. Целевые 1000 профилей/с для шага Y
> 1 мм не были подтверждены для окончательных active area и exposure: это надо
> проверить в Gocator Emulator или на датчике до закупки.

![Демонстрация измерения](assets/demo/measurement.png)

## Быстрый запуск

Нужны Python 3.12 и [uv](https://docs.astral.sh/uv/).

```bash
uv sync --frozen --python 3.12
uv run pytest -q
uv run ruff check .
uv run conveyor-dimensioning demo --output-dir assets/demo --seed 42
uv run conveyor-dimensioning measure assets/demo/sample_scene.npz \
  --item-id synthetic-check --seed 42
```

Полная воспроизводимая проверка:

```bash
uv run conveyor-dimensioning benchmark --output-dir assets/demo --seed 42
uv run conveyor-dimensioning sensor-benchmark --output-dir assets/demo --seed 42
uv run conveyor-dimensioning monte-carlo --output-dir assets/demo \
  --count 500 --seed 20261017
uv run conveyor-dimensioning multiframe-demo --output-dir assets/demo --seed 42
uv sync --frozen --python 3.12 --extra open3d
uv run python scripts/compare_obb.py --output assets/demo/obb_comparison.json
uv run python scripts/generate_diagrams.py
uv run python scripts/build_report.py
```

## Геометрия установки

Предварительный расчёт для одного Gocator 2880:

- высота над лентой — 916,7 мм;
- FOV на высоте товара 300 мм — 680 мм, по 40 мм запаса на сторону;
- FOV на ленте — 1006,25 мм;
- худший поперечный шаг X в рабочем объёме — 0,786 мм, или 12,72 отсчёта на 10 мм;
- целевой шаг Y — 1 мм при 1000 профилях/с.

Это `PRELIMINARY CALCULATED LAYOUT`, а не монтажный чертёж. Координаты уточняются
по заводской калибровочной модели. Реальная максимальная частота зависит от active
area, exposure, subsampling и двухкамерной конфигурации. Сценарии для 10-мм товара:
1000/800/500/380 Гц дают соответственно 10/8/5/3,8 профиля. 1000 Гц — целевой,
но пока не проверенный режим; 380 Гц имеет слишком малый запас для уверенного
выделения границ минимального товара.

Подробное сравнение 1×2880, 1×/2×2490, 3×2450 и 2×RealSense D457 находится в
[аппаратном исследовании](docs/hardware_trade_study.md).

## Что реализовано

- упрощённая line-profiler модель: номинальный шаг X задаётся верхним FOV и 1280
  samples/profile, Y — `speed/rate`; две встречные камеры, один depth на ячейку
  X/Y, тени, шум, dropout, пропуски целых профилей и height-dependent FOV clipping;
- скрытое дно не выдаётся за наблюдение; есть только **estimated support-contact
  completion** нижней полосы — эвристика для box-like объектов;
- RANSAC ленты, фильтрация, радиус кластеризации из наблюдаемого расстояния до
  соседей, соединение близких фрагментов и обнаружение двух товаров;
- оценка minimum-volume OBB (minimal-approx): устойчивое направление по dominant
  top plane с hull-based face/edge fallback/reference, допуск и медианная агрегация;
- runtime quality gate: при расхождении dominant-top и исходной OBB-оценки более
  25% результат получает `low_confidence`; ground truth в этом решении не участвует;
- реализованные проверки качества: число точек, структура кластеров, FOV/range
  и расхождение двух OBB-оценок; мониторинг пропусков профилей, fill rate,
  saturation, MAD между окнами и minimum valid-window count — расширение production,
  не реализованное в PoC;
- `confidence` — некалиброванный эвристический quality score по числу точек и
  согласованности OBB, а не вероятность метрологической корректности;
- статусы `ok`, `insufficient_depth_data`, `object_overlap`,
  `measurement_out_of_range`, `low_confidence`, частичный `calibration_error`;
- WMS-схема, стабильный `measurement_id`, UTC JSON и append-only JSONL outbox;
- тесты, три раздельных benchmark-набора, demo, PNG/GIF, схемы и русский PDF.

Модель называется `SIMPLIFIED LINE-PROFILER SYNTHETIC`: это не Gocator Emulator
и не физическая симуляция. Она не моделирует BRDF, speckle, multipath, насыщение
или преломление прозрачной упаковки.

## Зафиксированные результаты

Контрольные наборы seed 42: regression — 7/7 correct OK, p95 abs L/W/H
`2,371 / 2,413 / 2,622 мм`; simplified line-profiler — 7/7 correct OK,
`4,675 / 2,570 / 1,311 мм`.

`Acceptance rate=(correct OK+wrong OK)/expected-valid`; `precision among
accepted=correct OK/(correct OK+wrong OK)`; `correct measurement rate=correct
OK/expected-valid`.

| Monte Carlo subset | Total | Expected-valid | Expected-reject | Correct OK | Wrong OK | Rejected valid | Acceptance rate | Precision among accepted | Correct measurement rate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| yaw-only | 125 | 125 | 0 | 125 | 0 | 0 | 100,0% | 100,0% | 100,0% |
| tilted/irregular | 125 | 125 | 0 | 90 | 16 | 19 | 84,8% | 84,9% | 72,0% |
| small-object | 125 | 125 | 0 | 123 | 0 | 2 | 98,4% | 100,0% | 98,4% |
| noisy/incomplete | 125 | 100 | 25 | 89 | 11 | 0 | 100,0% | 89,0% | 89,0% |
| **Итого** | **500** | **475** | **25** | **427** | **27** | **21** | **95,6%** | **94,1%** | **89,9%** |

Все 25 expected-reject сценариев отклонены, false accepted — 0. Это synthetic
rejection-stress, а не прогноз false-ok физической линии. Порог quality gate выбран
только на development seed 1337. После заморозки tilted/irregular и полный набор
500 на final seed 20261017 были выполнены по одному разу; после результата порог
и алгоритм не менялись.

Для tilted/irregular quality gate повысил долю корректных среди принятых
синтетических измерений с 79,8% до 84,9%; acceptance rate равен 84,8%, correct
measurement rate — 72,0%. Эти случаи ограничены видимостью и support-моделью
упрощённого симулятора: они указывают на потенциальную проблему наблюдаемости,
но не доказывают идентичный отказ физического dual-camera Gocator. Если пилот
покажет недостаточный correct measurement rate, потребуется отдельный trade study.

Multi-frame demo: пять валидных центральных окон из девяти положений; медианный
результат `120,816×80,796×45,814 мм`, статус `ok`. Артефакты:
[график](assets/demo/multiframe_summary.png), [WMS JSON](assets/demo/multiframe_wms.json),
[анимация](assets/demo/multiframe_motion.gif).

## OBB и WMS

В проекте используется оценка minimum-volume OBB (minimal-approx): устойчивое
направление оценивается по доминирующей верхней плоскости, а hull-based face/edge
minimal-approx OBB служит fallback/reference и сигналом контроля. Это не доказанный
глобальный минимум. В Open3D 0.19.0 `MINIMAL_JYLANKI` недоступен; reference —
другой minimal-approx алгоритм.

В WMS реализованы контракт, детерминированный `measurement_id` как idempotency key,
сериализация и локальная append-only JSONL outbox. Для `status != ok` публичные
`length_mm`, `width_mm`, `height_mm` равны `null`; диагностические размеры остаются
только внутри `DimensionResult`.
HTTPS/mTLS, retry/backoff worker, ACK, dead-letter policy и TPM/OS keystore только
предложены и не выдаются за готовый transport.

## Структура

```text
src/conveyor_dimensioning/  библиотека и CLI
tests/                      unit/integration/regression tests
assets/demo/                benchmark и demo-артефакты
assets/diagrams/            PNG для PDF и редактируемые SVG-исходники
data/hardware_specs.csv     спецификации кандидатов
docs/report.md/.pdf         русский отчёт
docs/evidence/              проверка частоты профилей по источникам LMI
```

## PDF

```bash
uv run python scripts/generate_diagrams.py
uv run python scripts/build_report.py
pdfinfo docs/report.pdf
pdftotext docs/report.pdf /tmp/ozon-report.txt
! grep -E '■|�' /tmp/ozon-report.txt
```
