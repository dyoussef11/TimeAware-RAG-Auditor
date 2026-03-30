import os
import json
import pandas as pd
import random
from core.paths import PREPROCESSAMENTO_DATA, EXTRACAO_DATA

CAMINHO_METRICAS = EXTRACAO_DATA / "Contagem_Analise" / "prevalencia_com_comentarios.csv"
CAMINHO_INPUT_JSON = PREPROCESSAMENTO_DATA / "Dados_Consolidados_Por_Modelo"
CAMINHO_SAIDA_FINAL = PREPROCESSAMENTO_DATA / "Dados_Final_Threshold"

def executar_corte_final():
    MAX_POSTS = 50 # Teto para poupar a GTX 1050 Ti
    
    if not CAMINHO_SAIDA_FINAL.exists(): CAMINHO_SAIDA_FINAL.mkdir(parents=True)
    
    df = pd.read_csv(CAMINHO_METRICAS, sep=';')
    aprovados = df[(df['posts_unicos'] >= 20) & 
                   (df['densidade_tecnica'] >= 8.0) & 
                   (df['temas_cobertos'] >= 3)]

    modelos_eleitos = aprovados['modelo'].unique().tolist()

    for arq in os.listdir(CAMINHO_INPUT_JSON):
        with open(CAMINHO_INPUT_JSON / arq, 'r', encoding='utf-8') as f:
            dados = json.load(f)
        
        if dados.get('modelo_busca_utilizado') in modelos_eleitos:
            posts = dados['posts']
            # Amostragem para eficiência
            if len(posts) > MAX_POSTS:
                posts = random.sample(posts, MAX_POSTS)
            
            dados['posts'] = posts
            with open(CAMINHO_SAIDA_FINAL / arq, 'w', encoding='utf-8') as f:
                json.dump(dados, f, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    executar_corte_final()