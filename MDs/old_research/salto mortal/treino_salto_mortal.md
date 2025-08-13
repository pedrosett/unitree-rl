bora! dá pra treinar um **salto mortal (backflip)** do G1 do zero em simulação — mas é uma tarefa **bem mais difícil** que caminhar. Vou te passar um caminho didático, com opções de abordagem, o que muda no ambiente, como **esculpir recompensas**, e como treinar de fato no teu setup (Isaac Gym + RSL-RL). Foco 100% em simulação.

---

# 1) O que torna o backflip difícil (e o que precisamos)

* **Manobra balística + contatos**: agachar → impulso forte → fase aérea (voo) → rotação completa (\~360°) → aterrissagem estável.
* **Momento angular**: com apenas 12DOF (pernas) é possível, mas **bem mais difícil** do que com braços/torso (que ajudam a gerar/ajustar momento). Se puder, **considere treinar com 23DOF** depois que dominar a versão 12DOF.
* **Modelo de atuador**: você está controlando **posição de juntas** (PD) e não torque direto; logo, precisão dos ganhos PD e dos limites de velocidade é crucial para gerar impulso sem instabilidade numérica.
* **Física e timestep**: backflip exige **substeps e dt** menores para simular impacto e voo decentemente (ex.: `dt≈0.002–0.005`, `substeps=2–4`).

> Minha recomendação didática:
>
> 1. comece com **currículo** (vertical jump → meia volta → 3/4 → 360°), 12DOF;
> 2. depois, migre para **imitação de trajetória** (tracking de referência) para refinar;
> 3. se quiser excelência, libere **braços/torso (23DOF)**.

---

# 2) Estratégias de treino (escolha o caminho)

## A) Currículo (sem referência externa) – simples de começar

Você ensina o agente por **fases** e **metas graduais**:

1. **“Crouch & Jump”**: agachar e saltar verticalmente; aterrissar em pé.
2. **“Quarter flip”**: exigir \~90° de rotação no eixo pitch;
3. **“Half flip”**: \~180°;
4. **“Full backflip”**: \~360° (aterrissar de pé, orientação alinhada).

Como fazer: você adiciona um **sinal de fase** ou **comando-alvo** no *obs* que guia o agente (ex.: `target_pitch(t)` ou `target_rotation_fraction` ∈ \[0..1]). O reward dá **bônus por cumprir a meta atual** e você incrementa a meta ao longo do treino (ou em cada reset). É o caminho com menos assets.

## B) Imitação de movimento (tracking de referência) – mais estável

Crie/obtenha uma **trajetória de referência** (ângulos por junta, posição/velocidade do tronco e pés) ao longo do tempo para um backflip “bonito”. A recompensa foca em **aproximar-se da referência**:

* `r_pose = exp(-||q - q_ref||)`,
* `r_end_eff = exp(-||p_ee - p_ref||)`,
* `r_com_vel = exp(-||v_com - v_ref||)`,
* `r_orient = exp(-||quat_err||)`,
* “gates” para **no-contact** durante voo e **bom contato** no pouso.

Vantagem: **converge mais rápido e “aprende bonito”**. Desvantagem: requer referência (pode ser criada com IK, spline paramétrica ou captura).

> Comece com **A (currículo)** para entender a dinâmica, depois evolua para **B (tracking)**.

---

# 3) O que editar no `unitree_rl_gym` (conceito)

Vamos criar uma **nova task** chamada `g1_flip`. A ideia é **copiar** a base da task do G1 (locomoção) e modificar:

1. **Nova task** (arquivos típicos):

* `legged_gym/envs/g1/g1_flip_task.py` (classe do env)
* `legged_gym/envs/g1/g1_flip_config.py` (config, PD gains, limites, timestep, substeps, etc.)
* Registro da task no mecanismo de *factory* (onde hoje você passa `--task g1`; você vai poder passar `--task g1_flip`)

2. **Ação/Observação**

* **Ações**: mantenha **posições alvo** (12 valores). Ajuste **escalas** para permitir amplitude suficiente no agachamento/impulso.
* **Observações** (exemplos):

  * estados proprioceptivos: `q`, `q̇`, IMU (orientação do tronco),
  * **fase/tempo normalizado** ϕ ∈ \[0..1] (muito útil),
  * **alvo**: rotação desejada (ex.: `target_pitch_rate` ou `target_total_pitch`),
  * histórico curto (ex.: últimas 1–2 steps) ajuda estabilidade (ou use LSTM, que já está presente).

