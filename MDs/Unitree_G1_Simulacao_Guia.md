# Guia Completo — **Unitree G1 (12DOF)** no **Ubuntu 24.04** com **Isaac Gym** + **RSL‑RL** + **MuJoCo**
*(Ambiente validado e executando Sim2Sim com policy pré‑treinada; foco em **simulação**)*

> **Contexto (máquina do Pedro)**  
> Data base: **11/Ago/2025**  
> SO: **Ubuntu 24.04**  
> GPU: **RTX 4070 Super**  
> Driver NVIDIA: **575.64.03** (`CUDA Runtime 12.9` via `nvidia-smi`)  
> Conda: **Anaconda3** com env **`unitree-rl` (Python 3.8)**  
> **Pastas principais**  
> • Isaac Gym: `/home/pedro_setubal/Workspaces/unitree_rl/isaacgym`  
> • Projeto RL Gym: `/home/pedro_setubal/Workspaces/unitree_rl/isaacgym/python/examples/unitree_rl_gym`

---

## 0) Visão geral: o que é cada coisa

- **Isaac Gym (Preview 4)** — simulador com física **GPU PhysX** altamente paralelizável (milhares de ambientes). Usamos para **treinar** rápido.
- **RSL‑RL** — implementação **PPO** (ETH/Legged Robotics), otimizada para GPU, usada pelo *legged_gym*.
- **unitree_rl_gym** — código da Unitree com tarefas/robôs prontos (inclui **G1 12DOF**), scripts de **treino** (`train.py`), **visualização** (`play.py`) e **deploy** (MuJoCo e Real).
- **MuJoCo 3.2.3** — motor de física **preciso**. Usamos para **Sim2Sim**: validar a policy do Isaac em outro simulador.
- **Policy pré‑treinada** — arquivo `.pt` (rede do ator). Permite ver o G1 “andar” sem treinar do zero.

**Pipeline resumido**: **Treinar no Isaac Gym → Visualizar (play) → Validar no MuJoCo (Sim2Sim)**.  
*(Este guia vai até Sim2Sim; **não** cobre robô real).*

---

## 1) Instalação que foi feita **neste PC** (passo a passo fiel)

### 1.1 Drivers NVIDIA
```bash
sudo ubuntu-drivers devices
sudo apt update
sudo apt install -y nvidia-driver-575-open
sudo reboot
# Após reiniciar:
nvidia-smi   # → Driver 575.64.03, CUDA 12.9, RTX 4070 Super
```

### 1.2 Conda + ambiente
```bash
# Anaconda já instalado
conda create -y -n unitree-rl python=3.8
conda activate unitree-rl
```

### 1.3 Isaac Gym (Preview 4) — instalação **no caminho novo**
> Download no portal NVIDIA (login e aceite de licença).  
> **Observação importante:** movemos o Isaac Gym do `~/isaacgym` para  
> `/home/pedro_setubal/Workspaces/unitree_rl/isaacgym`. Por isso reinstalamos o pacote Python em modo editável.

```bash
# garantir ferramentas de build
pip install -U pip setuptools wheel

# instalar bindings do Isaac no caminho novo
pip install -e /home/pedro_setubal/Workspaces/unitree_rl/isaacgym/python
```

Variáveis usadas nos terminais de execução:
```bash
unset PYTHONPATH
export ISAAC_GYM_ROOT_DIR=/home/pedro_setubal/Workspaces/unitree_rl/isaacgym
export LD_LIBRARY_PATH="$CONDA_PREFIX/lib:$LD_LIBRARY_PATH"
export ISAAC_GYM_USE_GPU_PIPELINE=1
export CUDA_VISIBLE_DEVICES=0
```

Teste rápido (exemplos):
```bash
cd /home/pedro_setubal/Workspaces/unitree_rl/isaacgym/python/examples
python 1080_balls_of_solitude.py
# Alguns samples forçam CPU pipeline; para ver GPU pipeline:
python cartpole.py --use_gpu_pipeline --sim_device cuda:0 --rl_device cuda:0
```

