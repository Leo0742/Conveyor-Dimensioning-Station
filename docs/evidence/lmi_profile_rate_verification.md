# Проверка частоты профилей Gocator 2880

Дата проверки: 10 сентября 2026 года. Это журнал доказательств, а не результат
испытания датчика.

## Вывод

Целевая точка проекта — 1000 профилей/с при скорости 1000 мм/с, то есть шаг Y
1 мм. **Максимальная частота для окончательных active area, exposure,
sub-sampling и двухкамерной конфигурации не проверена.** До закупки её нужно
подтвердить в Gocator Emulator либо на физическом Gocator 2880.

## Что подтверждает производитель

1. Руководство LMI для Gocator 2300/2880 описывает раздел *Calculating Potential
   Maximum Frame Rate*: Emulator пересчитывает максимальную частоту в панели
   Trigger после изменения Active Area или Exposure. Источник:
   [Gocator 2300 & 2880 Series User Manual, раздел Gocator Emulator](https://lmi3d.com/wp-content/uploads/2016-08/15159-4.3.3.167_MANUAL_User_Gocator-2300-2880-Series.pdf).
2. Текущая документация GoPxL указывает, что максимальная возможная частота
   показана на странице Acquire и меняется от параметров Active Area, Exposure
   и Sub-sampling. Источник:
   [LMI GoPxL — Configuring Acquisition](https://ap.lmi3d.com/manuals/gopxl/gopxl-1.3/LMILaserLineProfiler/Content/WebInterface/Acquire/ConfiguringAcquisition.htm).
3. LMI перечисляет способы повышения частоты: уменьшение active area, сокращение
   exposure, sub-sampling и уменьшение maximum part length. Источник:
   [Improving Max Frame Rate](https://support.lmi3d.com/hc/en-us/articles/360033661791-Improving-Max-Frame-Rate).
4. При encoder-trigger, превышающем Max Frame Rate, Gocator начинает пропускать
   триггеры; Max Frame Rate зависит от exposure, active area и sub-sampling.
   Источник: [Trigger Drop warnings in Encoder Trigger mode](https://support.lmi3d.com/hc/en-us/articles/360033336991-Trigger-Drop-warnings-in-Encoder-Trigger-mode).
5. LMI называет наиболее точным способом оценить скорость моделирование
   конкретных настроек на Gocator/Emulator. Источник:
   [Estimating scanning speed under a given X or Z resolution](https://support.lmi3d.com/hc/en-us/articles/360033661731-Estimating-scanning-speed-under-a-given-X-or-Z-resolution-G2xxx).

## Почему число не получено локально

Официальная страница загрузки ведёт к пакету *Gocator Emulator and Utilities
6.3.7.2 (SR1)*, для доступа к ресурсу предлагает LOGIN/REGISTER. Руководство
описывает запуск `GoEmulator.exe`; текущая машина — `Darwin arm64`. Доступной
нативной macOS-версии или полностью браузерного конфигуратора, способного
рассчитать Max Frame Rate для выбранной active area/exposure, обнаружено не
было. Регистрация, ручная Windows-среда и ввод неподтверждённых параметров
экспозиции не выполнялись.

Никаких скриншотов или чисел Emulator в проекте нет, потому что конфигурация
фактически не запускалась.

## Расчётные рабочие точки

| Статус | Частота | Шаг Y при 1 м/с | Профилей на 10 мм |
|---|---:|---:|---:|
| TARGET, требует Emulator/датчика | 1000 Гц | 1,00 мм | 10,0 |
| Сценарий деградации, не проверен | 800 Гц | 1,25 мм | 8,0 |
| Сценарий деградации, не проверен | 500 Гц | 2,00 мм | 5,0 |
| Нижняя граница datasheet, не конфигурация | 380 Гц | 2,63 мм | 3,8 |

Даже арифметически достаточное число профилей не доказывает точность станции:
нужны видимые границы объекта, корректная экспозиция, отсутствие trigger drops,
калибровка и физическая MSA.
