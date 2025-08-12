# Guia WASD — Teleop do Unitree G1 no Isaac Gym (RSL‑RL)

> **Objetivo**  
> Habilitar o controle do robô **Unitree G1 (12DOF)** por teclado no **Isaac Gym** usando uma policy de locomoção treinada:  
> **W** = frente, **S** = ré, **A** = girar esquerda, **D** = girar direita (opcional **Shift** = “correr”).  
> O guia usa seu ambiente atual:
>
> - Conda env: `unitree-rl` (Python 3.8)  
> - Isaac Gym: `/home/pedro_setubal/Workspaces/unitree_rl/isaacgym`  
> - Projeto: `/home/pedro_setubal/Workspaces/unitree_rl/isaacgym/python/examples/unitree_rl_gym`

---

## 1) Pré‑requisitos e checagem rápida

1. **Ative o ambiente e exports** (ajuste se você já automatizou com *activate.d*):
   ```bash
   conda activate unitree-rl
   unset PYTHONPATH
   export ISAAC_GYM_ROOT_DIR=/home/pedro_setubal/Workspaces/unitree_rl/isaacgym
   export LD_LIBRARY_PATH="$CONDA_PREFIX/lib:$LD_LIBRARY_PATH"
   export ISAAC_GYM_USE_GPU_PIPELINE=1
   export CUDA_VISIBLE_DEVICES=0
   ```

2. **Entre no projeto**:
   ```bash
   cd /home/pedro_setubal/Workspaces/unitree_rl/isaacgym/python/examples/unitree_rl_gym
   ```

3. **Teste o play “puro”** (sem WASD ainda), carregando uma policy válida (pré‑treinada ou sua):
   ```bash
   python legged_gym/scripts/play.py --task g1 --headless False
   ```
   Deve abrir o viewer do Isaac Gym e o robô se equilibrar/locomover com o controlador aprendido.

> **Dica**: As policies treinadas são exportadas por `play.py` em `logs/<exp>/<timestamp>_<run>/exported/policies/policy_*.pt`.  
> Se quiser usar uma *policy específica*, edite a config/args do `play.py` como você já faz normalmente.

---

## 2) Opção A (recomendada): Patch simples no `play.py`

A forma mais robusta é **injetar o teleop WASD diretamente no `play.py`**, pois ele já sabe carregar a policy e o env corretamente.

> **Onde colar**:  
> - Bloco **A.1**: imediatamente **após criar** o `env` (onde existem `env.gym` e `env.viewer`).  
> - Bloco **A.2**: **dentro do loop principal**, logo **antes** de `env.step(actions)`.

### A.1 — Após criar o `env` (setup do teclado e estados)

```python
# --- WASD Teleop • Bloco A.1 (após criar env, antes do loop) ---
from isaacgym import gymapi

gym = env.gym
viewer = env.viewer

# Registrar teclas
gym.subscribe_viewer_keyboard_event(viewer, gymapi.KEY_W, "cmd_forward")
gym.subscribe_viewer_keyboard_event(viewer, gymapi.KEY_S, "cmd_back")
gym.subscribe_viewer_keyboard_event(viewer, gymapi.KEY_A, "cmd_left")
gym.subscribe_viewer_keyboard_event(viewer, gymapi.KEY_D, "cmd_right")
gym.subscribe_viewer_keyboard_event(viewer, gymapi.KEY_LEFT_SHIFT, "speed_boost")

# Estados de comando
vx, wz = 0.0, 0.0              # vy opcional (strafing) — humanoide costuma usar 0
VX_BASE, WZ_BASE = 0.8, 1.2    # limites seguros (m/s e rad/s) usados no treino
VX_FAST, WZ_FAST = 1.2, 1.8    # com Shift pressionado
boost = False

# Suavização (evita trancos)
vx_cmd, wz_cmd = 0.0, 0.0
alpha = 0.2   # 0..1 (maior = responde mais rápido)

def _apply_commands_to_env(_vx, _wz):
    # A maioria dos envs legged usa env.commands[:, 0:3] = [vx, vy, yawRate]
    if hasattr(env, "commands"):
        env.commands[:, 0] = _vx   # vx (m/s)
        # env.commands[:, 1] = 0.0 # vy (habilite se quiser Q/E p/ strafe)
        env.commands[:, 2] = _wz   # yaw (rad/s)
    else:
        # Adapte aqui se a sua task tiver outro buffer/atributo de comandos
        pass
# --- fim Bloco A.1 ---
```

