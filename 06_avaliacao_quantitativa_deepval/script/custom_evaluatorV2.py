from deepeval.models.base_model import DeepEvalBaseLLM
import ollama
import asyncio
import json
import re

class OllamaEvaluator(DeepEvalBaseLLM):
    def __init__(self, model_name="phi3.5:latest"):
        self.model_name = model_name

    def load_model(self):
        return self.model_name

    def _clean_response(self, content: str) -> str:
        content = content.strip()
        content = re.sub(r'```json\s*|\s*```', '', content)
        
        # Tenta localizar o JSON
        start = content.find('{')
        end = content.rfind('}')
        if start != -1 and end != -1:
            content = content[start:end+1]
        
        # [REPARO MANUAL] Corrige alucinações comuns do qwen3 de 4B
        # Se o modelo inventar chaves parecidas com 'verdict', substitui pela correta
        bad_keys = ['ver-than', 'ver之', 'veritecture', 'ver- dict', 'vering', 'veriad']
        for bk in bad_keys:
            content = content.replace(f'"{bk}"', '"verdict"')
        
        return content

    async def a_generate(self, prompt: str) -> str:
        """
        Versão assíncrona utilizada pelo DeepEval para rodar as métricas.
        """
        # --- SYSTEM PROMPT AJUSTADO PARA O CENÁRIO DE TAGGING HÍBRIDO ---
        # --- DENTRO DO MÉTODO a_generate ---

        system_content = (
            "You are a Senior Hardware RAG Auditor. Evaluate technical answers based on evidence.\n\n"
            "STRICT EVALUATION RULES:\n"
            "1. TAG NEUTRALITY: Ignore [RAG] or [INTERNAL] tags for Relevancy.\n"
            "2. TEMPORAL PROVENANCE: In the 'reason' field, check if the model correctly identified the 'age' "
            "of its internal knowledge. If the model uses internal data to describe hardware released AFTER "
            "its training cutoff (2024) without RAG evidence, penalize Faithfulness.\n"
            "3. VERACITY LOCK: Information tagged as [INTERNAL] must only be used for general concepts "
            "or industry standards. If [INTERNAL] memory is used to invent specific SKU specs (RAM, Battery) "
            "that are NOT in the [RAG] context, Score 0 for Faithfulness.\n"
            "4. RECENCY BIAS: The answer must prioritize the most recent RAG timestamps over internal training memory.\n"
            "5. OUTPUT: Return ONLY JSON object with 'score' and 'reason'."
        )

        response = await asyncio.to_thread(
            ollama.chat,
            model=self.model_name,
            messages=[
                {"role": "system", "content": system_content},
                {"role": "user", "content": prompt}
            ],
            format='json',
            options={"temperature": 0}
        )
        
        return self._clean_response(response['message']['content'])

    def generate(self, prompt: str) -> str:
        """Versão síncrona (fallback)."""
        return asyncio.run(self.a_generate(prompt))

    def get_model_name(self):
        return f"Ollama {self.model_name}"