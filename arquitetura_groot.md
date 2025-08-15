
# Arquitetura do NVIDIA Isaac GR00T (N1 e N1.5) — Guia Técnico Didático

> **TL;DR:** O GR00T é um **modelo fundacional de robótica** com duas partes acopladas: um **módulo de visão‑linguagem (System 2)** que entende a cena e a instrução, e um **módulo de ação baseado em Diffusion/Flow Matching (System 1)** que transforma esse contexto + propriocepção em **vetores de ação contínuos** (em *chunks*) para o robô. Em **N1.5**, o VLM fica **congelado** e há melhorias de *adapter*, objetivos de **FLARE** (world‑modeling) e uso de **DreamGen** para dados sintéticos, resultando em melhor *grounding* e *language following*. citeturn3view0turn6view0

---

## 1) Visão geral (dual‑system)

- **Entrada:** imagens (uma ou mais câmeras), **texto** (instrução), **estado do robô** (propriocepção: posições/velocidades de juntas, pose do EEF etc.).  
- **System 2 — VLM (Eagle/Eagle 2.5):** converte visão+texto em **tokens** compactos.  
- **System 1 — Diffusion Transformer (DiT) / Flow‑Matching Policy:** recebe **estado do robô**, **tokens do VLM** e **ações “ruidosas”** (action tokens) e **des‑ruida** para produzir um **action chunk** (vários passos de ação).  
- **Acoplamento:** ambos são *Transformers* treinados **fim‑a‑fim** para coordenação entre “entender” e “agir”. citeturn5view0

**Por que dois sistemas?** Inspirado em cognição humana: **System 2** (lento/deliberativo) para percepção e linguagem; **System 1** (rápido/reflexo) para controle motor contínuo em tempo quase real. citeturn3view0

---

## 2) System 2 — Vision‑Language Model (VLM)

