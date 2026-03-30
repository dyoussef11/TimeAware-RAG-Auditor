import os
import json
import pandas as pd
from core.paths import PREPROCESSAMENTO_DATA, EXTRACAO_DATA

# Configuração de Caminhos
CAMINHO_ENTRADA = PREPROCESSAMENTO_DATA / "Dados_Final_Threshold"
CAMINHO_METRICAS = EXTRACAO_DATA / "Contagem_Analise" / "prevalencia_com_comentarios.csv"
CAMINHO_SAIDA = PREPROCESSAMENTO_DATA / "Metricas_Pre_Processamento"

def gerar_indexacao_final():
    if not os.path.exists(CAMINHO_SAIDA):
        os.makedirs(CAMINHO_SAIDA)

    # 1. Carregar as métricas de qualidade para cruzar dados
    df_metricas = pd.read_csv(CAMINHO_METRICAS, sep=';', encoding='utf-8-sig')
    
    arquivos = [f for f in os.listdir(CAMINHO_ENTRADA) if f.endswith('.json')]
    manifesto_final = []

    print(f"Indexando {len(arquivos)} modelos qualificados...")

    for arquivo in arquivos:
        with open(CAMINHO_ENTRADA / arquivo, 'r', encoding='utf-8') as f:
            dados = json.load(f)
        
        modelo_id = dados.get('modelo_busca_utilizado')
        posts = dados.get('posts', [])
        
        # Busca a densidade e temas no CSV de métricas
        info_qualidade = df_metricas[df_metricas['modelo'] == modelo_id].iloc[0]

        manifesto_final.append({
            "arquivo": arquivo,
            "modelo": modelo_id,
            "qtd_posts": len(posts),
            "densidade_tecnica": info_qualidade['densidade_tecnica'],
            "temas_cobertos": info_qualidade['temas_cobertos'],
            "status_ner": "Pendente" # Para controle de progresso
        })

    df = pd.DataFrame(manifesto_final)
    caminho_csv = CAMINHO_SAIDA / "manifesto_final_para_ner.csv"
    df.to_csv(caminho_csv, index=False, sep=';', encoding='utf-8-sig')
    
    print(f"✅ Manifesto Final gerado: {caminho_csv}")

if __name__ == "__main__":
    gerar_indexacao_final()