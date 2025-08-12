import sys
from legged_gym import LEGGED_GYM_ROOT_DIR
import os
import sys
from legged_gym import LEGGED_GYM_ROOT_DIR

import isaacgym
from isaacgym import gymapi  # Import adicionado para WASD
from legged_gym.envs import *
from legged_gym.utils import  get_args, export_policy_as_jit, task_registry, Logger

import numpy as np
import torch


def play(args):
    env_cfg, train_cfg = task_registry.get_cfgs(name=args.task)
    # override some parameters for testing
    env_cfg.env.num_envs = 1  # Apenas 1 robô para WASD teleop
    env_cfg.terrain.mesh_type = 'plane'  # Forçar plano simples (não terrain complexo)
    env_cfg.terrain.num_rows = 1  # Apenas 1 linha (terrain menor)
    env_cfg.terrain.num_cols = 1  # Apenas 1 coluna (terrain menor) 
    env_cfg.terrain.max_init_terrain_level = 0  # Forçar terrain level 0 (flat)
    env_cfg.terrain.curriculum = False
    env_cfg.noise.add_noise = False
    env_cfg.domain_rand.randomize_friction = False
    env_cfg.domain_rand.push_robots = False

    env_cfg.env.test = True

    # prepare environment
    env, _ = task_registry.make_env(name=args.task, args=args, env_cfg=env_cfg)
    obs = env.get_observations()
    
    # load policy - aplicar argumentos de linha de comando se fornecidos
    if hasattr(args, 'load_run') and args.load_run is not None:
        train_cfg.runner.resume = True
        train_cfg.runner.load_run = args.load_run
        if hasattr(args, 'checkpoint') and args.checkpoint is not None:
            train_cfg.runner.checkpoint = args.checkpoint
        print(f"📂 Carregando checkpoint: run={args.load_run}, checkpoint={getattr(args, 'checkpoint', 'latest')}")
    else:
        train_cfg.runner.resume = False
        print("🔄 Nenhum checkpoint especificado, usando policy padrão")
    
    ppo_runner, train_cfg = task_registry.make_alg_runner(env=env, name=args.task, args=args, train_cfg=train_cfg)
    policy = ppo_runner.get_inference_policy(device=env.device)
    
    # export policy as a jit module (used to run it from C++)
    if EXPORT_POLICY:
        path = os.path.join(LEGGED_GYM_ROOT_DIR, 'logs', train_cfg.runner.experiment_name, 'exported', 'policies')
        export_policy_as_jit(ppo_runner.alg.actor_critic, path)
        print('Exported policy as jit script to: ', path)

    # --- WASD Teleop • Setup (após criar policy, antes do loop) ---
    gym = env.gym
    viewer = env.viewer
    
    # Configurar câmera para foco no robô  
    if viewer is not None:
        # Posicionar câmera para melhor visualização do robô durante teleop
        gym.viewer_camera_look_at(viewer, None, gymapi.Vec3(0, -2, 1.5), gymapi.Vec3(0, 0, 0.5))
    
    # Registrar teclas
    gym.subscribe_viewer_keyboard_event(viewer, gymapi.KEY_W, "cmd_forward")
    gym.subscribe_viewer_keyboard_event(viewer, gymapi.KEY_S, "cmd_back")
    gym.subscribe_viewer_keyboard_event(viewer, gymapi.KEY_A, "cmd_left")
    gym.subscribe_viewer_keyboard_event(viewer, gymapi.KEY_D, "cmd_right")
    gym.subscribe_viewer_keyboard_event(viewer, gymapi.KEY_LEFT_SHIFT, "speed_boost")
    
    # Estados de comando
    vx, wz = 0.0, 0.0              
    VX_BASE, WZ_BASE = 0.8, 0.8    # Limites seguros baseados no treino
    VX_FAST, WZ_FAST = 1.0, 1.0    # Com Shift (dentro dos limites de treino)
    boost = False
    
    # Suavização (evita trancos)
    vx_cmd, wz_cmd = 0.0, 0.0
    alpha = 0.2   # 0..1 (maior = responde mais rápido)
    
    def _apply_commands_to_env(_vx, _wz):
        """Aplica comandos de velocidade ao ambiente"""
        if hasattr(env, "commands"):
            env.commands[:, 0] = _vx   # vx (m/s) - frente/trás
            env.commands[:, 1] = 0.0   # vy (m/s) - lateral (zero para humanoide)
            env.commands[:, 2] = _wz   # yaw (rad/s) - rotação
        else:
            print("Aviso: env.commands não encontrado - verifique a implementação")
    # --- fim setup WASD ---

    # Inicializar variáveis do loop
    dones = torch.zeros(env.num_envs, dtype=torch.bool, device=env.device)
    
    for i in range(10*int(env.max_episode_length)):
        # --- WASD Teleop • Loop de eventos (dentro do loop principal) ---
        events = gym.query_viewer_action_events(viewer)
        for e in events:
            pressed = (e.value > 0.5)  # 1.0 quando pressionado, 0.0 quando solto
            if e.action == "cmd_forward":
                vx = +1.0 if pressed else 0.0
            elif e.action == "cmd_back":
                vx = -1.0 if pressed else 0.0
            elif e.action == "cmd_left":
                wz = +1.0 if pressed else 0.0  # Girar esquerda
            elif e.action == "cmd_right":
                wz = -1.0 if pressed else 0.0  # Girar direita
            elif e.action == "speed_boost":
                boost = True if pressed else False
        
        # Escala final levando em conta Shift
        VX = VX_FAST if boost else VX_BASE
        WZ = WZ_FAST if boost else WZ_BASE
        
        # Suavização (EMA) para movimento fluido
        vx_cmd = (1 - alpha) * vx_cmd + alpha * (vx * VX)
        wz_cmd = (1 - alpha) * wz_cmd + alpha * (wz * WZ)
        
        # Aplicar comandos ao ambiente
        _apply_commands_to_env(vx_cmd, wz_cmd)
            
        try:
            actions = policy(obs.detach())
            obs, _, rews, dones, infos = env.step(actions.detach())
            
            # Se robo caiu/resetou, mostrar info
            if hasattr(dones, 'any') and dones.any():
                print(f"🔄 Episode reset at step {i}")
        except Exception as e:
            print(f"❌ Erro na execução: {e}")
            print("Parando simulação...")
            break
        # --- fim loop WASD ---

if __name__ == '__main__':
    EXPORT_POLICY = True
    RECORD_FRAMES = False
    MOVE_CAMERA = False
    args = get_args()
    play(args)
