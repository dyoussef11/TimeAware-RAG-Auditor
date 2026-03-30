
import faiss
import numpy as np
import ollama
import asyncio
from RAG_Temporal_V8 import SpecialistTimeAwareRAG

class VanillaRAG(SpecialistTimeAwareRAG):
    """
    Versão Baseline: Usa o cérebro do V8, mas busca por similaridade pura.
    """
    def __init__(self, json_path, variant_name="V1_VANILLA_BASE"):
        super().__init__(json_path, variant_name)

    async def search(self, query, ref_date=None):
        res_embed = ollama.embeddings(model="bge-m3:latest", prompt=query)
        query_vector = np.array([res_embed['embedding']]).astype('float32')
        distances, indices = self.index.search(query_vector, k=50)
        
        scored_results = []
        labels = []
        for i, idx in enumerate(indices[0]):
            dist = distances[0][i]
            if idx != -1 and dist < 1.2: 
                doc = self.base_dados[idx]
                # No RAGNaoTemporal.py
                meta = doc.get('metadata', {})
                t = meta.get('title') or meta.get('model') or "Sem Título"
                labels.append(t)
                scored_results.append({'doc': doc})

        context_str = "\n\n".join([f"[[SOURCE_{i}]] {r['doc']['original_text']}" for i, r in enumerate(scored_results)])
        variant = self.prompts.get("V8_HYBRID_AUDITOR", {})
        
        sys_prompt = f"{variant.get('system_role')}\nRULES:\n{variant.get('constraints')}"
        user_content = f"CONTEXT:\n{context_str}\n\nQUERY: {query}"

        response = await asyncio.to_thread(
            ollama.chat, model="qwen3:4b-instruct",
            messages=[{'role': 'system', 'content': sys_prompt}, {'role': 'user', 'content': user_content}]
        )

        return {
            "answer": response['message']['content'],
            "sources": [r['doc']['original_text'] for r in scored_results],
            "titles": labels
        }