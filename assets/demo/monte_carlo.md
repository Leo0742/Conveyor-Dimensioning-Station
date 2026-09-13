# MONTE CARLO SYNTHETIC

> Проверяет геометрию на упрощённых синтетических данных линейного профилометра; не измеряет абсолютную точность физической станции.

Seed: 20261018; cases: 500; configuration: FROZEN BEFORE FINAL SEED.

| Поднабор | Total | Expected-valid | Expected-reject | Correct OK | Wrong OK | Rejected valid | Acceptance rate | Precision among accepted | Correct measurement rate | Reject correct / false accepted |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| yaw_only | 125 | 125 | 0 | 121 | 2 | 2 | 98.4% | 98.4% | 96.8% | 0 / 0 |
| tilted_irregular | 125 | 125 | 0 | 93 | 11 | 21 | 83.2% | 89.4% | 74.4% | 0 / 0 |
| small_object | 125 | 125 | 0 | 119 | 0 | 6 | 95.2% | 100.0% | 95.2% | 0 / 0 |
| noisy_incomplete | 125 | 100 | 25 | 79 | 15 | 6 | 94.0% | 84.0% | 79.0% | 25 / 0 |
| **Итого** | **500** | **475** | **25** | **412** | **28** | **35** | **92.6%** | **93.6%** | **86.7%** | **25 / 0** |

Reject stress — искусственный тест защитной отбраковки, а не оценка частоты ошибок физической станции.
