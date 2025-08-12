
from legged_gym.envs.base.legged_robot import LeggedRobot

from isaacgym.torch_utils import *
from isaacgym import gymtorch, gymapi, gymutil
import torch

class G1Robot(LeggedRobot):
    
    def _get_noise_scale_vec(self, cfg):
        """ Sets a vector used to scale the noise added to the observations.
            [NOTE]: Must be adapted when changing the observations structure

        Args:
            cfg (Dict): Environment config file

        Returns:
            [torch.Tensor]: Vector of scales used to multiply a uniform distribution in [-1, 1]
        """
        noise_vec = torch.zeros_like(self.obs_buf[0])
        self.add_noise = self.cfg.noise.add_noise
        noise_scales = self.cfg.noise.noise_scales
        noise_level = self.cfg.noise.noise_level
        noise_vec[:3] = noise_scales.ang_vel * noise_level * self.obs_scales.ang_vel
        noise_vec[3:6] = noise_scales.gravity * noise_level
        noise_vec[6:9] = 0. # commands
        noise_vec[9:9+self.num_actions] = noise_scales.dof_pos * noise_level * self.obs_scales.dof_pos
        noise_vec[9+self.num_actions:9+2*self.num_actions] = noise_scales.dof_vel * noise_level * self.obs_scales.dof_vel
        noise_vec[9+2*self.num_actions:9+3*self.num_actions] = 0. # previous actions
        noise_vec[9+3*self.num_actions:9+3*self.num_actions+2] = 0. # sin/cos phase
        
        return noise_vec

    def _init_foot(self):
        self.feet_num = len(self.feet_indices)
        
        rigid_body_state = self.gym.acquire_rigid_body_state_tensor(self.sim)
        self.rigid_body_states = gymtorch.wrap_tensor(rigid_body_state)
        self.rigid_body_states_view = self.rigid_body_states.view(self.num_envs, -1, 13)
        self.feet_state = self.rigid_body_states_view[:, self.feet_indices, :]
        self.feet_pos = self.feet_state[:, :, :3]
        self.feet_vel = self.feet_state[:, :, 7:10]
        
    def _init_buffers(self):
        super()._init_buffers()
        self._init_foot()
        
        # Buffer para comando de pulo neural (biomimético)
        self.jump_command_buf = torch.zeros(self.num_envs, 1, dtype=torch.float, device=self.device, requires_grad=False)
        self.jump_preparation_timer = torch.zeros(self.num_envs, dtype=torch.float, device=self.device, requires_grad=False)

    def update_feet_state(self):
        self.gym.refresh_rigid_body_state_tensor(self.sim)
        
        self.feet_state = self.rigid_body_states_view[:, self.feet_indices, :]
        self.feet_pos = self.feet_state[:, :, :3]
        self.feet_vel = self.feet_state[:, :, 7:10]
        
    def _post_physics_step_callback(self):
        self.update_feet_state()

        period = 0.8
        offset = 0.5
        self.phase = (self.episode_length_buf * self.dt) % period / period
        self.phase_left = self.phase
        self.phase_right = (self.phase + offset) % 1
        self.leg_phase = torch.cat([self.phase_left.unsqueeze(1), self.phase_right.unsqueeze(1)], dim=-1)
        
        return super()._post_physics_step_callback()
    
    
    def compute_observations(self):
        """ Computes observations
        """
        sin_phase = torch.sin(2 * np.pi * self.phase ).unsqueeze(1)
        cos_phase = torch.cos(2 * np.pi * self.phase ).unsqueeze(1)
        self.obs_buf = torch.cat((  self.base_ang_vel  * self.obs_scales.ang_vel,
                                    self.projected_gravity,
                                    self.commands[:, :3] * self.commands_scale,
                                    (self.dof_pos - self.default_dof_pos) * self.obs_scales.dof_pos,
                                    self.dof_vel * self.obs_scales.dof_vel,
                                    self.actions,
                                    sin_phase,
                                    cos_phase,
                                    self.jump_command_buf  # NOVO: Comando neural de pulo
                                    ),dim=-1)
        self.privileged_obs_buf = torch.cat((  self.base_lin_vel * self.obs_scales.lin_vel,
                                    self.base_ang_vel  * self.obs_scales.ang_vel,
                                    self.projected_gravity,
                                    self.commands[:, :3] * self.commands_scale,
                                    (self.dof_pos - self.default_dof_pos) * self.obs_scales.dof_pos,
                                    self.dof_vel * self.obs_scales.dof_vel,
                                    self.actions,
                                    sin_phase,
                                    cos_phase,
                                    self.jump_command_buf  # NOVO: Comando neural de pulo
                                    ),dim=-1)
        # add perceptive inputs if not blind
        # add noise if needed
        if self.add_noise:
            self.obs_buf += (2 * torch.rand_like(self.obs_buf) - 1) * self.noise_scale_vec

        
    def _reward_contact(self):
        res = torch.zeros(self.num_envs, dtype=torch.float, device=self.device)
        for i in range(self.feet_num):
            is_stance = self.leg_phase[:, i] < 0.55
            contact = self.contact_forces[:, self.feet_indices[i], 2] > 1
            res += ~(contact ^ is_stance)
        return res
    
    def _reward_feet_swing_height(self):
        contact = torch.norm(self.contact_forces[:, self.feet_indices, :3], dim=2) > 1.
        pos_error = torch.square(self.feet_pos[:, :, 2] - 0.08) * ~contact
        return torch.sum(pos_error, dim=(1))
    
    def _reward_alive(self):
        # Reward for staying alive
        return 1.0
    
    def _reward_contact_no_vel(self):
        # Penalize contact with no velocity
        contact = torch.norm(self.contact_forces[:, self.feet_indices, :3], dim=2) > 1.
        contact_feet_vel = self.feet_vel * contact.unsqueeze(-1)
        penalize = torch.square(contact_feet_vel[:, :, :3])
        return torch.sum(penalize, dim=(1,2))
    
    def _reward_hip_pos(self):
        return torch.sum(torch.square(self.dof_pos[:,[1,2,7,8]]), dim=1)
    
    def set_jump_command(self, jump_intent):
        """Sistema biomimético completo de pulo com aterrissagem estável"""
        if jump_intent > 0.0:
            print(f"🧠 JUMP SEQUENCE INITIATED - Current velocity: {self.base_lin_vel[0, :2].cpu().numpy()}")
            
        self.jump_command_buf[:, 0] = jump_intent
        
        # Timer para sequência de pulo (preparação → execução → aterrissagem → recuperação)
        if jump_intent > 0.0:
            self.jump_preparation_timer[:] = 1.0  # Ativa ciclo completo de pulo
    
    def _reward_jump_preparation(self):
        """FASE 1: Recompensa postura de preparação (agachamento) quando comando ativo"""
        jump_active = self.jump_command_buf[:, 0] > 0.5
        if not torch.any(jump_active):
            return torch.zeros(self.num_envs, device=self.device)
            
        # Recompensar flexão de joelhos e quadris para preparação biomimética
        knee_flex = self.dof_pos[:, [3, 9]]  # Joelhos esquerdo e direito 
        hip_flex = self.dof_pos[:, [2, 8]]   # Quadris esquerdo e direito
        
        # Posição ideal: joelhos ~0.4-0.6 rad, quadris ~-0.2 a -0.4 rad
        knee_preparation = torch.exp(-torch.sum((knee_flex - 0.5)**2, dim=1))
        hip_preparation = torch.exp(-torch.sum((hip_flex + 0.3)**2, dim=1))
        
        preparation_reward = (knee_preparation + hip_preparation) / 2.0
        return preparation_reward * jump_active.float()
    
    def _reward_jump_takeoff(self):
        """FASE 2: Recompensa extensão coordenada das pernas durante decolagem"""
        jump_active = self.jump_command_buf[:, 0] > 0.5
        
        # Detectar fase de decolagem (pés ainda tocando chão + força vertical)
        feet_contact = torch.norm(self.contact_forces[:, self.feet_indices, :], dim=2) > 1.0
        both_feet_contact = torch.all(feet_contact, dim=1)
        
        vertical_velocity = self.base_lin_vel[:, 2]  # Velocidade vertical
        taking_off = both_feet_contact & (vertical_velocity > 0.1)  # Subindo
        
        if not torch.any(taking_off & jump_active):
            return torch.zeros(self.num_envs, device=self.device)
        
        # Recompensar extensão coordenada (velocidade das juntas das pernas)
        leg_extension_vel = -self.dof_vel[:, [3, 9]]  # Extensão dos joelhos
        coordination = torch.exp(-torch.abs(leg_extension_vel[:, 0] - leg_extension_vel[:, 1]))
        
        takeoff_reward = coordination * torch.clamp(vertical_velocity, 0, 2.0)
        return takeoff_reward * taking_off.float() * jump_active.float()
        
    def _reward_jump_airtime(self):
        """FASE 3: Recompensa controle postural durante voo"""
        # Detectar fase aérea (sem contato com chão)
        feet_contact = torch.norm(self.contact_forces[:, self.feet_indices, :], dim=2) > 1.0
        airborne = ~torch.any(feet_contact, dim=1)  
        
        jump_active = self.jump_command_buf[:, 0] > 0.5
        
        if not torch.any(airborne & jump_active):
            return torch.zeros(self.num_envs, device=self.device)
            
        # Recompensar orientação estável durante voo
        orientation_stability = torch.exp(-torch.sum(self.base_ang_vel[:, :2]**2, dim=1))
        
        # Recompensar altura máxima atingida
        base_height = self.base_pos[:, 2]
        target_height = self.cfg.rewards.base_height_target  # 0.78m
        jump_height = torch.clamp(base_height - target_height - 0.1, 0, 0.5)
        
        airtime_reward = orientation_stability * (1.0 + 2.0 * jump_height)
        return airtime_reward * airborne.float() * jump_active.float()
    
    def _reward_jump_landing(self):
        """FASE 4: Recompensa aterrissagem controlada e estável"""
        # Detectar aterrissagem (transição aéreo → contato)
        feet_contact = torch.norm(self.contact_forces[:, self.feet_indices, :], dim=2) > 1.0
        both_feet_contact = torch.all(feet_contact, dim=1)
        
        # Aterrissagem = velocidade vertical negativa + ambos pés no chão
        vertical_velocity = self.base_lin_vel[:, 2]
        landing = both_feet_contact & (vertical_velocity < -0.1)
        
        jump_active = self.jump_command_buf[:, 0] > 0.5
        
        if not torch.any(landing & jump_active):
            return torch.zeros(self.num_envs, device=self.device)
            
        # Recompensar absorção suave do impacto (flexão controlada)
        knee_absorption = torch.sum(torch.clamp(self.dof_pos[:, [3, 9]] - 0.2, 0, 0.4), dim=1)
        
        # Recompensar estabilidade pós-aterrissagem (baixa velocidade angular)
        stability = torch.exp(-torch.sum(self.base_ang_vel**2, dim=1))
        
        # Penalizar aterrissagens muito bruscas
        impact_penalty = torch.exp(-torch.abs(vertical_velocity + 2.0))
        
        landing_reward = (knee_absorption + stability + impact_penalty) / 3.0
        return landing_reward * landing.float() * jump_active.float()
        
    def _reward_jump_recovery(self):
        """FASE 5: Recompensa recuperação e continuação do movimento"""
        jump_active = self.jump_command_buf[:, 0] > 0.5
        
        # Detectar fase de recuperação (pés no chão + estabilidade atingida)
        feet_contact = torch.norm(self.contact_forces[:, self.feet_indices, :], dim=2) > 1.0
        stable = torch.all(feet_contact, dim=1) & (torch.abs(self.base_lin_vel[:, 2]) < 0.2)
        
        if not torch.any(stable & jump_active):
            return torch.zeros(self.num_envs, device=self.device)
            
        # Recompensar manutenção do movimento horizontal original
        horizontal_vel = torch.norm(self.base_lin_vel[:, :2], dim=1)
        target_vel = torch.norm(self.commands[:, :2], dim=1)
        
        velocity_maintenance = torch.exp(-torch.abs(horizontal_vel - target_vel))
        
        # Recompensar postura vertical
        upright_posture = torch.exp(-torch.sum(self.projected_gravity[:, :2]**2, dim=1))
        
        recovery_reward = (velocity_maintenance + upright_posture) / 2.0
        return recovery_reward * stable.float() * jump_active.float()
    