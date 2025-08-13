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

### Directory Structure
- **models/**: Model versioning system
  - **MODEL_REGISTRY.md**: Track all model versions and metrics
  - **production/**: Production-ready models
  - **testing/**: Models under test (A/D fix, etc)
  - **experiments/**: Experimental versions
- **isaacgym/**: Isaac Gym simulator installation
  - **python/examples/unitree_rl_gym/**: Main project directory
    - **legged_gym/**: Core RL framework
      - **envs/**: Robot-specific environments (g1/, h1/, h1_2/, go2/)
      - **scripts/**: Training (train.py) and testing (play.py)
      - **utils/**: Task registry and helpers
    - **deploy/**: Deployment configurations
      - **deploy_mujoco/**: Sim2Sim validation
      - **deploy_real/**: Real robot deployment (Python + C++)
      - **pre_train/**: Pre-trained models
    - **resources/robots/**: URDF models and meshes
    - **logs/**: Training logs and checkpoints

### Key Components

1. **Environment Classes**: Each robot has its own environment class inheriting from `BaseTask`
   - Location: `legged_gym/envs/{robot_name}/{robot_name}_config.py`
   - Defines observation/action spaces, rewards, domain randomization

2. **Training Pipeline**: PPO algorithm from rsl-rl library
   - Entry point: `legged_gym/scripts/train.py`
   - Config loading → Environment creation → PPO training loop

3. **Deployment Pipeline**: 
   - Sim2Sim: Validates policies in MuJoCo before real deployment
   - Sim2Real: Deploys to physical robots with safety checks

### Configuration System

- **Robot Configs**: Python classes in `legged_gym/envs/{robot}/`
  - `{robot}_config.py`: Environment configuration
  - `{robot}.py`: Environment implementation

- **Deployment Configs**: YAML files in `deploy/*/configs/`
  - Control frequencies, gains, safety limits

## Important Notes

### GPU Requirements & Optimization
- Requires NVIDIA GPU with CUDA support
- Recommended: Driver 525+ for Isaac Gym compatibility
- Training uses GPU-accelerated parallel environments:
  - Default: 4096 envs (63% GPU utilization)
  - Optimized: 8192 envs (85-90% GPU utilization)
  - Maximum: 16384 envs (95-100% GPU utilization, 16GB+ VRAM required)

### Workflow Pattern
1. Train policy with `train.py` (logs to `logs/` directory)
2. Validate visually with `play.py`
3. Test robustness with MuJoCo sim2sim
4. Deploy to real robot with safety parameters

### Model Checkpoints & Versioning
- Saved in `logs/{robot_name}/{date_time}/` 
- TensorBoard events for monitoring training
- Load specific checkpoints with `--load_run` and `--checkpoint` flags
- **Model Registry**: Check `models/MODEL_REGISTRY.md` for:
  - Production models (e.g., Aug12_16-59-06_/model_1000.pt)
  - Testing models (e.g., A/D responsiveness fixes)
  - Naming convention: `{FEATURE}_{VARIANT}_v{MAJOR}.{MINOR}`

### Common Modifications
- **Reward tuning**: Edit reward scales in `{robot}_config.py`
  - Current focus: `tracking_ang_vel = 2.5` for A/D responsiveness
  - `action_rate = -0.005` for faster response
- **Observation space**: Modify `_get_obs()` in environment class
- **Domain randomization**: Adjust ranges in config classes
- **Action space**: Change `num_actions` and action scaling

### Dependencies
- Isaac Gym (proprietary, must be installed from NVIDIA)
- rsl-rl (PPO implementation)
- PyTorch 2.3.1 with CUDA
- MuJoCo 3.2.3 (for sim2sim validation)