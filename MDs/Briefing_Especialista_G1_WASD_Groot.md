# 🤖 Briefing Técnico: Otimização WASD + Isaac Groot - Unitree G1

## 📋 **CONTEXTO E SITUAÇÃO ATUAL**

### **🎯 Objetivos do Projeto**
- **Primário**: Controle teleoperado WASD responsivo para robô humanoide Unitree G1
- **Secundário**: Integração com NVIDIA Isaac Groot para capacidades generalistas
- **Framework**: Isaac Gym + PPO (Proximal Policy Optimization) + rsl-rl

### **🚨 PROBLEMA ATUAL - CONTROLE WASD NÃO FUNCIONAL**

#### **Estado Real do Sistema (Agosto 2025)**
```
✅ W/S Commands: FUNCIONAM (frente/trás responsivos)
❌ A/D Commands: NÃO FUNCIONAM (apenas leve movimento para um lado)
⚠️  Caminhada: DESEQUILIBRADA e não natural
⚠️  Equilíbrio: Robô fica em pé mas INSTÁVEL em repouso
📊 Status: PARÂMETROS NÃO OTIMIZADOS para controle de teclado
```

#### **Histórico de Experimentos**
1. **Modelo Initial (110 steps)**: Baseline funcional mas sub-treinado
2. **Modelo Extended (1110 steps)**: Melhorou estabilidade mas curvas lentas
3. **Modelo Natural (1000 steps)**: Documentado como "perfeito" mas NA PRÁTICA tem problemas
4. **Modelo A/D Fix (200 steps atual)**: Focado em responsividade angular - EM TREINAMENTO

#### **Métricas Reais vs Documentadas**
| Aspecto | Documentado | Realidade | Gap |
|---------|-------------|-----------|-----|
| **Episode Length** | 997.73 | ~200 | Instabilidade real |
| **A/D Response** | "Otimizado" | Não funciona | Parâmetros incorretos |
| **Natural Walking** | "Perfeito" | Desequilibrado | Reward mal balanceado |
| **Stability** | "Estável" | Instável em repouso | Base control deficiente |

---

## 🔧 **ANÁLISE TÉCNICA DETALHADA**

### **🧠 Glossário de Termos (Para Leigos)**

#### **Conceitos Fundamentais**
- **PPO (Proximal Policy Optimization)**: Algoritmo de aprendizado que ensina o robô através de tentativa e erro
- **Reward System**: Sistema de "notas" que diz ao robô se ele está fazendo certo ou errado
- **Observation Space**: Tudo que o robô "vê" e "sente" (posição, velocidade, contato dos pés, etc.)
- **Action Space**: Movimentos que o robô pode fazer (ângulos das 12 juntas das pernas)
- **Episode**: Uma "sessão" de tentativa do robô (como uma partida de videogame)
- **Isaac Gym**: Simulador físico da NVIDIA que acelera treinamento com GPU

#### **Conceitos Avançados**
- **Domain Randomization**: Variar condições (terreno, massa, etc.) para robustez
- **Curriculum Learning**: Ensinar progressivamente (fácil → difícil)
- **Sim2Real Transfer**: Transferir aprendizado da simulação para robô real
- **Isaac Groot**: IA generalista da NVIDIA para robôs humanoides

### **⚙️ Configuração Atual - PROBLEMÁTICA**

#### **Reward System (Sistema de Recompensas)**
```python
# g1_config.py - CONFIGURAÇÃO ATUAL PROBLEMÁTICA
class scales(LeggedRobotCfg.rewards.scales):
    tracking_lin_vel = 1.0      # Linear velocity tracking
    tracking_ang_vel = 2.5      # ⚠️ MUITO ALTO? Angular velocity tracking  
    action_rate = -0.005        # ⚠️ MUITO PERMISSIVO? Action smoothness penalty
    contact = 0.18              # ⚠️ MUITO BAIXO? Foot contact reward
    orientation = -0.8          # ⚠️ MUITO PERMISSIVO? Body orientation penalty
    alive = 0.15                # Basic stability reward
```