### A.2 — Dentro do loop principal, antes de `env.step(actions)`

```python
# --- WASD Teleop • Bloco A.2 (dentro do loop, antes de env.step(actions)) ---
events = gym.query_viewer_action_events(viewer)
for e in events:
    if e.type == gymapi.VIEWER_EVENT_KEYDOWN:
        if e.action == "cmd_forward": vx = +1.0
        elif e.action == "cmd_back":  vx = -1.0
        elif e.action == "cmd_left":  wz = +1.0
        elif e.action == "cmd_right": wz = -1.0
        elif e.action == "speed_boost": boost = True
    elif e.type == gymapi.VIEWER_EVENT_KEYUP:
        if e.action in ("cmd_forward","cmd_back"): vx = 0.0
        if e.action in ("cmd_left","cmd_right"):   wz = 0.0
        if e.action == "speed_boost":              boost = False

# Escala final levando em conta Shift
VX = VX_FAST if boost else VX_BASE
WZ = WZ_FAST if boost else WZ_BASE

# Suavização (EMA) para ficar gostoso de dirigir
vx_cmd = (1 - alpha) * vx_cmd + alpha * (vx * VX)
wz_cmd = (1 - alpha) * wz_cmd + alpha * (wz * WZ)

_apply_commands_to_env(vx_cmd, wz_cmd)
# --- fim Bloco A.2 ---
```

> **Importante**  
> - Use `--headless False` para aparecer o viewer (teclado só funciona com viewer aberto).  
> - Os limites `VX_*`/`WZ_*` devem respeitar **os ranges com que sua policy foi treinada**. Se mandar além, pode saturar/instabilizar.

---

## 3) Opção B (alternativa): Script independente `play_wasd.py`

Se não quiser mexer no `play.py`, você pode criar um script novo ao lado, reaproveitando a lógica de carregar policy/env do seu repositório. Como as chamadas podem variar entre versões, use o `play.py` como referência e **copie os mesmos métodos** de carga da policy e inferência. Abaixo um **esqueleto** para adaptar:

**Arquivo**: `legged_gym/scripts/play_wasd.py`
```python
#!/usr/bin/env python3
from isaacgym import gymapi
from legged_gym.utils.task_registry import task_registry
import torch

def main():
    # Carregue cfgs e env exatamente como o play.py faz na sua versão
    cfg, train_cfg, env_class, task_class = task_registry.get_cfgs("g1")
    env = env_class(cfg=cfg, sim_params=None, physics_engine="physx", sim_device="cuda:0", headless=False)
    obs = env.reset()

    # Carregue a policy com as MESMAS chamadas do seu play.py
    policy = task_class.get_actor_critic_model(env.num_obs, env.num_actions, train_cfg)   # <— ajuste
    task_class.load_policy(policy, train_cfg, device="cuda:0")                            # <— ajuste
    policy.eval(); torch.set_grad_enabled(False)

    gym = env.gym; viewer = env.viewer

    # Teclas
    gym.subscribe_viewer_keyboard_event(viewer, gymapi.KEY_W, "cmd_forward")
    gym.subscribe_viewer_keyboard_event(viewer, gymapi.KEY_S, "cmd_back")
    gym.subscribe_viewer_keyboard_event(viewer, gymapi.KEY_A, "cmd_left")
    gym.subscribe_viewer_keyboard_event(viewer, gymapi.KEY_D, "cmd_right")
    gym.subscribe_viewer_keyboard_event(viewer, gymapi.KEY_LEFT_SHIFT, "speed_boost")

    vx = wz = 0.0; vx_cmd = wz_cmd = 0.0
    VX_BASE, WZ_BASE = 0.8, 1.2
    VX_FAST, WZ_FAST = 1.2, 1.8
    alpha = 0.2; boost = False

    while not gym.query_viewer_has_closed(viewer):
        for e in gym.query_viewer_action_events(viewer):
            if e.type == gymapi.VIEWER_EVENT_KEYDOWN:
                if e.action == "cmd_forward": vx = +1.0
                elif e.action == "cmd_back":  vx = -1.0
                elif e.action == "cmd_left":  wz = +1.0
                elif e.action == "cmd_right": wz = -1.0
                elif e.action == "speed_boost": boost = True
            elif e.type == gymapi.VIEWER_EVENT_KEYUP:
                if e.action in ("cmd_forward","cmd_back"): vx = 0.0
                if e.action in ("cmd_left","cmd_right"):   wz = 0.0
                if e.action == "speed_boost":              boost = False

        VX = VX_FAST if boost else VX_BASE
        WZ = WZ_FAST if boost else WZ_BASE
        vx_cmd = (1 - alpha) * vx_cmd + alpha * (vx * VX)
        wz_cmd = (1 - alpha) * wz_cmd + alpha * (wz * WZ)

        if hasattr(env, "commands"):
            env.commands[:, 0] = vx_cmd
            env.commands[:, 2] = wz_cmd

        # Inferência — use a MESMA função do play.py
        actions = task_class.infer_action(policy, obs)   # <— ajuste conforme seu repo
        obs, _, _, _ = env.step(actions)
        env.render()

    env.close()

if __name__ == "__main__":
    main()
```

