# 📊 Model Registry - Unitree G1 WASD System

## 🎯 Production Models
| Model | Path | Steps | Performance | Features | Status |
|-------|------|-------|-------------|----------|--------|
| **WASD_Natural_v1.0** | `Aug12_16-59-06_/model_1000.pt` | 1000 | 997.73 ep, 25.51 reward | Natural walking, 1hr sim | ✅ PRODUCTION |

## 🧪 Testing Models  
| Model | Path | Steps | Performance | Issue | Status |
|-------|------|-------|-------------|-------|--------|
| WASD_Initial_v0.1 | `Aug12_10-26-07_/model_110.pt` | 110 | ~989 ep | Initial test | 🔄 Reference |
| WASD_Extended_v0.2 | `Aug12_12-51-21_/model_1110.pt` | 1110 | Good stability | Slow turns | 🔄 Reference |
| WASD_AD_Fix_v0.3 | `Aug12_17-38-50_/model_200.pt` | 200 | 5.06 reward, 178.13 ep | A/D responsiveness | 🧪 Testing |

## 🔬 Experiments
| Model | Path | Steps | Performance | Notes | Status |
|-------|------|-------|-------------|-------|--------|
| Biomimetic_Jump | `archive/` | 1000 | 30.88 reward | Heel walking | ❌ Failed |

## 📋 Naming Convention
```
{FEATURE}_{VARIANT}_v{MAJOR}.{MINOR}
- FEATURE: WASD, Jump, Natural, etc.
- VARIANT: Initial, Extended, Fix, Optimized
- MAJOR: Breaking changes
- MINOR: Incremental improvements
```

## 🎮 Quick Test Commands
```bash
# Production model (Natural walking)
python play.py --task g1 --load_run Aug12_16-59-06_ --checkpoint 1000 --num_envs 1

# Initial WASD test (110 steps)
python play.py --task g1 --load_run Aug12_10-26-07_ --checkpoint 110 --num_envs 1

# Extended WASD (1110 steps)
python play.py --task g1 --load_run Aug12_12-51-21_ --checkpoint 1110 --num_envs 1

# A/D Fix test (200 steps)
python play.py --task g1 --load_run Aug12_17-38-50_ --checkpoint 200 --num_envs 1
```