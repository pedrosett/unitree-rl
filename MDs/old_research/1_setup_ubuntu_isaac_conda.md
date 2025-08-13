````markdown
# Guia Completo — **Unitree G1 (12DOF)** no **Ubuntu 24.04** com **Isaac Gym** + **RSL-RL** + **MuJoCo**  
*(Ambiente validado e executando Sim2Sim com policy pré-treinada; foco em simulação)*

> **Contexto (máquina do Pedro)**  
> Data base: **11/Ago/2025**  
> SO: **Ubuntu 24.04**  
> GPU: **RTX 4070 Super**  
> Driver NVIDIA: **575.64.03** (`CUDA Runtime 12.9` via `nvidia-smi`)  
> Conda: **Anaconda3** com env **`unitree-rl` (Python 3.8)**  
> Pastas principais:  
> • Isaac Gym: `/home/pedro_setubal/Workspaces/unitree_rl/isaacgym`  
> • Projeto RL Gym: `/home/pedro_setubal/Workspaces/unitree_rl/isaacgym/python/examples/unitree_rl_gym`

---

## 0) Visão geral (o que é cada coisa)

- **Isaac Gym (Preview 4)**: simulador com física **GPU PhysX** altamente paralelizável. É onde coletamos amostras **rápido** para treinar RL (muitos ambientes em paralelo na GPU).  
- **RSL-RL**: implementação de **PPO** (ETH/Legged Robotics) otimizada para GPU e integrada ao ecossistema *legged_gym*.  
- **unitree_rl_gym**: código da Unitree com tarefas/robôs prontos (inclui **G1 12DOF**), scripts de treino (`train.py`), visualização (`play.py`) e *deploy* (MuJoCo e Real).  
- **MuJoCo (3.2.3)**: motor de física **preciso**. Usamos para **Sim2Sim** (testar a policy treinada no Isaac em outro simulador).  
- **Policy pré-treinada**: arquivo `.pt` com a rede do ator (controle). Permite ver o G1 “andar” **sem** treinar do zero.

> Pipeline resumido: **Treinar no Isaac Gym → Validar no Isaac (play) → Validar no MuJoCo (Sim2Sim)**.  
> *Neste guia vamos até Sim2Sim; **não** cobrimos deployment em robô real por opção.*

---

## 1) Instalação que foi feita **neste PC**

### 1.1 Drivers NVIDIA
```bash
sudo ubuntu-drivers devices
sudo apt update
sudo apt install -y nvidia-driver-575-open
sudo reboot
# Após reiniciar:
nvidia-smi   # → Driver 575.64.03, CUDA 12.9, RTX 4070 Super
````

### 1.2 Conda + ambiente

```bash
# Anaconda já instalado
conda create -y -n unitree-rl python=3.8
conda activate unitree-rl
```

### 1.3 Isaac Gym (Preview 4)

Download (NVIDIA Dev, login/aceite de licença), depois **instalação em modo editável**:

```bash
# Arquivos extraídos para:
# /home/pedro_setubal/Workspaces/unitree_rl/isaacgym

pip install -U pip setuptools wheel
pip install -e /home/pedro_setubal/Workspaces/unitree_rl/isaacgym/python
```

> **Mudança de caminho**: o Isaac Gym foi movido de `~/isaacgym` para
> `/home/pedro_setubal/Workspaces/unitree_rl/isaacgym`. Por isso **reinstalamos** o pacote em modo `-e` e atualizamos variáveis de ambiente.

Variáveis usadas nos terminais de execução:

```bash
unset PYTHONPATH
export ISAAC_GYM_ROOT_DIR=/home/pedro_setubal/Workspaces/unitree_rl/isaacgym
export LD_LIBRARY_PATH="$CONDA_PREFIX/lib:$LD_LIBRARY_PATH"
export ISAAC_GYM_USE_GPU_PIPELINE=1
export CUDA_VISIBLE_DEVICES=0
```

Teste rápido (exemplo gráfico do Isaac):

```bash
cd /home/pedro_setubal/Workspaces/unitree_rl/isaacgym/python/examples
python 1080_balls_of_solitude.py
# OBS: alguns exemplos "forçam" CPU pipeline; para ver GPU pipeline:
python cartpole.py --use_gpu_pipeline --sim_device cuda:0 --rl_device cuda:0
```

### 1.4 RSL-RL (versão compatível)

A *branch* mais nova pede `torch>=2.6`, então fixamos a tag estável **v1.0.2**:

```bash
# se preciso, limpe resquícios
pip uninstall -y rsl-rl-lib rsl_rl || true

