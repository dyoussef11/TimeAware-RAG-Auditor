import asyncio
import json
import os
from pathlib import Path
from tqdm import tqdm
from openai import AsyncOpenAI
from datetime import datetime

# --- CONFIGURAÇÕES DE PATHS ---
try:
    from core.paths import PREPROCESSAMENTO_DATA, NER_DATA
    DIR_ENTRADA = PREPROCESSAMENTO_DATA / 'Dados_Final_Threshold'
    DIR_SAIDA_FINAL = NER_DATA / 'Base_Conhecimento_Resumida'
    DIR_CHECKPOINTS = NER_DATA / "checkpoints_ia_v6"
except ImportError:
    DIR_ENTRADA = Path("./data/Dados_Final_Threshold")
    DIR_SAIDA_FINAL = Path("./data/Base_Conhecimento_Resumida")
    DIR_CHECKPOINTS = Path("./checkpoints_ia_v6")

DIR_SAIDA_FINAL.mkdir(parents=True, exist_ok=True)
DIR_CHECKPOINTS.mkdir(parents=True, exist_ok=True)

# --- CLIENTE E PARÂMETROS ---
client = AsyncOpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

TEMPERATURE = 0.1
EXTRA_OPTIONS = {
    "num_ctx": 4096,
    "top_p": 0.9,
    "repeat_penalty": 1.1
}

# --- FUNÇÕES AUXILIARES ---

def calcular_peso_post(post):
    tamanho_titulo = len(post.get('titulo', '') or '')
    tamanho_corpo = len(post.get('conteudo_post', '') or '')
    tamanho_comentarios = sum(len(c.get('conteudo', '') or '') for c in post.get('comentarios', []))
    return tamanho_titulo + tamanho_corpo + tamanho_comentarios

def obter_prompt_sumarizar(post, nome_modelo):
    titulo = post.get('titulo', 'N/A')
    corpo = post.get('conteudo_post', 'N/A')
    comentarios_str = " ".join([c.get('conteudo', '') for c in post.get('comentarios', [])])
    
    return f"""
You are a Senior Hardware Triage Lead. Summarize the "System State Baseline" for {nome_modelo}:
1. Exact Model and Specs.
2. Failure Mode (e.g., Thermal Throttling, BSOD).
3. Driver/BIOS versions mentioned.
Output a high-density Technical Brief in English.

Conversa:
Título: {titulo}
Conteúdo: {corpo}
Comentários: {comentarios_str}
"""

def obter_prompt_sys(analise_previa, nome_modelo):
    return f"""
You are a Senior Hardware Analyst. Your goal is to extract technical data into a SINGLE, FLAT JSON object.
### MANDATORY ARCHITECTURE:
1. ONLY 6 ALLOWED KEYS: "summary", "intent", "detected_fault", "suggested_solution", "technical_severity", "discussion_timeline".
### CONTENT RULES:
- summary: Start EXACTLY with "{nome_modelo}".
- technical_severity: Pick exactly one: Low | Medium | High | Critical.
- discussion_timeline: A single string "YYYY-MM-DD to YYYY-MM-DD".

Texto para análise: {analise_previa}
"""

async def workflow():
    arquivos = list(DIR_ENTRADA.glob("*.json"))
    # Carrega IDs de checkpoints uma única vez na memória para velocidade máxima
    checkpoints_existentes = {f.stem for f in DIR_CHECKPOINTS.glob("*.json")}
    
    print(f"🚀 Iniciando NER em {len(arquivos)} modelos.")

    for arq_path in tqdm(arquivos, desc="Arquivos"):
        with open(arq_path, 'r', encoding='utf-8') as f:
            dados_modelo = json.load(f)
        
        modelo_nome = dados_modelo.get('modelo_busca_utilizado', 'Laptop')
        posts_originais = dados_modelo.get('posts', [])
        
        # --- SEPARAÇÃO INTELIGENTE ---
        posts_para_processar = []
        posts_ja_prontos = []

        for p in posts_originais:
            p_id = str(p.get('id'))
            if p_id in checkpoints_existentes:
                # Se já existe checkpoint, carrega e pula a ordenação/IA
                try:
                    with open(DIR_CHECKPOINTS / f"{p_id}.json", 'r', encoding='utf-8') as f_cp:
                        p['analise_ia'] = json.load(f_cp)
                    posts_ja_prontos.append(p)
                except: 
                    posts_para_processar.append(p)
            else:
                posts_para_processar.append(p)

        # --- ORDENAÇÃO APENAS DO QUE FALTA ---
        # Isso faz o script "saltar" instantaneamente para o trabalho real
        posts_para_processar.sort(key=calcular_peso_post)
        
        if posts_para_processar:
            for post in tqdm(posts_para_processar, desc=f" -> Processando {modelo_nome[:15]}", leave=False):
                post_id = str(post.get('id'))
                
                if calcular_peso_post(post) > 15000:
                    continue

                # Chamada IA
                brief = await chamar_llama_api(obter_prompt_sumarizar(post, modelo_nome), json_mode=False)
                res_ia = await chamar_llama_api(obter_prompt_sys(brief, modelo_nome))

                # Ancoragem Temporal
                ts = post.get('data_post')
                data_str = datetime.fromtimestamp(float(ts)).strftime('%Y-%m-%d') if ts else "2024-01-01"
                res_ia['ancoragem_temporal'] = {"data_post": data_str, "periodo_referencia": data_str[:7]}

                # Salva Checkpoint e atualiza memória
                with open(DIR_CHECKPOINTS / f"{post_id}.json", 'w', encoding='utf-8') as f_cp:
                    json.dump(res_ia, f_cp, ensure_ascii=False)
                
                post['analise_ia'] = res_ia
                posts_ja_prontos.append(post)

        # Re-unifica a lista para salvar o arquivo final (mantendo todos os posts analisados)
        if posts_ja_prontos:
            dados_modelo['posts'] = posts_ja_prontos
            # Opcional: Aqui você pode rodar a consolidação final se desejar
            with open(DIR_SAIDA_FINAL / f"NER_{arq_path.name}", 'w', encoding='utf-8') as f_out:
                json.dump(dados_modelo, f_out, indent=4, ensure_ascii=False)

async def chamar_llama_api(prompt, json_mode=True):
    try:
        response = await client.chat.completions.create(
            model="llama3.2:3b",
            messages=[{"role": "user", "content": prompt}],
            temperature=TEMPERATURE,
            extra_query=EXTRA_OPTIONS,
            response_format={"type": "json_object"} if json_mode else None
        )
        content = response.choices[0].message.content
        return json.loads(content) if json_mode else content
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    asyncio.run(workflow())