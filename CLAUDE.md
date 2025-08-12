# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a reinforcement learning (RL) framework for training Unitree robots (Go2, G1, H1, H1_2) using Isaac Gym simulation. The project implements a complete pipeline from simulation training to real robot deployment.

## Development Commands

### Environment Setup
```bash
# Activate conda environment
conda activate unitree-rl

# If environment doesn't exist:
conda create -n unitree-rl python=3.8
conda activate unitree-rl
cd isaacgym/python && pip install -e .
cd examples/unitree_rl_gym && pip install -e .
```

### Training
```bash
# Train a robot policy (from unitree_rl_gym directory)
python legged_gym/scripts/train.py --task=g1  # Options: go2, g1, h1, h1_2

# Resume training from checkpoint
python legged_gym/scripts/train.py --task=g1 --resume --load_run=<run_folder> --checkpoint=<checkpoint_number>
```

### Testing and Visualization
```bash
# Visualize trained policy
python legged_gym/scripts/play.py --task=g1

# Load specific checkpoint
python legged_gym/scripts/play.py --task=g1 --load_run=<run_folder> --checkpoint=<checkpoint_number>

# IMPORTANT: Always run simulations in separate terminal and provide feedback
# Example with latest G1 model (WASD+JUMP OPTIMIZED):
cd /home/pedro_setubal/Workspaces/unitree_rl/isaacgym/python/examples/unitree_rl_gym
python legged_gym/scripts/play.py --task g1 --load_run Aug12_13-38-50_ --checkpoint 1000 --num_envs 1

# BREAKTHROUGH ACHIEVED (Aug 12, 2025):
# - Angular velocity tracking: 6,748% improvement (0.0100 → 0.6848)
# - Episode stability: 997.73 steps (virtually immortal robot)
# - Jump integration: Ready for SPACEBAR activation
# - Tight turns: 87% faster response with optimized WZ parameters
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

### GPU Requirements
- Requires NVIDIA GPU with CUDA support
- Recommended: Driver 525+ for Isaac Gym compatibility
- Training uses GPU-accelerated parallel environments (typically 4096+)

### Workflow Pattern
1. Train policy with `train.py` (logs to `logs/` directory)
2. Validate visually with `play.py`
3. Test robustness with MuJoCo sim2sim
4. Deploy to real robot with safety parameters

### Model Checkpoints
- Saved in `logs/{robot_name}/{date_time}/` 
- TensorBoard events for monitoring training
- Load specific checkpoints with `--load_run` and `--checkpoint` flags

### Common Modifications
- **Reward tuning**: Edit reward scales in `{robot}_config.py`
- **Observation space**: Modify `_get_obs()` in environment class
- **Domain randomization**: Adjust ranges in config classes
- **Action space**: Change `num_actions` and action scaling

### Dependencies
- Isaac Gym (proprietary, must be installed from NVIDIA)
- rsl-rl (PPO implementation)
- PyTorch 2.3.1 with CUDA
- MuJoCo 3.2.3 (for sim2sim validation)