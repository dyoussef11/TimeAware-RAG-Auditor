import json
import asyncio
from pathlib import Path
from datetime import datetime
from ollama import AsyncClient
from tqdm.asyncio import tqdm

# --- CONFIGURAÇÃO DE CAMINHOS ---
try:
    from core.paths import NER_DATA, VETORIZATION_DATA
    
    DIR_ENTRADA = NER_DATA / 'Base_Conhecimento_Resumida'
    CAMINHO_SAIDA = VETORIZATION_DATA / 'base_conhecimento_multilingueV2.json'
except ImportError:
    DIR_ENTRADA = Path("./data/Base_Conhecimento_Resumida")
    CAMINHO_SAIDA = Path("./data/base_conhecimento_multilingueV2.json")

# Configurações de Processamento
CONCORRENCIA_MAXIMA = 10 
MODELO_EMBEDDING = "bge-m3:latest"

async def processar_post(client, item, semaphore, pbar):
    """
    Gera o embedding para um texto processado e retorna o objeto estruturado.
    """
    async with semaphore:
        try:
            response = await client.embeddings(
                model=MODELO_EMBEDDING, 
                prompt=item['texto_final']
            )
            
            pbar.update(1)
            
            return {
                'id': item['id'],
                'vector': response['embedding'],
                'original_text': item['texto_final'],
                'date_iso': item['date_iso'],
                'metadata': item['metadata']
            }
        except Exception as e:
            pbar.write(f"❌ Erro no post {item['id']}: {e}")
            pbar.update(1)
            return None

async def gerar_base_vetorial():
    print(f"--- 🚀 INICIANDO VETORIZAÇÃO (BGE-M3) ---")
    
    client = AsyncClient()
    semaphore = asyncio.Semaphore(CONCORRENCIA_MAXIMA)
    
    # 1. Localizar todos os arquivos de conhecimento gerados pelo NER
    arquivos = list(DIR_ENTRADA.glob("*.json"))
    if not arquivos:
        print(f"⚠️ Nenhum arquivo encontrado em {DIR_ENTRADA}")
        return

    fila_trabalho = []

    # 2. Varredura e Montagem da Fila
    for arq_path in arquivos:
        try:
            with open(arq_path, 'r', encoding='utf-8') as f:
                dados_modelo = json.load(f)
        except Exception as e:
            print(f"❌ Erro ao ler {arq_path.name}: {e}")
            continue
        
        # Nome do modelo conforme a raiz do seu JSON
        modelo_ref = dados_modelo.get('modelo_busca_utilizado', 'Unknown Device')
        
        for post in dados_modelo.get('posts', []):
            analise = post.get('analise_ia', {})
            if not analise:
                continue

            # Extração de campos para o texto denso (Melhora recuperação no RAG)
            timeline = analise.get('discussion_timeline', 'N/A')
            ancora = analise.get('ancoragem_temporal', {})
            data_str = ancora.get('data_post', '2024-01-01')

            # Estruturação do texto para o embedding
            texto_final = (
                f"TIMELINE: {timeline}. " 
                f"MODEL: {modelo_ref}. "
                f"TITLE: {post.get('titulo', 'Untitled')}. "
                f"INTENT: {analise.get('intent', 'N/A')}. "
                f"SEVERITY: {analise.get('technical_severity', 'N/A')}. "
                f"FAULT: {analise.get('detected_fault', 'N/A')}. "
                f"SUMMARY: {analise.get('summary', 'N/A')}. "
                f"RESOLUTION: {analise.get('suggested_solution', 'N/A')}."
            ).strip()

            fila_trabalho.append({
                'id': post.get('id'),
                'texto_final': texto_final,
                'date_iso': data_str,
                'metadata': {
                    'title': post.get('titulo', 'Untitled Post'),
                    'data_str':data_str,  
                    'model': modelo_ref,
                    'severity': analise.get('technical_severity', 'N/A'),
                    'fault': analise.get('detected_fault', 'N/A'),
                    'category': post.get('categoria', 'general'),
                    'timeline': timeline
                }
            })

    # 3. Execução Assíncrona dos Embeddings
    total_posts = len(fila_trabalho)
    print(f"📦 Total de posts para vetorizar: {total_posts}")

    with tqdm(total=total_posts, desc="Vetorizando", unit="post") as pbar:
        tasks = [processar_post(client, item, semaphore, pbar) for item in fila_trabalho]
        resultados = await asyncio.gather(*tasks)

    # 4. Consolidação e Salvamento
    base_conhecimento = [r for r in resultados if r is not None]

    if base_conhecimento:
        CAMINHO_SAIDA.parent.mkdir(parents=True, exist_ok=True)
        with open(CAMINHO_SAIDA, 'w', encoding='utf-8') as f:
            json.dump(base_conhecimento, f, ensure_ascii=False, indent=4)
        print(f"\n✨ SUCESSO! {len(base_conhecimento)} vetores salvos em: {CAMINHO_SAIDA}")

if __name__ == "__main__":
    asyncio.run(gerar_base_vetorial())