
# STEP 4 — 🔄 Isaac Lab Teleop + G1 Walking + (Prep) GR00T Locomotion

**Objetivo (escopo reduzido):** validar, no seu sistema, que **teleoperação por teclado** funciona no Isaac Lab e que **o Unitree G1 caminha na simulação** usando um ambiente de locomoção já registrado. Em paralelo, deixaremos **o servidor de inferência do GR00T** pronto para a próxima etapa (integração efetiva). *Deploy no robô real não é requerido.*

> Este passo parte dos seus resultados dos **STEP 1–3** (Instalação do Isaac Sim; Conversão URDF→USD; Smoke test do USD) fileciteturn2file6 fileciteturn2file0 fileciteturn2file9, e usa **procedimentos oficiais do Isaac Lab e do GR00T** (teleoperação e devices; ambientes de locomoção G1; servidor de inferência do GR00T). Consulte as referências online citadas ao final dos blocos.

---

## ✅ Resultado esperado deste Step

1) **Isaac Lab Teleop Demo pronto** (script abre, sem erros).  
2) **Controle por teclado (SE(2))** ativo — setas direcionais para translação e **Z/X** para yaw (rotacionar).  
3) **G1 Walking em simulação** — ambiente `Isaac‑Velocity‑Flat‑G1‑Play‑v0` abre, o G1 aparece e responde aos comandos.  
4) **Servidor GR00T em execução** localmente (modelo N1.5‑3B, quantizado ou não), validado via cliente de teste.

> **Nota sobre teclas:** no Isaac Lab, o device de locomotion **SE(2) Keyboard** usa **setas** e **Z/X** (não WASD) por padrão. Para manipulação/SE(3), há mapeamento WASD. Isso é o comportamento documentado. Fonte: *SE(2) Keyboard* e *Devices API/Teleoperation* do Isaac Lab (ver referências).

---

## 🔧 Pré‑requisitos rápidos (confirmar)

- Ambientes dos **STEP 1–3** feitos e validados. fileciteturn2file6 fileciteturn2file0 fileciteturn2file9  
- Conda env: `unitree-groot` (Python 3.11).  
- Isaac Sim 5.0 instalado e funcional (UI abre). fileciteturn2file12  
- USD do G1 gerado:  
  `/home/pedro_setubal/Workspaces/unitree_rl/IsaacLab/source/extensions/omni.isaac.lab_assets/data/Robots/Unitree/G1/23dof/g1_23dof.usd` fileciteturn2file9

```bash
# Preparar terminal
source ~/anaconda3/etc/profile.d/conda.sh
conda activate unitree-groot
export OMNI_KIT_ACCEPT_EULA=YES
cd ~/Workspaces/unitree_rl/IsaacLab
```

---

## A) 🔄 Sanidade do catálogo de ambientes (G1 registrado)

1. **Listar ambientes disponíveis** no Isaac Lab e confirmar os G1 *Velocity* (Flat/Rough/Play):  
   ```bash
   ./isaaclab.sh -p scripts/environments/list_envs.py | grep -i "G1"
   ```
   Esperado: entradas como **`Isaac-Velocity-Flat-G1-Play-v0`** (e Rough). (Referência: *Available Environments*.)

> Se nada aparecer, atualize o Isaac Lab para a *branch* estável mais recente.

---

## B) 🎮 Teleop SE(2) por teclado + G1 “Flat‑Play”

1. **Executar teleop SE(2) com teclado** no ambiente G1 “Flat‑Play” (1 env para debug):  
   ```bash
   ./isaaclab.sh -p scripts/environments/teleoperation/teleop_se2_agent.py        --task Isaac-Velocity-Flat-G1-Play-v0        --teleop_device keyboard        --num_envs 1
   ```

2. **Controles (SE(2) Keyboard)** — confirmados na doc:  
   - **Setas↑/↓**: avanço/recuo (v_x)  
   - **Setas←/→**: deslocamento lateral (v_y)  
   - **Z/X**: yaw ‑ rotação (ω_z)  
   - **Esc**: encerrar  
   > Fonte: *SE(2) Keyboard device* e *Teleoperation docs*.

3. **Critérios de sucesso**  
   - [ ] Janela abre sem *traceback*; *fps* estável.  
   - [ ] O **G1 aparece** na cena e **responde** às teclas (translação e yaw).  
   - [ ] Sem *warnings* de “missing articulation” ou “invalid prim path”.  
   - [ ] Física estável (sem “explodir”).  

> Dica: o modo “Flat‑Play” é para **execução/controle**, não requer *checkpoint* de RL. Se precisar, rode **Rough‑Play** para testar terreno irregular. As tasks de velocidade G1 fazem parte dos ambientes do Isaac Lab. (Ver *Performance Benchmarks* e *Available Environments*.)

**Troubleshooting rápido**  
- **G1 não aparece**: confirme o *task name* e se o pacote do Isaac Lab está atualizado; valide com `list_envs.py` (Seção A).  
- **Sem resposta ao teclado**: garanta o foco na janela do Isaac Sim; verifique que o argumento `--teleop_device keyboard` está presente (em versões recentes o nome do *flag* é exatamente esse).  
- **Oscilações/derrapagem**: reabra o USD do G1 e confira materiais de atrito nos pés (você aplicou no STEP 3) fileciteturn2file14; no *Play* os ganhos são conservadores.

