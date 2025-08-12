# Unitree RL - WASD Teleop Implementation

![Status](https://img.shields.io/badge/Status-WASD%20Funcionando-brightgreen)
![Platform](https://img.shields.io/badge/Platform-Isaac%20Gym-blue)
![Robot](https://img.shields.io/badge/Robot-Unitree%20G1-orange)

Implementação de controle WASD em tempo real para o robô humanoide Unitree G1 no Isaac Gym.

## 🎮 Funcionalidades

- **W/S**: Movimento frente/trás
- **A/D**: Rotação esquerda/direita  
- **Shift**: Boost de velocidade
- **Suavização EMA**: Transições fluidas
- **Single robot teleop**: Ambiente otimizado para controle

## 🚀 Como Executar

```bash
# 1. Ativar ambiente conda
conda activate unitree-rl
export LD_LIBRARY_PATH=$CONDA_PREFIX/lib:$LD_LIBRARY_PATH

# 2. Navegar para diretório do Isaac Gym
cd ~/Workspaces/unitree_rl/isaacgym/python/examples/unitree_rl_gym

# 3. Executar com checkpoint específico  
python legged_gym/scripts/play.py --task g1 --load_run Aug11_15-13-56_ --checkpoint 10
```

## 📁 Estrutura

```
unitree-rl/
├── README.md                    # Este arquivo
├── CLAUDE.md                    # Documentação para IA
├── scripts/
│   └── play_wasd.py            # Script WASD modificado
├── MDs/                        # Documentação completa
│   ├── Implementacao_WASD_Teleop_G1.md  # Guia detalhado
│   └── ...                     # Outros guias
└── isaacgym/                   # Isaac Gym (não versionado)
    └── python/examples/unitree_rl_gym/
        └── legged_gym/scripts/
            └── play.py         # Script modificado in-place
```

## ✅ Status da Implementação

### Funcionando
- ✅ Controles WASD detectando teclas corretamente
- ✅ Checkpoint loading com argumentos específicos
- ✅ Isaac Gym + conda environment
- ✅ rsl_rl versão compatível (1.0.2)
- ✅ Terrain configurado para 1 tile flat

### Em Desenvolvimento  
- 🔄 Problema de equilíbrio: Episódios resetando constantemente
- 🔄 Standing policy: Robot não mantém equilíbrio sem comandos

## 🔧 Problemas Resolvidos

1. **Isaac Gym Compilation**: Headers crypt.h + LD_LIBRARY_PATH
2. **TorchScript vs Checkpoint**: Logic corrigida para state_dict loading  
3. **Keyboard Events**: Usando `.value` ao invés de `.type`
4. **Variable Initialization**: Bug de `dones` não inicializada

## 📚 Documentação

- [`MDs/Implementacao_WASD_Teleop_G1.md`](MDs/Implementacao_WASD_Teleop_G1.md) - Guia completo de implementação
- [`CLAUDE.md`](CLAUDE.md) - Documentação do projeto para IA
- [`scripts/play_wasd.py`](scripts/play_wasd.py) - Script WASD standalone

## 🛠️ Dependências

- Isaac Gym Preview 4
- Python 3.8 (conda environment)
- PyTorch 2.4.1+cu121
- rsl_rl 1.0.2
- NVIDIA GPU com CUDA

## 📝 Próximos Passos

1. **Investigar equilíbrio**: Por que robot não consegue ficar em pé
2. **Policy analysis**: Verificar se checkpoint inicial é adequado
3. **Standing configuration**: Research idle/standing mode

## 🤝 Contribuição

Este projeto foi desenvolvido com assistência da IA Claude Code.

---

**🎯 Objetivo**: Controle direto e intuitivo do Unitree G1 via teclado no Isaac Gym
**📅 Última Atualização**: 12 Agosto 2025