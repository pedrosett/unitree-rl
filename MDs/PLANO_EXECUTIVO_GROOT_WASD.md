# 🚀 Plano Executivo: GR00T + Isaac Sim + WASD Locomotion

## 🎯 Objetivo ÚNICO
**Controlar Unitree G1 via WASD usando GR00T N1.5 na simulação Isaac Sim**

### Escopo Definitivo
- ✅ **W**: Andar para frente
- ✅ **S**: Andar para trás  
- ✅ **A**: Curva à esquerda
- ✅ **D**: Curva à direita
- ❌ **Sem manipulação**
- ❌ **Sem tarefas complexas**
- ❌ **Sem deploy real**
- ❌ **Sem métricas de performance**

## 🏗️ Arquitetura Simples

```
WASD → Isaac Lab → GR00T → Isaac Sim G1 → Validação Visual
  ↑        ↓         ↓         ↓             ↓
Teclado  Teleop  Foundation  Simulação   Usuário
Input   Framework  Model     Walking    Valida
```

## 📋 Checklist de Implementação

### ☑️ Fase 1: Setup Ambiente (Usar `unitree-rl` existente)
- [ ] **1.1** - Ativar ambiente `conda activate unitree-rl`
- [ ] **1.2** - Instalar Isaac Sim via pip
- [ ] **1.3** - Clonar e instalar Isaac Lab  
- [ ] **1.4** - Clonar e instalar GR00T N1.5
- [ ] **1.5** - Download GR00T model weights
- [ ] **1.6** - Testar instalação básica

**Comandos para Usuário Executar (TODOS os repos DENTRO de unitree_rl):**
```bash
conda activate unitree-rl
pip install "isaacsim[all,extscache]==5.0.0" --extra-index-url https://pypi.nvidia.com

# IMPORTANTE: Clonar DENTRO do repo unitree_rl (padrão como isaacgym)
cd /home/pedro_setubal/Workspaces/unitree_rl
git clone https://github.com/isaac-sim/IsaacLab.git
cd IsaacLab && ./isaaclab.sh --install

# GR00T também DENTRO do repo unitree_rl
cd /home/pedro_setubal/Workspaces/unitree_rl  
git clone https://github.com/NVIDIA/Isaac-GR00T.git
cd Isaac-GR00T && pip install -e .
```

### ☑️ Fase 2: Teste Isaac Lab WASD
- [ ] **2.1** - Executar demo teleoperation básico
- [ ] **2.2** - Validar WASD keyboard input
- [ ] **2.3** - Confirmar Isaac Lab funcionando
- [ ] **2.4** - Usuário reporta status visual

**Comando para Usuário Testar:**
```bash
conda activate unitree-rl
cd /home/pedro_setubal/Workspaces/unitree_rl/IsaacLab
./isaaclab.sh -p source/standalone/demos/teleoperation.py --task Isaac-Reach-Franka-v0 --teleop_device keyboard
```

**Validação do Usuário:**
- ✅ WASD respondem?
- ✅ Robot se move na simulação?
- ✅ Console sem erros críticos?

### ☑️ Fase 3: GR00T + Unitree G1 Integration
- [ ] **3.1** - Criar Unitree G1 task no Isaac Lab
- [ ] **3.2** - Integrar GR00T como policy backend  
- [ ] **3.3** - Configurar WASD → GR00T mapping
- [ ] **3.4** - Primeira execução G1 + GR00T
- [ ] **3.5** - Validação visual pelo usuário

**Comando Target (a desenvolver):**
```bash
conda activate unitree-rl
cd /home/pedro_setubal/Workspaces/unitree_rl
./isaaclab.sh -p scripts/groot_wasd_locomotion.py --robot unitree_g1 --policy groot_n15 --device keyboard
```

### ☑️ Fase 4: Validação Final WASD
- [ ] **4.1** - Testar W (frente) - usuário valida visualmente
- [ ] **4.2** - Testar S (trás) - usuário valida visualmente  
- [ ] **4.3** - Testar A (esquerda) - usuário valida visualmente
- [ ] **4.4** - Testar D (direita) - usuário valida visualmente
- [ ] **4.5** - Confirmar locomotion natural e responsiva
- [ ] **4.6** - Sistema pronto para uso

## 🎮 Protocolo de Validação

### Responsabilidades Claras
**Claude**: Fornece comandos completos para execução
**Usuário**: Executa em terminal separado e reporta:
- Console output (erros/warnings)
- Comportamento visual (robot anda?)
- WASD responsividade
- Qualquer problema encontrado

### Critérios de Sucesso (Validação Visual)
- ✅ W faz G1 andar para frente de forma natural
- ✅ S faz G1 andar para trás de forma natural  
- ✅ A faz G1 virar à esquerda mantendo equilíbrio
- ✅ D faz G1 virar à direita mantendo equilíbrio
- ✅ Movimentos são suaves e responsivos
- ✅ Robot não cai nem perde estabilidade

## 🔧 Ambiente Técnico

### Sistema Alvo
- **Ambiente**: `unitree-rl` (Python 3.8.20, GLIBC 2.39)
- **Simulação**: Isaac Sim 5.0.0 via pip  
- **Framework**: Isaac Lab para teleoperation
- **AI Model**: GR00T N1.5 foundation model
- **Robot**: Unitree G1 humanoid
- **Input**: Keyboard WASD only

### Comparação com Sistema Atual
**Isaac Gym (funcional)**:
```bash
conda activate unitree-rl
cd /home/pedro_setubal/Workspaces/unitree_rl/isaacgym/python/examples/unitree_rl_gym
python legged_gym/scripts/play.py --task g1 --load_run Aug12_16-59-06_ --checkpoint 1000 --num_envs 1
```

**Isaac Lab + GR00T (meta)**:
```bash
conda activate unitree-rl
cd /home/pedro_setubal/Workspaces/unitree_rl
./isaaclab.sh -p scripts/groot_wasd_locomotion.py --robot unitree_g1 --policy groot_n15 --device keyboard
```

---

**🎯 META: WASD simples funcionando com GR00T + Isaac Sim, validação visual pelo usuário.**