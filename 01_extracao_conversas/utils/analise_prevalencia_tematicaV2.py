import os
import json
import pandas as pd
from core.paths import PREPROCESSAMENTO_DATA, EXTRACAO_DATA


CAMINHO_JSON = PREPROCESSAMENTO_DATA / "Dados_Consolidados_Por_Modelo"
CAMINHO_SAIDA = EXTRACAO_DATA / "Contagem_Analise"

SEARCH_GROUPS = {
    "performance": ["fps", "stuttering", "bottleneck", "benchmarks"],
    "thermal": ["overheating", "throttling", "undervolt", "repaste", "temp", "°c"],
    "energy": ["battery", "drain", "charging", "power"],
    "display": ["bleed", "flickering", "screen", "pixels"],
    "stability": ["bsod", "crash", "freeze", "bootloop"]
}

def analisar_qualidade():
    relatorio = []
    for arquivo in [f for f in os.listdir(CAMINHO_JSON) if f.endswith('.json')]:
        with open(CAMINHO_JSON / arquivo, 'r', encoding='utf-8') as f:
            dados = json.load(f)
            resumo = {"modelo": dados.get('modelo_busca_utilizado'), "posts_unicos": 0, "palavras": 0, **{t: 0 for t in SEARCH_GROUPS}}
            
            for post in dados.get('posts', []):
                texto = f"{post['titulo']} {post['conteudo_post']} " + " ".join([c['conteudo'] for c in post['comentarios']])
                texto = texto.lower()
                resumo["posts_unicos"] += 1
                resumo["palavras"] += len(texto.split())
                for tema, keys in SEARCH_GROUPS.items():
                    resumo[tema] += sum(texto.count(k) for k in keys)
            relatorio.append(resumo)

    df = pd.DataFrame(relatorio)
    temas = list(SEARCH_GROUPS.keys())
    df['total_mencoes'] = df[temas].sum(axis=1)
    df['densidade_tecnica'] = (df['total_mencoes'] / df['palavras'] * 1000).round(2)
    df['temas_cobertos'] = (df[temas] > 0).sum(axis=1)
    
    if not os.path.exists(CAMINHO_SAIDA): os.makedirs(CAMINHO_SAIDA)
    df.to_csv(CAMINHO_SAIDA / "prevalencia_com_comentarios.csv", index=False, sep=';', encoding='utf-8-sig')

if __name__ == "__main__":
    analisar_qualidade()