#### **Neural Architecture**
```python
# Observações que o robô recebe
num_observations = 47          # 47 números descrevendo estado atual
num_privileged_obs = 50        # 50 números com informações extras (terreno, etc.)
num_actions = 12               # 12 motores das juntas para controlar

# LSTM Memory
hidden_dims = [512, 256, 128]  # Rede neural de 3 camadas
activation = 'elu'             # Função de ativação
```

### **🎮 Interface WASD - ANÁLISE DO PROBLEMA**

#### **Como Funciona (Teoria)**
```python
# play.py - Mapeamento de teclas para velocidades
KEYBOARD_MAPPING = {
    'w': (VX_BASE, 0, 0),      # ✅ FUNCIONA: Frente
    's': (-VX_BASE, 0, 0),     # ✅ FUNCIONA: Trás  
    'a': (0, 0, WZ_BASE),      # ❌ NÃO FUNCIONA: Curva esquerda
    'd': (0, 0, -WZ_BASE),     # ❌ NÃO FUNCIONA: Curva direita
}

# Valores atuais
VX_BASE = 1.0    # Velocidade linear - OK
WZ_BASE = 1.5    # Velocidade angular - PROBLEMA AQUI?
```

#### **Possíveis Causas do Problema A/D**
1. **Reward Imbalance**: `tracking_ang_vel` muito alto causa instabilidade
2. **Action Smoothing**: `action_rate` muito permissivo não força coordenação
3. **Base Control**: Falta reward específico para movimento angular estável
4. **Observation Missing**: Robô não "vê" comando angular claramente
5. **Training Data**: Poucos exemplos de curvas durante treinamento

---

## 🗃️ **DATASETS E MODELOS PRÉ-TREINADOS**

### **🔍 Pesquisa de Datasets Online**

#### **Datasets Conhecidos para Humanoides**
```
⚠️ ATENÇÃO: Informações baseadas em conhecimento geral até Jan 2025
Especialista deve verificar links e disponibilidade atual
```

1. **DeepMind MoCapAct Dataset**
   - **Descrição**: Motion capture data for humanoid control
   - **URL**: `https://github.com/deepmind/dm_control/tree/main/dm_control/locomotion`
   - **Relevância**: Padrões de caminhada natural
   - **Como usar**: Fine-tuning com Isaac Gym

2. **CMU Motion Capture Database**
   - **Descrição**: Extenso banco de dados de movimento humano
   - **URL**: `http://mocap.cs.cmu.edu/`
   - **Relevância**: Referência para caminhada natural e curvas
   - **Como usar**: Converter para targets de treinamento RL

3. **SMPL-X Human Models**
   - **Descrição**: Modelos 3D de corpo humano com movimento
   - **URL**: `https://smpl-x.is.tue.mpg.de/`
   - **Relevância**: Biomecânica para robôs humanoides
   - **Como usar**: Imitation learning targets

#### **Modelos Pré-treinados Específicos para G1**
```
❓ PESQUISA NECESSÁRIA: Especialista deve investigar
```
- **Unitree Official Models**: Verificar se existem modelos oficiais
- **Community Models**: GitHub, HuggingFace, Papers with Code
- **Isaac Gym Community**: Fóruns e repositórios da comunidade
- **Academic Papers**: Modelos de papers recentes sobre G1

### **🔄 Como Integrar Modelos Pré-treinados**

#### **Metodologia de Fine-tuning**
```python
# Estratégia recomendada
1. Load pre-trained weights
2. Freeze base locomotion layers  
3. Fine-tune only WASD control layers
4. Progressive unfreezing if needed
```

---

## 🚀 **NVIDIA ISAAC GROOT - INTEGRAÇÃO COMPLETA**

### **🤔 O que é Isaac Groot? (Explicação para Leigos)**

Isaac Groot é como um "ChatGPT para robôs humanoides" desenvolvido pela NVIDIA. Assim como o ChatGPT foi treinado em textos da internet inteira, o Isaac Groot foi treinado em milhares de movimentos de robôs humanoides.

#### **Analogia Simples**
- **Nosso método atual**: Ensinar o robô do zero, como ensinar uma criança a andar
- **Isaac Groot**: Usar conhecimento de milhares de robôs que já sabem andar, como contratar um instrutor experiente

