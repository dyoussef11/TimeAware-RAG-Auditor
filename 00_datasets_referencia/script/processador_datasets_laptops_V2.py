import sys
import pandas as pd
import json
import re
import logging
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Optional


from core.paths import ( 
    DATASET_CONFIG,
    DATASET_KAGGLE,
    DATASET_FINAL_CSV 
)


# --- CONFIGURAÇÃO DE LOGS ---
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class ConfiguracaoProcessamento:
    
    COLUNAS_PADRAO: List[str] = field(default_factory=list)
    PADROES_HARDWARE: Dict[str, str] = field(default_factory=dict)
    CATEGORIAS: Dict[str, List[str]] = field(default_factory=dict)

    @classmethod
    def carregar(cls, caminho: Path):
        with open(caminho, 'r', encoding='utf-8') as f:
            return cls(**json.load(f))

class LimpadorModelos:
    """Carrega as regras do JSON e limpa o nome do modelo preservando SKUs."""
    def __init__(self, caminho_json: Path):
        with open(caminho_json, 'r', encoding='utf-8') as f:
            config = json.load(f)
            self.termos_genericos = config['termos_genericos']
            self.padroes_corte = config['padroes_corte']
            self.regex_corte = re.compile('|'.join(self.padroes_corte), re.IGNORECASE)

    def extrair_modelo(self, texto: str) -> str:
        if not isinstance(texto, str) or texto.lower() == 'nan':
            return "modelo não identificado"
        
        nome = texto.strip()
        # 1. Limpeza de termos genéricos
        for termo in self.termos_genericos:
            nome = re.sub(termo, '', nome, flags=re.IGNORECASE).strip()

        # 2. Corte nas especificações técnicas
        match = self.regex_corte.search(nome)
        if match:
            nome = nome[:match.start()].strip()

        # 3. Refinamento final
        nome = re.sub(r'[\s\-,/]+$', '', nome) 
        nome = re.sub(r'\s+', ' ', nome)      
        return nome.strip()

