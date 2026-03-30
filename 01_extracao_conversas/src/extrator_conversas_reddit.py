import json
import pandas as pd
import re
import datetime
from pathlib import Path
from tqdm import tqdm 
from concurrent.futures import ThreadPoolExecutor, as_completed

# Importando suas configurações de caminhos e o serviço otimizado
from core.paths import EXTRACAO_DATA, DATASET_FINAL_CSV
from extractors.reddit_serviceV2 import RedditService # Ajuste conforme seu arquivo real

DIRETORIO_BRUTO = EXTRACAO_DATA / 'bruto'
DIRETORIO_PROCESSADO = EXTRACAO_DATA / 'processado'
CAMINHO_ENTRADA_CSV = DATASET_FINAL_CSV / 'dataset_laptops_GAMER_ONLY_V2.csv'
CAMINHO_SAIDA_JSON = DIRETORIO_PROCESSADO / 'reddit_notebook_dados_limposV3.json'

class ExtractionUtils:
    @staticmethod
    def limpar_nome_arquivo(nome):
        """Evita erros de sistema de arquivos com nomes de modelos."""
        nome_limpo: str = re.sub(r'[\\/*?:"<>|]', '_', str(nome))
        return nome_limpo.strip().replace(' ', '_')

class RedditExtractionPipeline:
    def __init__(self, limite=None, max_workers=3, time_filter="all"):
        self.reddit = RedditService()
        self.limite = limite
        self.max_workers = max_workers
        self.time_filter = time_filter 
        self.utils = ExtractionUtils()
        
        DIRETORIO_BRUTO.mkdir(parents=True, exist_ok=True)
        DIRETORIO_PROCESSADO.mkdir(parents=True, exist_ok=True)

    def preparar_tarefas(self):
        """Filtra notebooks já processados para permitir retomada (checkpoint)."""
        df = pd.read_csv(CAMINHO_ENTRADA_CSV)
        if self.limite:
            df = df.head(self.limite)
            
        tarefas_pendentes = []
        for _, row in df.iterrows():
            nome_arq = f"{self.utils.limpar_nome_arquivo(row['id_unico'])}.json"
            if not (DIRETORIO_BRUTO / nome_arq).exists():
                tarefas_pendentes.append({
                    'modelo_limpo': row['modelo_limpo'], 
                    'id_unico': row['id_unico']
                })
        
        print(f"✅ Total no CSV: {len(df)} | 🚀 Pendentes: {len(tarefas_pendentes)}")
        return tarefas_pendentes

    def processar_modelo(self, tarefa):
        """Worker: Limpa o SKU, executa a busca e salva metadados com timestamp."""
        id_notebook = tarefa['id_unico']
        modelo_original = str(tarefa['modelo_limpo'])
        
        # 1. ✂️ Limpeza de SKU para busca
        modelo_limpo = modelo_original.lower()
        modelo_busca = re.sub(r'\b\w*\d\w*-\w*\d\w*\b', '', modelo_limpo)
        termos = modelo_busca.split()
        modelo_busca = " ".join(termos[:4]) if len(termos) > 4 else " ".join(termos)
        modelo_busca = modelo_busca.strip()

        print(f"    🎯 Busca Real: '{modelo_busca}' | (Original: {modelo_original})")
        
        # 2. 🚀 Chamada do Serviço com Verificação de Saúde
        try:
            posts = self.reddit.buscar_modelo(modelo_busca, time_filter=self.time_filter)
            limites = self.reddit.consultar_limites_api()
            
            if limites["restante"] is not None and limites["restante"] < 20:
                print(f"\n⚠️  ALERTA DE COOLDOWN: {int(limites['restante'])} requisições restantes.")

        except Exception as e:
            if "RATELIMIT" in str(e).upper():
                print(f"\n🛑 LIMITE ATINGIDO em {modelo_busca}. Aguardando reset...")
            raise e
        
        # 3. 📊 Estrutura de Resultado com TIMESTAMP (Float)
        resultado = {
            "modelo_original": modelo_original,
            "modelo_busca_utilizado": modelo_busca,
            "id_notebook": id_notebook,
            # Alterado para timestamp numérico conforme solicitado
            "data_extracao": datetime.datetime.now().timestamp(), 
            "config_time_filter": self.time_filter,
            "api_health_at_extraction": limites,
            "total_posts_encontrados": len(posts),
            "posts": posts 
        }

        # 4. Save individual (Checkpoint)
        nome_arquivo = f"{self.utils.limpar_nome_arquivo(id_notebook)}.json"
        with open(DIRETORIO_BRUTO / nome_arquivo, 'w', encoding='utf-8') as f:
            json.dump(resultado, f, ensure_ascii=False, indent=4)
            
        return id_notebook

    def consolidar(self):
        """Une os JSONs individuais em um dataset final."""
        print(f"\n📦 Consolidando dados em {CAMINHO_SAIDA_JSON.name}...")
        arquivos = list(DIRETORIO_BRUTO.glob("*.json"))
        dados_finais = []
        
        for arq in tqdm(arquivos, desc="Lendo checkpoints"):
            try:
                with open(arq, 'r', encoding='utf-8') as f:
                    dados_finais.append(json.load(f))
            except Exception as e:
                print(f"⚠️ Erro ao ler {arq.name}: {e}")
                
        with open(CAMINHO_SAIDA_JSON, 'w', encoding='utf-8') as f:
            json.dump(dados_finais, f, ensure_ascii=False, indent=4)
        print(f"✨ Sucesso!")

    def executar(self):
        tarefas = self.preparar_tarefas()
        if tarefas:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = {executor.submit(self.processar_modelo, t): t for t in tarefas}
                for future in tqdm(as_completed(futures), total=len(tarefas), desc="🔥 Extraindo"):
                    try:
                        future.result()
                    except Exception as e:
                        print(f"\n❌ Erro crítico: {e}")
        self.consolidar()

if __name__ == "__main__":
    # Reduzido para 3 workers para ser mais conservador com o 429
    pipeline = RedditExtractionPipeline(limite=None, max_workers=4, time_filter="all")
    pipeline.executar()