#### **Vantagens Técnicas**
1. **Zero-shot Learning**: Robô já sabe andar sem treinamento específico
2. **Generalization**: Funciona em diferentes terrenos e situações
3. **Multi-task**: Uma só IA para andar, pegar objetos, equilibrar, etc.
4. **Robust**: Mais estável que modelos treinados do zero
5. **Fast Deployment**: Semanas vs meses de treinamento

### **📋 Passo-a-Passo: Integração Isaac Groot + G1**

#### **1. Pré-requisitos e Setup**
```bash
# 1.1 Verificar compatibilidade NVIDIA
nvidia-smi  # Verificar GPU e drivers

# 1.2 Instalar Isaac Sim (required for Groot)
# Download de: https://developer.nvidia.com/isaac-sim
# Requisitos: RTX 2070+ ou A4000+, 32GB RAM, Ubuntu 20.04+

# 1.3 Instalar Omniverse Launcher
wget https://install.launcher.omniverse.nvidia.com/Omniverse-Launcher-linux.AppImage
chmod +x Omniverse-Launcher-linux.AppImage
./Omniverse-Launcher-linux.AppImage
```

#### **2. Isaac Groot Installation**
```bash
# 2.1 Através do Omniverse Launcher
# - Abrir Launcher
# - Ir em Exchange tab  
# - Procurar "Isaac Groot"
# - Install

# 2.2 Via Docker (alternativa)
docker pull nvcr.io/nvidia/isaac-groot:latest
docker run --gpus all -it nvcr.io/nvidia/isaac-groot:latest
```

#### **3. Configuração do Modelo G1**
```python
# 3.1 Criar configuração G1 para Isaac Groot
# Arquivo: groot_g1_config.py

import omni.isaac.groot as groot

class G1GrootConfig:
    # Robot specifications
    robot_asset_path = "/resources/robots/g1/urdf/g1.urdf"
    
    # Groot model selection
    groot_model = "humanoid_locomotion_v2"  # Modelo mais recente
    
    # Control interface
    control_mode = "keyboard_teleop"
    observation_space = "standard_humanoid"  # 48D observations
    
    # Fine-tuning parameters
    learning_rate = 1e-4
    fine_tune_layers = ["policy_head", "wasd_controller"]
```

#### **4. Adaptação da Interface WASD**
```python
# 4.1 Integrar WASD com Groot
# Arquivo: groot_wasd_interface.py

from omni.isaac.groot.teleop import KeyboardTeleop

class GrootWASDController:
    def __init__(self):
        self.groot_model = groot.load_model("humanoid_locomotion_v2")
        self.teleop = KeyboardTeleop()
        
    def process_wasd_input(self, key):
        # Converter WASD para comandos Groot
        if key == 'w':
            return groot.create_forward_command(velocity=1.0)
        elif key == 's':
            return groot.create_backward_command(velocity=1.0)
        elif key == 'a':
            return groot.create_turn_command(angular_vel=1.5, direction='left')
        elif key == 'd':
            return groot.create_turn_command(angular_vel=1.5, direction='right')
```

#### **5. Fine-tuning Específico para G1**
```bash
# 5.1 Script de fine-tuning
python groot_finetune.py \
    --robot g1 \
    --base_model humanoid_locomotion_v2 \
    --task wasd_teleop \
    --environments 4096 \
    --steps 1000

# 5.2 Validação
python groot_validate.py \
    --model g1_wasd_finetuned \
    --test_scenarios keyboard_control,stability,turning
```

### **🔧 Troubleshooting Isaac Groot**

#### **Problemas Comuns e Soluções**
1. **GPU Memory Error**: Reduzir number of environments
2. **URDF Compatibility**: Adaptar G1 URDF para Isaac Sim format
3. **Control Latency**: Ajustar physics timestep
4. **Simulation Mismatch**: Calibrar physical parameters

---

## 📈 **PLANO DE AÇÃO PRIORITIZADO**

### **🎯 PRIORIDADE 1: Otimizar Parâmetros WASD (Esta Semana)**

