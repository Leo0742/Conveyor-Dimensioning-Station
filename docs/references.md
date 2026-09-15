# Источники

Дата доступа для веб-источников: 13 сентября 2026 года.

## Задание и материалы Ozon Tech

1. Ozon Tech × Университет Иннополис. «Тестовое задание: трек „Компьютерное зрение“, вариант 1». PDF с условиями задачи, 2 страницы.
2. Мария Гафурова, Ozon Tech. [«Размер имеет значение. Как Ozon автоматизировал измерение товаров на складах»](https://habr.com/ru/companies/ozontech/articles/809409/), 23 апреля 2024. Из статьи я взял общий контекст о том, как Ozon измеряет товары на складах.

## Сенсоры и синхронизация

3. LMI Technologies. [Gocator 2880 — официальная страница серии](https://lmi3d.com/series/gocator-2800-series/). Две камеры, 1280 точек/профиль, FOV и MR.
4. LMI Technologies. [Gocator 2880 Dual Camera 3D Smart Profile Sensor Datasheet](https://lmi3d.com/wp-content/uploads/2024/09/DATASHEET_Gocator_2880_Wood_US.pdf), rev. 2.3, ©2023. Таблица с разрешением по X/Z, линейностью по Z, частотой сканирования, входами энкодера и триггера.
5. LMI Technologies. [Gocator 2490 Datasheet](https://lmi3d.com/wp-content/uploads/2020-02/DATASHEET_Gocator_2490_US_WEB.pdf), rev. 1.1. Точки на профиль, разрешение по X, линейность и повторяемость по Z, FOV, MR и частота сканирования.
6. LMI Technologies. [Gocator 2490 — официальная продуктовая страница](https://lmi3d.com/gocator-2490-3d-laser-line-profiler/). Заявленная производителем работа для 1×1 м при 800 Гц и 2 м/с.
7. LMI Technologies. [Gocator 2400 Series Datasheet](https://lmi3d.com/wp-content/uploads/2024/02/DATASHEET_Gocator_2400_US_WEB-1.pdf). Параметры моделей 2450 и 2490.
8. LMI Technologies. [Gocator 2400 Series — актуальная страница](https://lmi3d.com/series/gocator-2400-series/). Быстрые спецификации и назначение синего лазера.
9. LMI Technologies. [Объединение нескольких датчиков](https://lmi3d.com/technology/networking/). Синхронизация датчиков и распределение сигналов энкодера.
10. LMI Technologies. [Дополнительное оборудование Gocator](https://lmi3d.com/product-accessories/). Кабели, энкодеры и калибровочные мишени.
11. RealSense. [Промышленная камера D457](https://www.realsenseai.com/products/d457-gmsl-fakra/). Глобальный затвор, разрешение глубины 1280×720, 90 кадров/с, поле зрения 87°×58° и рабочий диапазон.
12. RealSense. [Аппаратная синхронизация D457](https://dev.realsenseai.com/docs/d457-hardware-synchronization/). Синхронизация нескольких камер.
13. RealSense. [Настройка нескольких камер D400](https://dev.realsenseai.com/docs/multiple-depth-cameras-configuration/). Перекрывающиеся области, синхронизация и проекторы.
14. SICK. [Технические характеристики DFS60I-BHPC65536](https://www.sick.com/media/pdf/2/62/762/dataSheet_DFS60I-BHPC65536_1091640_en.pdf). 65 536 импульсов на оборот и частота до 820 кГц.
15. SICK. [Информация о серии W4F](https://www.sick.com/media/docs/4/24/724/product_information_w4f_en_im0093724.pdf). Семейство промышленных фотоэлектрических датчиков.
16. SICK. [Технические характеристики WLF4FI-973121A0ZZZ](https://www.sick.com/media/pdf/5/45/645/dataSheet_WLF4FI-973121A0ZZZ_1124155_en.pdf). Точечный ИК-луч, световое пятно Ø40 мм на расстоянии 1 м и рекомендуемый диапазон 0,4–7 м.

## Вычислитель и ПО

17. OnLogic. [Документация Karbon K800](https://support.onlogic.com/product-documentation/rugged-products/karbon-k800-series/k801-k802-k803-k804). Процессор, память, сеть, питание, температура и вибрация.
18. Open3D 0.19. [Документация ориентированного параллелепипеда](https://www.open3d.org/docs/release/python_api/open3d.geometry.OrientedBoundingBox.html). Метод `create_from_points_minimal` с приближённым поиском минимального OBB.
19. Open3D 0.19. [Руководство по облакам точек](https://www.open3d.org/docs/release/tutorial/geometry/pointcloud.html). Поиск плоскости и фильтрация.
20. SciPy. [Построение выпуклой оболочки](https://docs.scipy.org/doc/scipy/reference/generated/scipy.spatial.ConvexHull.html). Представление граней выпуклой оболочки.
21. OpenCV. [Калибровка камеры и трёхмерная реконструкция](https://docs.opencv.org/4.x/d9/d0c/group__calib3d.html). Модели камер, калибровка и преобразования.
22. Open3D. [Дополнительные способы расчёта OBB](https://www.open3d.org/docs/latest/python_api/open3d.t.geometry.OrientedBoundingBox.html). Здесь описаны приближённый `MINIMAL_APPROX` и более точный `MINIMAL_JYLANKI`. В стабильной версии Open3D 0.19 второй способ недоступен.

## Дополнительные материалы LMI

23. LMI Technologies. [Анонс Gocator 2880](https://lmi3d.com/news/lmi-technologies-unveils-gocator-2880-the-first-all-in-one-3d-profile-sensor-with-dual-cameras/). Работа с крупными сложными формами и уменьшение слепых зон двумя камерами.
24. LMI Technologies. [Измерение свободного объёма внутри коробки](https://lmi3d.com/blog/box-void-fill-measurement-with-a-dual-camera-smart-3d-laser-profiler/). Пример применения Gocator 2880.
25. LMI Technologies. [Пошаговое описание измерения коробки](https://lmi3d.com/wp-content/uploads/2023/03/Box-void-fill-Walkthrough.pdf). Измерение внутреннего объёма двумя камерами 2880.
26. LMI Technologies. [Руководство пользователя Gocator 2300/2880](https://lmi3d.com/wp-content/uploads/2016-08/15159-4.3.3.167_MANUAL_User_Gocator-2300-2880-Series.pdf). Emulator, триггер, энкодер и настройки сбора данных.
27. LMI Technologies. [Настройка сбора данных в GoPxL](https://ap.lmi3d.com/manuals/gopxl/gopxl-1.3/LMILaserLineProfiler/Content/WebInterface/Acquire/ConfiguringAcquisition.htm). Расчёт максимальной частоты.
28. LMI Technologies. [Как увеличить максимальную частоту кадров](https://support.lmi3d.com/hc/en-us/articles/360033661791-Improving-Max-Frame-Rate). Влияние выдержки, области сканирования и уменьшения числа отсчётов.
29. LMI Technologies. [Пропуски сигналов энкодера при высокой частоте](https://support.lmi3d.com/hc/en-us/articles/360033336991-Trigger-Drop-warnings-in-Encoder-Trigger-mode). Поведение датчика при слишком частых импульсах.
30. LMI Technologies. [Японская спецификация Gocator 2490](https://lmi3d.com/wp-content/uploads/2020-02/DATASHEET_Gocator_2490_JP_WEB_0.pdf), версия 1.1. В таблице указано разрешение по Z 0,06–1,5 мм; в англоязычной версии отдельной строки с этим параметром нет.

## Публичные данные

Я не нашёл компактный открытый набор с движущимися посылками, точными эталонными размерами и разрешением на свободное распространение. Поэтому в проекте нет стороннего датасета: алгоритм проверяется на синтетических сценариях. Для физического пилота понадобится собственный набор проходов с заранее измеренными товарами.
