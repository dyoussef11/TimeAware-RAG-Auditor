import json
import decimal
from core.paths import NER_DATA, PREPROCESSAMENTO_DATA, NER_RULES
# Centralização de Caminhos

CAMINHO_ENTRADA_JSON = PREPROCESSAMENTO_DATA/ 'limpo_amostras' / 'reddit_amostra_limpa_e_filtrada_V2.json'
CAMINHO_SAIDA_JSON = NER_DATA / 'reddit_dados_com_resumo_qwen_Unique.json'

DIR_CHECKPOINTS = NER_DATA / 'checkpoints_ia_qwenUnique'
RULES_PATH = NER_RULES / 'hardware_patterns.json'

class CustomEncoderPreProcess(json.JSONEncoder):
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