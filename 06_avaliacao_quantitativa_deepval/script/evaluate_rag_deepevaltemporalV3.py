import asyncio
import sys
import json
from datetime import datetime
from pathlib import Path

from core.paths import VETORIZATION_DATA, VALIDACAO_SCRIPT, AVALIACAO_DATA 
sys.path.append(str(VALIDACAO_SCRIPT))

# from RAG_Final_Refinado_Ollama_LinearV6ComExpansao import SpecialistTimeAwareRAG
from RAG_Temporal_V8 import SpecialistTimeAwareRAG
from dataset_avaliacaoV3 import TEST_SUITE
from custom_evaluatorV2 import OllamaEvaluator

from deepeval.test_case import LLMTestCase, LLMTestCaseParams
from deepeval.metrics import (
    ContextualRelevancyMetric,
    ContextualPrecisionMetric,
    ContextualRecallMetric,
    FaithfulnessMetric,
    AnswerRelevancyMetric,
    GEval
)

CAMINHO_BASE = VETORIZATION_DATA / 'base_conhecimento_multilingueV2.json'

async def rodar_avaliacao_deepeval():
    print("--- 🧪 INICIANDO AVALIAÇÃO CIENTÍFICA V3 (AUDITORIA DE FONTES) ---")
    
    rag = SpecialistTimeAwareRAG(CAMINHO_BASE, variant_name="V8_HYBRID_AUDITOR")
    avaliador_local = OllamaEvaluator(model_name="qwen3:4b-instruct")
    
    # Métricas com justificativa
    m_context_rel = ContextualRelevancyMetric(threshold=0.7, model=avaliador_local, include_reason=True)
    m_context_prec = ContextualPrecisionMetric(threshold=0.7, model=avaliador_local, include_reason=True)
    m_context_rec = ContextualRecallMetric(threshold=0.7, model=avaliador_local, include_reason=True)
    m_faith = FaithfulnessMetric(threshold=0.8, model=avaliador_local, include_reason=True)
    m_ans_rel = AnswerRelevancyMetric(threshold=0.7, model=avaliador_local, include_reason=True)
    
    m_zero_trust = GEval(
        name="Zero_Trust_Compliance",
        criteria="Verify if output rejects temporal anomalies and SKU mismatches based on provided sources.",
        evaluation_params=[LLMTestCaseParams.INPUT, LLMTestCaseParams.ACTUAL_OUTPUT, LLMTestCaseParams.RETRIEVAL_CONTEXT],
        model=avaliador_local, threshold=0.8
    )

    m_attribution = GEval(
        name="Source_Attribution_Accuracy",
        criteria="Verify if [RAG] tags match the TITLES provided in context.",
        evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT, LLMTestCaseParams.RETRIEVAL_CONTEXT],
        model=avaliador_local, threshold=0.8
    )

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    arquivo_relatorio = AVALIACAO_DATA / f"relatorio_compliance_do_V8_{timestamp}.txt"

    with open(arquivo_relatorio, 'w', encoding='utf-8') as f_out:
        f_out.write("==== RELATÓRIO CIENTÍFICO RAG V3 - RASTREABILIDADE DE FONTES ====\n\n")

        for test_data in TEST_SUITE:
            print(f" ▶ Avaliando ID: {test_data['id']}")
            res_rag = await rag.search(test_data["input"], test_data.get("reference_date", "2026-03-26"))
            
            # --- CONSTRUÇÃO DO CONTEXTO COM TÍTULOS ---
            contexto_para_juiz = []
            fontes_listadas_relatorio = []
            
            sources = res_rag.get("sources", [])
            metas = res_rag.get("retrieved_metadata", [])
            # Pegamos os títulos retornados pela engine

            for i, txt in enumerate(sources):
                m = metas[i] if i < len(metas) else {}
                t = m.get('title', 'Sem Título')
                
                entry = (
                    f"SOURCE_{i} [TITLE: {t}] "
                    f"[DATE: {m.get('data_str', 'N/A')}] "
                    f"[MODEL: {m.get('model', 'N/A')}] "
                    f"[FAULT: {m.get('fault', 'N/A')}] "
                    f"[SEVERITY: {m.get('severity', 'N/A')}] "
                    f"[TIMELINE: {m.get('timeline', 'N/A')}]: {txt}"
                )
                contexto_para_juiz.append(entry)
                
                # Guardamos para o log final do relatório
                fontes_listadas_relatorio.append(f"- {t} ({m.get('data_str')}) [Fault: {m.get('fault')}]")

            test_case = LLMTestCase(
                input=test_data["input"],
                actual_output=res_rag["answer"],
                expected_output=test_data["expected_output"],
                retrieval_context=contexto_para_juiz,
                expected_context=test_data.get("expected_context", [])
            )

            metrics_dict = {
                "Retrieval_Relevancy": m_context_rel,
                "Retrieval_Precision": m_context_prec,
                "Retrieval_Recall": m_context_rec,
                "Gen_Faithfulness": m_faith,
                "Gen_Answer_Rel": m_ans_rel,
                "Audit_Zero_Trust": m_zero_trust,
                "Audit_Attribution": m_attribution
            }

            f_out.write(f"{'='*80}\n")
            f_out.write(f"ID TESTE: {test_data['id']}\n")
            f_out.write(f"QUERY: {test_data['input']}\n")
            f_out.write(f"FONTES RECUPERADAS:\n" + "\n".join(fontes_listadas_relatorio) + "\n")
            f_out.write(f"{'-'*80}\n")
            f_out.write(f"RESPOSTA IA: {res_rag['answer']}\n")
            f_out.write(f"{'-'*80}\n")
            
            for name, m in metrics_dict.items():
                try:
                    m.measure(test_case)
                    f_out.write(f"[{'✅' if m.is_successful() else '❌'}] {name}: {m.score:.2f}\n")
                    f_out.write(f"   💡 MOTIVO: {getattr(m, 'reason', 'N/A')}\n\n")
                except Exception as e:
                    f_out.write(f"[⚠️ ERROR] {name}: {str(e)}\n\n")
            
            f_out.write(f"{'='*80}\n\n")

    print(f"✅ Relatório com Títulos Gerado: {arquivo_relatorio}")

if __name__ == "__main__":
    asyncio.run(rodar_avaliacao_deepeval())