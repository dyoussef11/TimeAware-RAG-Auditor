import json
import faiss
import numpy as np
import ollama
import asyncio
import pandas as pd
from datetime import datetime
from pathlib import Path
from core.paths import VETORIZATION_DATA
# Configurações (Ajuste os caminhos se necessário)
JSON_PATH = VETORIZATION_DATA / 'base_conhecimento_multilingueV2.json'
REF_DATE = "2026-03-23"
# QUERY = "Latest BIOS update for Helios Neo 16 overheating"
QUERY = "Latest BIOS update for acer predator helios 500"

async def testar_impacto_temporal():
    print(f"--- 🔍 INICIANDO TESTE REAL (Ref: {REF_DATE}) ---")
    
    # 1. Carregar Base Real
    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        base_dados = json.load(f)
    
    # 2. Inicializar FAISS
    dimension = 1024
    index = faiss.IndexFlatL2(dimension)
    vectors = np.array([d['vector'] for d in base_dados]).astype('float32')
    index.add(vectors)
    
    # 3. Gerar Embedding da Query (Via Ollama)
    print(f"Embeddings para: '{QUERY}'...")
    res_embed = ollama.embeddings(model="bge-m3:latest", prompt=QUERY)
    query_vector = np.array([res_embed['embedding']]).astype('float32')
    
    # 4. Busca Inicial (Pegamos 50 para ver a dança das cadeiras)
    distances, indices = index.search(query_vector, k=50)
    ref_dt = datetime.strptime(REF_DATE, "%Y-%m-%d")
    
    dados_comparativos = []
    
    for i, idx in enumerate(indices[0]):
        doc = base_dados[idx]
        dist_original = distances[0][i]
        
        # --- Lógica de Penalidade do V6 ---
        doc_date_str = doc.get('date_iso', '2024-01-01')[:10]
        doc_dt = datetime.strptime(doc_date_str, "%Y-%m-%d")
        diff_years = max(0, (ref_dt - doc_dt).days / 365.25)
        
        penalty = 1.0 + (diff_years * 0.04) # 4% ao ano
        score_final = dist_original * penalty
        
        dados_comparativos.append({
            "ID": idx,
            "Título": (doc.get('metadata', {}).get('title') or "Sem Título")[:30],
            "Data": doc_date_str,
            "Dist_Original": round(dist_original, 4),
            "Score_Final": round(score_final, 4),
            "Penalidade": f"{round((penalty-1)*100, 1)}%",
            "Anos_Diff": round(diff_years, 2)
        })

    # 5. Gerar os dois Rankings
    df_original = pd.DataFrame(dados_comparativos).sort_values("Dist_Original").reset_index(drop=True)
    df_temporal = pd.DataFrame(dados_comparativos).sort_values("Score_Final").reset_index(drop=True)
    
    print("\n🏆 RANKING PURO (APENAS SIMILARIDADE TEXTUAL):")
    print(df_original[["Título", "Data", "Dist_Original"]].head(5))
    
    print("\n⏳ RANKING COM DECAIMENTO TEMPORAL (LOGICA V6):")
    print(df_temporal[["Título", "Data", "Score_Final", "Penalidade"]].head(5))
    
    # Verificar se houve inversão
    if df_original.iloc[0]["ID"] != df_temporal.iloc[0]["ID"]:
        print("\n✅ SUCESSO: O decaimento temporal alterou o Top 1! Um documento mais novo subiu no ranking.")
    else:
        print("\nℹ️ O Top 1 permaneceu o mesmo (provavelmente já era o mais recente ou muito mais relevante).")

if __name__ == "__main__":
    asyncio.run(testar_impacto_temporal())