#### **Experimentos Sugeridos**
```python
# Experimento A: Rebalancear Rewards
tracking_lin_vel = 1.2      # Slight increase
tracking_ang_vel = 1.8      # REDUZIR de 2.5 → 1.8  
action_rate = -0.02         # More strict de -0.005 → -0.02
contact = 0.3               # AUMENTAR de 0.18 → 0.3
orientation = -1.2          # More strict de -0.8 → -1.2

# Experimento B: Enhanced Observations
# Adicionar ao observation space:
- comando_angular_atual      # What A/D command was given
- velocidade_angular_target  # What angular velocity is desired  
- erro_angular              # Difference between target and actual

# Experimento C: Curriculum Learning
# Phase 1: Only forward/backward (100 steps)
# Phase 2: Add gentle turns (200 steps)  
# Phase 3: Full WASD responsiveness (700 steps)
```

#### **Protocolo de Teste**
1. **Train 200 steps** com configuração A
2. **Test WASD responsiveness** em simulação
3. **Se melhorar**: Continue para 1000 steps
4. **Se não**: Try configuração B
5. **Document results** detalhadamente

### **🎯 PRIORIDADE 2: Investigar Isaac Groot (Próximo Sprint)**

#### **Research Tasks**
1. **Verificar disponibilidade** atual do Isaac Groot (pode estar em beta)
2. **Testar compatibilidade** com Isaac Gym workflow atual
3. **Comparar performance** Groot vs nosso treinamento customizado
4. **Avaliar licensing** e requisitos comerciais

#### **Integration Milestones**
1. **Week 1**: Setup Isaac Sim + Groot
2. **Week 2**: Adapt G1 model for Groot
3. **Week 3**: Implement WASD interface
4. **Week 4**: Compare with optimized PPO approach

---

## 💡 **PERGUNTAS PARA O ESPECIALISTA**

### **🔬 Sobre Otimização WASD**
1. **Reward Engineering**: Qual a melhor proporção entre `tracking_lin_vel` e `tracking_ang_vel` para movimento responsivo mas estável?
2. **Observation Space**: Que informações adicionais o robô precisa para associar comandos A/D com movimento angular?
3. **Training Curriculum**: Como estruturar aprendizado progressivo de movimentos básicos → curvas?
4. **Action Smoothing**: Como balancear `action_rate` para responsividade sem jitter?

### **🚀 Sobre Isaac Groot**
1. **Availability**: Isaac Groot está disponível para download público em 2025?
2. **Integration**: Como integrar Groot com Isaac Gym workflow existente?
3. **Customization**: Groot permite fine-tuning para tarefas específicas como WASD?
4. **Performance**: Groot supera PPO customizado para controle de teclado?

### **🎯 Estratégia Geral**
1. **Prioritização**: Devemos focar em otimizar PPO ou migrar para Groot?
2. **Datasets**: Que datasets públicos recomendam para humanoid locomotion?
3. **Sim2Real**: Como garantir que controle WASD funcione no robô físico?
4. **Benchmarks**: Como medir sucesso objetivamente além de observação visual?

---

## 📚 **RECURSOS E REFERÊNCIAS**

### **Documentação do Projeto**
- `models/MODEL_REGISTRY.md` - Histórico de modelos e métricas
- `MDs/Sistema_Final_WASD_Caminhada_G1.md` - Configuração "funcionando" (problemática)
- `models/testing/WASD_AD_Fix_v0.3_RESULTS.md` - Experimento atual

### **Comandos de Teste**
```bash
# Modelo atual em treinamento (200→1000 steps)
cd /home/pedro_setubal/Workspaces/unitree_rl/isaacgym/python/examples/unitree_rl_gym
python legged_gym/scripts/play.py --task g1 --load_run Aug12_17-38-50_ --checkpoint 200 --num_envs 1

# Para testar novos checkpoints conforme treinamento avança
python legged_gym/scripts/play.py --task g1 --load_run Aug12_17-38-50_ --checkpoint [400/600/800/1000] --num_envs 1
```

---

**📅 Data**: Agosto 12, 2025  
**👥 Equipe**: Pedro Setubal + Claude Code + Especialista LLM  
**🎯 Meta**: WASD totalmente funcional + Isaac Groot integration  
**⏱️ Timeline**: 2-4 semanas para solução completa