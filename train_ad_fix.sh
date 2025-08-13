#!/bin/bash
# Script para treino focado em A/D responsiveness fix
# 200 steps teste para validação com GPU OTIMIZADA

echo "🎯 Iniciando treino A/D Fix - 200 steps"
echo "⚡ GPU OTIMIZADA: 8192 ambientes (85-90% utilização)"
echo "📊 Configuração:"
echo "  - tracking_ang_vel: 2.5 (vs 1.2 original)"
echo "  - action_rate: -0.005 (vs -0.01 original)"
echo "  - num_envs: 8192 (vs 4096 padrão)"
echo "  - Objetivo: Melhorar responsividade de curvas + otimizar GPU"

cd /home/pedro_setubal/Workspaces/unitree_rl/isaacgym/python/examples/unitree_rl_gym

# Treino com 200 iterações e GPU otimizada (8192 ambientes)
python legged_gym/scripts/train.py \
    --task g1 \
    --max_iterations 200 \
    --headless \
    --num_envs 8192

echo "✅ Treino concluído!"
echo "📊 GPU deve ter atingido ~85-90% de utilização"
echo "📁 Verifique logs em: logs/g1/"
echo "🎮 Para testar: python play.py --task g1 --load_run [NOVO_RUN] --checkpoint 200"