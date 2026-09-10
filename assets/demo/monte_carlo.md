# MONTE CARLO SYNTHETIC

> Проверяет геометрию на упрощённых синтетических данных линейного профилометра; не измеряет абсолютную точность физической станции.

Seed: 20261017; cases: 500; configuration: FROZEN BEFORE FINAL SEED.

| Поднабор | Total | Expected-valid | Expected-reject | Correct OK | Wrong OK | Rejected valid | Acceptance rate | Precision among accepted | Correct measurement rate | Reject correct / false accepted |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| yaw_only | 125 | 125 | 0 | 125 | 0 | 0 | 100.0% | 100.0% | 100.0% | 0 / 0 |
| tilted_irregular | 125 | 125 | 0 | 90 | 16 | 19 | 84.8% | 84.9% | 72.0% | 0 / 0 |
| small_object | 125 | 125 | 0 | 123 | 0 | 2 | 98.4% | 100.0% | 98.4% | 0 / 0 |
| noisy_incomplete | 125 | 100 | 25 | 89 | 11 | 0 | 100.0% | 89.0% | 89.0% | 25 / 0 |
| **Итого** | **500** | **475** | **25** | **427** | **27** | **21** | **95.6%** | **94.1%** | **89.9%** | **25 / 0** |

Expected-reject stress - искусственный тест защитной отбраковки, а не оценка частоты ошибок физической станции.
