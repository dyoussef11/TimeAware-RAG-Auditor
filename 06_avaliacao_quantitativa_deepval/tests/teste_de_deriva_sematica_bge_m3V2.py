import json
import faiss
import numpy as np
import ollama
import asyncio
import pandas as pd
import re
from datetime import datetime
from pathlib import Path
from core.paths import VETORIZATION_DATA, VALIDACAO_CONFIG

# Configurações
JSON_PATH = VETORIZATION_DATA / 'base_conhecimento_multilingueV2.json'
SINONIMOS_PATH = VALIDACAO_CONFIG / 'dictionary_synonyms_refined.json'
REF_DATE = "2026-03-23"
# QUERY_TESTE = "Qual a RAM máxima do Acer Aspire 5 15?"
QUERY_TESTE = "Qual a RAM máxima do Helios 300?"

def expandir_query_logic(query, dicionario):
    query_norm = query.lower()
    expansao = []
    for nome_canonico, apelidos in dicionario.items():
        for apelido in apelidos:
            pattern = rf'\b{re.escape(apelido.lower())}\b'
            if re.search(pattern, query_norm):
                expansao.append(nome_canonico)
                break
    return f"{query} ({', '.join(expansao)})" if expansao else query

def calcular_rank_temporal(indices, distances, base_dados, ref_dt):
    resultados = []
    for i, idx in enumerate(indices[0]):
        if idx == -1: continue
        doc = base_dados[idx]
        dist_orig = distances[0][i]
        
        # Lógica Temporal
        doc_date_str = doc.get('date_iso', '2024-01-01')[:10]
        doc_dt = datetime.strptime(doc_date_str, "%Y-%m-%d")
        diff_years = max(0, (ref_dt - doc_dt).days / 365.25)
        
        penalty = 1.0 + (diff_years * 0.04)
        score_final = dist_orig * penalty
        
        resultados.append({
            "ID": idx,
            "Título": (doc.get('metadata', {}).get('title') or "N/A")[:30],
            "Data": doc_date_str,
            "Dist_Pura": round(dist_orig, 4),
            "Score_Temporal": round(score_final, 4),
            "Penalidade": f"{round((penalty-1)*100, 1)}%"
        })
    return pd.DataFrame(resultados)

async def testar_impacto_total():
    print(f"--- 🧪 AUDITORIA: EXPANSÃO vs. TEMPORALIDADE (Ref: {REF_DATE}) ---")
    
    # 1. Carga de Dados
    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        base_dados = json.load(f)
    with open(SINONIMOS_PATH, 'r', encoding='utf-8') as f:
        sinonimos = json.load(f)
    ref_dt = datetime.strptime(REF_DATE, "%Y-%m-%d")
    
    # 2. Setup FAISS
    exemplo = base_dados[0]
    vector_key = 'embedding' if 'embedding' in exemplo else 'vector'
    index = faiss.IndexFlatL2(1024)
    vectors = np.array([d[vector_key] for d in base_dados]).astype('float32')
    index.add(vectors)
    
    # 3. Processamento de Queries
    query_orig = QUERY_TESTE
    query_exp = expandir_query_logic(query_orig, sinonimos)
    print(f"🔹 ORIGINAL:  {query_orig}")
    print(f"🔸 EXPANDIDA: {query_exp}\n")
    
    # 4. Busca Vetorial (Top 50 para re-ranking)
    emb_orig = ollama.embeddings(model="bge-m3:latest", prompt=query_orig)['embedding']
    d_orig, i_orig = index.search(np.array([emb_orig]).astype('float32'), k=50)
    
    emb_exp = ollama.embeddings(model="bge-m3:latest", prompt=query_exp)['embedding']
    d_exp, i_exp = index.search(np.array([emb_exp]).astype('float32'), k=50)
    
    # 5. Geração dos Rankings
    df_orig_temp = calcular_rank_temporal(i_orig, d_orig, base_dados, ref_dt)
    df_exp_temp = calcular_rank_temporal(i_exp, d_exp, base_dados, ref_dt)
    
    # 6. Exibição Comparativa
    print("📋 RANKING: QUERY ORIGINAL + TEMPO")
    print(df_orig_temp.sort_values("Score_Temporal").head(5)[["Título", "Data", "Dist_Pura", "Score_Temporal"]])
    
    print("\n🚀 RANKING: QUERY EXPANDIDA + TEMPO")
    print(df_exp_temp.sort_values("Score_Temporal").head(5)[["Título", "Data", "Dist_Pura", "Score_Temporal"]])

    # 7. Análise de Interseção Final
    top_orig = set(df_orig_temp.sort_values("Score_Temporal").head(5)["ID"])
    top_exp = set(df_exp_temp.sort_values("Score_Temporal").head(5)["ID"])
    comuns = top_orig.intersection(top_exp)
    
    print(f"\n📊 CONCLUSÃO DA AUDITORIA:")
    print(f"- Documentos que sobreviveram a ambos os filtros: {len(comuns)}/5")
    print(f"- A expansão trouxe {5 - len(comuns)} novos documentos para o Top 5 final.")

if __name__ == "__main__":
    asyncio.run(testar_impacto_total())