### 1.4 RSL‑RL (versão compatível)
A branch mais nova exige `torch>=2.6`. Fixamos a tag **v1.0.2** (compatível com seu setup):
```bash
# limpar resquícios, se houver
pip uninstall -y rsl-rl-lib rsl_rl || true

# A) via PyPI (se disponível)
pip install rsl-rl-lib==1.0.2

# B) via Git (garantido)
cd /tmp
git clone https://github.com/leggedrobotics/rsl_rl.git
cd rsl_rl
git checkout v1.0.2
pip install -e .
```

### 1.5 unitree_rl_gym (repositório do projeto)
```bash
cd /home/pedro_setubal/Workspaces/unitree_rl/isaacgym/python/examples
git clone https://github.com/unitreerobotics/unitree_rl_gym.git
pip install -e /home/pedro_setubal/Workspaces/unitree_rl/isaacgym/python/examples/unitree_rl_gym
```

> Se mover o repositório novamente e aparecer `ModuleNotFoundError: legged_gym`, reinstale com `pip install -e <novo_caminho_do_repo>`.

### 1.6 MuJoCo (Sim2Sim)
O projeto pede **3.2.3**:
```bash
pip uninstall -y mujoco mujoco-python-viewer
pip install mujoco==3.2.3

# Para headless (sem GUI) no Linux:
export MUJOCO_GL=egl
```

---

## 2) Validações que rodamos

### 2.1 “Smoke test” de treino (G1 12DOF, 10 iterações)
```bash
cd /home/pedro_setubal/Workspaces/unitree_rl/isaacgym/python/examples/unitree_rl_gym
python legged_gym/scripts/train.py \
  --task g1 \
  --num_envs 64 \
  --max_iterations 10 \
  --headless
```
**Sinais OK**:
- `+++ Using GPU PhysX` e `GPU Pipeline: enabled`
- Compilação de `gymtorch` concluída
- Logs de iteração (0→9) com métricas (rewards, losses etc.)

> Em 10 iterações a reward fica próxima de zero — é esperado (teste de fumaça).

### 2.2 Sim2Sim no MuJoCo com **policy pré‑treinada**
Confirmamos o arquivo padrão:
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
**Resultado**: MuJoCo carregou e o **G1 apareceu andando** usando a policy pré‑treinada ✅

---

## 3) “Mão na massa” — *cheat‑sheet* para o dia a dia

### 3.1 Ativar ambiente e variáveis
```bash
conda activate unitree-rl
unset PYTHONPATH
export ISAAC_GYM_ROOT_DIR=/home/pedro_setubal/Workspaces/unitree_rl/isaacgym
export LD_LIBRARY_PATH="$CONDA_PREFIX/lib:$LD_LIBRARY_PATH"
export ISAAC_GYM_USE_GPU_PIPELINE=1
export CUDA_VISIBLE_DEVICES=0
```
*(opcional) Persistir via hooks do conda: atualize `activate.d/unitree.sh` com o caminho novo acima.*

### 3.2 Teste Isaac Gym (GPU pipeline)
```bash
cd /home/pedro_setubal/Workspaces/unitree_rl/isaacgym/python/examples
python cartpole.py --use_gpu_pipeline --sim_device cuda:0 --rl_device cuda:0
```

### 3.3 Treinar o G1 (run “de verdade”)
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
Exporta para algo como:
```
logs/G1_12DOF_PPO/<timestamp>_run1/exported/policies/policy_1.pt
```

### 3.5 Validar no MuJoCo (com **sua** policy)
Edite `deploy/deploy_mujoco/configs/g1.yaml` → `policy_path: "<caminho/para/sua/policy_1.pt>"`, então:
```bash
export MUJOCO_GL=egl   # se quiser headless
python deploy/deploy_mujoco/deploy_mujoco.py g1.yaml
```

---

## 4) Solução de problemas (o que já resolvemos)

- **Após mover pastas, Isaac Gym “sumiu”**  
  → Reinstalar em modo editável:  
  `pip install -e /home/pedro_setubal/Workspaces/unitree_rl/isaacgym/python`

