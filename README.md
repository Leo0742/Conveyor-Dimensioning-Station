# Conveyor Dimensioning Station

[![CI](https://github.com/Leo0742/Conveyor-Dimensioning-Station/actions/workflows/ci.yml/badge.svg)](https://github.com/Leo0742/Conveyor-Dimensioning-Station/actions/workflows/ci.yml)

Для тестового задания Ozon Tech × Университет Иннополис я спроектировал станцию,
которая измеряет габариты товара на движущемся конвейере. В репозитории есть
сравнение датчиков, расчёт компоновки и синтетический Python-прототип пути от
облака точек до JSON для WMS.

**[Полный технический отчёт (PDF)](docs/report.pdf)**

![Синтетический пример измерения](assets/demo/measurement.png)

## Задача

Требуется измерять L×W×H товаров от 10×10×10 до 400×300×300 мм на ленте
шириной 600 мм при скорости 1 м/с. Допуск для каждой стороны —
`±max(5 %, 5 мм)`, результат нужно передать в WMS.

## Решение

Я выбрал один двухкамерный лазерный профилометр **LMI Gocator 2880**. Товар
обнаруживает **SICK WLF4FI**, а **SICK DFS60** с мерным колесом задаёт координату
по движению. Профили обрабатываются локально на **OnLogic Karbon K801**, после
чего результат попадает в WMS.

Почему 2880:

- две камеры в одном калиброванном корпусе уменьшают затенение боковых граней;
- расчётный FOV 680 мм на высоте товара 300 мм оставляет по 40 мм запаса с каждой стороны;
- предварительная высота монтажа — около 916,7 мм над лентой;
- один 2880 проще синхронизировать и калибровать, чем два встречных Gocator 2490.

Целевые 1000 профилей/с дают шаг 1 мм по Y, но этот режим ещё нужно проверить
в Gocator Emulator или на реальном датчике. Расчёт FOV и высоты — предварительная
компоновка, а не замена заводской калибровочной модели.

## Как работает прототип

```text
триггер + энкодер → профили X–Z → облако точек → удаление ленты
→ фильтрация и кластеры → приближённый OBB → проверка качества → WMS JSON
```

## Что реализовано

В коде есть:

- упрощённая модель линейного профилометра с шагом по FOV/частоте, двумя ракурсами,
  шумом, пропусками точек и целых профилей;
- RANSAC плоскости ленты, фильтрация, кластеризация и обнаружение двух товаров;
- эвристика контакта с опорной плоскостью и приближённый minimum-volume OBB;
- статусы и проверки качества, WMS-схема и локальная JSONL-очередь;
- regression, sensor-like и Monte Carlo benchmark, а также multi-frame demo.

Для физической станции ещё нужны адаптер Gocator/PLC, стендовая калибровка,
транспорт в WMS по HTTPS/mTLS с повторами, мониторинг и механика отвода товара
на ручной поток.

## Результаты

На зафиксированном синтетическом наборе (`seed=20261017`):

| Всего | Expected-valid | Correct OK | Wrong OK | Rejected valid | Acceptance | Precision among accepted | Correct measurement rate |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 500 | 475 | 427 | 27 | 21 | 95,6% | 94,1% | 89,9% |

Acceptance — доля принятых среди expected-valid; precision among accepted — доля
корректных среди принятых. Все 25/25 искусственных expected-reject сценариев были
отклонены.

Самый сложный срез — наклонённые и нерегулярные объекты: 84,9% precision among
accepted и 72,0% correct measurement rate. Это результаты проверки программной
геометрии на синтетике, а не оценка точности физической станции.

## Запуск

Нужны Python 3.12 и [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/Leo0742/Conveyor-Dimensioning-Station.git
cd Conveyor-Dimensioning-Station
uv sync --frozen --python 3.12
uv run ruff check .
uv run pytest -q
uv run conveyor-dimensioning demo --output-dir assets/demo --seed 42
```

Полезные отдельные команды:

```bash
uv run conveyor-dimensioning measure assets/demo/sample_scene.npz \
  --item-id synthetic-check --seed 42
uv run conveyor-dimensioning sensor-benchmark --output-dir assets/demo --seed 42
uv run conveyor-dimensioning monte-carlo --output-dir assets/demo \
  --count 500 --seed 20261017
uv run conveyor-dimensioning multiframe-demo --output-dir assets/demo --seed 42
```

<details>
<summary>Сборка отчёта и сравнение с Open3D</summary>

```bash
uv run python scripts/generate_diagrams.py
uv run python scripts/build_report.py
uv sync --frozen --python 3.12 --extra open3d
uv run python scripts/compare_obb.py --output assets/demo/obb_comparison.json
```

</details>

## Структура проекта

```text
src/conveyor_dimensioning/  библиотека и CLI
tests/                      автоматические тесты
assets/demo/                демо и зафиксированные результаты
assets/diagrams/            PNG-иллюстрации и SVG-исходники
data/hardware_specs.csv     спецификации для сравнения
docs/                       отчёт, ссылки и аппаратное сравнение
```

## Ограничения

Симулятор не является Gocator Emulator и не моделирует реальную оптику чёрной,
глянцевой и прозрачной упаковки. Скрытое дно не восстанавливается; оценка контакта
с опорной плоскостью остаётся эвристикой. OBB — приближённый, а `confidence` —
некалиброванный показатель качества, не вероятность. Абсолютную погрешность
физической станции можно подтвердить только на стенде через калибровку и
MSA/Gage R&R.

Подробное [сравнение оборудования](docs/hardware_trade_study.md), схема станции,
метрологические ограничения, план ML-fallback и физической валидации собраны
в [отчёте](docs/report.pdf).

## Автор

Леонид Болбачан, Университет Иннополис.
