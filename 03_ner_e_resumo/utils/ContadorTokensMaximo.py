import json
from pathlib import Path
import numpy as np
from core.paths import  PREPROCESSAMENTO_DATA
# Ajuste os caminhos conforme seu ambiente
# CAMINHO_ENTRADA = NER_DATA / "reddit_50_notebooks_w_componentsV2.json"
CAMINHO_ENTRADA = PREPROCESSAMENTO_DATA / "limpo_amostras_filtrados" / "reddit_amostra_limpa_e_filtrada_V2.json"

def process_comments_len(comments, max_chars=4000):
    formatted = []
    sorted_comments = sorted(comments, key=lambda x: x.get('score', 0), reverse=True)
    current_length = 0
    for c in sorted_comments:
        content = c.get('conteudo_limpo', '').strip()
        if len(content) < 10: continue
        entry = f"COMMENT (Score {c.get('score')}): {content}\n"
        if current_length + len(entry) > max_chars: break
        formatted.append(entry)
        current_length += len(entry)
    return current_length

def analisar_contexto():

    with open(CAMINHO_ENTRADA, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    objetos = [data] if isinstance(data, dict) else data
    tamanhos = []
    contagem_comentarios = []

    post_mais_comentado = {"titulo": "", "quantidade": -1}

    for item in objetos:
        search_group = item.get('modelo_busca_utilizado', 'general')
        for post in item.get('posts', []):
            # Simulando a montagem do prompt final
            len_specs = len(str(post.get('detected_component', {})))
            titulo_atual = post.get('titulo_limpo', 'Sem título')
            len_title = len(post.get('titulo_limpo', ''))
            len_post = len(post.get('conteudo_post_limpo', ''))
            len_comments = process_comments_len(post.get('comentarios', []))
            n_comments = post.get('num_comments', 0)
            
            try:
                n_comments = int(n_comments)
            except (ValueError, TypeError):
                n_comments = 0

            # 2. Lógica para encontrar o MÁXIMO INDIVIDUAL
            if n_comments > post_mais_comentado["quantidade"]:
                post_mais_comentado["quantidade"] = n_comments
                post_mais_comentado["titulo"] = titulo_atual

            # ... (restante do seu cálculo de len_specs, len_comments, etc) ...
            len_comments = process_comments_len(post.get('comentarios', []))
            total_chars = len(str(post.get('detected_component', {}))) + len(titulo_atual) + len_comments + 500
            tamanhos.append(total_chars)
            
            contagem_comentarios.append(n_comments)
            # Contexto total aproximado (incluindo as strings fixas do prompt)
            
            total_chars = len(search_group) + len_specs + len_title + len_post + len_comments + 500 # +500 para as labels fixas
            tamanhos.append(total_chars)

    # Estatísticas
    max_chars = max(tamanhos)
    avg_chars = int(np.mean(tamanhos))
    p95_chars = int(np.percentile(tamanhos, 95)) # 95% dos posts estão abaixo disso
    # Estatísticas de Comentários
    print("-" * 30)
    print("📊 ANÁLISE DE CARACTERES")
    print("-" * 30)
    print(f"Total de posts analisados: {len(tamanhos)}")
    print(f"Média: {avg_chars} chars (~{avg_chars//4} tokens)")
    print(f"Máximo: {max_chars} chars (~{max_chars//4} tokens)")
    print(f"Percentil 95 (P95): {p95_chars} chars (~{p95_chars//4} tokens)")

    print("-" * 30)
    
    # Recomendação
    token_rec = (p95_chars // 4) + 512 # p95 + margem para a resposta da IA
    print(f"💡 Recomendação de num_ctx: {max(2048, token_rec)}")

    print("-" * 30)
    print("🏆 POST COM MAIOR ENGAJAMENTO (INDIVIDUAL)")
    print("-" * 30)
    if post_mais_comentado["quantidade"] >= 0:
        print(f"Título: {post_mais_comentado['titulo']}")
        print(f"Quantidade de comentários: {post_mais_comentado['quantidade']}")
    else:
        print("Nenhum post processado.")
    print("-" * 30)

    
if __name__ == "__main__":
    analisar_contexto()