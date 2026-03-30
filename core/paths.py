from pathlib import Path
from core.bootstrap import ensure_project_root_in_path

# Garante que a raiz do projeto está disponível
ROOT = ensure_project_root_in_path()


# ==========================================================
# PASTAS PRINCIPAIS DO PIPELINE
# ==========================================================

DATASET_GAMER = ROOT / "00_datasets_referencia"
EXTRACAO = ROOT / "01_extracao_conversas"
PREPROCESSAMENTO = ROOT / "02_preprocessamento"
NER = ROOT / "03_ner_e_resumo"
VETORIZATION = ROOT / "04_vetorizacao"
VALIDACAO = ROOT / "05_definicao_sistemas_rags"
# VALIDACAO = ROOT / "05_validacao_time_aware"


# 05_validacao_time_aware
# ==========================================================
# SUBPASTAS IMPORTANTES
# ==========================================================

# --- DATASET GAMER ---
DATASET_CONFIG = DATASET_GAMER / "config"
DATASET_DATA = DATASET_GAMER / "data"
DATASET_FINAL_CSV = DATASET_GAMER/ "dataset_final_csv"
DATASET_KAGGLE = DATASET_GAMER / "kaggle_coletados_csv"
DATASET_SCRIPTS = DATASET_GAMER / "script"
DATASET_UTILS = DATASET_GAMER / "utils"


# --- EXTRAÇÃO ---
EXTRACAO_CONFIG = EXTRACAO / "config"
EXTRACAO_DATA = EXTRACAO / "data"
EXTRACAO_DATA_BRUTO = EXTRACAO_DATA / "bruto"
EXTRACAO_DATA_PROCESSADO = EXTRACAO_DATA / "processado"
EXTRACAO_SCRIPT = EXTRACAO / "script"
EXTRACAO_SRC = EXTRACAO / "src"
EXTRACAO_SRC_CORE = EXTRACAO_SRC / "core_extration"
EXTRACAO_SRC_EXTRACTORS = EXTRACAO_SRC / "extractors"


# --- PREPROCESSAMENTO ---

PREPROCESSAMENTO_DATA= PREPROCESSAMENTO / "data" 
PREPROCESSAMENTO_SCRIPT= PREPROCESSAMENTO / "script"
PREPROCESSAMENTO_RULES= PREPROCESSAMENTO / "rules"
PREPROCESSAMENTO_UTILS = PREPROCESSAMENTO / "utils"

# --- NER ---

NER_DATA = NER / "data"
NER_RULES = NER / "rules"
NER_SCRIPT = NER / "script"
NER_UTILS = NER / "utils"

# --- VETORIZATION ---

VETORIZATION_CONFIG = VETORIZATION / "config"
VETORIZATION_DATA = VETORIZATION / "data"
VETORIZATION_SCRIPT = VETORIZATION / "script"
VETORIZATION_UTILS = VETORIZATION / "utils"

# --- VALIDAÇÃO ---

VALIDACAO_CONFIG = VALIDACAO / "config"
VALIDACAO_DATA = VALIDACAO / "data"
VALIDACAO_SCRIPT = VALIDACAO / "script"
VALIDACAO_UTILS = VALIDACAO / "utils"

# --- AVALIAÇÃO DE METRICAS RAG TEMPORAL ---

AVALIACAO = ROOT / "06_avaliacao_quantitativa_deepval"
AVALIACAO_DATA = AVALIACAO / "data"
AVALIACAO_SCRIPT = AVALIACAO / "script"

