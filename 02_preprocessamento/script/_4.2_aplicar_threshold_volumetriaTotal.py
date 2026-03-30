import json
import os
import pandas as pd
import shutil
from core.paths import PREPROCESSAMENTO_DATA, EXTRACAO_DATA

CAMINHO_METRICAS = EXTRACAO_DATA / "Contagem_Analise" / "prevalencia_com_comentarios.csv"
CAMINHO_INPUT_JSON = PREPROCESSAMENTO_DATA / "Dados_Prontos_Sem_Threshold"
CAMINHO_SAIDA_FINAL = PREPROCESSAMENTO_DATA / "Dados_Final_Threshold"

def aplicar_corte_cientifico():
    # Parâmetros validados pelos seus gráficos
    MIN_POSTS = 20
    MIN_DENSIDADE = 8.0
    MIN_TEMAS = 3

    if not os.path.exists(CAMINHO_SAIDA_FINAL): os.makedirs(CAMINHO_SAIDA_FINAL)
    
    df = pd.read_csv(CAMINHO_METRICAS, sep=';')
    aprovados = df[(df['posts_unicos'] >= MIN_POSTS) & 
                   (df['densidade_tecnica'] >= MIN_DENSIDADE) & 
                   (df['temas_cobertos'] >= MIN_TEMAS)]

    modelos_lista = aprovados['modelo'].unique().tolist()
    
    for arq in os.listdir(CAMINHO_INPUT_JSON):
        with open(CAMINHO_INPUT_JSON / arq, 'r', encoding='utf-8') as f:
            m_nome = json.load(f).get('modelo_busca_utilizado')
        if m_nome in modelos_lista:
            shutil.copy2(CAMINHO_INPUT_JSON / arq, CAMINHO_SAIDA_FINAL / arq)

    print(f"Sucesso: {len(aprovados)} modelos aprovados para a etapa de IA.")

if __name__ == "__main__":
    aplicar_corte_cientifico()