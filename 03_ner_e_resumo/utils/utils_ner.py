import json
import decimal
from pathlib import Path
from core.paths import NER_DATA, NER_RULES


CAMINHO_ENTRADA_JSON = NER_DATA / 'reddit_50_notebooks_w_componentsV2.json'

CAMINHO_SAIDA_JSON3 = NER_DATA / 'reddit_dados_com_resumo_phi4-mini.json'

CAMINHO_SAIDA_JSONLLAMA = NER_DATA / 'reddit_dados_com_resumo_Llama.json'

CAMINHO_SAIDA_JSON = NER_DATA / 'reddit_dados_com_resumo_qwen_Unique.json'

CAMINHO_SAIDA_JSONV2 = NER_DATA / 'reddit_dados_com_resumo_qwen_UniqueV2.json'

DIR_CHECKPOINTS = NER_DATA / 'checkpoints_ia_qwenUnique'

DIR_CHECKPOINTSV2 = NER_DATA / 'checkpoints_ia_qwenUniqueV2'

DIR_CHECKPOINTSV3 = NER_DATA / 'checkpoints_ia_phi4-mini'

DIR_CHECKPOINTSLLAMA = NER_DATA / 'checkpoints_ia_Llama'

RULES_PATH = NER_RULES / 'hardware_patterns.json'

class CustomEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, decimal.Decimal):
            return float(obj)
        return super().default(obj)

def carregar_checkpoint(post_id):
    path = DIR_CHECKPOINTS / f"{post_id}.json"
    if path.exists():
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None