3. **Resets**

* **Falha**: caiu (tronco abaixo de certa altura, orientação muito errada, velocidade vertical muito negativa pós-pouso).
* **Sucesso** (no currículo): atingiu rotação alvo e **parou em pé** (orientação próxima da vertical, pés no chão, velocidade base baixa). Pode encerrar episódio com **grande bônus**.

4. **Recompensas** (exemplos práticos)

* **Fase agachamento** (se usar currículo por fases):

  * `+` agachar (reduzir altura do COM / ângulo de joelho alto) sem antecipar contato errado;
* **Impulso**:

  * `+` grande **velocidade angular** no pitch, `+` **velocidade vertical** do COM;
  * penalize **torque/velocidade** exagerados para não explodir numericamente;
* **Voo**:

  * `+` manter **no-contact** até atingir fração da rotação (use “gates”: só dá reward de voo se nenhum pé em contato);
  * `+` alinhar pitch à referência/objetivo;
* **Pouso**:

  * `+` pés firmes (contatos “sem escorregar”), **orientação do tronco próxima de vertical**, **velocidades pequenas** pós-impacto;
  * grande **bônus de sucesso** quando cumpre a rotação (\~360°) **e** estabiliza em pé.
* **Penalidades gerais**: saturação de torque/vel/joint-limits, *jerk* de ação, auto-colisões se houver.

5. **Física (estabilidade)**

* `dt` pequeno (ex.: `0.002–0.005 s`), `substeps=2–4`;
* fricção do solo **realista** (0.8 ± DR), restituição baixa (0–0.1);
* PD gains: comece **mais baixos** e aumente conforme estabilidade. Impulso forte com PD muito alto pode instabilizar.

6. **Domain Randomization (DR)**

* massa do tronco/pernas ±(5–15)%, fricção, leve ruído no IMU;
* isso ajuda a **generalização** pro MuJoCo (*Sim2Sim*).

---

# 4) Recompensas (exemplos concretos)

Suponha **currículo** com alvo de rotação `θ*` no eixo pitch, e fase ϕ (0→1):

* **Rotação alvo:**
  `r_rot = exp(-α * |θ(t) - θ*(ϕ)|)`  (α \~ 5–10)
  Onde `θ*(ϕ)` é uma rampa/spline que cresce até ≈ `2π` no final (para backflip). No currículo, `θ*` é menor (ex.: `π/2`, `π`, `3π/2`, `2π`) e vai aumentando entre episódios.

* **Velocidade angular no impulso:**
  `r_ω = clamp( (|ω_pitch| - ω_min) / (ω_max - ω_min), 0, 1 )`
  (só ativa numa janela de tempo/fase; encoraja gerar momento).

* **Voo sem contato:**
  `r_air = 1` se `contacts_feet == 0` durante janela de voo; senão 0.
  (penalize contato precoce)

* **Pouso estável (gate no fim):**
  `r_land = 1` se:
  `upright(tronco) < ε_orient` **e** `|v_base| < ε_vel` **e** `contacts_feet >= thresh` **e** `θ ≈ 2π ± ε_rot`.

* **Penalidades:**
  `r_pen = - k1 * ||τ||^2 - k2 * ||q̇||^2 - k3 * jerk(ações)`
  `- k4 * limits_violation - k5 * slip(feet)`.

* **Bônus de sucesso:**
  no último terço do episódio, se `r_land` verdadeiro, adicione `+R_success` (grande).

> Dica: **gating** é essencial — certos termos só valem na **fase certa** (agachamento, impulso, voo, pouso). Evita “trapaças”.

---

# 5) Como treinar (no seu PC)

## 5.1 Criar a task `g1_flip`

* Duplique a task do G1 como base (onde hoje está a tarefa de locomoção).
  Ex.: copie `g1_task.py` → `g1_flip_task.py` e `g1_config.py` → `g1_flip_config.py`.
