# Источники

Дата доступа для веб-источников: 10 сентября 2026 года.

## Исходное задание и отраслевой контекст

1. Ozon Tech × Университет Иннополис. «Тестовое задание, трек Компьютерное зрение, вариант 1». Исходный PDF, 2 страницы, предоставлен вместе с заданием.
2. Мария Гафурова, Ozon Tech. [«Размер имеет значение. Как Ozon автоматизировал измерение товаров на складах»](https://habr.com/ru/companies/ozontech/articles/809409/), 23 апреля 2024. Использовано как отраслевой контекст, а не как проект для копирования.

## Сенсоры и синхронизация

3. LMI Technologies. [Gocator 2880 — официальная страница серии](https://lmi3d.com/series/gocator-2800-series/). Две камеры, 1280 точек/профиль, FOV и MR.
4. LMI Technologies. [Gocator 2880 Dual Camera 3D Smart Profile Sensor Datasheet](https://lmi3d.com/wp-content/uploads/2024/09/DATASHEET_Gocator_2880_Wood_US.pdf), rev. 2.3, ©2023, размещён в актуальном каталоге LMI. Полная таблица X/Z resolution, Z linearity, scan rate, encoder/trigger, интерфейсы.
5. LMI Technologies. [Gocator 2490 Datasheet](https://lmi3d.com/wp-content/uploads/2020-02/DATASHEET_Gocator_2490_US_WEB.pdf), rev. 1.1. Точки/профиль, X resolution, Z linearity/repeatability, FOV, MR, scan rate.
6. LMI Technologies. [Gocator 2490 — официальная продуктовая страница](https://lmi3d.com/gocator-2490-3d-laser-line-profiler/). Заявленная производителем работа для 1×1 м при 800 Гц и 2 м/с.
7. LMI Technologies. [Gocator 2400 Series Datasheet](https://lmi3d.com/wp-content/uploads/2024/02/DATASHEET_Gocator_2400_US_WEB-1.pdf). Параметры моделей 2450 и 2490.
8. LMI Technologies. [Gocator 2400 Series — актуальная страница](https://lmi3d.com/series/gocator-2400-series/). Быстрые спецификации и назначение синего лазера.
9. LMI Technologies. [Sensor Networking](https://lmi3d.com/technology/networking/). Master hub, распределение encoder/I/O и синхронизация до 1 мкс.
10. LMI Technologies. [Gocator accessories](https://lmi3d.com/product-accessories/). I/O cordset, quadrature encoder и калибровочные мишени.
11. RealSense. [D457 GMSL/FAKRA](https://www.realsenseai.com/products/d457-gmsl-fakra/). Global shutter, 1280×720, 90 fps, 87°×58°, диапазон и заявленная depth accuracy.
12. RealSense. [D457 Hardware Synchronization](https://dev.realsenseai.com/docs/d457-hardware-synchronization/). Синхронизация нескольких камер.
13. RealSense. [Multi-Camera Configurations — D400](https://dev.realsenseai.com/docs/multiple-depth-cameras-configuration/). Перекрывающиеся камеры, синхронизация и проекторы.
14. SICK. [DFS60I-BHPC65536 datasheet](https://www.sick.com/media/pdf/2/62/762/dataSheet_DFS60I-BHPC65536_1091640_en.pdf). 65 536 импульсов/оборот, TTL/HTL, 820 кГц.
15. SICK. [W4F product information](https://www.sick.com/media/docs/4/24/724/product_information_w4f_en_im0093724.pdf). Семейство промышленных фотоэлектрических датчиков.
16. SICK. [WLF4FI-973121A0ZZZ datasheet](https://www.sick.com/media/pdf/5/45/645/dataSheet_WLF4FI-973121A0ZZZ_1124155_en.pdf). Ретрорефлекторный датчик W4F для сложных объектов.

## Вычислитель и ПО

17. OnLogic. [Karbon K801/K802/K803/K804 documentation](https://support.onlogic.com/product-documentation/rugged-products/karbon-k800-series/k801-k802-k803-k804). CPU, память, сеть, питание, температура и вибрация.
18. Open3D 0.19. [OrientedBoundingBox API](https://www.open3d.org/docs/release/python_api/open3d.geometry.OrientedBoundingBox.html). Stable `create_from_points_minimal`; face-frame minimal approximation.
19. Open3D 0.19. [Point cloud tutorial](https://www.open3d.org/docs/release/tutorial/geometry/pointcloud.html). RANSAC plane segmentation и фильтрация.
20. SciPy. [ConvexHull API](https://docs.scipy.org/doc/scipy/reference/generated/scipy.spatial.ConvexHull.html). Qhull и представление граней выпуклой оболочки.
21. OpenCV. [Camera calibration and 3D reconstruction](https://docs.opencv.org/4.x/d9/d0c/group__calib3d.html). Модели камер, калибровка и преобразования.
22. Open3D development API. [Tensor OrientedBoundingBox](https://www.open3d.org/docs/latest/python_api/open3d.t.geometry.OrientedBoundingBox.html). Отдельно документирует `MINIMAL_APPROX` и более точный `MINIMAL_JYLANKI`; это development-документация, не API стабильного 0.19.

## Дополнительные официальные материалы LMI финального прохода

23. LMI Technologies. [Gocator 2880 launch: dual-camera 3D profile sensor](https://lmi3d.com/news/lmi-technologies-unveils-gocator-2880-the-first-all-in-one-3d-profile-sensor-with-dual-cameras/). Производитель указывает крупные сложные формы, уменьшение окклюзий и применение в packaging.
24. LMI Technologies. [Box Void Fill Measurement with a Dual-Camera Smart 3D Laser Profiler](https://lmi3d.com/blog/box-void-fill-measurement-with-a-dual-camera-smart-3d-laser-profiler/). Официальный packaging use case с Gocator 2880.
25. LMI Technologies. [Box Void Fill Walkthrough](https://lmi3d.com/wp-content/uploads/2023/03/Box-void-fill-Walkthrough.pdf). Официальное пошаговое описание измерения внутреннего объёма коробки двумя камерами 2880.
26. LMI Technologies. [Gocator 2300/2880 Series User Manual](https://lmi3d.com/wp-content/uploads/2016-08/15159-4.3.3.167_MANUAL_User_Gocator-2300-2880-Series.pdf). Emulator, trigger/encoder и acquisition settings.
27. LMI Technologies. [GoPxL — Configuring Acquisition](https://ap.lmi3d.com/manuals/gopxl/gopxl-1.3/LMILaserLineProfiler/Content/WebInterface/Acquire/ConfiguringAcquisition.htm). Официальное описание Trigger panel и расчёта максимальной частоты.
28. LMI Technologies Support. [Improving Max Frame Rate](https://support.lmi3d.com/hc/en-us/articles/360033661791-Improving-Max-Frame-Rate). Зависимость от exposure, active area и subsampling.
29. LMI Technologies Support. [Trigger Drop warnings in Encoder Trigger mode](https://support.lmi3d.com/hc/en-us/articles/360033336991-Trigger-Drop-warnings-in-Encoder-Trigger-mode). Поведение при encoder-trigger выше доступной частоты.

## Публичные данные

Подходящий компактный открытый набор именно для движущихся посылок с метрическим ground truth и разрешённым перераспространением не найден. Репозиторий поэтому не включает сторонние данные: synthetic benchmark проверяет только алгоритм. Перед production-пилотом нужен собственный калиброванный набор проходов через станцию.
