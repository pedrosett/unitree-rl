# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview - ISAAC SIM MIGRATION 🚀

**MAJOR TRANSITION**: This project is migrating from Isaac Gym to NVIDIA Isaac Sim + Isaac Lab + GR00T integration for next-generation humanoid robot control.

### Current State
- **Legacy System**: Isaac Gym with PPO training (deprecated but functional)
- **Target System**: Isaac Sim 5.0.0 + Isaac Lab + GR00T N1.5 foundation model
- **Migration Focus**: Unitree G1 humanoid robot with keyboard/gamepad teleoperation

### New Architecture (Isaac Sim + Isaac Lab)
- **Simulation**: NVIDIA Isaac Sim 5.0.0 (Omniverse USD-based)
- **Framework**: Isaac Lab (GPU-accelerated robotics learning)
- **AI Foundation**: GR00T N1.5 (pre-trained humanoid behaviors)  
- **Control**: Keyboard teleoperation → Future gamepad integration
- **Target Robot**: Unitree G1 humanoid (primary focus)

## Development Commands

### Environment Setup - Isaac Sim Migration

### 📂 PADRÃO DE ORGANIZAÇÃO OBRIGATÓRIO
**TODOS os repos externos devem ser clonados DENTRO de `/home/pedro_setubal/Workspaces/unitree_rl/`**

Exemplo isaacgym (já existente):
- ✅ `/home/pedro_setubal/Workspaces/unitree_rl/isaacgym/`

Novos repos devem seguir o mesmo padrão:
- 🔄 `/home/pedro_setubal/Workspaces/unitree_rl/IsaacLab/`
- 🔄 `/home/pedro_setubal/Workspaces/unitree_rl/Isaac-GR00T/`

#### AMBIENTE EXISTENTE: unitree-rl (USAR ESTE)
```bash
# Usar ambiente existente (NÃO criar novo)
conda activate unitree-rl  # Python 3.8.20 + GLIBC 2.39

# Instalar Isaac Sim no ambiente existente
pip install "isaacsim[all,extscache]==5.0.0" --extra-index-url https://pypi.nvidia.com

# Isaac Lab from source (DENTRO DO REPO unitree_rl)
cd /home/pedro_setubal/Workspaces/unitree_rl
git clone https://github.com/isaac-sim/IsaacLab.git
cd IsaacLab && ./isaaclab.sh --install

# GR00T N1.5 (DENTRO DO REPO unitree_rl)
cd /home/pedro_setubal/Workspaces/unitree_rl
git clone https://github.com/NVIDIA/Isaac-GR00T.git
cd Isaac-GR00T && pip install -e .
```

#### SISTEMA ISAAC GYM (MANTER PARA COMPARAÇÃO)
```bash
# ✅ FUNCIONAL - Manter para comparação com GR00T
conda activate unitree-rl  # Mesmo ambiente
cd /home/pedro_setubal/Workspaces/unitree_rl/isaacgym/python/examples/unitree_rl_gym
# Modelo WASD atual disponível para testes
```

### Isaac Lab Teleoperation + GR00T (FOCO PRINCIPAL)

#### NOVA ABORDAGEM: Isaac Lab + GR00T (SEM TRAINING)
```bash
# Ativar ambiente Isaac Lab
conda activate isaac-lab-groot

# Isaac Lab teleoperation com keyboard
cd IsaacLab
./isaaclab.sh -p source/standalone/demos/teleoperation.py --task Isaac-Reach-Franka-v0 --teleop_device keyboard

# Target: Unitree G1 teleoperation
./isaaclab.sh -p source/standalone/demos/teleoperation.py --task Isaac-Humanoid-Unitree-G1-v0 --teleop_device keyboard

# Isaac Lab + GR00T integration (meta)
./isaaclab.sh -p scripts/groot_teleop.py --robot unitree_g1 --policy groot_n15 --device keyboard --sim_device cuda
```

#### SISTEMA DEPRECIADO: Isaac Gym (REMOVIDO)
```bash
# ⚠️ COMPLETAMENTE DEPRECIADO
# Não usamos mais treinamento RL/PPO
# Apenas GR00T inference via Isaac Lab
```

### Testing and Visualization
```bash
# Visualize trained policy
python legged_gym/scripts/play.py --task=g1

# Load specific checkpoint
python legged_gym/scripts/play.py --task=g1 --load_run=<run_folder> --checkpoint=<checkpoint_number>

# IMPORTANT: Always run simulations in separate terminal and provide feedback
# Example with FINAL WORKING MODEL (WASD + Natural Walking):
cd /home/pedro_setubal/Workspaces/unitree_rl/isaacgym/python/examples/unitree_rl_gym
python legged_gym/scripts/play.py --task g1 --load_run Aug12_16-59-06_ --checkpoint 1000 --num_envs 1

# FINAL SYSTEM SUCCESS (Aug 12, 2025):
# - WASD + Natural Walking: 997.73 episode length (practically immortal)
# - Mean Reward: 25.51 (proven biomimetic behavior)
# - Perfect Foot Contact: Natural walking, no heel walking
# - Continuous Simulation: 1 hour episodes (3600s vs 20s)
# - GPU Optimization: 63% → 95% utilizable (4096 → 8192 → 16384 envs)
# - MODEL: Aug12_16-59-06_/model_1000.pt (PRODUCTION READY)
```

