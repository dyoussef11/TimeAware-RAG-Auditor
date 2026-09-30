

# 💻 Specialist Time-Aware RAG Engine (V8 Hybrid Auditor)

### Framework de RAG Temporal para Mitigação de Alucinações por Obsolescência em Hardware

Este projeto apresenta uma arquitetura avançada de **Retrieval-Augmented Generation (RAG)** focada na resolução de um problema crítico em domínios técnicos: a **obsolescência informacional**. Diferente de sistemas RAG convencionais, esta engine integra sensibilidade temporal e auditoria lógica de série para garantir que assistentes de suporte não sugiram drivers ou especificações ultrapassadas.

---

## 🎯 Conceitos Centrais

### 1. Motor de Decaimento Linear (LinearV3)
Para resolver o fenômeno do **Borrão Semântico** (onde problemas técnicos de 2021 e 2026 parecem idênticos para o FAISS), implementamos uma taxa de obsolescência parametrizada em **4% ao ano**. Isso garante que, em caso de "empate técnico" vetorial, a solução mais recente tenha prioridade no re-ranqueamento.


A pontuação final ($S_{final}$) é ajustada pela idade da informação ($\Delta t$ em anos):
$$S_{final} = S_{vectorial} \times (1 - 0.04 \times \Delta t)$$

### 2. Protocolo V8 & SKU-Lock
Mecanismo de auditoria híbrida que impõe uma trava lógica de entidade. O sistema é instruído a:
* **Invalidar Inferências de Série:** Não assume que o que funciona para o Nitro AN515-58 funciona para o AN515-56.
* **Zero-Trust Grounding:** Prefere a omissão segura ("Informação não encontrada") à alucinação baseada no conhecimento interno do modelo.

---

## ⚙️ Instalação e Setup

O projeto utiliza uma estrutura modular. Para que o diretório `/core` seja reconhecido corretamente em todos os estágios do pipeline, siga as instruções abaixo:

### 1. Ambiente Virtual
```bash
Instale o python 3.12.10, Antes de criar o venv:
```
https://www.python.org/downloads/release/python-31210/


### 1.1 Ambiente Virtual
```bash
python -m venv .venv
.\.venv\Scripts\activate  # Windows
```

### 2. Instalação das Dependências e Módulo Core
Instale os pacotes necessários e configure o projeto em modo editável para habilitar o tratamento do `core` como um módulo do sistema:
```bash
pip install -r requirements.txt
pip install -e .
```

### 3. Configuração do PRAW (Reddit API)
A etapa de extração requer credenciais da API do Reddit:
1. Navegue até `01_extracao_conversas/src/extractors/`.
2. Renomeie o arquivo `praw.ini.example` para `praw.ini`.
3. Insira seu `client_id`, `client_secret` e `user_agent`.
*Nota: Caso o arquivo não seja configurado, o sistema poderá falhar na coleta de novos dados, mas pode ser testado com logs existentes.*

### 4. Descompactação da Base de Conhecimento (JSON)
Devido ao tamanho dos dados vetorizados, a base de conhecimento multilingue está compactada:
1. Navegue até `04_vetorizacao\data\`.
2. Descompacte o arquivo `base_conhecimento_multilingueV2.json.bz2` para o mesmo diretório, resultando em `base_conhecimento_multilingueV2.json`.

---

## 🚀 Como Executar (Orquestrador Central)

Para facilitar a execução, o projeto conta com um script de gerenciamento centralizado (`run_pipeline.py`) que lida com as dependências e o fluxo de trabalho.

### Execução Geral
Execute o comando abaixo para acessar o menu interativo:
```bash
python run_pipeline.py
```

### Opções do Menu
O gerenciador permite executar etapas isoladas ou o fluxo completo:
* **Opção 1:** Gera os datasets base (Geral -> Gamer).
* **Opção 3:** Executa a sequência de 6 passos de pré-processamento (Limpeza, Thresholds e Indexação).
* **Opção 7:** Executa o **Pipeline Completo**, garantindo que a saída de um estágio alimente o próximo na ordem lógica correta.


---

## 🛠️ Pipeline de Processamento (6 Estágios)

O fluxo automatizado pelo orquestrador transforma discussões informais em **Relatórios Técnicos Densos**:

| Estágio | Operação | Objetivo Técnico |
| :--- | :--- | :--- |
| **00 - Referência** | `dataset_laptops_GAMER_ONLY_V2.csv` | Consolidação de especificações canônicas para ancoragem. |
| **01 - Extração** | `extrator_conversas_reddit.py` | Captura de relatos reais via API PRAW. |
| **02 - Pre-proc** | `filtro_tecnico_conversas` | Sequência de limpeza e thresholds de volumetria. |
| **03 - NER & Resumo** | `NerResumLLAMA3.2-3.8b.py` | Extração de entidades e sumarização via SLMs. |
| **04 - Vetorização** | `revetorizar_multilingue.py` | Indexação densa com suporte multilingue via BGE-M3. |
| **05 - Time-Aware** | `RAG_Temporal_V8.py` | Execução do motor RAG com re-ranking cronológico. |
| **06 - Avaliação** | `evaluate_rag_deepevalNaoTemporalV3.py` | Auditoria via DeepEval (LLM-as-a-Judge). |

---

## 🛠️ Stack Tecnológico & Otimização Local

Desenvolvido para ser executado em ambientes restritos (**GTX 1050 Ti 4GB**), o sistema utiliza:

* **Modelos Compactos (SLMs):** `Llama 3.2 3B` (NER), `Qwen 3 4B-Instruct` (Geração) e `Phi3.5:latest` (Juiz LLM).
* **Orquestração de VRAM:** Uso de `asyncio.Semaphore(1)` para processamento serial, evitando estouro de memória.
* **Post-Processing:** Camada de reparo heurístico para garantir integridade de JSON em modelos de baixa escala.

---

## 📂 Organização do Repositório

```bash
.
├── 00_datasets_referencia/      # Datasets canônicos e scripts de filtragem gamer.
├── 01_extracao_conversas/
│   └── src/
        └── extractors/                     # Scripts PRAW (Requer praw.ini baseado no .example).
├── 02_preprocessamento/         # Limpeza, indexação e gráficos de sensibilidade.
├── 03_ner_e_resumo/             # Pipeline de extração de entidades e sumarização.
├── 04_vetorizacao/              # Geração de índices FAISS com BGE-M3 e base JSON.
├── 05_validacao_time_aware/     # O núcleo do RAG: Motores Vanilla vs LinearV7.
├── 06_avaliacao_quantitativa/   # Suíte DeepEval, logs e simuladores de decaimento.
├── core/                        # Centralização de caminhos (paths.py) e bootstrap.
└── run_pipeline.py              # Orquestrador central com menu CLI.
```

---

Por **Daniel Youssef De Hollanda Lopes**