### 2.1 Backbone Eagle/Eagle 2.x
- O GR00T usa o **Eagle‑2**/**Eagle 2.5** como VLM pré‑treinado em dados em escala web. citeturn5view0turn6view0
- No **N1.5**, o VLM fica **congelado na pré e na pós‑treinagem**, com **adapter MLP** simplificado + **LayerNorm** em visuais e texto, o que **melhora o grounding e o seguimento de linguagem**. citeturn6view0

### 2.2 Tokenização multimodal
- Frames RGB são codificados (ex.: **SigLIP‑2**), *pixel‑shuffle* e viram **~64 tokens por frame**; o texto é codificado por LLM (ex.: **SmolLM2/T5**, conforme variante). Em N1, **usa‑se embeddings de uma camada intermediária do LLM** para melhor velocidade e acurácia na política. citeturn5view0turn7view0
- **Multi‑view / multi‑frame:** os *image tokens* de todas as vistas/frames são **concatenados** e depois vêm os **tokens de linguagem**. citeturn8view0

**Saída do VLM:** uma **sequência de embeddings** visão‑linguagem que o System 1 consulta via **cross‑attention**. citeturn5view0

---

## 3) System 1 — Política de Ação (Diffusion Transformer / Flow Matching)

### 3.1 Encoders de estado e ação (por embodiment)
- **Estado (propriocepção)** e **ação** têm dimensões variáveis a depender do robô (**embodiment**). O GR00T usa **MLPs específicos por embodiment** para projetar tudo a um **espaço comum** de embeddings. citeturn5view0
- O **Action Encoder** também injeta a **etapa de difusão/flow** (timestep) junto com a **ação ruidosa**. citeturn5view0

### 3.2 “Action tokens” e *action chunking*
- **Action tokens** são **vetores de ação com ruído** que o modelo **des‑ruida** (*denoising*) passo a passo até virar **ações contínuas**. citeturn7view0
- A política **opera em *chunks*** — um **bloco** de vários passos de ação (ex.: 16) é previsto de uma vez, o que dá **suavidade** e **baixa latência** (ex.: ~64 ms num L40 para 16 passos, em bf16). citeturn5view0

### 3.3 Núcleo DiT com *self‑/cross‑attention*
- O **DiT** alterna blocos de **self‑attention** (sobre *action tokens* + **estado**) com **cross‑attention** nos **tokens visão‑linguagem** do VLM; o condicionamento de difusão usa **AdaLN**. citeturn5view0turn8view0
- Ao final, um **Action Decoder (MLP)** **por embodiment** produz o vetor de ação no **espaço de controle** correto (juntas absolutas, **delta de EEF**, etc.). citeturn7view0

### 3.4 Treinamento e inferência (Flow Matching / Diffusion)
- **Objetivo principal (N1):** *flow matching* de ações com **DiT**; treina‑se para **des‑ruidar** *chunks* de ação. citeturn5view0
- **Inferência:** amostra‑se **ruído Gaussiano**, e o modelo **reconstrói iterativamente** o vetor de ação através de sua **predição de velocidade/campo vetorial** em poucas etapas (poucos passos de *denoising*). citeturn7view0turn8view0
- **N1.5:** mantém a cabeça DiT/**flow matching**, mas com **conector MLP** melhorado e **objetivo adicional FLARE** (*Future Latent Representation Alignment*) para aprender também de **vídeos humanos** (world‑modeling). citeturn6view0turn7view0

---

## 4) Espaços de observação e ação (*Embodiment heads*)

O GR00T fornece **cabeças pré‑treinadas** para diferentes robôs (o *EmbodimentTag* escolhe o formato correto de observação/ação):

- **`EmbodimentTag.GR1`** — humanoide com mãos: **espaço de juntas absolutas**;  
- **`EmbodimentTag.OXE_DROID`** — braço único: **controle por delta do EEF**;  
- **`EmbodimentTag.AGIBOT_GENIE1`** — humanoide com *grippers*: **juntas absolutas**.  
Há também um **`NEW_EMBODIMENT`** para novos formatos. citeturn1view0

> **Na prática:** o **formato da ação** depende da cabeça escolhida; a sua aplicação (sim/hardware) deve **mapear o vetor de ação** para o controlador correspondente (ex.: torques/velocidades/poses). citeturn1view0

---

## 5) Dados e estratégia de treinamento

### 5.1 Pirâmide de dados
- O GR00T organiza os dados como uma **pirâmide**: base com **vídeos humanos e web‑scale**, meio com **trajetórias sintéticas/simuladas**, topo com **teleop real** no robô. citeturn5view0

### 5.2 Unificação por “latent actions”
- Para fontes **sem ações explícitas** (vídeos humanos/neural), o GR00T aprende um **codebook de ações latentes (VQ‑VAE)** e/ou usa **modelo de dinâmica inversa** para inferir **pseud‑ações**, tratando tudo como “mais um embodiment”. citeturn5view0

### 5.3 Objetivos e dados extras no N1.5
- **FLARE** (alinhamento de representações futuras) como objetivo adicional;  
- **DreamGen** para **trajetórias sintéticas** de novos verbos e variações;  
- **VLM** atualizado (Eagle 2.5) com melhor *grounding*. citeturn6view0

---

## 6) Pipeline de inferência e integração

### 6.1 Uso básico (repo oficial)
1. Converter seus dados para o **schema LeRobot**;  
2. Carregar um **checkpoint Hugging Face**;  
3. Rodar **`Gr00tPolicy.get_action(sample)`** para obter um **action chunk**;  
4. Conectar a política ao **controlador do robô** (sim/hardware). citeturn1view0

> O repositório inclui **serviço de inferência** (cliente/servidor) e guias para **TensorRT/Jetson**. citeturn1view0

### 6.2 Teleop (WASD) — onde “entrar”
- **Teleop no simulador (Isaac Lab):** há *devices* prontos (Keyboard, Gamepad, SpaceMouse, OpenXR). Para **WASD**, use a **Keyboard** que expõe **SE(2)**/**SE(3)** conforme a cena. citeturn0search2
- **Mesclar com GR00T (opcional):** você pode combinar `a_gr00t` e `a_teleop` no **mesmo espaço de ação** do *embodiment* (ex.: `a_final = α·a_gr00t + (1−α)·a_teleop`). **Cuidado** para não conflitar com estabilização/locomoção.
- **Pós‑treino a partir de teleop:** colete demos com teleop → **post‑train** o GR00T para que ele aprenda o seu estilo/comando sem teclado em *runtime*. (O time da NVIDIA demonstra pós‑treino em robôs como **Unitree G1**.) citeturn6view0