Execute:
```bash
python legged_gym/scripts/play_wasd.py
```

> **Atenção**: os métodos `get_actor_critic_model / load_policy / infer_action` são **exemplos**.  
> Copie exatamente os nomes/funções usados no seu `play.py` atual para garantir compatibilidade.

---

## 4) Testar e validar

1. Inicie o viewer:
   ```bash
   python legged_gym/scripts/play.py --task g1 --headless False
   ```
2. Pressione **W** (vai pra frente), **S** (ré), **A**/**D** (girar).  
3. Segure **Shift** para “correr” (usa `VX_FAST/WZ_FAST`).  
4. Solte as teclas e confirme que o robô desacelera suavemente (EMA com `alpha`).

**Sinais de sucesso**: resposta rápida às teclas, marcha estável dentro dos limites de velocidade e yaw definidos pelo treino.

---

## 5) Dicas e troubleshooting

- **Nada acontece ao apertar teclas** → confirme `--headless False` (viewer aberto) e que os blocos A.1/A.2 estão nas posições corretas.
- **Chacoalha/satura** → reduza `VX_*`/`WZ_*` para os **ranges usados no treino** da policy (ex.: 0.6 m/s e 1.0 rad/s).
- **Inverteu o giro** → troque o sinal de `wz` (+/−) se o sentido estiver ao contrário.
- **Sem `env.commands`** → procure no código da sua task como ela recebe comandos (ex.: `command_manager`, `desired_cmd`). Adapte `_apply_commands_to_env`.
- **Baixo FPS/latência alta** → feche outras janelas; sem logs excessivos; GPU livre; mantenha **headless** só no treino — no play deixe GUI.
- **LSTM** → se sua policy for recorrente, o `play.py` já gerencia `hidden states`. Mantenha a lógica original para inferência.

---

## 6) Extensões (opcional)

- **QE para strafe**: registre Q/E e escreva em `env.commands[:,1]` (vy).  
- **ESPACO para salto**: combine com sua *policy de salto* (modo “JUMP”); ao pressionar Espaço, congele `vx/wz`, acione a policy de salto até o pouso; depois volte à de andar.  
- **Blending**: misturar ações de duas policies com peso *w* para transições suaves (avançado; comece com troca discreta).

---

## 7) Resumo

- Patch A (no `play.py`) é o **caminho mais simples/compatível**.
- Use limites coerentes com o **treino da policy**.  
- A lógica WASD controla **comandos de velocidade**; a policy treinada transforma isso em locomoção estável — como um “jogo”.