# Opção A (PyPI, quando disponível):
pip install rsl-rl-lib==1.0.2

# Opção B (garantia por Git):
cd /tmp
git clone https://github.com/leggedrobotics/rsl_rl.git
cd rsl_rl
git checkout v1.0.2
pip install -e .
```

### 1.5 unitree\_rl\_gym (repositório do projeto)

```bash
cd /home/pedro_setubal/Workspaces/unitree_rl/isaacgym/python/examples
git clone https://github.com/unitreerobotics/unitree_rl_gym.git
pip install -e /home/pedro_setubal/Workspaces/unitree_rl/isaacgym/python/examples/unitree_rl_gym
```

> **Após mover pastas**: se aparecer `ModuleNotFoundError: legged_gym`, reinstale com `pip install -e <novo_caminho_do_repo>` (como acima).

### 1.6 MuJoCo (Sim2Sim)

A versão do projeto pede **3.2.3**:

```bash
pip uninstall -y mujoco mujoco-python-viewer
pip install mujoco==3.2.3
# Para rodar sem GUI no Linux:
export MUJOCO_GL=egl
```

---

## 2) Validações que rodamos

### 2.1 Smoke test de treino (G1 12DOF, 10 iterações)

```bash
cd /home/pedro_setubal/Workspaces/unitree_rl/isaacgym/python/examples/unitree_rl_gym
python legged_gym/scripts/train.py \
  --task g1 \
  --num_envs 64 \
  --max_iterations 10 \
  --headless
```

**Sinais OK**:

* `+++ Using GPU PhysX` e `GPU Pipeline: enabled`
* Compilação de `gymtorch` concluída
* Logs de iteração (0→9) com métricas (rewards, losses etc.)

> Observamos `Actor/ Critic` MLP + **LSTM** sendo criados e métricas aumentando pouco (normal em 10 iterações — é só “teste de fumaça”, não para “aprender a andar”).

### 2.2 Sim2Sim no MuJoCo com **policy pré-treinada**

Confirmamos que o arquivo existe:

```
/home/pedro_setubal/Workspaces/unitree_rl/isaacgym/python/examples/unitree_rl_gym/deploy/pre_train/g1/motion.pt
```

Rodamos:

```bash
cd /home/pedro_setubal/Workspaces/unitree_rl/isaacgym/python/examples/unitree_rl_gym
# opcional headless:
export MUJOCO_GL=egl
python deploy/deploy_mujoco/deploy_mujoco.py g1.yaml
```

**Resultado**: janela (ou headless) do MuJoCo com o **G1 andando** usando a policy pré-treinada 🟢

---

## 3) “Mão na massa”: *cheat-sheet* para uso diário

### 3.1 Ativar ambiente e variáveis

```bash
conda activate unitree-rl
unset PYTHONPATH
export ISAAC_GYM_ROOT_DIR=/home/pedro_setubal/Workspaces/unitree_rl/isaacgym
export LD_LIBRARY_PATH="$CONDA_PREFIX/lib:$LD_LIBRARY_PATH"
export ISAAC_GYM_USE_GPU_PIPELINE=1
export CUDA_VISIBLE_DEVICES=0
```

*(opcional) Persistir via hooks do conda: atualize `activate.d/unitree.sh` com o novo caminho acima.*

### 3.2 Teste Isaac Gym rápido

```bash
cd /home/pedro_setubal/Workspaces/unitree_rl/isaacgym/python/examples
python cartpole.py --use_gpu_pipeline --sim_device cuda:0 --rl_device cuda:0
```

### 3.3 Treinar G1 (run “de verdade”)

```bash
cd /home/pedro_setubal/Workspaces/unitree_rl/isaacgym/python/examples/unitree_rl_gym
python legged_gym/scripts/train.py \
  --task g1 \
  --num_envs 2048 \
  --max_iterations 10000 \
  --experiment_name G1_12DOF_PPO \
  --run_name run1 \
  --headless