---

## 7) Glossário rápido

- **VLM (Vision‑Language Model):** backbone que gera **embeddings** de visão+texto; no N1.5 ele é **congelado**. citeturn6view0  
- **Action tokens:** **ações corrompidas por ruído** usadas pelo DiT para aprender a **des‑ruidar** via *flow matching/diffusion*. citeturn7view0  
- **Diffusion Transformer (DiT):** *Transformer* com condicionamento de etapa (AdaLN) que alterna **self‑/cross‑attention** para prever ações. citeturn5view0turn8view0  
- **Flow Matching:** objetivo que treina um **campo vetorial** para levar ações ruidosas às ações alvo, viabilizando **inferência iterativa** estável e rápida. citeturn7view0  
- **Action chunk:** **bloco** de N passos de ação gerado de uma vez (latência baixa, suavidade alta). citeturn5view0  
- **Embodiment head/EmbodimentTag:** define **formatos** de observação/ação específicos por robô (juntas absolutas, delta‑EEF, etc.). citeturn1view0

---

## 8) Considerações de projeto

- **Congelar o VLM** (como no N1.5) costuma **ajudar generalização** e evitar *overfit* de linguagem ao pós‑treinar com pouco dado. citeturn6view0  
- **Escolha do espaço de ação** (juntas vs delta‑EEF) afeta estabilidade e facilidade para teleop/blend; use a **head** que mais combina com sua *stack*. citeturn1view0  
- **Aceleração e latência:** inferência para *chunks* curtos (ex.: 16 passos) fica na casa de **dezenas de milissegundos** em GPUs modernas, suficiente para **controle fechado**. citeturn5view0

---

## 9) Referências úteis

- **Repositório oficial, README, exemplos e serviço de inferência.** citeturn1view0  
- **Paper GR00T N1 (arquitetura detalhada, *flow matching*, *latent actions*, pirâmide de dados).** citeturn5view0  
- **Página de pesquisa N1.5 (diferenças vs N1, FLARE, DreamGen, VLM congelado).** citeturn6view0  
- **Model Cards (N1 e N1.5) — detalhes de *flow matching*, AdaLN/DiT, concatenação multi‑view, espaços de entrada/saída.** citeturn7view0turn8view0  
- **Teleop no Isaac Lab (Keyboard/Gamepad/SpaceMouse/OpenXR).** citeturn0search2

---

### Apêndice A — Trechos de integração (esqueleto)

> **Aviso:** exemplo didático, adapte ao seu *embodiment* e controlador.

```python
from gr00t.model.policy import Gr00tPolicy
from gr00t.data.embodiment_tags import EmbodimentTag

# carregar política pré-treinada
policy = Gr00tPolicy(
    model_path="nvidia/GR00T-N1.5-3B",
    embodiment_tag=EmbodimentTag.GR1,
    device="cuda",
)

# obter um chunk de ações a partir de uma amostra (obs + texto + proprio)
action_chunk = policy.get_action(sample)  # shape: [T_chunk, action_dim]

# (opcional) blend com teleop do Isaac Lab
a_final = alpha * action_chunk[0] + (1 - alpha) * a_teleop  # mesmo espaço de ação
controller.step(a_final)
```
citeturn1view0

---

> **Resumo:** pense no GR00T como **“compreender com o VLM”** + **“agir com Diffusion/Flow”**; você injeta teleop **fora** do DiT (no controlador ou mesclando com a ação prevista). Com **N1.5**, você ganha melhor *grounding*, melhor **seguimento de linguagem** e aprendizado mais amplo graças a **FLARE** e **DreamGen**. citeturn6view0
