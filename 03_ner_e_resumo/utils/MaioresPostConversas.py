import json
from pathlib import Path
from tqdm import tqdm

# --- CONFIGURAÇÃO DE AMBIENTE ---
try:
    from core.paths import PREPROCESSAMENTO_DATA, NER_DATA
    CAMINHO_ENTRADA_JSON = PREPROCESSAMENTO_DATA / 'limpo_amostras_filtrados' / 'reddit_amostra_157_filtrada_limpa_V3.json'
    # Define o caminho do arquivo de saída no diretório NER_DATA
    CAMINHO_SAIDA_TXT = NER_DATA / 'ranking_posts_extensos.txt'
except ImportError:
    CAMINHO_ENTRADA_JSON = Path("data/reddit_amostra_157_filtrada_limpa_V3.json")
    CAMINHO_SAIDA_TXT = Path("ranking_posts_extensos.txt")

def identificar_posts_extensos(top_n=1000):
    if not CAMINHO_ENTRADA_JSON.exists():
        print(f"❌ Arquivo não encontrado: {CAMINHO_ENTRADA_JSON}")
        return

    print(f"🔍 Analisando volume de texto em: {CAMINHO_ENTRADA_JSON.name}")
    
    with open(CAMINHO_ENTRADA_JSON, 'r', encoding='utf-8') as f:
        notebooks = json.load(f)

    ranking_posts = []

    for notebook in notebooks:
        modelo = notebook.get('modelo_limpo') or notebook.get('modelo_original') or "Laptop"
        for post in notebook.get('posts', []):
            p_id = post.get('id', 'N/A')
            titulo = post.get('titulo', '')
            conteudo_op = post.get('conteudo_limpo', '')
            
            len_comentarios = sum(len(c.get('conteudo_limpo', '')) for c in post.get('comentarios', []))
            total_chars = len(titulo) + len(conteudo_op) + len_comentarios
            
            ranking_posts.append({
                "id": p_id,
                "modelo": modelo,
                "titulo": titulo[:100].replace('\n', ' ') + "...",
                "chars_op": len(conteudo_op),
                "chars_coments": len_comentarios,
                "total": total_chars,
                "tokens_est": total_chars // 4
            })

    ranking_ordenado = sorted(ranking_posts, key=lambda x: x['total'], reverse=True)

    # --- GRAVAÇÃO NO ARQUIVO TXT ---
    with open(CAMINHO_SAIDA_TXT, 'w', encoding='utf-8') as out:
        out.write("="*70 + "\n")
        out.write(f"🏆 RANKING: TOP {top_n} POSTS COM MAIOR CARGA DE TEXTO\n")
        out.write("="*70 + "\n\n")

        for i, p in enumerate(ranking_ordenado[:top_n], 1):
            out.write(f"{i}º | ID: {p['id']} | TOTAL: {p['total']:,} chars (~{p['tokens_est']:,} tokens)\n")
            out.write(f"   Modelo: {p['modelo']}\n")
            out.write(f"   Título: {p['titulo']}\n")
            out.write(f"   [OP: {p['chars_op']:,} chars | Comentários: {p['chars_coments']:,} chars]\n")
            out.write("-" * 70 + "\n")

        if ranking_ordenado:
            media_total = sum(p['total'] for p in ranking_ordenado) / len(ranking_ordenado)
            out.write(f"\n📊 RESUMO GERAL:\n")
            out.write(f"   - Total de posts analisados: {len(ranking_ordenado)}\n")
            out.write(f"   - Média de caracteres por post: {media_total:.0f}\n")
            out.write(f"   - Post mais pesado: {ranking_ordenado[0]['total']:,} chars\n")
            out.write("="*70 + "\n")

    print(f"✅ Sucesso! Ranking exportado para: {CAMINHO_SAIDA_TXT}")

if __name__ == "__main__":
    identificar_posts_extensos(top_n=1000)