```

### 3.4 Visualizar e exportar policy no Isaac (play)

```bash
python legged_gym/scripts/play.py \
  --task g1 \
  --experiment_name G1_12DOF_PPO \
  --run_name run1 \
  --headless False
```

Será exportado algo como:

```
logs/G1_12DOF_PPO/<timestamp>_run1/exported/policies/policy_1.pt
```

### 3.5 Validar no MuJoCo (usando sua policy)

Edite `deploy/deploy_mujoco/configs/g1.yaml` → `policy_path: "<caminho/para/sua/policy_1.pt>"`, então:

```bash
export MUJOCO_GL=egl   # se quiser headless
python deploy/deploy_mujoco/deploy_mujoco.py g1.yaml
```

---

## 4) Solução de problemas (o que já resolvemos)

* **Após mover pastas, Isaac Gym “sumiu”**
  → Reinstale em modo editável:
  `pip install -e /home/pedro_setubal/Workspaces/unitree_rl/isaacgym/python`

* **`ModuleNotFoundError: legged_gym`**
  → Reinstale o projeto no novo caminho:
  `pip install -e /home/pedro_setubal/Workspaces/unitree_rl/isaacgym/python/examples/unitree_rl_gym`

* **`rsl_rl` exigindo `torch>=2.6`**
  → Fixe a versão **v1.0.2** (PyPI `rsl-rl-lib==1.0.2` ou Git `git checkout v1.0.2`)

* **`GLIBCXX_3.4.32 not found` ao compilar `gymtorch`**
  → `conda install -c conda-forge libstdcxx-ng>=12.2.0 gxx_linux-64=12` e limpe cache:
  `rm -rf ~/.cache/torch_extensions/py38_cu121/gymtorch`

* **Alguns exemplos do Isaac mostram “Forcing CPU pipeline”**
  → É comportamento do *sample*. Para forçar GPU, use `cartpole.py` com `--use_gpu_pipeline`

* **MuJoCo sem GUI no servidor**
  → `export MUJOCO_GL=egl`

---

## 5) **Treinar sua própria policy** (didático e direto)

1. **Escolher parâmetros base**

   * `--num_envs`: 1024–4096 (ajuste pela VRAM; mais envs = mais rápido)
   * `--max_iterations`: 10k–50k (humanoides exigem mais tempo que quadrúpedes)
   * `--headless`: sem render = mais performance
   * `--experiment_name / --run_name`: organização dos logs/output

2. **Rodar o treino**

   ```bash
   python legged_gym/scripts/train.py \
     --task g1 \
     --num_envs 2048 \
     --max_iterations 20000 \
     --experiment_name G1_12DOF_PPO \
     --run_name run2 \
     --headless
   ```

3. **Acompanhar progresso**

   * Reward média subindo, queda na frequência de “quedas” (terminações precoces), *value loss* estável.
   * Se estagnar, considere: mais iterações, revisar pesos de recompensa, *domain randomization*, learning rate.

4. **Visualizar/Exportar**

   ```bash
   python legged_gym/scripts/play.py \
     --task g1 \
     --experiment_name G1_12DOF_PPO \
     --run_name run2 \
     --headless False
   ```

   O *play* exporta a policy para `exported/policies/policy_1.pt`.

5. **Sim2Sim (MuJoCo)**
   Edite `policy_path` no `g1.yaml` e rode `deploy_mujoco.py`.

> **Onde ficam os checkpoints?**
> Em `logs/<experiment>/<timestamp>_<run_name>/model_<iter>.pt` (checkpoints) e
> `logs/<experiment>/exported/policies/policy_*.pt` (export prontos para deploy).

---

## 6) **Novas ideias / Próximos passos** (inclui **WASD**)

### 6.1 Controle por teclado **WASD** no Isaac Gym (play)

Objetivo: dirigir o G1 como num “jogo”, alterando **comandos de velocidade** (vx, vy, yaw) em tempo real no `play.py`.

**Como funciona por baixo:** o ambiente de locomoção recebe um “comando-alvo” de velocidade (linear x/y e angular yaw). No *play*, podemos **substituir** esse comando pela leitura do teclado.

**Passo-a-passo (patch simples no `play.py`):**

1. Garanta que está rodando **com GUI** (`--headless False`).
2. Abra `legged_gym/scripts/play.py` e, logo após criar o `env`, **insira**:

```python
from isaacgym import gymapi