### Simulation Testing Protocol
**CRITICAL**: Claude should NEVER execute simulation commands directly. Instead:

1. **Claude provides command**: Complete bash command ready to execute
2. **User runs in separate terminal**: Copy-paste and execute command
3. **User provides feedback**: Console output, behavior observations, errors
4. **Claude analyzes results**: Based on user feedback, not direct execution

**Rationale**: 
- Isaac Gym simulations require interactive GUI focus
- WASD keyboard controls need user input
- Visual behavior assessment requires human observation
- Long-running processes benefit from user monitoring

### Deployment
```bash
# Sim2Sim validation with MuJoCo
python deploy/deploy_mujoco/deploy_mujoco.py g1.yaml

# Real robot deployment
python deploy/deploy_real/deploy_real.py {network_interface} g1.yaml
```

### Testing
```bash
# No formal test suite - validation is done through:
# 1. Training convergence monitoring (TensorBoard)
# 2. Visual inspection with play.py
# 3. Sim2Sim validation with MuJoCo
```

## Architecture

### Directory Structure (Updated for GR00T)
- **README.md**: Documentação principal GR00T + Isaac Sim
- **CLAUDE.md**: Este arquivo - workflow Isaac Lab + GR00T
- **PLANO_EXECUTIVO_GROOT_WASD.md**: Checklist implementação
- **MDs/**: Documentação organizada
  - **old_research/**: 🚫 Era Isaac Gym (DEPRECADO)
    - ***.md**: Guias Isaac Gym + PPO  
    - **salto mortal/**: Pesquisa pulos
    - ***.pdf**: Documentos antigos
  - **README_OLD_RESEARCH.md**: Explicação organização
- **IsaacLab/**: 🔄 Isaac Lab framework (será clonado)
- **Isaac-GR00T/**: 🔄 GR00T N1.5 foundation model (será clonado)
- **isaacgym/**: Sistema legacy Isaac Gym (manter para comparação)
- **models/**: Modelos Isaac Gym (legacy)

### Key Components (GR00T Era)

1. **Isaac Lab Framework**: Teleoperation and robotics learning
   - Location: `IsaacLab/source/standalone/demos/teleoperation.py`
   - Provides keyboard/gamepad input handling
   - Task management for different robots

2. **GR00T Foundation Model**: Pre-trained humanoid intelligence
   - Location: `Isaac-GR00T/` 
   - N1.5 model with locomotion behaviors
   - Zero training required - inference only

3. **Isaac Sim Integration**: Physics simulation
   - USD-based robot models
   - Real-time visualization and validation
   - GPU-accelerated simulation

### Configuration System (GR00T Era)

- **Isaac Lab Tasks**: Robot environments in Isaac Lab
  - `IsaacLab/source/extensions/omni.isaac.lab_tasks/`
  - Task definitions for different robots
  - Built-in teleoperation support

- **GR00T Configs**: Foundation model parameters  
  - `Isaac-GR00T/configs/` - Model configurations
  - Pre-trained weights and inference settings
  - WASD to action mappings

## Important Notes

### GPU Requirements & Optimization
- Requires NVIDIA GPU with CUDA support
- Recommended: Driver 525+ for Isaac Gym compatibility
- Training uses GPU-accelerated parallel environments:
  - Default: 4096 envs (63% GPU utilization)
  - Optimized: 8192 envs (85-90% GPU utilization)
  - Maximum: 16384 envs (95-100% GPU utilization, 16GB+ VRAM required)

### Workflow Pattern (GR00T Era)
1. **Setup**: Install Isaac Sim + Isaac Lab + GR00T in `unitree-rl` environment
2. **Test Isaac Lab**: Validate teleoperation framework with demos
3. **Integrate GR00T**: Connect foundation model as policy backend
4. **WASD Validation**: User tests W/S/A/D controls visually
5. **No Training**: Only inference - GR00T has pre-trained behaviors

### GR00T Model Management
- **Foundation Model**: GR00T N1.5 pre-trained weights
- **Zero Training**: No checkpoints, no training logs
- **Isaac Lab Integration**: GR00T as policy backend
- **Legacy System**: Keep Isaac Gym for comparison
  - Previous model: `Aug12_16-59-06_/model_1000.pt`

### GR00T Integration Notes
- **No Reward Tuning**: GR00T is pre-trained, no reward functions needed
- **WASD Mapping**: Configure keyboard inputs in Isaac Lab
  - W/S: Forward/backward locomotion commands
  - A/D: Left/right turning commands
- **Task Configuration**: Isaac Lab task setup for Unitree G1
- **Model Loading**: GR00T N1.5 weights and inference configuration

### Dependencies (Updated)
- **Isaac Sim 5.0.0**: Main simulation platform (via pip)
- **Isaac Lab**: Teleoperation framework (from source)
- **GR00T N1.5**: Foundation model (from source)  
- **PyTorch 2.4.1**: Already installed in unitree-rl
- **Legacy Isaac Gym**: Kept for comparison