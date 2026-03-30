import asyncio
import json
import time
import statistics
import re
from pathlib import Path
from openai import AsyncOpenAI
from core.paths import NER_DATA

# --- SEU PROMPT REAL (Slightly optimized for stability) ---
PROMPT_SYS = """
You are a Technical Data Structurer. 
GOAL: Extract technical facts from a laptop repair discussion chunk.

STRICT RULES:
1. SUMMARY FORMAT: You MUST start the summary string EXACTLY with the laptop model name, followed by a comma. Start directly with the technical facts (after the comma dont create this "[technical fact]:"). 
2. NO CHATBOT TEXT: NEVER use conversational filler phrases like "The user reported", "The author says", or "This chunk discusses". Write objectively like a technical log.
3. PRIORITY: Identify if a cause or fix is mentioned in this specific chunk.
4. LANGUAGE: English.
5. FORMAT: You must return as JSON. Do not add markdown blocks, explanations, or conversational text.

EXPECTED JSON SCHEMA:
{
    "summary": "laptop model name, Chronological narrative of the problem, context, and actions.",
    "intent": "Technical Problem | Purchase Advice | Upgrade | Benchmarking | Discussion | N/A",
    "detected_fault": "Fault identified in this chunk (or null if none)",
    "suggested_solution": "Solution mentioned in this chunk (or null if none)",
    "technical_severity": "Low | Medium | High | Critical | N/A"
}
"""

# --- CONFIGURAÇÕES DE TESTE ---
CAMINHO_ENTRADA = NER_DATA / "reddit_50_notebooks_w_components.json"
MODELO = "phi4-mini:latest"
AMOSTRA_TAMANHO = 3 # Posts para comparação qualitativa (para não ficar um log gigante)

# 10 VARIAÇÕES DE HARDWARE (Ajustadas para sua GTX 1050 Ti 4GB)
CONFIGS = {
    "01_V4_ATUAL": {"num_ctx": 4096, "num_gpu": 35, "num_thread": 6, "num_batch": 256, "temperature": 0.1},
    "02_STABLE_VRAM": {"num_ctx": 3072, "num_gpu": 99, "num_thread": 6, "num_batch": 128, "f16_kv": True, "temperature": 0.0},
    "03_FAST_PREFILL": {"num_ctx": 2048, "num_gpu": 99, "num_thread": 8, "num_batch": 512, "f16_kv": True, "temperature": 0.0},
    "04_LOW_LATENCY": {"num_ctx": 3072, "num_gpu": 32, "num_thread": 6, "num_batch": 32, "low_vram": False, "temperature": 0.0},
    "05_HYPERTHREAD": {"num_ctx": 2560, "num_gpu": 35, "num_thread": 12, "num_batch": 128, "temperature": 0.1},
    "06_ULTRA_LEAN": {"num_ctx": 1536, "num_gpu": 99, "num_thread": 6, "num_batch": 128, "temperature": 0.0},
    "07_HIGH_CTX": {"num_ctx": 8192, "num_gpu": 35, "num_thread": 6, "num_batch": 256, "temperature": 0.1}, # Risco de Shared Memory
    "08_NO_GPU_OFF": {"num_ctx": 3072, "num_gpu": 0, "num_thread": 12, "num_batch": 512}, # Apenas CPU
    "09_BALANCED": {"num_ctx": 2560, "num_gpu": 99, "num_thread": 6, "num_batch": 256, "f16_kv": True, "temperature": 0.0},
    "10_EMERGENCY": {"num_ctx": 1024, "num_gpu": 20, "num_thread": 4, "num_batch": 32, "temperature": 0.0}
}

async def run_mega_benchmark():
    client = AsyncOpenAI(base_url='http://localhost:11434/v1', api_key='ollama')
    
    with open(CAMINHO_ENTRADA, 'r', encoding='utf-8') as f:
        full_data = json.load(f)
    sample_posts = full_data[0]['posts'][:AMOSTRA_TAMANHO]
    
    results = {}
    qualitative_log = {i: {} for i in range(AMOSTRA_TAMANHO)}

    print(f"🔬 Iniciando Super Benchmark (10 variações) em {AMOSTRA_TAMANHO} posts...")

    for nome, opt in CONFIGS.items():
        print(f"\n▶️ Testando Perfil: {nome}")
        latencies = []
        metrics = {"json_ok": 0, "rule_ok": 0}
        
        for i, post in enumerate(sample_posts):
            content = f"TITLE: {post.get('titulo_limpo','')}\nDATA: {post.get('conteudo_post_limpo','')}"[:2500]
            
            t0 = time.perf_counter()
            try:
                resp = await client.chat.completions.create(
                    model=MODELO,
                    messages=[{"role": "system", "content": PROMPT_SYS}, {"role": "user", "content": content}],
                    response_format={"type": "json_object"},
                    extra_body={"options": opt},
                    timeout=90
                )
                t1 = time.perf_counter()
                latencies.append(t1 - t0)
                
                data = json.loads(resp.choices[0].message.content)
                summary = data.get("summary", "N/A")
                
                # Armazena texto para comparação
                qualitative_log[i][nome] = summary
                metrics["json_ok"] += 1
                
                # Validação da Regra: Começar com Modelo + Vírgula
                if "," in summary[:40] and not summary.lower().startswith("the"):
                    metrics["rule_ok"] += 1
                    
                print(f"  [{nome}] Post {i+1} OK ({t1-t0:.2f}s)", end="\r")
            except Exception as e:
                qualitative_log[i][nome] = f"FALHA: {str(e)[:40]}"

        results[nome] = {
            "avg": statistics.mean(latencies) if latencies else 0,
            "json": (metrics["json_ok"] / AMOSTRA_TAMANHO) * 100,
            "regra": (metrics["rule_ok"] / AMOSTRA_TAMANHO) * 100
        }

    # --- RELATÓRIO QUANTITATIVO ---
    print("\n\n" + "="*85)
    print(f"{'VARIAÇÃO CONFIG':<20} | {'MÉDIA (s)':<10} | {'JSON %':<10} | {'REGRA %':<10}")
    print("-" * 85)
    for name, r in results.items():
        print(f"{name:<20} | {r['avg']:>9.2f}s | {r['json']:>8.1f}% | {r['regra']:>8.1f}%")

    # --- RELATÓRIO QUALITATIVO (O DECAIMENTO) ---
    print("\n" + "="*85)
    print("🔍 COMPARAÇÃO DO RESUMO (DECAIMENTO TÉCNICO)")
    print("="*85)
    for i in range(AMOSTRA_TAMANHO):
        print(f"\n📌 POST {i+1} - ORIGINAL: {sample_posts[i].get('titulo_limpo','')[:70]}...")
        for name in CONFIGS.keys():
            resumo = qualitative_log[i].get(name, "N/A")
            # Corta o resumo para exibição na tabela
            print(f"  -> [{name:<15}]: {resumo[:150]}...")
    print("="*85)

if __name__ == "__main__":
    asyncio.run(run_mega_benchmark())