class ProcessadorDatasetLaptops:
    def __init__(self, config: ConfiguracaoProcessamento, limpador: LimpadorModelos):
        self.config = config
        self.limpador = limpador

    def limpar_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Padroniza strings: remove espaços extras."""
        for col in df.select_dtypes(include=['object']).columns:
            df[col] = df[col].astype(str).str.strip()
        return df

    def extrair_regex(self, texto: str, chave: str) -> str:
        """Extrai hardware usando os padrões do hardware_rules.json."""
        if pd.isna(texto) or texto == 'nan' or texto == '':
            return "não identificado"
        padrao = self.config.PADROES_HARDWARE.get(chave)
        if not padrao: return "não identificado"
        match = re.search(padrao, str(texto), re.IGNORECASE)
        return match.group(0).strip().lower() if match else "não identificado"

    def classificar_categoria(self, row: pd.Series) -> str:

        modelo = str(row.get('modelo_completo', '')).lower()
        gpu = str(row.get('gpu', '')).lower()
        if any(kw.lower() in modelo for kw in self.config.CATEGORIAS.get('KEYWORDS_GAMER', [])) or 'rtx' in gpu or 'gtx' in gpu:
            return 'gamer'
        if any(kw.lower() in modelo for kw in self.config.CATEGORIAS.get('KEYWORDS_CREATOR', [])) or 'quadro' in gpu:
            return 'creator'
        if any(kw.lower() in modelo for kw in self.config.CATEGORIAS.get('KEYWORDS_BUSINESS', [])):
            return 'business'
        return 'geral'

    def gerar_id_unico(self, row: pd.Series) -> str:
        """Gera assinatura baseada em Marca + Modelo Limpo + CPU + RAM."""
        def fix(x): return str(x).lower().replace(' ', '').strip() if x != "não identificado" else "na"
        marca = fix(row.get('marca', 'gen'))
        modelo = fix(row.get('modelo_limpo', 'gen'))
        cpu = fix(row.get('cpu'))
        ram = fix(row.get('ram'))
        return f"{marca}_{modelo[:30]}_{cpu}_{ram}"

    def processar_arquivo(self, caminho: Path, mapeamento: Dict[str, str]) -> Optional[pd.DataFrame]:
        try:
            enc = 'latin1' if 'Unveiling' in caminho.name else 'utf-8'
            df = pd.read_csv(caminho, encoding=enc)
            
            # 1. Renomear conforme mapeamento (copia dados diretos do CSV)
            df = df.rename(columns={k: v.lower() for k, v in mapeamento.items()})
            df = self.limpar_dataframe(df)

            # 2. Lógica "Plano B": Extração de Hardware
            campos_hardware = {
                'cpu': 'cpu', 'gpu': 'gpu', 'ram': 'ram', 
                'storage': 'storage', 'tela': 'screen', 'ano_lancamento': 'ano'
            }
            
            for col_df, chave_regex in campos_hardware.items():
                if col_df not in df.columns:
                    df[col_df] = "não identificado"
                
                # Só usa regex se a coluna estiver vazia ou "não identificado"
                df[col_df] = df.apply(
                    lambda row: self.extrair_regex(row['modelo_completo'], chave_regex) 
                    if str(row.get(col_df, "não identificado")).lower() in ["não identificado", "nan", "none", ""] 
                    else str(row[col_df]).lower(),
                    axis=1
                )

            # 3. Limpeza do Nome do Modelo
            df['modelo_limpo'] = df['modelo_completo'].apply(self.limpador.extrair_modelo)

            # 4. Filtro de Segurança (Remove acessórios)
            df = df[~((df['cpu'] == "não identificado") & (df['ram'] == "não identificado"))]
            if df.empty: return None

            # 5. Classificação e IDs
            df['categoria'] = df.apply(self.classificar_categoria, axis=1)
            df['id_unico'] = df.apply(self.gerar_id_unico, axis=1)

            # 6. Organização Final das Colunas (modelo_limpo à esquerda de modelo_completo)
            colunas_ordenadas = []
            for col in self.config.COLUNAS_PADRAO:
                if col == "modelo_completo":
                    colunas_ordenadas.append("modelo_limpo")
                colunas_ordenadas.append(col)
            
            # Preenche colunas padrão faltantes
            for col in colunas_ordenadas:
                if col not in df.columns: df[col] = "não identificado"
                
            return df[colunas_ordenadas + ['id_unico']]

        except Exception as e:
            logger.error(f"Erro ao processar {caminho.name}: {e}")
            return None

# ==================== EXECUÇÃO PRINCIPAL ====================

if __name__ == "__main__":
    # print(ConfiguracaoProcessamento.__doc__)
    PATH_CONFIG = DATASET_CONFIG
    PATH_DADOS = DATASET_KAGGLE
    PATH_OUTPUT = DATASET_FINAL_CSV / "dataset_laptops_UNICOS_V3.csv"

    try:
        config = ConfiguracaoProcessamento.carregar(PATH_CONFIG / "hardware_rules.json")
        limpador = LimpadorModelos(PATH_CONFIG / "models_rules.json")
        
        with open(PATH_CONFIG / "mapeamento_arquivos_aprimorado.json", 'r', encoding='utf-8') as f:
            mapeamentos_json = json.load(f)["mapeamentos"]

        processador = ProcessadorDatasetLaptops(config, limpador)
        datasets_validados = []

        for item in mapeamentos_json:
            caminho_csv = PATH_DADOS / item["arquivo"]
            if caminho_csv.exists():
                logger.info(f"Processando: {item['arquivo']}")
                df_p = processador.processar_arquivo(caminho_csv, item["colunas"])
                if df_p is not None: datasets_validados.append(df_p)

        if datasets_validados:
            df_final = pd.concat(datasets_validados, ignore_index=True)
            total_antes = len(df_final)
            df_final = df_final.drop_duplicates(subset=['id_unico'], keep='first')
            
            PATH_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
            df_final.to_csv(PATH_OUTPUT, index=False)
            logger.info(f"✅ Concluído! Dataset salvo em: {PATH_OUTPUT}")
            logger.info(f"✅ Sucesso! Total: {total_antes} -> Únicos: {len(df_final)}")
        else:
            logger.error("Nenhum dado processado com sucesso.")

    except Exception as e:
        logger.error(f"Erro fatal: {e}")