---

## C) 🚶‍♂️ G1 Walking — validação mínima

1. Já no processo do item **B**, **ative o Play** (barra de espaço) e aplique pequenos comandos:  
   - Avance devagar (↑ curto), pare (soltar), gire levemente (Z/X).  
2. Observe: **centro de massa**, contato dos pés (sem *slip* graças ao material), e **limites** de junta respeitados. (Você checou limites/massas no STEP 2–3.) fileciteturn2file17 fileciteturn2file9

> Se quiser validar outras variações: substitua `Flat` por `Rough` no nome da task e repita o teste.

---

## D) 🤖 (Preparação) GR00T como *walking backend* — servidor local

> Integração direta GR00T→ações de locomoção ainda é experimental para humanoides; por isso, neste STEP 4 **somente preparamos e validamos o servidor de inferência** do GR00T para uso no próximo passo (ponte GR00T→SE(2) do Isaac Lab).

1. **Clonar e instalar o GR00T** (repositório oficial):  
   ```bash
   cd ~/Workspaces/unitree_rl
   git clone https://github.com/NVIDIA/Isaac-GR00T.git
   cd Isaac-GR00T
   python -m pip install -e .
   # (Opcional) quantização leve
   python -m pip install bitsandbytes
   ```

2. **Baixar modelo aberto e iniciar o servidor de inferência** (GPU):  
   ```bash
   # Modelo aberto recomendado (público): GR00T-N1.5-3B
   # Observação: não há "nano" oficial público; o 3B roda em 12 GB com quantização.
   python scripts/inference_service.py --server        --model-path nvidia/GR00T-N1.5-3B        --device cuda
   ```

3. **Testar com o cliente oficial** (sanidade do servidor):  
   ```bash
   # Em outro terminal
   cd ~/Workspaces/unitree_rl/Isaac-GR00T
   python scripts/inference_service.py --client        --model-path nvidia/GR00T-N1.5-3B        --device cuda
   # Envie um prompt simples (seguindo instruções do cliente) e verifique resposta.
   ```

4. **Critérios de sucesso (GR00T)**  
   - [ ] Servidor sobe sem erro; **baixa** pesos do HF na primeira vez.  
   - [ ] Cliente conecta e **recebe resposta** do servidor.  
   - [ ] GPU é utilizada (ver *logs*).  

> Referência: README do **Isaac‑GR00T** (servidor/cliente de inferência; `--server/--client`, `--model-path`, `--device`).

**Observação sobre “modelo nano”**  
- Até esta data, os **modelos abertos** documentados são **3B** e **8B**; variantes “nano” não constam publicamente. É possível **quantizar** o 3B (ex.: 4‑bit) para reduzir memória, mantendo usabilidade na sua **RTX 4070 SUPER 12 GB**. (Ver docs e README do GR00T.)

---

## E) ✅ Checklist de Validação (preencha durante o teste)

- [ ] **Teleop script ok**: `teleop_se2_agent.py` inicia sem erros.  
- [ ] **Device teclado ok**: `--teleop_device keyboard` reconhecido.  
- [ ] **G1 aparece**: task `Isaac‑Velocity‑Flat‑G1‑Play‑v0` carrega o robô.  
- [ ] **Caminhada**: setas/Z‑X produzem deslocamento/rotação estáveis.  
- [ ] **GR00T**: servidor de inferência rodando; cliente retorna resposta.

---

## 📎 Próximo passo (STEP 5 — integração GR00T↔Isaac Lab)

- Implementar uma **ponte SE(2)** simples (ex.: *“text‑to‑velocity”*), na qual comandos de linguagem natural passam pelo servidor GR00T e **viram vetores (v_x, v_y, ω_z)** injetados na **mesma interface SE(2)** usada pelo teclado.  
- Padrão robusto: manter **GR00T como planejador de alto nível** (texto→velocidade) e **locomoção reativa** pelo controlador/ambiente do Isaac Lab (que já é funcional).

---

## 🔗 Referências confiáveis (online)

- **Teleoperation & Devices (Isaac Lab):** visão geral de *Teleoperation and Imitation Learning* e **flag `--teleop_device`**; *SE(3) agent* e exemplos de uso.  
  ⮕ Docs: Teleoperation tutorial e devices API, inclusive *keyboard* (teclas e execução).  
- **SE(2) Keyboard (Isaac Lab):** mapeamento de teclas para locomoção no plano (setas, Z/X).  
- **Available Environments (Isaac Lab):** lista e nomes de tasks, incluindo **`Isaac‑Velocity‑Flat‑G1‑Play‑v0`**.  
- **Performance Benchmarks:** confirma tasks de velocidade (Flat/Rough) e perfis.  
- **GR00T (NVIDIA):** repositório e README de **Isaac‑GR00T**, com **`inference_service.py`** (`--server/--client`, `--model-path`, `--device`).

*(As URLs constam no dossiê técnico deste projeto e foram consultadas para garantir comandos/conceitos atualizados.)*
