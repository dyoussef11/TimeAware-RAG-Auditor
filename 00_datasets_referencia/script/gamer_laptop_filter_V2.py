import sys
import pandas as pd
import logging
from pathlib import Path


from core.paths import (
    DATASET_FINAL_CSV
)

# --- CONFIGURAÇÃO DE LOGS ---
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class FiltradorGamer:
    """
    Classe responsável por filtrar e segmentar o dataset principal.
    Focada em isolar notebooks da categoria 'gamer'.
    """
    def __init__(self, caminho_input: Path, caminho_output: Path):
        self.caminho_input = caminho_input
        self.caminho_output = caminho_output

    def executar_filtro(self):
        """Lê o dataset unificado e salva apenas os registros gamer."""
        try:
            if not self.caminho_input.exists():
                logger.error(f"Arquivo de entrada não encontrado: {self.caminho_input}")
                return

            # 1. Carregar o dataset completo
            logger.info("Carregando dataset unificado...")
            df = pd.read_csv(self.caminho_input)

            # 2. Aplicar o filtro
            logger.info("Filtrando notebooks da categoria 'gamer'...")
            df_gamer = df[df['categoria'] == 'gamer'].copy()

            # 3. Salvar o resultado
            if not df_gamer.empty:
                self.caminho_output.parent.mkdir(parents=True, exist_ok=True)
                df_gamer.to_csv(self.caminho_output, index=False)
                
                logger.info("=" * 30)
                logger.info(f"✅ Filtro concluído com sucesso!")
                logger.info(f"📊 Total Original: {len(df)}")
                logger.info(f"🔥 Total Gamer: {len(df_gamer)}")
                logger.info(f"💾 Salvo em: {self.caminho_output}")
            else:
                logger.warning("Nenhum notebook 'gamer' foi encontrado no dataset.")

        except Exception as e:
            logger.error(f"Erro ao filtrar dados: {e}")

# ==================== EXECUÇÃO ====================

if __name__ == "__main__":
    # Caminhos baseados na estrutura do projeto
    INPUT = DATASET_FINAL_CSV / "dataset_laptops_UNICOS_V3.csv"
    OUTPUT = DATASET_FINAL_CSV / "dataset_laptops_GAMER_ONLY_V2.csv"

    # Instancia a classe e executa a ação
    filtrador = FiltradorGamer(INPUT, OUTPUT)
    filtrador.executar_filtro()