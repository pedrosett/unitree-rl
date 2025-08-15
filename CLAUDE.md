# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview - DUAL SYSTEM ARCHITECTURE 🚀

**MAJOR EVOLUTION**: This project now operates as a **dual system** combining both established RL Local training with cutting-edge GR00T foundation model integration.

### Current State - Two Complementary Systems
- **System 1 - RL Local**: Isaac Gym + PPO training (**✅ PRODUCTION READY**)
- **System 2 - GR00T**: Isaac Sim 5.0.0 + Isaac Lab + GR00T N1.5 foundation model (**🔄 IN DEVELOPMENT**)
- **Focus**: Unitree G1 humanoid robot with WASD teleoperation on RTX 4070 Super

### System 1 - RL Local (Production Ready)
- **Status**: ✅ **FULLY OPERATIONAL** - RTX 4070 Super + Ubuntu 24.04
- **Environment**: Python 3.8.20 + Isaac Gym + PyTorch 2.4.1
- **Performance**: 989+ episode length, WASD W/S perfect, A/D functional but slow
- **Current Model**: `Aug12_12-51-21_/model_1110.pt` (WASD_Extended_v0.2)
- **Next Action**: Continue training 1110 → 5000 iterations to fix A/D curves

### System 2 - GR00T Architecture (In Development)
- **Simulation**: NVIDIA Isaac Sim 5.0.0 (Omniverse USD-based) ✅ Working
- **Framework**: Isaac Lab (GPU-accelerated robotics learning)
- **AI Foundation**: GR00T N1.5 (pre-trained humanoid behaviors)  
- **Control**: SE(2) teleoperation + Natural language commands
- **Target Robot**: Unitree G1 humanoid (primary focus)
- **Status**: STEP 4 ready for execution (Isaac Lab + GR00T integration)

## Development Commands - Dual System

### 📂 MANDATORY ORGANIZATION STANDARD
**ALL external repos must be cloned INSIDE `/home/pedro_setubal/Workspaces/unitree_rl/`**

Current structure:
- ✅ `/home/pedro_setubal/Workspaces/unitree_rl/isaacgym/` (System 1)
- ✅ `/home/pedro_setubal/Workspaces/unitree_rl/local_RL/` (System 1 docs)
- ✅ `/home/pedro_setubal/Workspaces/unitree_rl/unitree-groot/` (System 2 docs)
- 🔄 `/home/pedro_setubal/Workspaces/unitree_rl/IsaacLab/` (System 2)
- 🔄 `/home/pedro_setubal/Workspaces/unitree_rl/Isaac-GR00T/` (System 2)

### System 1 - RL Local Environment (ACTIVE)
```bash
# ALWAYS USE for System 1 (RL Local)
source ~/anaconda3/etc/profile.d/conda.sh
conda activate unitree-rl  # Python 3.8.20 + Isaac Gym working

# Complete environment setup
unset PYTHONPATH
export ISAAC_GYM_ROOT_DIR=/home/pedro_setubal/Workspaces/unitree_rl/isaacgym
export LD_LIBRARY_PATH="$CONDA_PREFIX/lib:$LD_LIBRARY_PATH"
export ISAAC_GYM_USE_GPU_PIPELINE=1
export CUDA_VISIBLE_DEVICES=0
cd /home/pedro_setubal/Workspaces/unitree_rl/isaacgym/python/examples/unitree_rl_gym
```

### System 2 - GR00T Environment Setup
```bash
# Use for System 2 (GR00T)
conda activate unitree-groot  # Python 3.11.13 + Isaac Sim

# Install Isaac Sim (if not already installed)
pip install "isaacsim[all,extscache]==5.0.0" --extra-index-url https://pypi.nvidia.com

# Isaac Lab from source (INSIDE unitree_rl repo)
cd /home/pedro_setubal/Workspaces/unitree_rl
git clone https://github.com/isaac-sim/IsaacLab.git
cd IsaacLab && ./isaaclab.sh --install

# GR00T N1.5 (INSIDE unitree_rl repo)
cd /home/pedro_setubal/Workspaces/unitree_rl
git clone https://github.com/NVIDIA/Isaac-GR00T.git
cd Isaac-GR00T && pip install -e .
```

## System 1 - RL Local Commands (PRODUCTION)

### Current Working Model Testing
```bash
# Test current model (WASD_Extended_v0.2 - A/D slow issue)
python legged_gym/scripts/play.py --task g1 --load_run Aug12_12-51-21_ --checkpoint 1110 --num_envs 1

# Test production model (for comparison)
python legged_gym/scripts/play.py --task g1 --load_run Aug12_16-59-06_ --checkpoint 1000 --num_envs 1
```

