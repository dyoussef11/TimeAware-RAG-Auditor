import json
import faiss
import numpy as np
import ollama
import asyncio
import pandas as pd
from datetime import datetime
from pathlib import Path
from core.paths import VETORIZATION_DATA

# Configurações
JSON_PATH = VETORIZATION_DATA / 'base_conhecimento_multilingueV2.json'
REF_DATE = "2026-03-27"
QUERY = "Latest BIOS update for acer predator helios 500"
TAXAS_DECLINO = [ 0.20, 0.18, 0.16, 0.14, 0.12, 0.10, 0.08, 0.07, 0.06, 0.05, 0.04, 0.03] 

async def testar_sensibilidade_temporal():
    print(f"--- 🧪 TESTE DE SENSIBILIDADE TEMPORAL (Ref: {REF_DATE}) ---")
    print(f"Query: '{QUERY}'\n")

    if not JSON_PATH.exists():
        print(f"❌ Erro: Ficheiro não encontrado em {JSON_PATH}")
        return

    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        base_dados_bruta = json.load(f)
    
    # 1. Preparação FAISS
    exemplo = base_dados_bruta[0] if base_dados_bruta else {}
    vector_key = 'embedding' if 'embedding' in exemplo else 'vector'
    base_dados = [d for d in base_dados_bruta if vector_key in d]
    
    dimension = 1024
    index = faiss.IndexFlatL2(dimension)
    vectors = np.array([d[vector_key] for d in base_dados]).astype('float32')
    index.add(vectors)
    
    # 2. Embedding da Query
    res_embed = ollama.embeddings(model="bge-m3:latest", prompt=QUERY)
    query_vector = np.array([res_embed['embedding']]).astype('float32')
    
    # 3. Busca Top 50
    distances, indices = index.search(query_vector, k=min(50, len(base_dados)))
    ref_dt = datetime.strptime(REF_DATE, "%Y-%m-%d")
    
    # 4. Dados Base para o Ranking Puro (Demonstração FAISS)
    dados_puros = []
    for i, idx in enumerate(indices[0]):
        if idx == -1: continue
        doc = base_dados[idx]
        dist_orig = distances[0][i]
        
        # Demonstração da fórmula L2: Σ(qi - vi)²
        # Como o FAISS IndexFlatL2 já retorna a distância ao quadrado:
        formula_l2 = "Σ(V_query - V_doc)²"
        calculo_baseline = f"{dist_orig:.4f} * 1.0 (Penalidade Zero)"
        
        dados_puros.append({
            "Título": (doc.get('metadata', {}).get('title') or "Sem Título")[:30],
            "Data": doc.get('date_iso', '2024-01-01')[:10],
            "Fórmula_FAISS_L2": formula_l2,
            "Cálculo_Baseline": calculo_baseline,
            "Dist_Original": round(dist_orig, 4)
        })

    print("🏆 TOP 5 - RANKING PURO (DEMONSTRAÇÃO DE RELEVÂNCIA VETORIAL):")
    df_puro = pd.DataFrame(dados_puros).sort_values("Dist_Original").head(5)
    print(df_puro[["Título", "Data", "Fórmula_FAISS_L2", "Cálculo_Baseline", "Dist_Original"]])
    print("-" * 125)

    # 5. Loop de Teste de Taxas (Ranking Temporal)
    for taxa in TAXAS_DECLINO:
        print(f"\n⏳ RE-RANKING TEMPORAL - TAXA DE {taxa*100}% AO ANO:")
        
        resultados_taxa = []
        for i, idx in enumerate(indices[0]):
            if idx == -1: continue
            doc = base_dados[idx]
            dist_orig = distances[0][i]
            
            doc_dt = datetime.strptime(doc.get('date_iso', '2024-01-01')[:10], "%Y-%m-%d")
            diff_years = max(0, (ref_dt - doc_dt).days / 365.25)
            
            penalty = 1.0 + (diff_years * taxa)
            score_final = dist_orig * penalty
            
            calc_final = f"{dist_orig:.4f} * {penalty:.4f} (Penalidade: {taxa*100}%)"
            
            resultados_taxa.append({
                "Título": (doc.get('metadata', {}).get('title') or "Sem Título")[:30],
                "Data": doc.get('date_iso', '2024-01-01')[:10],
                "Cálculo_Final": calc_final,
                "Score_Final": round(score_final, 4)
            })
        
        df_temp = pd.DataFrame(resultados_taxa).sort_values("Score_Final").head(5)
        print(df_temp[["Título", "Data", "Cálculo_Final", "Score_Final"]])

if __name__ == "__main__":
    asyncio.run(testar_sensibilidade_temporal())