- **`ModuleNotFoundError: legged_gym`**  
  → Reinstalar o projeto:  
  `pip install -e /home/pedro_setubal/Workspaces/unitree_rl/isaacgym/python/examples/unitree_rl_gym`

- **`rsl_rl` pedindo `torch>=2.6`**  
  → Fixar versão **v1.0.2** (PyPI `rsl-rl-lib==1.0.2` ou Git `git checkout v1.0.2`).

- **`GLIBCXX_3.4.32 not found` ao compilar `gymtorch`**  
  → `conda install -c conda-forge libstdcxx-ng>=12.2.0 gxx_linux-64=12` e limpar cache:  
  `rm -rf ~/.cache/torch_extensions/py38_cu121/gymtorch`

- **Exemplo do Isaac mostra “Forcing CPU pipeline”**  
  → É do sample. Para GPU, use `cartpole.py` com `--use_gpu_pipeline`.

- **MuJoCo sem GUI/driver de display**  
  → `export MUJOCO_GL=egl` para rodar headless.

---

## 5) **Treinar sua própria policy** (didático e direto)

1. **Parâmetros base**
   - `--num_envs`: 1024–4096 (ajuste pela VRAM; mais envs = mais rápido)
   - `--max_iterations`: 10k–50k (humanoides precisam de mais iterações)
   - `--headless`: sem render = mais performance
   - `--experiment_name` / `--run_name`: organização dos logs/output

2. **Rodar treino**
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
   - Reward média crescendo, menos “quedas” (terminações precoces), losses estáveis.
   - Se estagnar: mais iterações, ajustar recompensas, *domain randomization*, LR, etc.

4. **Visualizar/Exportar (play)**
```bash
python legged_gym/scripts/play.py \
  --task g1 \
  --experiment_name G1_12DOF_PPO \
  --run_name run2 \
  --headless False
```
   Exporta para `logs/.../exported/policies/policy_1.pt`.

5. **Sim2Sim (MuJoCo)**
   - Ajuste `policy_path` no `deploy/deploy_mujoco/configs/g1.yaml` para seu `policy_1.pt`.
   - Rode `python deploy/deploy_mujoco/deploy_mujoco.py g1.yaml` (use `MUJOCO_GL=egl` se headless).

**Onde ficam os checkpoints?**  
`logs/<experiment>/<timestamp>_<run_name>/model_<iter>.pt` (checkpoints)  
`logs/<experiment>/exported/policies/policy_*.pt` (export prontos para deploy).

---

## 6) **Controle por teclado (WASD) no Isaac Gym** — *modo “joguinho”*

Objetivo: controlar o G1 no **play** ajustando **comandos de velocidade** `(vx, vy, yaw)` em tempo real pelas teclas **WASD** (e **Q/E** para yaw).

> **Por quê assim?** As tasks *legged_gym* aceitam um **comando de velocidade desejada** que a policy tenta seguir. Alteramos esse comando no loop do `play.py` com o teclado.

### Passo‑a‑passo (patch no `play.py`)
1) Rode com GUI (`--headless False`).  
2) Abra `legged_gym/scripts/play.py` e, após criar o `env`, **adicione**:

```python
from isaacgym import gymapi

gym = env.gym
viewer = env.viewer

# registrar teclas
gym.subscribe_viewer_keyboard_event(viewer, gymapi.KEY_W, "cmd_forward")
gym.subscribe_viewer_keyboard_event(viewer, gymapi.KEY_S, "cmd_back")
gym.subscribe_viewer_keyboard_event(viewer, gymapi.KEY_A, "cmd_left")
gym.subscribe_viewer_keyboard_event(viewer, gymapi.KEY_D, "cmd_right")
gym.subscribe_viewer_keyboard_event(viewer, gymapi.KEY_Q, "cmd_yaw_left")
gym.subscribe_viewer_keyboard_event(viewer, gymapi.KEY_E, "cmd_yaw_right")

# comandos do usuário
vx, vy, wz = 0.0, 0.0, 0.0
VX, VY, WZ = 0.7, 0.3, 0.6   # máximos (ajuste conforme seu setup)
```

3) Dentro do **loop principal** (antes de `env.step()`), **adicione**:

```python
events = gym.query_viewer_action_events(viewer)
for evt in events:
    if evt.type == gymapi.VIEWER_EVENT_KEYDOWN:
        if evt.action == "cmd_forward":    vx = +VX
        elif evt.action == "cmd_back":     vx = -VX
        elif evt.action == "cmd_left":     vy = +VY
        elif evt.action == "cmd_right":    vy = -VY
        elif evt.action == "cmd_yaw_left": wz = +WZ
        elif evt.action == "cmd_yaw_right":wz = -WZ
    elif evt.type == gymapi.VIEWER_EVENT_KEYUP:
        if evt.action in ("cmd_forward","cmd_back"):      vx = 0.0
        if evt.action in ("cmd_left","cmd_right"):        vy = 0.0
        if evt.action in ("cmd_yaw_left","cmd_yaw_right"):wz = 0.0

# aplicar comandos em todos os envs
if hasattr(env, "commands"):
    env.commands[:, 0] = vx   # vx (m/s)
    env.commands[:, 1] = vy   # vy (m/s)
    env.commands[:, 2] = wz   # yaw (rad/s)
```

4) Executar:
```bash
python legged_gym/scripts/play.py --task g1 --headless False
```

**Notas rápidas**
- Se sua task tiver outra estrutura, ajuste o acesso (ex.: `env.command_input` etc.). Para locomoção *legged*, `env.commands[:, :3]` é comum.
- Quer “aceleração suave”? Em vez de ligar/desligar, incremente `vx,vy,wz` gradualmente por *ramp* dentro do loop.
- Ajuste `VX,VY,WZ` para valores seguros (comece baixo).

---

## 7) Anexo — Diagnósticos úteis

```bash
# Isaac Gym está no caminho novo?
python - << 'PY'
import isaacgym, inspect
print("isaacgym em:", inspect.getfile(isaacgym))
PY

# legged_gym está no caminho novo?
python - << 'PY'
import legged_gym, inspect
print("legged_gym em:", inspect.getfile(legged_gym))
PY

# Limpar cache do torch extensions (gymtorch) se recompilar
rm -rf ~/.cache/torch_extensions/py38_cu121/gymtorch

# Versões rápidas
python - << 'PY'
import torch, sys, mujoco
print("Torch:", torch.__version__, "CUDA?", torch.cuda.is_available())
print("Python:", sys.version)
print("MuJoCo:", mujoco.__version__)
PY
```

---

## 8) O que aprendemos / Histórico fiel do que foi feito

- Instalamos **driver 575.64.03** (CUDA **12.9**) e confirmamos com `nvidia-smi`.
- Criamos o env **`unitree-rl` (Python 3.8)**.
- Instalamos o **Isaac Gym** e posteriormente **movemos** para  
  `/home/pedro_setubal/Workspaces/unitree_rl/isaacgym`; por isso, **reinstalamos** com `pip install -e` e atualizamos variáveis.
- Instalamos **RSL‑RL v1.0.2** (evitando dependências de Torch 2.6+).
- Instalamos e registramos o **unitree_rl_gym** no novo caminho.
- Instalamos **MuJoCo 3.2.3** e rodamos com `MUJOCO_GL=egl` quando necessário.
- Validamos com “smoke test” de **10 iterações** no G1 (Isaac) e depois **rodamos o G1 andando no MuJoCo** com a **policy pré‑treinada**.
- Organizamos um **cheat‑sheet** e adicionamos um **modo WASD** no `play.py` para teleop na simulação.

---

## 9) Próximas ideias

- **Treinos longos** (20k–50k iterações) e *domain randomization* para robustez.
- **Curriculum** (começa com vx; depois libera vy/yaw).
- **Ablations**: MLP vs LSTM, histórico de estados, escalas de ação.
- **Salvar vídeos** periódicos (Isaac/MuJoCo) para inspeção de falhas.
- **Comparar policies** (pré‑treinada vs sua) e métricas (tracking de velocidade, quedas por minuto, etc.).

> Com isso você tem um ambiente de simulação sólido, entende onde cada peça entra no pipeline e pode avançar para treinos próprios com segurança. Bom proveito! 🚀
