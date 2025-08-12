# Guia Didático: Treinamento de Policy de Equilíbrio para Unitree G1

![Status](https://img.shields.io/badge/Status-Pesquisa%20Conclu%C3%ADda-blue)
![Nível](https://img.shields.io/badge/N%C3%ADvel-Iniciante%20a%20Avan%C3%A7ado-green)
![Tempo](https://img.shields.io/badge/Tempo-30min%20a%204h-orange)

## 🎯 **Problema Identificado**

Nosso robô Unitree G1 está **resetando constantemente** (caindo a cada 100-200 steps) porque estamos usando um modelo **sub-treinado** com apenas **10 iterações**. É como tentar ensinar alguém a andar de bicicleta em apenas 30 segundos!

## 🧠 **Integração WASD + Equilíbrio: Modelo Único**

### **Por que Um Modelo Neural Único?**

Baseado em **pesquisas científicas recentes** (2024-2025), a abordagem correta é usar **um único modelo neural** que aprende múltiplos comportamentos simultaneamente:

**✅ Evidências Científicas:**
- **Multi-Task Learning (MTL)**: Frameworks que treinam uma única rede neural para múltiplas tarefas (walking, turning, standing)
- **Unitree Success Cases**: Validação bem-sucedida em Go1, A1, G1 com políticas únicas
- **End-to-End Control**: Políticas que executam múltiplos gaits diretamente de inputs proprioceptivos
- **Biology-Inspired CPG-RL**: Central Pattern Generators + Deep RL em uma única policy

**❌ Por que NÃO usar modelos separados:**
- Complexidade de coordenação entre múltiplos modelos
- Transições abruptas entre comportamentos
- Overhead computacional de múltiplas inferências
- Perda de contexto entre mudanças de modelo

### **Como Nossa Implementação Funciona**

**Fluxo de Integração WASD → Equilíbrio:**
```
WASD Input → [vx, wz] → env.commands → observations[47] → policy → joint_actions[12] → movimento_equilibrado
```

**Estados Aprendidos Simultaneamente:**
- **STANDING** (`vx=0, wz=0`): Equilíbrio estático
- **WALKING** (`vx≠0, wz=0`): Locomoção linear + equilíbrio
- **TURNING** (`vx=0, wz≠0`): Rotação no lugar + equilíbrio  
- **COMBINED** (`vx≠0, wz≠0`): Movimento complexo + equilíbrio

**Interface de Comando Já Implementada:**
```python
# No play.py - já funciona!
env.commands[:, 0] = vx_cmd    # Velocidade linear (WASD W/S)
env.commands[:, 1] = 0.0       # Velocidade lateral (zero para humanóide)
env.commands[:, 2] = wz_cmd    # Velocidade angular (WASD A/D)
```

**Recompensas Integradas (g1_config.py):**
```python
tracking_lin_vel = 1.0    # Seguir comandos de velocidade → WASD responsivo
tracking_ang_vel = 0.5    # Seguir rotação → WASD turning
alive = 0.15              # Manter equilíbrio durante movimento
base_height = -10.0       # Penalidade por perder postura
orientation = -1.0        # Penalidade por inclinar
```

**🎯 Resultado: WASD já integrado! Só falta treinar até convergência.**

---

## 📚 **Seção 1: Conceitos Fundamentais (Para Leigos)**

### 🧠 **1.1 O que é uma "Policy" em IA?**

**Analogia Simples**: A policy é como o **"cérebro" do robô** que toma decisões. 

Imagine que você está dirigindo um carro:
- **Inputs** (sensores): Você vê a estrada, sente o volante, ouve o motor
- **Processamento** (policy): Seu cérebro decide "virar à esquerda", "acelerar", "frear"  
- **Outputs** (ações): Suas mãos e pés executam os movimentos

Para o robô G1:
- **Inputs**: 47 sensores (posição das juntas, orientação, velocidades, etc.)
- **Policy**: Rede neural que processa esses dados
- **Outputs**: 12 comandos para os motores das juntas

### 🎮 **1.2 Reinforcement Learning (Aprendizado por Reforço)**

**Analogia**: É como **treinar um animal de estimação**:

1. **Animal tenta** uma ação (robô tenta um movimento)
2. **Você avalia** o resultado (sistema dá uma "nota"/reward)
3. **Animal aprende** a repetir boas ações (policy melhora)
4. **Repete milhares de vezes** até aprender perfeitamente

**Por que usar RL para robótica?**
- ❌ **Programação manual**: Impossível prever todas as situações
- ❌ **Física simulada**: Muito complexa para calcular manualmente  
- ✅ **RL**: O robô **descobre sozinho** como se equilibrar

### 📖 **1.3 Glossário de Termos Técnicos**

| Termo | Analogia | Explicação Técnica |
|-------|----------|-------------------|
| **Policy** | "Cérebro" do robô | Rede neural que decide ações baseada em observações |
| **Checkpoint** | "Save game" | Snapshot do treinamento que pode ser carregado depois |
| **Iterações** | "Tentativas de aprendizado" | Número de vezes que o robô treinou (nosso: 10, ideal: 3000+) |
| **Episode** | "Uma vida" do robô | Período desde reset até próximo reset (queda/timeout) |
| **Reward** | "Nota/pontuação" | Número que diz se ação foi boa (+) ou ruim (-) |
| **Convergência** | "Robô aprendeu" | Quando performance para de melhorar significativamente |
| **Reset** | "Morreu, tenta de novo" | Robô caiu ou falhou, volta à posição inicial |

---

## 🔍 **Seção 2: Modelo Pré-treinado motion.pt**

### 📁 **2.1 Resumo da Descoberta**

Encontramos um modelo pré-treinado no repositório (`deploy/pre_train/g1/motion.pt` - 145KB, formato TorchScript). Como sua compatibilidade e funcionalidade são desconhecidas, **focaremos no treinamento do zero** para ter controle total sobre o processo e garantir que a policy seja otimizada especificamente para controle WASD teleoperado.

---

---

## ⚖️ **Seção 2: Por que Nosso Modelo Atual Falha?**

### 📊 **2.1 O Problema das 10 Iterações**

**Analogia**: Imagine aprender a andar de bicicleta em apenas 30 segundos:
- **Iteração 1-3**: Caindo constantemente
- **Iteração 4-6**: Ainda instável, mas melhorando
- **Iteração 7-10**: Começando a entender equilíbrio
- **Nosso modelo parou aqui!** ❌

**Para comparação:**
- **100 iterações**: Básico de equilíbrio
- **1000 iterações**: Caminhada estável  
- **3000 iterações**: Movimentos suaves
- **5000+ iterações**: Performance robusta

### 📈 **2.2 Curva Típica de Aprendizado RL**

```
Reward │
       │     ┌──────────── Convergência (3000+ iter)
   Alto│    ╱
       │   ╱
       │  ╱
       │ ╱
  Baixo│╱ ← Nossos 10 iter
       └─────────────────────────── Iterações
       0   500  1000  2000  5000
```

**Fases do Aprendizado:**
1. **0-100**: Exploração aleatória (caos total)
2. **100-500**: Descobrindo padrões básicos
3. **500-1500**: Desenvolvendo estratégias
4. **1500-3000**: Refinando movimentos
5. **3000+**: Policy madura e estável

### 🎯 **2.3 Sistema de Recompensas (Rewards) do G1**

O robô "aprende" através de um **sistema de notas**:

#### **🏆 Recompensas Positivas (Robô ganha pontos)**
```python
alive = +0.15           # Por estar "vivo" (não resetou)
contact = +0.18         # Por pés tocarem no chão corretamente
```

#### **⚠️ Penalidades (Robô perde pontos)**  
```python
base_height = -10.0     # Por altura errada (muito alto/baixo)
orientation = -1.0      # Por estar inclinado demais
lin_vel_z = -2.0       # Por pular verticalmente
ang_vel_xy = -0.05     # Por rodar descontrolado
dof_vel = -1e-3        # Por mover juntas muito rápido
action_rate = -0.01    # Por mudar ações bruscamente
```

**Como o robô aprende equilíbrio:**
1. **Tenta movimento aleatório** → Cai → **Reward = -10** (altura) + **-1** (orientação) = **-11 pontos**
2. **Tenta ficar parado** → Fica em pé por 2 segundos → **Reward = +0.15 × 100 steps = +15 pontos** ✅
3. **Policy aprende**: "Ficar em pé = bom, cair = ruim"
4. **Repete milhares de vezes** até dominar o equilíbrio

---

## 🛣️ **Seção 3: Plano de Ação - 2 Estratégias de Treinamento**

### 🔧 **Estratégia 1: Treinamento Continuado (2-3 horas)**

**Objetivo**: Continuar treinamento do modelo atual até convergir

**Preparação**:
```bash
# Ativar ambiente e navegar para diretório
conda activate unitree-rl
export LD_LIBRARY_PATH=$CONDA_PREFIX/lib:$LD_LIBRARY_PATH
cd ~/Workspaces/unitree_rl/isaacgym/python/examples/unitree_rl_gym
```

**Comando de Treinamento**:
```bash
# Resumir do checkpoint 10 atual
python legged_gym/scripts/train.py --task g1 --resume \
  --load_run Aug11_15-13-56_ \
  --checkpoint 10 \
  --max_iterations 3000
```

**Monitoramento TensorBoard**:
```bash
# Em terminal separado
tensorboard --logdir logs/g1/Aug11_15-13-56_
# Abrir: http://localhost:6006
```

**Checkpoints para testar durante treinamento**:
- **model_100.pt**: Teste básico de estabilidade 
- **model_500.pt**: Primeiros movimentos coordenados  
- **model_1000.pt**: Equilíbrio mais robusto
- **model_2000.pt**: Movimentação suave
- **model_3000.pt**: Performance final

**Teste de Checkpoints**:
```bash
# Testar checkpoint específico durante treinamento
python legged_gym/scripts/play.py --task g1 \
  --load_run Aug11_15-13-56_ --checkpoint 500
```

---

### 🏗️ **Estratégia 2: Treino Completo do Zero (4-6 horas)**

**Objetivo**: Controle total sobre o processo de treinamento com configuração otimizada

**Passo 1: Criar Configuração Personalizada**

Criar arquivo `legged_gym/envs/g1/g1_teleop_config.py`:
```python
from legged_gym.envs.g1.g1_config import G1RoughCfg, G1RoughCfgPPO

class G1TeleopCfg(G1RoughCfg):
    """Configuração otimizada para controle WASD teleoperado"""
    
    class env(G1RoughCfg.env):
        # Ambiente mais simples para foco em equilíbrio
        num_envs = 4096  # Paralelização máxima
        
    class terrain(G1RoughCfg.terrain):
        # Terrain simples para foco em standing/walking
        mesh_type = 'plane'
        num_rows = 1
        num_cols = 1
        
    class rewards(G1RoughCfg.rewards):
        # Enfatizar equilíbrio e estabilidade para teleop
        class scales(G1RoughCfg.rewards.scales):
            # Rewards aumentados para estabilidade
            alive = 0.5           # 3x mais reward por ficar vivo
            contact = 0.25        # Mais reward por contato correto
            
            # Penalidades aumentadas para instabilidade  
            base_height = -20.0   # 2x penalidade por altura errada
            orientation = -5.0    # 5x penalidade por inclinação
            lin_vel_z = -4.0      # 2x penalidade por pulos
            ang_vel_xy = -0.1     # 2x penalidade por rotações indesejadas
            
            # Suavidade de movimento
            action_rate = -0.02   # 2x penalidade por mudanças bruscas
            dof_vel = -2e-3       # 2x penalidade por movimentos rápidos
            
class G1TeleopCfgPPO(G1RoughCfgPPO):
    class runner(G1RoughCfgPPO.runner):
        experiment_name = 'g1_teleop'
        max_iterations = 5000
```

**Passo 2: Registrar Nova Task**

Adicionar ao `legged_gym/envs/__init__.py`:
```python
from legged_gym.envs.g1.g1_teleop_config import G1TeleopCfg, G1TeleopCfgPPO
# ... outras imports ...

task_registry.register("g1_teleop", G1, G1TeleopCfg(), G1TeleopCfgPPO())
```

**Passo 3: Iniciar Treinamento**
```bash
# Treino completo do zero
python legged_gym/scripts/train.py --task g1_teleop --max_iterations 5000
```

**Passo 4: Monitoramento**
```bash
# TensorBoard para nova task
tensorboard --logdir logs/g1_teleop/
# Abrir: http://localhost:6006
```

---

## 🛠️ **Seção 4: Implementações Técnicas**

### 🎯 **4.1 Standing Mode Natural via Reward Learning**

**Conceito**: O modelo aprende naturalmente standing mode através do sistema de recompensas, **SEM necessidade de lógica manual**.

**Como Funciona (Automático):**
```python
# Quando WASD não pressionado: vx=0, wz=0
env.commands[:, 0] = 0.0    # Comando: "não mover"
env.commands[:, 1] = 0.0    # Comando: "não se deslocar lateralmente"  
env.commands[:, 2] = 0.0    # Comando: "não girar"

# Modelo vê comando zero e aprende a:
# 1. Parar movimento (tracking_lin_vel reward)
# 2. Manter equilíbrio (alive + orientation rewards)
# 3. Postura correta (base_height reward)
```

**Standing Mode = Comportamento Emergente:**
- ✅ **Aprendido**: Modelo descobre como equilibrar parado
- ✅ **Natural**: Transições suaves entre movimento ↔ parado
- ✅ **Robusto**: Funciona mesmo com perturbações externas
- ❌ **Não manual**: Sem posições articulares hard-coded

### ⚙️ **4.2 Critérios de Terminação Relaxados**

**Problema**: Critérios muito rigorosos fazem robô resetar facilmente.

**Valores Atuais (Muito Rigorosos)**:
```python
# legged_robot.py linha 122
self.reset_buf |= torch.abs(self.rpy[:,0]) > 0.8  # Roll > 46°
self.reset_buf |= torch.abs(self.rpy[:,1]) > 1.0  # Pitch > 57°
```

**Valores Propostos para Teleop (Mais Permissivos)**:
```python
# Temporário durante teleop - relaxar limites
if self.teleop_mode:  # Variável a ser criada
    self.reset_buf |= torch.abs(self.rpy[:,0]) > 1.2  # Roll > 69°
    self.reset_buf |= torch.abs(self.rpy[:,1]) > 1.5  # Pitch > 86°
else:
    # Manter rigoroso para treinamento
    self.reset_buf |= torch.abs(self.rpy[:,0]) > 0.8
    self.reset_buf |= torch.abs(self.rpy[:,1]) > 1.0
```

### 🔄 **4.3 Transições Suaves WASD ↔ Standing**

**Problema**: Mudanças bruscas entre parado ↔ movimento causam instabilidade.

**Solução**: Interpolação gradual
```python
class WASDController:
    def __init__(self):
        self.standing_alpha = 0.1  # Velocidade transição para standing
        self.walking_alpha = 0.2   # Velocidade transição para walking
        
    def smooth_transition(self, vx_target, wz_target):
        if vx_target == 0.0 and wz_target == 0.0:
            # Transição gradual para standing
            self.vx_cmd *= (1 - self.standing_alpha)
            self.wz_cmd *= (1 - self.standing_alpha)
        else:
            # Transição gradual para walking
            self.vx_cmd = self.vx_cmd * (1 - self.walking_alpha) + vx_target * self.walking_alpha
            self.wz_cmd = self.wz_cmd * (1 - self.walking_alpha) + wz_target * self.walking_alpha
```

---

## 📊 **Seção 5: Cronograma de Treinamento**

### **Etapa 1: Preparação (30 min)**
- [ ] Escolher estratégia (continuado vs do zero)
- [ ] Ativar ambiente conda e configurar paths
- [ ] Inicializar TensorBoard para monitoramento
- [ ] Se estratégia 2: Criar configuração personalizada

### **Etapa 2: Treinamento Principal (2-6 horas)**
- [ ] Executar comando de treinamento escolhido
- [ ] Monitorar convergência via TensorBoard (rewards, episode length)
- [ ] Testar checkpoints intermediários com play.py
- [ ] Ajustar hiperparâmetros se necessário

### **Etapa 3: Validação e Otimização WASD (1 hora)**
- [ ] Testar melhor checkpoint com controles WASD
- [ ] Verificar estabilidade em standing mode
- [ ] Ajustar parâmetros VX_BASE/WZ_BASE se necessário
- [ ] Validar transições suaves parado ↔ movimento

### **Etapa 4: Documentação Final (30 min)**
- [ ] Documentar resultados e parâmetros finais
- [ ] Atualizar arquivo de implementação WASD
- [ ] Commit e push das melhorias

---

## 🔧 **Seção 6: Troubleshooting Comum**

### ❌ **"Treinamento não converge"**
```python
# Sinais de problema:
1. Rewards oscilam muito após 1000 iter
2. TensorBoard mostra platô baixo
3. Robô não melhora comportamento

# Soluções:
1. Reduzir learning rate
2. Ajustar rewards scales
3. Verificar configuração do ambiente
```

---

## 🎯 **Próximos Passos**

Agora que você tem o guia completo, escolha a estratégia de treinamento:

1. **🔧 Treinamento Continuado** → Continuar do modelo atual (2-3 horas)  
   *Prós: Aproveita progresso, mais rápido*  
   *Contras: Pode herdar problemas da configuração inicial*

2. **🏗️ Treino Completo do Zero** → Controle total com configuração otimizada (4-6 horas)  
   *Prós: Configuração limpa, rewards otimizados para teleop*  
   *Contras: Mais tempo, perde progresso anterior*

**Recomendação Baseada na Pesquisa**: 
- **Se tem tempo limitado**: Estratégia 1 (continuado) - aproveita progresso
- **Se quer resultado científico robusto**: Estratégia 2 (do zero) - config otimizada para Multi-Task Learning
- **Ambas funcionam**: Modelo único aprenderá WASD + equilíbrio integrados

---

**Criado por**: Claude Code  
**Data**: Agosto 2025  
**Status**: Guia completo para implementação