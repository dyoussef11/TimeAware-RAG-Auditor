

import asyncio
import pandas as pd
import sys
import os
from datetime import datetime
from tqdm import tqdm
from pathlib import Path

# Configuração de caminhos
from core.paths import VETORIZATION_DATA, AVALIACAO_DATA, VALIDACAO_SCRIPT
sys.path.append(str(VALIDACAO_SCRIPT))

from RAGNaoTemporal import VanillaRAG

# from RAG_Final_Refinado_Ollama_LinearV5 import SpecialistTimeAwareRAG
# from RAG_Final_Refinado_Ollama_LinearV6ComExpansao import SpecialistTimeAwareRAG
from RAG_Temporal_V8 import SpecialistTimeAwareRAG
from custom_evaluatorV2 import OllamaEvaluator
from dataset_avaliacaoV3 import TEST_SUITE
from deepeval.test_case import LLMTestCase
from deepeval.metrics import (
    ContextualPrecisionMetric, 
    ContextualRelevancyMetric,
    ContextualRecallMetric,
    FaithfulnessMetric, 
    AnswerRelevancyMetric
)

# --- CONFIGURAÇÃO DE HARDWARE (GTX 1050Ti) ---
# Em placas de 4GB, concorrência > 1 causa instabilidade nas justificativas (reasons)
CONCURRENT_TASKS = 1
semaphore = asyncio.Semaphore(CONCURRENT_TASKS)

async def measure_with_reason(metric, test_case):
    """Executa a métrica e extrai a justificativa do qwen3."""
    async with semaphore:
        try:
            # Roda a medição em thread para não bloquear o event loop
            await asyncio.to_thread(metric.measure, test_case)
            
            # Algumas métricas usao 'reason', outras 'explanation'
            reason = getattr(metric, 'reason', None) or getattr(metric, 'explanation', 'Sem justificativa.')
            return float(metric.score), str(reason).replace('\n', ' ')
        except Exception as e:
            return 0.0, f"Erro: {str(e)}"

async def duelo_auditor_detalhado():
    print(f"\n--- 🧪 DUELO CIENTÍFICO: V1 vs V8 (Modo Low-VRAM) ---")
    
    avaliador_local = OllamaEvaluator(model_name="qwen3:4b-instruct")
    base_path = VETORIZATION_DATA / 'base_conhecimento_multilingueV2.json'
    
    rag_v1 = VanillaRAG(base_path)
    rag_v8 = SpecialistTimeAwareRAG(base_path, variant_name="V8_HYBRID_AUDITOR")
    

    # Inicialização das Métricas
    metrics = {
    "Context_Precisao": ContextualPrecisionMetric(threshold=0.7, model=avaliador_local, include_reason=True),
    "Context_Relevancia": ContextualRelevancyMetric(threshold=0.7, model=avaliador_local, include_reason=True),
    "Context_Recall": ContextualRecallMetric(threshold=0.6, model=avaliador_local, include_reason=True),
    "Faithfulness": FaithfulnessMetric(threshold=0.8, model=avaliador_local, include_reason=True), # RIGOROSO
    "Resposta_Relevante": AnswerRelevancyMetric(threshold=0.7, model=avaliador_local, include_reason=True)
}

    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    txt_path = AVALIACAO_DATA / f"RELATORIO_FINAL_V8_{timestamp}V2.txt"
    csv_path = AVALIACAO_DATA / f"METRICAS_DETALHADAS_{timestamp}V2.csv"
    
    results_table = []
    pbar = tqdm(total=len(TEST_SUITE), desc="Auditando")

    with open(txt_path, 'w', encoding='utf-8') as f_report:
        f_report.write(f"AUDITORIA RAG - GTX 1050TI OPTIMIZED\nData: {timestamp}\n{'='*80}\n\n")

        for tc in TEST_SUITE:
            query = tc["input"]
            ref_date = tc.get("reference_date", "2026-03-12")
            
            # 1. Busca em paralelo (rápido)
            res_v1, res_v8 = await asyncio.gather(
                rag_v1.search(query),
                rag_v8.search(query, ref_date)
            )

            # 2. ESCREVER RESPOSTAS NO RELATÓRIO (Adicionado para contextualização)
            f_report.write(f"ID: {tc['id']} | QUERY: {query}\n")
            f_report.write(f"{'='*40}\n")
            f_report.write(f"📝 RESPOSTA V1 (Vanilla):\n{res_v1['answer']}\n\n")
            f_report.write(f"📝 RESPOSTA V8 (Temporal):\n{res_v8['answer']}\n\n")
            f_report.write(f"📖 FONTES UTILIZADAS V8: {', '.join(res_v8.get('titles', ['N/A']))}\n")
            f_report.write(f"{'-'*40}\n")

            # 2. Preparação dos Casos
            case_v1 = LLMTestCase(
                input=query, actual_output=res_v1["answer"], 
                retrieval_context=res_v1["sources"], expected_output=tc.get("expected_output"),
                expected_context=tc.get("expected_context", [])
            )
            case_v8 = LLMTestCase(
                input=query, actual_output=res_v8["answer"], 
                retrieval_context=res_v8["sources"], expected_output=tc.get("expected_output"),
                expected_context=tc.get("expected_context", [])
            )

            f_report.write(f"ID: {tc['id']} | QUERY: {query}\n")
            f_report.write(f"FONTES V8: {', '.join(res_v8.get('titles', ['N/A']))}\n")
            f_report.write(f"{'-'*40}\n")

            metrics_row = {"ID": tc['id']}

            # 3. Avaliação Serial (Seguro para a GPU)
            for name, m in metrics.items():
                # Avalia o V8 primeiro
                s8, r8 = await measure_with_reason(m, case_v8)
                # Avalia o V1
                s1, r1 = await measure_with_reason(m, case_v1)

                f_report.write(f"Métrica: {name}\n")
                f_report.write(f"  [V1] {s1:.2f} | Razão: {r1}\n")
                f_report.write(f"  [V8] {s8:.2f} | Razão: {r8}\n\n")
                
                metrics_row[f"V1_{name}"] = s1
                metrics_row[f"V8_{name}"] = s8

            f_report.write(f"{'='*80}\n\n")
            results_table.append(metrics_row)
            pd.DataFrame(results_table).to_csv(csv_path, index=False)
            pbar.update(1)

    pbar.close()
    print(f"\n✅ Relatório: {txt_path}")

if __name__ == "__main__":
    asyncio.run(duelo_auditor_detalhado())