gym = env.gym
viewer = env.viewer

# Registrar teclas
gym.subscribe_viewer_keyboard_event(viewer, gymapi.KEY_W, "cmd_forward")
gym.subscribe_viewer_keyboard_event(viewer, gymapi.KEY_S, "cmd_back")
gym.subscribe_viewer_keyboard_event(viewer, gymapi.KEY_A, "cmd_left")
gym.subscribe_viewer_keyboard_event(viewer, gymapi.KEY_D, "cmd_right")
gym.subscribe_viewer_keyboard_event(viewer, gymapi.KEY_Q, "cmd_yaw_left")
gym.subscribe_viewer_keyboard_event(viewer, gymapi.KEY_E, "cmd_yaw_right")

# Comando do usuário (valores exemplo; ajuste para sua tarefa)
vx, vy, wz = 0.0, 0.0, 0.0
VX, VY, WZ = 0.7, 0.3, 0.6   # máximos desejados
```

3. Dentro do **loop principal** do `play.py` (antes de aplicar `env.step()`), **adicione**:

```python
# Ler eventos do teclado
events = gym.query_viewer_action_events(viewer)
for evt in events:
    # Pressionar tecla
    if evt.type == gymapi.VIEWER_EVENT_KEYDOWN:
        if evt.action == "cmd_forward":    vx = +VX
        elif evt.action == "cmd_back":     vx = -VX
        elif evt.action == "cmd_left":     vy = +VY
        elif evt.action == "cmd_right":    vy = -VY
        elif evt.action == "cmd_yaw_left": wz = +WZ
        elif evt.action == "cmd_yaw_right":wz = -WZ

    # Soltar tecla → zera o respectivo comando
    elif evt.type == gymapi.VIEWER_EVENT_KEYUP:
        if evt.action in ("cmd_forward","cmd_back"):      vx = 0.0
        if evt.action in ("cmd_left","cmd_right"):        vy = 0.0
        if evt.action in ("cmd_yaw_left","cmd_yaw_right"):wz = 0.0

# Aplicar comandos do usuário em TODOS os ambientes (batelada)
if hasattr(env, "commands"):
    env.commands[:, 0] = vx   # vx (m/s)
    env.commands[:, 1] = vy   # vy (m/s)
    env.commands[:, 2] = wz   # yaw (rad/s)
```

4. Execute:

```bash
python legged_gym/scripts/play.py --task g1 --headless False
```

> **Notas**
> • Em muitas tasks *legged\_gym*, `env.commands` existe (shape `[num_envs, 3]`). Se **não** existir, alternativa é “injetar” diretamente as **ações** (posições articulares) — mas para locomoção, controlar **comandos de velocidade** é mais natural.
> • Ajuste `VX, VY, WZ` para valores seguros.
> • Se quiser “aceleração suave”, em vez de ligar/desligar, altere `vx, vy, wz` gradualmente por *ramp*.

### 6.2 Treinos melhores (ideias)

* **Domain Randomization**: variar massa, fricção, atrasos e ruído para robustez Sim2Sim.
* **Curriculum**: começar com `vy=0` e yaw=0, depois liberar transversal e giro.
* **Recompensas**: balancear “seguir velocidade” vs “estabilidade/erros” para não correr e cair.
* **Monitoramento**: salvar vídeos no Isaac/MuJoCo periodicamente para inspecionar falhas.
* **Ablations**: testar MLP vs LSTM, histórico na observação, diferentes escalas de ação.

---

## 7) Anexo — Comandos úteis de diagnóstico

```bash
# Confirmar binding do Isaac Gym após mover pasta
python -c "import isaacgym, inspect; print(inspect.getfile(isaacgym))"

# Confirmar binding do legged_gym no caminho novo
python -c "import legged_gym, inspect; print(inspect.getfile(legged_gym))"

# Limpar cache das extensões do torch se recompilar gymtorch
rm -rf ~/.cache/torch_extensions/py38_cu121/gymtorch

# Ver versões rápidas
python - << 'PY'
import torch, sys, mujoco
print("Torch:", torch.__version__, "CUDA?", torch.cuda.is_available())
print("Python:", sys.version)
print("MuJoCo:", mujoco.__version__)
PY
```

---