### Continue Training (Fix A/D Curves)
```bash
# Phase 1: 500 additional iterations (validation)
python legged_gym/scripts/train.py --task g1 \
  --resume --load_run Aug12_12-51-21_ --checkpoint 1110 \
  --max_iterations 1610 --headless --num_envs 8192

# Phase 2: Full convergence (if Phase 1 positive)  
python legged_gym/scripts/train.py --task g1 \
  --resume --load_run Aug12_12-51-21_ --checkpoint 1610 \
  --max_iterations 5000 --headless --num_envs 8192
```

### TensorBoard Monitoring
```bash
# Monitor training progress (separate terminal)
tensorboard --logdir logs/g1/ --port 6006
# Focus metric: rew_tracking_ang_vel should grow 0.21 → 0.55+
```

## System 2 - GR00T Commands (DEVELOPMENT)

### Isaac Sim Testing (Working)
```bash
# Launch Isaac Sim UI (tested and working)
conda activate unitree-groot
export OMNI_KIT_ACCEPT_EULA=YES
isaacsim isaacsim.exp.full --reset-user --/exts/isaacsim.ros2.bridge/enabled=false
```

### Isaac Lab + GR00T Integration (STEP 4)
```bash
# Follow complete STEP 4 guide (7 parts A-G)
# See: unitree-groot/STEP4_G1_TELEOP_AND_GROOT.md

# Isaac Lab teleoperation with keyboard (target)
cd IsaacLab
./isaaclab.sh -p source/standalone/demos/teleoperation.py --task Isaac-Humanoid-Unitree-G1-v0 --teleop_device keyboard

# Isaac Lab + GR00T integration (meta - target)
./isaaclab.sh -p scripts/groot_teleop.py --robot unitree_g1 --policy groot_n15 --device keyboard --sim_device cuda
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

### Directory Structure (Dual System)
- **README.md**: Main dual system documentation (both RL Local + GR00T)
- **CLAUDE.md**: This file - dual system workflow and commands
- **local_RL/**: System 1 - RL Local documentation and setup guides
  - **RL_LOCAL_4070_RTX_Setup_Treinamento.md**: Complete setup guide 
  - **MODEL_REGISTRY.md**: All trained models registry
  - **README.md**: RL Local system index
- **unitree-groot/**: System 2 - GR00T documentation and setup guides  
  - **README.md**: GR00T system documentation (original README)
  - **STEP4_G1_TELEOP_AND_GROOT.md**: Current development guide
- **isaacgym/**: System 1 - RL Local Isaac Gym implementation
- **IsaacLab/**: 🔄 System 2 - Isaac Lab framework (will be cloned)
- **Isaac-GR00T/**: 🔄 System 2 - GR00T N1.5 foundation model (will be cloned)
- **models/**: System 1 - Trained models and checkpoints
- **MDs/**: Historical documentation (pre-dual system)

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

### Current Status Summary

#### System 1 - RL Local Status
- **Environment**: ✅ **FULLY WORKING** - RTX 4070 Super + Python 3.8 + Isaac Gym
- **Model**: WASD_Extended_v0.2 (1110 iterations) - W/S perfect, A/D slow curves
- **Issue Identified**: Subtraining - need 5000+ iterations for full convergence  
- **Solution**: Continue training 1110 → 1610 → 5000 (scientific prediction: 85% success)
- **Performance**: 989+ episode length, 19.04 mean reward, natural walking

#### System 2 - GR00T Status  
- **Isaac Sim**: ✅ **WORKING** - UI stable, physics validated
- **G1 USD Model**: ✅ **WORKING** - Converted and tested
- **Current Phase**: STEP 4 - Isaac Lab + GR00T N1.5 integration
- **Target**: Zero-training foundation model with SE(2) teleoperation + NL commands

### Development Workflow
1. **System 1 Priority**: Fix A/D curves via extended training (immediate)
2. **System 2 Development**: Complete STEP 4 Isaac Lab + GR00T integration
3. **Comparison**: Validate both systems for different use cases
4. **Documentation**: Maintain both systems documentation in parallel

### Hardware Requirements
- **GPU**: NVIDIA RTX 4070 Super (verified working both systems)
- **OS**: Ubuntu 24.04 LTS with X11 session
- **Driver**: NVIDIA 575.64.03 (stable for both Isaac Gym + Isaac Sim)
- **RAM**: 32GB recommended (both systems can run concurrently)
- **Storage**: ~40GB total (Isaac Gym ~15GB + Isaac Sim ~25GB)