* No novo arquivo, implemente:

  * **obs** estendida (inclua `ϕ`, alvos, seno/cosseno de ϕ ajudam muito);
  * **reset** especial (sucesso e falha);
  * **compute\_reward()** com os termos acima e **gates de fase**;
  * **update\_phase** por step (ex.: `ϕ += Δt/T`, reinicia ao final);
  * **currículo**: aumente alvo `θ*` se o agente bateu meta N vezes.
* Registre a task para poder chamá-la com `--task g1_flip`.

> Se preferir começar mais rápido, implemente uma **versão mínima**:
> (i) `ϕ` progride linearmente,
> (ii) reward só com `r_rot`, `r_air`, `r_land` e penalidades básicas,
> (iii) currículo manual: coloque `θ*` = `π/2` por 1–2k iterações, depois `π`, etc.

## 5.2 Hiperparâmetros e física

* `--num_envs`: 2048–4096 (se sobrar VRAM).
* `--max_iterations`: **≥ 20k–50k** (bem mais que caminhada).
* `dt=0.002–0.005`, `substeps=2–4`.
* **PD gains**: comece moderado (evitar saturação), aumente depois.
* **Action scale**: permita amplitude para agachamento e impulso.

## 5.3 Comandos de treino (exemplo)

```bash
cd /home/pedro_setubal/Workspaces/unitree_rl/isaacgym/python/examples/unitree_rl_gym

# treino com currículo inicial (quarter/half flip):
python legged_gym/scripts/train.py \
  --task g1_flip \
  --num_envs 2048 \
  --max_iterations 20000 \
  --experiment_name G1_FLIP_curriculum \
  --run_name run1 \
  --headless
```

**Acompanhe**: reward média, taxa de sucesso (defina um métrico), quedas.
Se empacar: aumente iterações, ajuste pesos, simplifique (ex.: peça só “pular e voltar em pé” antes de pedir rotação grande), revise PD/time-step.

## 5.4 Visualizar e exportar

```bash
python legged_gym/scripts/play.py \
  --task g1_flip \
  --experiment_name G1_FLIP_curriculum \
  --run_name run1 \
  --headless False
```

Isso exporta `policy_1.pt` em `logs/.../exported/policies/`.
Depois valide no MuJoCo ajustando `policy_path` no `g1.yaml` e rodando `deploy_mujoco.py`.

---

# 6) Debug que salva horas

* **Sem sair do chão?** aumente **action scale** ou PD; verifique limites de velocidade; confira se reward no impulso está ativo (gates corretos).
* **Derrapa/escorrega no pouso?** fricção do solo/sola dos pés; penalize *slip*; reduza restituição.
* **Explode numericamente?** diminua `dt` ou aumente `substeps`; reduza PD; limite torque/velocidade; normalize observações.
* **Aprende “truques” indesejados?** reforce gating e termos de sucesso; penalize comportamentos errados explícitos.

---

# 7) Extensões bacanas

* **Trigger pelo teclado** (no `play.py`): mapeie, por exemplo, a tecla **F** para “iniciar flip” definindo `ϕ=0` e “congelando” comandos de marcha enquanto durar o flip.
* **Imitação (track de referência)**: quando dominar o currículo, gere uma trajetória de referência (keyframes ou IK) e troque o reward principal por tracking — costuma gerar flips mais “limpos” e aterrissagens suaves.
* **23DOF**: libere braços/torso depois; fica mais fácil gerar e ajustar **momento angular** no ar.

---

## Resumo do plano mínimo (para você começar hoje)

1. **Duplique** a task do G1 para `g1_flip` e **adicione**: fase ϕ, alvo de rotação `θ*`, rewards com **gates** (impulso, voo, pouso).
2. **Currículo**: `θ*` = `π/2` → `π` → `3π/2` → `2π`.
3. **Física**: `dt≈0.002–0.005`, `substeps=2–4`, PD moderado.
4. **Treine** `--num_envs 2048`, `--max_iterations 20k+`.
5. **Play** e **Sim2Sim** (MuJoCo).
6. Quando fechar o 360° com estabilidade, **refine** com tracking ou 23DOF.

Se quiser, eu te ajudo criando um **esqueleto de task `g1_flip`** (arquivos base + funções de recompensa e currículo) já plugado no `unitree_rl_gym` — aí você só preenche os detalhes que preferir. Quer que eu gere esse boilerplate?
