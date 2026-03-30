import sys
from gradio import Dataframe
import pandas as pd
import re
from pathlib import Path


from core.paths import (

EXTRACAO_CONFIG,
EXTRACAO_DATA,
DATASET_FINAL_CSV,
EXTRACAO_SRC
)

# This Python class `ModelLoader` contains methods to clean and simplify product names for searching
# on Reddit.
class ModelLoader:
    def __init__(self, config):
        self.config = config

    def simplificar_nome(self, nome):
        """Limpa o nome para busca no Reddit: remove specs e parênteses."""
        if not nome or pd.isna(nome): return ""
        # 1. Remove parênteses
        res = re.sub(r'\s*\(.*?\)', '', str(nome))
        # 2. Remove ruído (gaming, laptop, specs técnicos)
        ruido = r'(?i)\b(gaming|laptop|notebook|edition|202\d|201\d)\b'
        res = re.sub(ruido, '', res)
        # 3. Remove specs isoladas (8gb, ssd, etc)
        specs = r'(?i)\b(\d+gb|\d+tb|ssd|hdd|rtx\s*\d+|gtx\s*\d+)\b'
        res = re.sub(specs, '', res)
        # 4. Limpeza final
        res = re.sub(r'\s+', ' ', res).strip()
        return res

    def carregar_modelos_preparados(self, caminho_csv: Path):
        """Retorna lista de dicionários com nome original e simplificado."""
        df: Dataframe = pd.read_csv(caminho_csv)
        modelos_unicos: str = df['modelo_completo'].unique()
        return [{"original": m, "busca": self.simplificar_nome(m)} for m in modelos_unicos]