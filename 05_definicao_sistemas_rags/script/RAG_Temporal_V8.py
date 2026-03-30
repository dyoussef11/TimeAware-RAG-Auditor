import json
import faiss
import ijson
import numpy as np
import ollama
import asyncio
import re
from pathlib import Path
from datetime import datetime
from typing import  Dict,  Union
import gc

from core.paths import VALIDACAO_CONFIG, VETORIZATION_DATA

class SpecialistTimeAwareRAG:
    """
    Engine RAG com Auditoria Silenciosa e Normalização por Sinônimos.
    Aplica penalidade temporal e expansão de SKU para maior precisão técnica.
    """
    
    def __init__(self, json_path: Union[str, Path], variant_name: str = "V8_HYBRID_AUDITOR") -> None:
        self.dimension: int = 1024  # Dimensão do BGE-M3
        self.caminho_prompts: Path = VALIDACAO_CONFIG / 'prompt_rag_temporal_hybrid_V8.json'
        # [NOVO] Caminho para o dicionário de sinônimos
        self.caminho_sinonimos: Path = VALIDACAO_CONFIG / 'dictionary_synonyms_refined.json'
        self.variant_name = variant_name
        
        print(f"--- 🧠 RAG ENGINE ATIVADA (Variante: {variant_name}) ---")
        
        # 1. Carregar a base de conhecimento
        self.base_dados = []
        try:
            with open(json_path, 'rb') as f:
                for item in ijson.items(f, 'item'):
                    self.base_dados.append(item)
            print(f"✅ Base carregada: {len(self.base_dados)} documentos.")
        except Exception as e:
            print(f"❌ Erro ao carregar base: {e}")
            self.base_dados = []

        # 2. Carregar Dicionário de Sinônimos
        self.sinonimos = {}
        try:
            with open(self.caminho_sinonimos, 'r', encoding='utf-8') as f:
                self.sinonimos = json.load(f)
            print(f"✅ Dicionário de sinônimos carregado.")
        except Exception as e:
            print(f"⚠️ Aviso: Não foi possível carregar sinônimos: {e}")

        # 3. Inicializar Index FAISS
        self.index = faiss.IndexFlatL2(self.dimension)
        if self.base_dados:
            vectors = np.array([d['vector'] for d in self.base_dados]).astype('float32')
            self.index.add(vectors)

        # 4. Carregar Prompts
        with open(self.caminho_prompts, 'r', encoding='utf-8') as f:
            self.prompts = json.load(f)

    def _extrair_auditoria(self, full_response: str) -> Dict[str, str]:
        audit_match = re.search(r"AUDIT:(.*?)(?=ANSWER:|$)", full_response, re.DOTALL | re.IGNORECASE)
        answer_match = re.search(r"ANSWER:(.*)", full_response, re.DOTALL | re.IGNORECASE)
        
        return {
            "audit_log": audit_match.group(1).strip() if audit_match else "No audit log provided.",
            "clean_answer": answer_match.group(1).strip() if answer_match else full_response.strip()
        }

    async def search(self, query: str, ref_date: str = "2026-03-23"):
        ref_dt = datetime.strptime(ref_date, "%Y-%m-%d")

        query_processada = query
        
        # 1. Embedding da Query (usando a query expandida para melhor match vetorial)
        res_embed = await asyncio.to_thread(
            ollama.embeddings, model="bge-m3:latest", prompt=query_processada
        )
        query_vector = np.array([res_embed['embedding']]).astype('float32')

        # 2. Busca Inicial (k=15 para ter margem de re-ranking)
        distances, indices = self.index.search(query_vector, k=50)
        
        scored_results = []
        for i, idx in enumerate(indices[0]):
            if idx == -1: continue
            
            doc = self.base_dados[idx]
            dist_score = distances[0][i]
            
            # 3. Penalidade Temporal
            doc_date_str = doc.get('date_iso', '2024-01-01')[:10]
            doc_dt = datetime.strptime(doc_date_str, "%Y-%m-%d")
            diff_years = max(0, (ref_dt - doc_dt).days / 365.25)
            
            # Fórmula: $$1.0 + (diff\_years \times 0.04)$$
            time_penalty = 1.0 + (diff_years * 0.04)
            final_score = dist_score * time_penalty
            
            scored_results.append({'doc': doc, 'score': final_score})

        # 4. Re-ranking e Seleção (Top 50)
        scored_results = sorted(scored_results, key=lambda x: x['score'])[:10]
        
        # 5. Preparação do Contexto para a IA
        context_parts = []
        titles_auditoria = []
        for i, r in enumerate(scored_results):
            meta = r['doc'].get('metadata', {})
            titulo = meta.get('title') or meta.get('model') or f"Source_{i}"
            titles_auditoria.append(titulo)
            
            context_parts.append(
                f"[[ID_{i} | DATE: {doc_date_str} | TITLE: {titulo}]]\n"
                f"{r['doc']['original_text']}"
            )
        
        context_str = "\n\n".join(context_parts)
        # --- DENTRO DO MÉTODO search ---

        # 6. Prompt com Instrução de Dupla Saída (AJUSTADO)
        variant = self.prompts.get(self.variant_name, {})
        template = variant.get('prompt_template', "{context}\n{query}")

        # Adicionamos a data de referência no sys_prompt para o modelo se situar no tempo
        sys_prompt = (
            f"{variant.get('system_role', '')}\n\n"
            f"MANDATORY FORMAT:\n"
            f"Your output MUST follow this structure:\n"
            f"AUDIT: [List IDs used. If using internal knowledge, you MUST state: 'Internal knowledge as of my 2024 training'. Explain why it is time-compatible with {ref_date}]\n"
            f"ANSWER: [Your professional technical response, NO tags, NO meta-talk]"
        )

        # 7. Geração com Qwen (Ajustando as variáveis do template)
        # Garantimos que o ref_date seja passado para o preenchimento do template se necessário
        user_content = template.format(
            context=context_str, 
            query=query, 
            ref_date=ref_date  # Certifique-se que o JSON do prompt tenha a chave {ref_date}
        )
        # Caso o template do JSON não tenha a chave, podemos reforçar:
        user_content += f"\n\nREFERENCE DATE: {ref_date}\nSKU EXPANSION: {query_processada}"

        # 7. Geração com Qwen
        response = await asyncio.to_thread(
            ollama.chat, 
            model="qwen3:4b-instruct", 
            messages=[
                {'role': 'system', 'content': sys_prompt},
                {'role': 'user', 'content': user_content}
            ],
            options={"temperature": 0.1}
        )
        
        full_text = response['message']['content']
        extracted = self._extrair_auditoria(full_text)

        return {
        "answer": extracted["clean_answer"],
        "audit_trail": extracted["audit_log"],
        "titles": titles_auditoria,
        "sources": [r['doc']['original_text'] for r in scored_results],
        # [ADICIONE ESTA LINHA] para enviar os metadados brutos ao avaliador
        "retrieved_metadata": [r['doc'].get('metadata', {}) for r in scored_results],
        "normalized_query": query_processada 
        }

if __name__ == "__main__":
    async def main():
        engine = SpecialistTimeAwareRAG(
            VETORIZATION_DATA / 'base_conhecimento_multilingueV2.json'
        )
        
        # Teste com termo curto presente no dicionário (ex: "helios")
        pergunta = "Qual a RAM máxima do Helios?"
        res = await engine.search(pergunta)
        
        print(f"\n📝 QUERY ORIGINAL: {pergunta}")
        print(f"🔍 QUERY EXPANDIDA: {res['normalized_query']}")
        print(f"\n🤖 RESPOSTA FINAL:\n{res['answer']}")
        print(f"\n📜 AUDIT TRAIL:\n{res['audit_trail']}")

    asyncio.run(main())